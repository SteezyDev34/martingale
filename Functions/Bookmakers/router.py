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

# Demarre le bridge WebSocket dedie Stake (port 9101, cf. StakeBridge.py) des
# l'import de ce module — sans ca, StakeScraper.is_connected() reste toujours
# False dans ce process (celui qui place reellement les paris, via
# ProcessTelegramBets.py) et retombe silencieusement sur l'ancien Selenium,
# meme si le bridge tourne par ailleurs dans le process du watcher
# (SCRIPTS_WATCH/main-1.py via session_init.py). wait_timeout=10 (pas 0) :
# constate en prod le 2026-10-16 -- le tout premier pari traite juste apres
# le demarrage du process voyait is_connected()=False (extension pas encore
# connectee) et retombait sur Selenium, une fraction de seconde avant que
# l'extension se connecte reellement. Cette attente bloquante ne coute que
# quelques secondes une seule fois a l'import (StakeBridge.start_stake_bridge
# est idempotent) ; si l'extension n'est vraiment pas disponible, wait_connected
# leve TimeoutError, capture ci-dessous, et le fallback Selenium s'applique
# normalement pour tous les paris (comme avant ce fix).
try:
    from Functions.Bookmakers.StakeBridge import start_stake_bridge
    start_stake_bridge(wait_timeout=10)
except Exception as e:
    log(f"⚠️ Démarrage StakeBridge échoué (fallback Selenium): {e}", "warning")

# Meme chose pour le bridge 1xBet general (websocket_server.bridge, utilise par
# XBetScraper) : sans ca, "Extension Chrome non connectee" systematique dans ce
# process (constate le 2026-10-16, XBetScraper._fetch_odds_sync echoue direct).
# Port dedie 9102 (pas le 9999 par defaut) : le watcher (SCRIPTS_WATCH/main-1.py)
# tourne deja sur 9999 en parallele, meme port = collision au bind si les deux
# process tournent en meme temps (cas normal en prod).
try:
    from websocket_server import start_bridge as _start_xbet_bridge, bridge as _xbet_bridge
    _start_xbet_bridge(wait_timeout=10, port=9102)
    # Ouvre/enregistre l'onglet dedie a CE process (meme principe que les scripts
    # SCRIPTS_1530A/SCRIPTS_4P6P au demarrage) -- sans ca, _tab_id reste None et
    # _search_and_open_match (OneXBetBridge.py, clique un bouton recherche)
    # echoue tout de suite en "no_tab" : aucune fenetre ne s'ouvrait jamais,
    # "match_not_found" quasi instantane sans recherche reelle (constate 2026-10-16).
    import config as _config
    import time as _time
    # Version mobile, pas desktop : partout ailleurs dans le bot (recherche de
    # match, page de match individuelle, placement), ScriptRechercheDeMatch.py
    # bascule systematiquement en ?platform_type=mobile des qu'il s'agit
    # d'autre chose que lister des ligues -- le bouton de recherche
    # (.home-navigation__link--search, 1xbet.js) est vraisemblablement propre
    # au DOM mobile (constate le 2026-10-16 : clic sans effet en desktop).
    _xbet_search_url = _config.site_url.replace('?platform_type=desktop', '').replace('?platform_type=mobile', '') + '?platform_type=mobile'
    _xbet_bridge.navigate(_xbet_search_url)
    # Laisse la page se charger avant le premier clic (meme pattern que
    # _bridge_recherche_match dans ScriptRechercheDeMatch.py) -- sans ca, le
    # tout premier pari traite juste apres le demarrage tombait sur un timeout
    # de click_search_button (page encore en cours de chargement, constate le
    # 2026-10-16).
    _time.sleep(2)
except Exception as e:
    log(f"⚠️ Démarrage bridge 1xBet échoué: {e}", "warning")

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
    "Stake":    {"enabled": False, "balance": None},
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
    # Tous les résultats reçus (cote trouvée ou non), pour pouvoir diagnostiquer
    # POURQUOI aucune cote n'a été trouvée si `results` finit vide -- avant ce
    # correctif, un résultat sans cote (ex: error="match_not_found") était jeté
    # silencieusement (constaté le 2026-10-18, BetTrace enregistrait
    # error:null/bookmaker:null pour ces cas). Exposé sur `bet` (pattern déjà
    # utilisé ailleurs, cf. bet['_xbet_match_url']) plutôt que de changer la
    # signature de cette fonction (son seul appelant est place_best_bet).
    attempts = []

    with ThreadPoolExecutor(max_workers=len(active_scrapers)) as executor:
        futures = {
            executor.submit(_fetch_odds_sync, cls, bet): cls.name
            for cls in active_scrapers
        }
        for future in futures:
            bk_name = futures[future]
            try:
                result = future.result(timeout=120)
                attempts.append(result)
                if result.get("odds"):
                    results.append(result)
                    log(f"[Router] {result['bookmaker']}: {result['odds']}", "info")
                else:
                    log(f"[Router] {bk_name}: pas de cote ({result.get('error', 'raison inconnue')})", "warning")
            except Exception as e:
                log(f"[Router] Erreur scraper {bk_name}: {e}", "error")
                attempts.append({"bookmaker": bk_name, "odds": None, "error": str(e)})

    bet['_odds_attempts'] = attempts

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


def place_combined_bet(matches_list: List[Dict], mise: float, trace_dir: str = None) -> Dict:
    """
    Place un pari combiné (accumulateur) sur Lollybet.
    matches_list : liste de dicts match (equipe_1, equipe_2, selection, sport, date, intitule, categorie)
    """
    if not _is_bookmaker_active("Lollybet"):
        log("[Router] ❌ Lollybet désactivé — impossible de placer le combiné", "error")
        return {"bookmaker": "Lollybet", "success": False, "error": "lollybet_disabled"}

    bet = {"is_combined": True, "matches_list": matches_list, "mise": mise, "trace_dir": trace_dir}
    log(f"[Router] 🎯 Placement combiné {len(matches_list)} legs sur Lollybet", "info")
    return _place_bet_sync(LollybetScraper, bet)


def place_best_bet(bet: Dict) -> Dict:
    """
    Point d'entrée principal appelé depuis process_api_bets.
    1. Enrichit le pari avec les défis actifs (IA)
    2. Défi détecté → placement direct sur le bookmaker du défi
    3. 1xBet prioritaire : si trouvé avec une cote, pari direct dessus (pas de comparaison)
    4. Sinon, comparaison sur tous les bookmakers actifs (Playwright + 1xBet via l'extension Chrome)
    5. Place le pari sur le meilleur bookmaker
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
            result = _place_bet_sync(scraper_map[target_bk], bet)
            if result.get("success"):
                return result
            log(
                f"[Router] Échec placement défi sur {target_bk} ({result.get('error', 'raison inconnue')}) "
                f"— repli sur la comparaison multi-bookmaker", "warning"
            )

    # 1xBet en priorité stricte (demandé le 2026-10-16) : s'il trouve le match
    # avec une cote valide, on parie direct dessus sans comparer aux autres
    # bookmakers. Sinon (match non trouvé, erreur), on retombe sur la
    # comparaison multi-bookmaker ci-dessous comme avant.
    if _is_bookmaker_active("1xBet"):
        xbet_odds = _fetch_odds_sync(XBetScraper, bet)
        if xbet_odds.get("odds"):
            log(f"[Router] 🎯 1xBet prioritaire @ {xbet_odds['odds']}", "info")
            return _place_bet_sync(XBetScraper, bet)
        else:
            log(f"[Router] 1xBet prioritaire sans cote ({xbet_odds.get('error')}) — comparaison multi-bookmaker", "info")

    # Comparaison multi-bookmaker : récupérer les cotes sur tous
    best = get_best_odds(bet)
    if not best:
        attempts = bet.get('_odds_attempts', [])
        if attempts:
            reasons = "; ".join(f"{a.get('bookmaker', '?')}:{a.get('error') or 'pas de cote'}" for a in attempts)
        else:
            reasons = "aucun bookmaker actif"
        log(f"[Router] ❌ Aucune cote trouvée ({reasons})", "error")
        return {"bookmaker": None, "success": False, "error": f"no_odds_found: {reasons}"}

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
        return {"bookmaker": None, "success": False, "error": f"unknown_bookmaker:{best['bookmaker']}"}

    log(f"[Router] 🎯 Placement sur {best['bookmaker']} @ {best['odds']}", "info")
    return _place_bet_sync(target_cls, bet)
