# -*- coding: utf-8 -*-
"""
BookmakerRouter — orchestre la recherche des meilleures cotes sur tous les bookmakers,
détecte les défis actifs et place le pari sur le bookmaker optimal.
"""
import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Functions.Bookmakers.WinamaxScraper import WinamaxScraper
from Functions.Bookmakers.BetclicScraper import BetclicScraper
from Functions.Bookmakers.LollybetScraper import LollybetScraper
from Functions.Bookmakers.StakeScraper import StakeScraper
from Functions.Bookmakers.XBetScraper import XBetScraper
from Functions.BetLabelsDB import get_all_challenges_for_prompt
from Functions.Logs.Logger import log

# Bookmakers sans VPN — lancés en parallèle (Lollybet mis de côté, désactivé via BOOKMAKER_STATE)
NO_VPN_SCRAPERS = [WinamaxScraper, BetclicScraper]

# Bookmakers nécessitant le VPN Toronto — lancés séquentiellement après le groupe sans VPN
VPN_SCRAPERS = [StakeScraper]

# Liste complète pour les autres usages (refresh challenges, etc.) — hors 1xBet
# qui n'a pas de "challenges" et ne passe pas par Playwright.
PLAYWRIGHT_SCRAPERS = NO_VPN_SCRAPERS + VPN_SCRAPERS

# État des bookmakers : enabled (actif) + balance (solde connu)
# Modifiables à la volée depuis n'importe quel module via router.BOOKMAKER_STATE
BOOKMAKER_STATE: Dict[str, Dict] = {
    "Winamax":  {"enabled": False,  "balance": None},
    "Betclic":  {"enabled": False,  "balance": None},
    "Lollybet": {"enabled": False, "balance": None},
    "Stake":    {"enabled": True,  "balance": None},
    "1xBet":    {"enabled": True,  "balance": None},
}


def _is_bookmaker_active(name: str) -> bool:
    """Retourne False si le bookmaker est désactivé ou si son solde est à 0."""
    state = BOOKMAKER_STATE.get(name, {})
    if not state.get("enabled", True):
        log(f"[Router] ⏭ {name} ignoré (désactivé)", "info")
        return False
    balance = state.get("balance")
    if balance is not None and float(balance) <= 0:
        log(f"[Router] ⏭ {name} ignoré (solde nul : {balance})", "info")
        return False
    return True


def _fetch_odds_sync(scraper_class, bet: Dict) -> Dict:
    """Récupère uniquement la cote (sans placer le pari)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        scraper = scraper_class()
        return loop.run_until_complete(scraper.fetch_odds(bet))
    except Exception as e:
        return {"bookmaker": getattr(scraper_class, 'name', '?'), "odds": None, "error": str(e)}
    finally:
        loop.close()


def _place_bet_sync(scraper_class, bet: Dict) -> Dict:
    """Place le pari sur un bookmaker donné."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        scraper = scraper_class()
        return loop.run_until_complete(scraper.run(bet))
    except Exception as e:
        return {"bookmaker": getattr(scraper_class, 'name', '?'), "odds": None, "success": False, "error": str(e)}
    finally:
        loop.close()


ALL_SCRAPERS = [WinamaxScraper, BetclicScraper, LollybetScraper, StakeScraper, XBetScraper]


def get_best_odds(bet: Dict) -> Optional[Dict]:
    """
    Récupère les cotes sur tous les bookmakers actifs (enabled=True, balance>0) en parallèle,
    retourne le dict du bookmaker avec la meilleure cote (sans placer le pari).
    """
    active_scrapers = [cls for cls in ALL_SCRAPERS if _is_bookmaker_active(cls.name)]
    if not active_scrapers:
        log("[Router] Aucun bookmaker actif disponible", "warning")
        return None

    results = []

    with ThreadPoolExecutor(max_workers=len(active_scrapers)) as executor:
        futures = {
            executor.submit(_fetch_odds_sync, cls, bet): cls.name
            for cls in active_scrapers
        }
        for future in futures:
            try:
                result = future.result(timeout=120)
                if result.get("odds"):
                    results.append(result)
                    log(f"[Router] {result['bookmaker']}: {result['odds']}", "info")
            except Exception as e:
                log(f"[Router] Erreur scraper {futures[future]}: {e}", "error")

    if not results:
        log("[Router] Aucune cote trouvée", "warning")
        return None

    # Priorité : défi activé > meilleure cote
    with_challenge = [r for r in results if r.get("challenge_activated")]
    if with_challenge:
        best = max(with_challenge, key=lambda r: r["odds"] or 0)
    else:
        best = max(results, key=lambda r: r["odds"] or 0)

    log(f"[Router] ✅ Meilleure cote: {best['bookmaker']} @ {best['odds']}", "info")
    return best


def refresh_all_challenges():
    """
    Re-scrappe les défis de tous les bookmakers et met à jour la DB.
    À appeler périodiquement (ex: au démarrage du script ou toutes les heures).
    """
    async def _refresh_one(scraper_class):
        try:
            from playwright.async_api import async_playwright
            scraper = scraper_class()
            async with async_playwright() as pw:
                browser = await scraper.get_browser(pw)
                page = browser.pages[0] if browser.pages else await browser.new_page()
                try:
                    if not await scraper.is_logged_in(page):
                        await scraper.login(page)
                    challenges = await scraper.get_challenges(page)
                    log(f"[Router] {scraper.name}: {len(challenges)} défi(s) rafraîchi(s)", "info")
                finally:
                    await browser.close()
        except Exception as e:
            log(f"[Router] Erreur refresh challenges {scraper_class.name}: {e}", "error")

    def _run(cls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_refresh_one(cls))
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=len(PLAYWRIGHT_SCRAPERS)) as executor:
        list(executor.map(_run, PLAYWRIGHT_SCRAPERS))


def enrich_bet_with_challenges(bet: Dict, openai_client=None) -> Dict:
    """
    Injecte les défis actifs dans le pari et demande à l'IA si un défi correspond.
    Retourne le pari enrichi avec 'matched_challenge' si trouvé.
    """
    challenges_text = get_all_challenges_for_prompt()
    if challenges_text == "Aucun défi actif." or not openai_client:
        return bet

    try:
        prompt = (
            f"Voici un pari sportif :\n"
            f"Match: {bet.get('equipe_1')} vs {bet.get('equipe_2')}\n"
            f"Sélection: {bet.get('selection')}\n"
            f"Sport: {bet.get('sport')}\n"
            f"Cote: {bet.get('odds')}\n\n"
            f"Voici les défis actifs sur les bookmakers (format: BOOKMAKER | TITRE | CONDITION) :\n"
            f"{challenges_text}\n\n"
            f"Ce pari correspond-il à un des défis listés ? "
            f"Si oui, retourne un JSON : {{\"matched\": true, \"bookmaker\": \"...\", \"challenge_title\": \"...\", \"reason\": \"...\"}}. "
            f"Si non, retourne : {{\"matched\": false}}. Réponds uniquement avec le JSON."
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Nettoyer le JSON
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        result = json.loads(content)
        if result.get("matched"):
            bet["matched_challenge"] = result
            log(f"[Router] 🎯 Défi détecté par IA: {result.get('challenge_title')} sur {result.get('bookmaker')}", "info")
    except Exception as e:
        log(f"[Router] Erreur détection défi IA: {e}", "warning")

    return bet


def place_combined_bet(matches_list: List[Dict], mise: float) -> Dict:
    """
    Place un pari combiné (accumulateur) sur Lollybet.
    matches_list : liste de dicts match (equipe_1, equipe_2, selection, sport, date, intitule, categorie)
    """
    if not _is_bookmaker_active("Lollybet"):
        log("[Router] ❌ Lollybet désactivé — impossible de placer le combiné", "error")
        return {"bookmaker": "Lollybet", "success": False, "error": "lollybet_disabled"}

    bet = {"is_combined": True, "matches_list": matches_list, "mise": mise}
    log(f"[Router] 🎯 Placement combiné {len(matches_list)} legs sur Lollybet", "info")
    return _place_bet_sync(LollybetScraper, bet)


def place_best_bet(bet: Dict) -> Dict:
    """
    Point d'entrée principal appelé depuis process_api_bets.
    1. Enrichit le pari avec les défis actifs (IA)
    2. Lance la comparaison sur tous les bookmakers actifs (Playwright + 1xBet via l'extension Chrome)
    3. Place le pari sur le meilleur bookmaker
    Retourne un dict résultat.
    """
    # Pari combiné sur le même match → Stake uniquement (MyMatch)
    if bet.get("combined_events"):
        log(f"[Router] 🎯 Pari Same Game Multi détecté → Stake uniquement: {bet.get('combined_label', '')}", "info")
        if _is_bookmaker_active("Stake"):
            return _place_bet_sync(StakeScraper, bet)
        else:
            log("[Router] ❌ Stake désactivé ou solde nul — impossible de placer le MyMatch", "error")
            return {"bookmaker": "Stake", "success": False, "error": "stake_disabled"}

    # Optionnel : enrichir avec les défis (nécessite OpenAI client)
    try:
        import config
        if hasattr(config, 'openai_client'):
            bet = enrich_bet_with_challenges(bet, config.openai_client)
    except Exception:
        pass

    # Si un défi a été détecté par l'IA sur un bookmaker spécifique → placer directement là
    matched_challenge = bet.get("matched_challenge", {})
    if matched_challenge.get("matched"):
        target_bk = matched_challenge.get("bookmaker", "")
        scraper_map = {
            "Winamax": WinamaxScraper,
            "Betclic": BetclicScraper,
            "Lollybet": LollybetScraper,
        }
        if target_bk in scraper_map and _is_bookmaker_active(target_bk):
            log(f"[Router] Placement direct sur {target_bk} (défi détecté)", "info")
            result = _run_scraper_sync(scraper_map[target_bk], bet)
            if result.get("success"):
                return result

    # Comparaison multi-bookmaker : récupérer les cotes sur tous
    best = get_best_odds(bet)
    if not best:
        log("[Router] ❌ Aucune cote trouvée", "error")
        return {"bookmaker": None, "success": False}

    # Placer le pari uniquement sur le meilleur bookmaker
    scraper_map = {
        "Winamax":  WinamaxScraper,
        "Betclic":  BetclicScraper,
        "Lollybet": LollybetScraper,
        "Stake":    StakeScraper,
        "1xBet":    XBetScraper,
    }
    target_cls = scraper_map.get(best["bookmaker"])
    if not target_cls:
        log(f"[Router] ❌ Bookmaker inconnu: {best['bookmaker']}", "error")
        return {"bookmaker": None, "success": False}

    log(f"[Router] 🎯 Placement sur {best['bookmaker']} @ {best['odds']}", "info")
    return _place_bet_sync(target_cls, bet)
