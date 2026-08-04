# -*- coding: utf-8 -*-
"""
Scraper Selenium pour Stake.bet — fenêtre 11 du driver partagé (port 43151).
VPN requis (Toronto / Canada).
DOM standard (pas de shadow root).
"""
import os
import json
import time
import random
from typing import Optional, List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Functions.BetLabelsDB import get_label
from Functions.Logs.Logger import log


# ── Résolution IA des labels Stake ──────────────────────────────────────────

def _get_anthropic_client():
    """Retourne un client Anthropic initialisé depuis la variable d'env."""
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", "")
        if not api_key:
            return None
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


def _ai_resolve_match(candidates: List[Dict], equipe_1: str, equipe_2: str) -> Optional[str]:
    """
    Demande à Claude de choisir le bon match parmi les résultats de recherche.
    candidates = [{"text": "Panama\nAngleterre", "url": "https://..."}]
    Retourne l'URL du match ou None.
    """
    client = _get_anthropic_client()
    if not client or not candidates:
        return None
    try:
        lines = "\n".join(
            f"{i+1}. [{c['text'].strip()[:60]}] → {c['url']}"
            for i, c in enumerate(candidates)
        )
        prompt = (
            f"Je cherche le match de sport entre '{equipe_1}' et '{equipe_2}'.\n"
            f"Voici les résultats trouvés sur Stake.bet :\n{lines}\n\n"
            f"Quel numéro correspond au bon match ? "
            f"Réponds uniquement avec le numéro (ex: 1) ou 'aucun' si rien ne correspond."
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = resp.content[0].text.strip().lower()
        if answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(candidates):
                log(f"[Stake AI] ✅ Match résolu: {candidates[idx]['text'].strip()[:50]}", "info")
                return candidates[idx]["url"]
    except Exception as e:
        log(f"[Stake AI] Erreur résolution match: {e}", "warning")
    return None


def _ai_resolve_outcome(available_outcomes: List[str], event: Dict) -> Optional[str]:
    """
    Demande à Claude de choisir le bon bouton parmi les outcomes disponibles.
    available_outcomes = ["Angleterre\n1,15", "Kane, Harry\n1,49", ...]
    event = {"intitule": "Buteur Harry Kane", "selection": "Harry Kane", "type_de_pari": "..."}
    Retourne le label (première ligne du texte bouton) du bon outcome, ou None.
    """
    client = _get_anthropic_client()
    if not client or not available_outcomes:
        return None
    try:
        labels = [o.split("\n")[0].strip() for o in available_outcomes]
        lines  = "\n".join(f"{i+1}. {l}" for i, l in enumerate(labels))
        equipe_ctx = ""
        if event.get("equipe_1") and event.get("equipe_2"):
            e1, e2 = event["equipe_1"], event["equipe_2"]
            equipe_ctx = (
                f"Match : {e1} (équipe 1 / domicile) vs {e2} (équipe 2 / extérieur).\n"
                f"Double Chance : 1X = {e1} gagne OU nul | X2 = nul OU {e2} gagne | 12 = {e1} OU {e2} gagne (pas de nul).\n"
            )
        betting_glossary = (
            "=== GLOSSAIRE PARIS SPORTIFS (1XBET / Stake) ===\n"
            "\n"
            "RÉSULTAT (1x2):\n"
            "  V1 / 1 / W1 / Home Win / Victoire 1 / Équipe 1 gagne = victoire domicile\n"
            "  X / N / Draw / Nul / Match Nul = match nul\n"
            "  V2 / 2 / W2 / Away Win / Victoire 2 / Équipe 2 gagne = victoire extérieur\n"
            "\n"
            "DOUBLE CHANCE (Double chance):\n"
            "  1X / DC 1X = domicile OU nul\n"
            "  X2 / 2X / DC X2 = nul OU extérieur — NE PAS confondre avec V2 seul !\n"
            "  12 / DC 12 = domicile OU extérieur (pas de nul)\n"
            "\n"
            "TOTAUX BUTS (Total / Over-Under):\n"
            "  'Total Plus de N' = Over N = O N = +N = plus de N buts au total\n"
            "  'Total Moins de N' = Under N = U N = -N = moins de N buts au total\n"
            "  'Total Individuel 1 Plus de N' = plus de N buts par l'équipe 1\n"
            "  'Total Individuel 2 Plus de N' = plus de N buts par l'équipe 2\n"
            "  Exemples : Total Plus de 0.5 / 1.5 / 2.5 / 3.5 / 4.5 / 5 ...\n"
            "\n"
            "BOTH TEAMS TO SCORE (Les deux équipes vont marquer):\n"
            "  BTTS Oui / Les deux équipes vont marquer - Oui / Both Score Yes = les 2 marquent\n"
            "  BTTS Non / Les deux équipes vont marquer - Non / Both Score No = au moins 1 ne marque pas\n"
            "  'Chaque Equipe va marquer 2 Ou Plus - Oui' = les 2 marquent ≥2 buts\n"
            "\n"
            "HANDICAP EUROPÉEN (Handicap):\n"
            "  'Handicap 1 (+N)' = équipe 1 avec +N buts d'avantage\n"
            "  'Handicap 1 (-N)' = équipe 1 doit gagner par plus de N buts\n"
            "  'Handiсap 2 (+N)' = équipe 2 avec +N buts d'avantage\n"
            "  'Handiсap 2 (-N)' = équipe 2 doit gagner par plus de N buts\n"
            "\n"
            "HANDICAP ASIATIQUE (Handicap asiatique):\n"
            "  'Handicap 1 (0)' / AH 0 / Draw No Bet / DNB / Remboursé si nul = remboursé si nul\n"
            "  'Handicap 1 (-0.5)' = équipe 1 doit gagner (pas de nul)\n"
            "  'Handicap 1 (+0.5)' = équipe 1 gagne si victoire OU nul\n"
            "  'Handicap 1 (-0.25)' / (-0.75) / (-1.25) = quart de handicap asiatique\n"
            "\n"
            "TOTAL ASIATIQUE (Total Asiatique):\n"
            "  Fonctionne comme Over/Under mais avec remboursement partiel sur la ligne exacte\n"
            "\n"
            "PROCHAIN BUT (Prochain But):\n"
            "  'Equipe 1 va marquer le prochain But N' = équipe 1 marque le Nème but\n"
            "  'Equipe 2 va marquer le prochain But N' = équipe 2 marque le Nème but\n"
            "  'Aucune Equipe ne va marquer le prochain But N' = pas de Nème but\n"
            "\n"
            "SCORE EXACT (Score exact):\n"
            "  'Score exact 0-0', '1-0', '0-1', '1-1', '2-0', '2-1', '0-2' etc.\n"
            "\n"
            "PAIR/IMPAIR (Pair/Impair):\n"
            "  Pair / Even = nombre de buts pair (0, 2, 4...)\n"
            "  Impair / Odd = nombre de buts impair (1, 3, 5...)\n"
            "\n"
            "MI-TEMPS:\n"
            "  1ère mi-temps = 1MT = HT = résultat/total de la 1ère mi-temps\n"
            "  2ème mi-temps = 2MT = résultat/total de la 2ème mi-temps\n"
            "  Mi-Temps/Final / MT-Fin = combiné résultat MT + résultat final\n"
            "\n"
            "BUTEURS (Statistiques des joueurs):\n"
            "  '[Joueur] va marquer un but à tout moment - Oui' = buteur anytime\n"
            "  '[Joueur] va marquer un but, remplacements compris - Oui' = buteur remplaçant inclus\n"
            "  'Va marquer le premier But [Joueur]' = premier buteur\n"
            "  'Va marquer le dernier But [Joueur]' = dernier buteur\n"
            "  '[Joueur] Va marquer Plus de (1.5)' = marque 2 buts ou plus\n"
            "  Noms inversés sur Stake : 'Harry Kane' → 'Kane, Harry'\n"
            "\n"
            "CORNERS (Corners):\n"
            "  'Total Plus/Moins de N. Corners' = total corners\n"
            "  'Handicap asiatique. Corners' = handicap sur les corners\n"
            "\n"
            "TENNIS (labels Stake réels) :\n"
            "  Vainqueur match : bouton = nom du joueur ex. 'Vukic, Aleksandar' ou 'Brooksby, Jenson'\n"
            "  '1st set - vainqueur' / '2nd set - vainqueur' : bouton = nom du joueur\n"
            "  'Set handicap' : boutons '1.5' / '-1.5' (positif = joueur 1, négatif = joueur 2)\n"
            "  'Jeux handicap' : boutons '3.5'/'-3.5', '4.5'/'-4.5', '5.5'/'-5.5'\n"
            "  'Total jeux' : 'Plus de 37.5' / 'Moins de 37.5' (ou 38.5, 39.5...)\n"
            "  '1st set - total jeux' : 'Plus de 8.5' / 'Moins de 8.5' (ou 9.5, 10.5...)\n"
            "  'Total sets' : 'Plus de 3.5' / 'Moins de 3.5' / 'Plus de 4.5' / 'Moins de 4.5'\n"
            "  'Nombre exact de sets' : bouton '3' / '4' / '5'\n"
            "  '[Joueur] total jeux' : 'Plus de 18.5' / 'Moins de 18.5'\n"
            "  '[Joueur] remporte un set' : 'oui' / 'non'\n"
            "  '[Joueur] gagnera exactement 1 set' / '2 sets' : 'oui' / 'non'\n"
            "  'Vainqueur et total' : 'Joueur & plus de 38.5' / 'Joueur & moins de 38.5'\n"
            "  'Résulat double (1er set/match)' : ex. 'VUK/VUK' = gagne 1er set ET match\n"
            "  Scores en sets 1XBET → Stake : 'Victoire en Sets 2-0' / '2-1' = 'Score correct' 2-0 ou 2-1\n"
            "  Aces / Breaks : 'Total Plus/Moins de N. Aces' / 'Total Plus/Moins de N. Breaks'\n"
            "\n"
            "BASKETBALL (labels Stake réels) :\n"
            "  'Vainqueur (prolongations incluses)' : bouton = nom de l'équipe\n"
            "  'Handicap (prolongations incluses)' : '-5'/'+5', '-5.5'/'+5.5' etc.\n"
            "  'Total (prolongations incluses)' : 'Plus de 179.5' / 'Moins de 179.5'\n"
            "  '[Equipe] total (prolongations incluses)' : 'Plus de 93.5' / 'Moins de 93.5'\n"
            "  'Mi-temps/Fin de match' : 'IND/IND', 'IND/LAS' etc. (abréviations)\n"
            "  'Marge de victoire (inclus prolongations)' : 'par 1-5' / 'par 6-10' / 'par 11 ou +'\n"
            "  'Y aura-t-il des prolongations ?' : 'oui' / 'non'\n"
            "  'Points du joueur (incluent la prolongation)' : '[Joueur] 10+' / '12+' / '14+' etc.\n"
            "  'Rebonds du joueur (incl. prolongations)' : 'Plus de 9.5' / 'Moins de 9.5'\n"
            "  Double-Double / Triple-Double = stats combinées joueur\n"
            "\n"
            "================================================\n"
        )
        prompt = (
            f"{betting_glossary}"
            f"{equipe_ctx}"
            f"Je veux parier sur : '{event.get('intitule', '')}' "
            f"(sélection: '{event.get('selection', '')}', "
            f"type: '{event.get('type_de_pari', '')}').\n\n"
            f"Voici les boutons disponibles sur Stake.bet :\n{lines}\n\n"
            f"Quel numéro correspond à ma sélection ? "
            f"Réponds uniquement avec le numéro (ex: 3) ou 'aucun' si rien ne correspond."
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = resp.content[0].text.strip().lower()
        if answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(labels):
                log(f"[Stake AI] ✅ Outcome résolu: '{labels[idx]}'", "info")
                return labels[idx]
    except Exception as e:
        log(f"[Stake AI] Erreur résolution outcome: {e}", "warning")
    return None

STAKE_URL    = "https://stake.bet"
LOGIN_URL    = "https://stake.bet/?modal=login"
STAKE_WINDOW = 11

SPORTS_MAP = {
    "1": "soccer",
    "2": "tennis",
    "3": "soccer",
    "4": "basketball",
    "5": "rugby",
    "6": "american-football",
    "7": "baseball",
    "8": "handball",
    "9": "ice-hockey",
    "10": "table-tennis",
    "11": "volleyball",
    "12": "boxing",
    "13": "mma",
    "14": "cricket",
    "15": "golf",
    "16": "formula-1",
    "17": "cycling",
    "18": "darts",
    "19": "snooker",
    "20": "futsal",
    "21": "padel",
    "22": "badminton",
    "23": "waterpolo",
    "24": "rugby",
}

SEL_SESSION = [
    "[class*='userBalance']", "[class*='user-balance']",
    "[data-test='balance']", "[class*='HeaderUser']",
    "[class*='walletBalance']", "[class*='wallet-balance']",
    "button[class*='wallet']",
]


def _human_wait(a: float = 0.8, b: float = 1.5):
    import random
    time.sleep(a + random.random() * (b - a))


_CDP_STEALTH = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR','fr','en-US']});
if (!window.chrome) window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
"""


def _clear_type(driver, element, text: str):
    element.click(); time.sleep(0.2)
    try: element.clear()
    except Exception: pass
    driver.execute_script("arguments[0].value='';", element)
    time.sleep(0.15)
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.07, 0.17))


class StakeScraper:
    name = "Stake"
    requires_vpn = False

    def _get_driver(self):
        import config
        from ChromeDriver.SetDriver import get_script_driver
        return get_script_driver(STAKE_WINDOW)

    # ── Session ──────────────────────────────────────────────────────────

    def is_logged_in(self, driver) -> bool:
        try:
            driver.get(STAKE_URL)
            _human_wait(2.5, 3.5)
            for sel in SEL_SESSION:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in els:
                        try:
                            if el.text.strip():
                                log(f"[Stake] Session active ({sel})", "info")
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
            # Si le bouton "Se Connecter" est absent, probablement connecté
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "button")
                btn_texts = []
                for b in btns:
                    try:
                        btn_texts.append(b.text.strip().lower())
                    except Exception:
                        continue
                if not any("connecter" in t for t in btn_texts):
                    log("[Stake] Session active (bouton connexion absent)", "info")
                    return True
            except Exception:
                pass
            return False
        except Exception as e:
            log(f"[Stake] Erreur is_logged_in: {e}", "error")
            return False

    # ── Login automatique ────────────────────────────────────────────────

    def login(self, driver) -> bool:
        """Connexion automatique Stake via modal (3 retries)."""
        email    = os.getenv("STAKE_EMAIL", "")
        password = os.getenv("STAKE_PASSWORD", "")
        if not email or not password:
            log("[Stake] Credentials manquants (STAKE_EMAIL / STAKE_PASSWORD)", "error")
            return False

        driver.set_window_size(1280, 900)
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                                   {"source": _CDP_STEALTH})
        except Exception:
            pass

        for attempt in range(1, 4):
            log(f"[Stake] Tentative {attempt}/3...", "info")
            try:
                if self._attempt_login(driver, email, password):
                    return True
            except Exception as e:
                log(f"[Stake] Erreur tentative {attempt}: {e}", "error")
            if attempt < 3:
                log("[Stake] Rechargement avant retry...", "info")
                driver.get(STAKE_URL)
                _human_wait(3.0, 4.0)

        log("[Stake] Echec apres 3 tentatives", "error")
        return False

    def _attempt_login(self, driver, email: str, password: str) -> bool:
        driver.get(STAKE_URL)
        _human_wait(3.0, 4.5)

        # Clic bouton "Se Connecter"
        se_connecter = None
        for btn in driver.find_elements(By.CSS_SELECTOR, "button"):
            if "connecter" in (btn.text or "").lower():
                se_connecter = btn
                break
        if not se_connecter:
            log("[Stake] Bouton connexion introuvable", "error")
            return False

        driver.execute_script("arguments[0].click();", se_connecter)
        _human_wait(2.0, 3.0)

        # Champs du modal
        email_inp = driver.find_elements(By.CSS_SELECTOR,
            "input[autocomplete*='username'], input[type='email'], input[type='text']")
        pwd_inp   = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")

        if not email_inp or not pwd_inp:
            log("[Stake] Champs login/password introuvables", "error")
            return False

        _clear_type(driver, email_inp[0], email)
        _human_wait(0.4, 0.8)
        _clear_type(driver, pwd_inp[0], password)
        _human_wait(0.4, 0.8)

        # Submit
        submit = None
        for btn in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button"):
            t = btn.text.strip().lower()
            if any(w in t for w in ["connecter", "login", "sign in", "connexion"]):
                submit = btn
                break
        if submit:
            driver.execute_script("arguments[0].click();", submit)
        else:
            pwd_inp[0].send_keys(Keys.RETURN)

        _human_wait(5.0, 7.0)

        # Verif session
        for sel in SEL_SESSION:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                if el.text.strip():
                    log("[Stake] Connexion reussie", "info")
                    return True
        # Bouton connexion toujours present ?
        btns = [b.text.strip().lower() for b in driver.find_elements(By.CSS_SELECTOR, "button")]
        if not any("connecter" in t for t in btns):
            log("[Stake] Connexion reussie (bouton absent)", "info")
            return True

        log("[Stake] Echec connexion", "error")
        return False

    # ── Recherche de match ───────────────────────────────────────────────

    def search_match(self, driver, equipe_1: str, equipe_2: str, sport: str, date: str) -> Optional[str]:
        """
        Cherche un match via la barre de recherche globale de Stake.bet.
        Flux validé par inspection DOM :
          1. Clic sur l'icône loupe (header)
          2. Saisie du nom d'une équipe dans input[placeholder='Rechercher sur Stake.com']
          3. Clic sur le lien match dans les résultats (a.absolute.inset-0 ou a[href*='/sports/'])
        """
        try:
            # ── 0. Naviguer vers la page sport pour filtrer les résultats ──
            sport_slug = SPORTS_MAP.get(str(sport), "soccer")
            sport_url = f"{STAKE_URL}/fr/sports/{sport_slug}/matches/all"
            log(f"[Stake] Navigation sport: {sport_url}", "info")
            driver.get(sport_url)
            _human_wait(4.0, 5.0)

            e1, e2 = equipe_1.lower(), equipe_2.lower()

            # ── 1. Ouvrir la barre de recherche ───────────────────────────
            # Sélecteurs de l'input de recherche (priorité ordre)
            SEARCH_INPUT_SELS = [
                'input.game-search__input',
                '[class*="game-search__input"]',
                'input[placeholder*="Rechercher sur Stake"]',
                'input[placeholder*="Search"]',
            ]

            def _find_search_input():
                for sel in SEARCH_INPUT_SELS:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        return els[0]
                return None

            # Vérifier si l'input est déjà visible
            _human_wait(1.0, 1.5)
            search_input = _find_search_input()

            # Si pas visible, essayer de cliquer le bouton loupe
            if not search_input:
                # Essai 1 : data-testid / class search
                for sel in ['[data-testid="top-search"]', 'button[data-testid*="search"]',
                            '[class*="search-icon"]', '[class*="game-search"]']:
                    btns = driver.find_elements(By.CSS_SELECTOR, sel)
                    for btn in btns:
                        try:
                            driver.execute_script(
                                "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}))", btn)
                            _human_wait(0.8, 1.2)
                            search_input = _find_search_input()
                            if search_input:
                                break
                        except Exception:
                            continue
                    if search_input:
                        break

            # Essai 2 : cliquer bouton anonyme dans SECTION (ancienne méthode)
            if not search_input:
                driver.execute_script("""
                    var SKIP_TESTID = new Set(['coin-toggle','wallet','user-dropdown-toggle','left-sidebar-close']);
                    var SKIP_ARIA  = new Set(['Toggle Notifications Widget','Open Dropdown','Toggle Sidebar']);
                    var all = Array.from(document.querySelectorAll('button'));
                    for (var b of all) {
                        var r = b.getBoundingClientRect();
                        if (r.x <= 0 || r.y < 0 || r.y > 80 || r.width <= 0) continue;
                        var tid = b.getAttribute('data-testid') || '';
                        var aria = b.getAttribute('aria-label') || '';
                        if (SKIP_TESTID.has(tid) || SKIP_ARIA.has(aria)) continue;
                        if (tid || aria) continue;
                        var p = b.parentElement;
                        while (p) {
                            if (p.tagName === 'SECTION') { b.click(); return true; }
                            p = p.parentElement;
                        }
                    }
                    return false;
                """)
                _human_wait(0.8, 1.2)
                search_input = _find_search_input()

            if not search_input:
                log("[Stake] ❌ Barre de recherche non trouvée", "error")
                return None

            log("[Stake] ✅ Barre de recherche trouvée", "info")

            driver.execute_script("""
                arguments[0].focus();
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, key: 'a'}));
            """, search_input, equipe_1)
            _human_wait(2.0, 2.5)

            # ── 3. Cliquer sur "Paris Sportifs" si présent ────────────────
            for btn in driver.find_elements(By.CSS_SELECTOR, "button"):
                if "paris sportifs" in (btn.text or "").lower():
                    driver.execute_script(
                        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}))", btn)
                    _human_wait(0.5, 1.0)
                    break

            # ── 4. Collecter tous les candidats match dans les résultats ──
            candidates = []
            seen_urls = set()
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/sports/']")
            for link in links:
                try:
                    if not link.is_displayed():
                        continue
                    href = (link.get_attribute("href") or "").split("?")[0]
                    text = (link.text or "").strip()
                    # Ignorer les liens de catégorie (pas de slug de match)
                    if not href or href in seen_urls:
                        continue
                    parts = href.rstrip("/").split("/")
                    if len(parts) < 7:  # URL de match = au moins 7 segments
                        continue
                    seen_urls.add(href)
                    candidates.append({"text": text, "url": href})
                except Exception:
                    continue

            if not candidates:
                log(f"[Stake] Aucun candidat match trouvé pour: {equipe_1} vs {equipe_2}", "warning")
                return None

            # ── 5. Match exact d'abord (rapide, sans appel API) ───────────
            for c in candidates:
                t = c["text"].lower()
                href_lower = c["url"].lower()
                e1_slug = e1.replace(" ", "-")
                e2_slug = e2.replace(" ", "-")
                if (e1 in t and e2 in t) or (e1_slug in href_lower and e2_slug in href_lower):
                    log(f"[Stake] ✅ Match exact: {c['text'][:60]}", "info")
                    return c["url"]

            # ── 6. Résolution IA si pas de match exact ────────────────────
            log(f"[Stake] Résolution IA pour: {equipe_1} vs {equipe_2} ({len(candidates)} candidats)", "info")
            url = _ai_resolve_match(candidates, equipe_1, equipe_2)
            if url:
                return url

            log(f"[Stake] Match non trouvé: {equipe_1} vs {equipe_2}", "warning")
            return None
        except Exception as e:
            log(f"[Stake] Erreur search_match: {e}", "error")
            return None

    # ── Cotes ────────────────────────────────────────────────────────────

    def _find_dnb_outcome(self, driver, team_idx: int) -> Optional[float]:
        """Cherche la cote Draw No Bet (Remboursé si match nul) pour team_idx (1 ou 2)."""
        import re as _re
        result = driver.execute_script("""
            var spans = Array.from(document.querySelectorAll('span'));
            var dnbSpan = spans.find(s => s.textContent.trim().toLowerCase().includes('remboursé si match nul')
                                       || s.textContent.trim().toLowerCase().includes('draw no bet'));
            if (!dnbSpan) return null;
            var container = dnbSpan;
            for (var i = 0; i < 10; i++) {
                container = container.parentElement;
                if (!container) break;
                var btns = Array.from(container.querySelectorAll('[data-testid="fixture-outcome"]'));
                if (btns.length >= 2) return btns.map(b => b.innerText.trim());
            }
            return null;
        """)
        if not result:
            return None
        # Dédupliquer en gardant l'ordre
        seen, unique = set(), []
        for t in result:
            key = t.split("\n")[0].strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(t)
        idx = team_idx - 1  # team 1 → index 0, team 2 → index 1
        if idx < len(unique):
            parts = unique[idx].split("\n")
            for p in parts:
                try:
                    v = float(p.replace(",", "."))
                    if 1.01 < v < 200:
                        return v
                except ValueError:
                    pass
        return None

    def get_odds(self, driver, match_url: str, selection: str, categorie: str) -> Optional[float]:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)

            # Handicap X (0) = Draw No Bet pour l'équipe X
            import re as _re
            m = _re.match(r'handicap\s*([12])\s*\(0\)', selection.lower().strip())
            if m:
                team_idx = int(m.group(1))
                v = self._find_dnb_outcome(driver, team_idx)
                if v:
                    log(f"[Stake] ✅ Cote DNB équipe {team_idx}: {v}", "info")
                    return v
                log(f"[Stake] Cote DNB non trouvée pour équipe {team_idx}", "warning")
                return None

            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Stake", sport_id, selection)
            search_label = (label_bk or selection).lower()

            odds_els = driver.find_elements(By.CSS_SELECTOR,
                "[class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']")
            for el in odds_els:
                parent_text = driver.execute_script("""
                    var el = arguments[0].closest('[class*="market"], [class*="Market"], [class*="bet"]');
                    return el ? el.innerText : '';
                """, el)
                if search_label in (parent_text or "").lower():
                    raw = el.text.strip().replace(",", ".")
                    try:
                        v = float(raw)
                        if 1.01 < v < 200:
                            return v
                    except ValueError:
                        pass

            log(f"[Stake] Cote non trouvée pour: {selection}", "warning")
            return None
        except Exception as e:
            log(f"[Stake] Erreur get_odds: {e}", "error")
            return None

    # ── Placement ────────────────────────────────────────────────────────

    def _click_dnb_outcome(self, driver, team_idx: int) -> bool:
        """Clique sur le bouton Draw No Bet pour team_idx (1 ou 2)."""
        clicked = driver.execute_script("""
            var teamIdx = arguments[0];
            var spans = Array.from(document.querySelectorAll('span'));
            var dnbSpan = spans.find(s => s.textContent.trim().toLowerCase().includes('remboursé si match nul')
                                       || s.textContent.trim().toLowerCase().includes('draw no bet'));
            if (!dnbSpan) return false;
            var container = dnbSpan;
            for (var i = 0; i < 10; i++) {
                container = container.parentElement;
                if (!container) break;
                var btns = Array.from(container.querySelectorAll('[data-testid="fixture-outcome"]'));
                if (btns.length >= 2) {
                    // Dédupliquer par premier label
                    var seen = {}, unique = [];
                    for (var b of btns) {
                        var k = b.innerText.trim().split('\\n')[0].trim().toLowerCase();
                        if (!seen[k]) { seen[k] = true; unique.push(b); }
                    }
                    var btn = unique[teamIdx - 1];
                    if (btn) { btn.scrollIntoView({behavior:'instant',block:'center'}); btn.click(); return true; }
                }
            }
            return false;
        """, team_idx)
        return bool(clicked)

    def place_bet(self, driver, match_url: str, selection: str, categorie: str, mise: float) -> bool:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)

            # Handicap X (0) = Draw No Bet pour l'équipe X
            import re as _re
            m = _re.match(r'handicap\s*([12])\s*\(0\)', selection.lower().strip())
            if m:
                team_idx = int(m.group(1))
                if not self._click_dnb_outcome(driver, team_idx):
                    log(f"[Stake] ❌ Bouton DNB équipe {team_idx} non trouvé", "error")
                    return False
                log(f"[Stake] ✅ Clic DNB équipe {team_idx}", "info")
                _human_wait(0.8, 1.5)
                # Saisir la mise et confirmer (code commun en bas)
                clicked = True
            else:
                sport_id = _detect_sport_from_url(match_url)
                label_bk = get_label("Stake", sport_id, selection)
                search_label = (label_bk or selection).lower()

                # Vider le betslip AVANT de cliquer (évite reset post-clic)
                try:
                    reset = driver.find_elements(By.CSS_SELECTOR, '[data-testid="reset-betslip"]')
                    if reset:
                        reset[0].click()
                        time.sleep(0.8)
                except Exception:
                    pass

                bet_btns = driver.find_elements(By.CSS_SELECTOR,
                    "button[class*='outcome'], [class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']")
                clicked = False
                for btn in bet_btns:
                    parent_text = driver.execute_script("""
                        var el = arguments[0].closest('[class*="market"], [class*="Market"], [class*="bet"]');
                        return el ? el.innerText : '';
                    """, btn)
                    if search_label in (parent_text or "").lower():
                        driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                        log(f"[Stake] ✅ Clic sélection: {selection}", "info")
                        break

            if not clicked:
                log(f"[Stake] ❌ Bouton cote non trouvé pour: {selection}", "error")
                return False

            # Pour DNB : vider betslip puis re-cliquer (déjà géré en amont pour std bets)
            if m:
                try:
                    reset = driver.find_elements(By.CSS_SELECTOR, '[data-testid="reset-betslip"]')
                    if reset:
                        reset[0].click()
                        time.sleep(0.8)
                except Exception:
                    pass
                _human_wait(0.3, 0.5)
                self._click_dnb_outcome(driver, team_idx)

            # Attente polling pour la mise input (jusqu'à 8s)
            mise_input = None
            for _ in range(16):
                time.sleep(0.5)
                for sel in ['[data-testid="input-bet-amount"]', 'input[type="number"][class*="spacing"]', 'input[type="number"]']:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    if els and els[0].is_displayed():
                        mise_input = els[0]
                        break
                if mise_input:
                    break

            if mise_input:
                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", mise_input)
                mise_input.click()
                time.sleep(0.3)
                mise_input.send_keys(Keys.CONTROL + "a")
                mise_input.send_keys(str(mise))
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, mise_input)
                _human_wait(0.5, 1.0)
            else:
                log("[Stake] ⚠️ Input mise non trouvé, tentative sans mise", "warning")

            # Bouton Parier via JS (contourne les overlays)
            _human_wait(0.5, 0.8)
            parier_clicked = driver.execute_script("""
                var btn = document.querySelector('[data-testid="betSlip-place-bets-button"]');
                if (btn && !btn.disabled) { btn.click(); return true; }
                return false;
            """)

            if parier_clicked:
                _human_wait(2.0, 3.0)
                log("[Stake] ✅ Pari placé", "info")
                return True

            log("[Stake] ❌ Bouton confirmation non trouvé", "error")
            return False
        except Exception as e:
            log(f"[Stake] Erreur place_bet: {e}", "error")
            return False

    # ── Same Game Multi (MyMatch combiné) ────────────────────────────────

    def place_same_game_multi(self, driver, match_url: str,
                              combined_events: List[Dict], mise: float,
                              equipe_1: str = "", equipe_2: str = "") -> bool:
        """
        Place un pari combiné sur le même match (SGM — "Pari Multiple sur un Même Match").

        Flux réel Stake.bet (validé par inspection DOM) :
          1. Clic tab "Pari Multiple sur un Même Match"
          2. Clic sur chaque button.outcome dans .market (texte = "Label\\ncote")
             → Noms de joueurs inversés : "Harry Kane" → "Kane, Harry"
          3. Clic PHYSIQUE sur "Ajouter un pari" → le pari apparaît dans le betslip de droite
          4. Input mise : input[type='number'][placeholder='0.00']
          5. Clic sur bouton "Parier"
        """
        try:
            driver.get(match_url)
            _human_wait(2.0, 3.0)

            # ── 1. Cliquer sur le tab SGM (data-testid validé) ───────────
            sgm_clicked = False
            for sel in ['[data-testid="tab-customBet"]', 'button[data-testid*="customBet"]']:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)
                if btns:
                    driver.execute_script(
                        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}))", btns[0])
                    sgm_clicked = True
                    log(f"[Stake] ✅ Tab SGM cliqué (data-testid)", "info")
                    _human_wait(1.0, 1.5)
                    break
            # Fallback texte
            if not sgm_clicked:
                for btn in driver.find_elements(By.CSS_SELECTOR, "button"):
                    txt = (btn.text or "").strip()
                    if "pari multiple sur un même match" in txt.lower() or "same game" in txt.lower():
                        driver.execute_script(
                            "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}))", btn)
                        sgm_clicked = True
                        log(f"[Stake] ✅ Tab SGM cliqué (texte): '{txt[:50]}'", "info")
                        _human_wait(1.0, 1.5)
                        break

            if not sgm_clicked:
                log("[Stake] ⚠️ Tab SGM non trouvé", "warning")

            # ── 2. Sélectionner chaque événement ─────────────────────────
            selections_clicked = 0
            for event in combined_events:
                selection = event.get("selection", "")
                intitule  = event.get("intitule", "")

                sport_id = _detect_sport_from_url(match_url)
                label_bk = get_label("Stake", sport_id, selection)
                base     = (label_bk or selection).strip()

                # Stake affiche les joueurs "Nom, Prénom" → générer les variantes
                search_variants = [base.lower()]
                parts = base.split()
                if len(parts) == 2:
                    search_variants.append(f"{parts[1]}, {parts[0]}".lower())
                    search_variants.append(parts[1].lower())
                if intitule:
                    words = intitule.split()
                    if len(words) >= 2:
                        search_variants.append(words[-1].lower())

                log(f"[Stake] Recherche SGM: {search_variants}", "info")

                def _fetch_sgm_buttons():
                    btns = driver.find_elements(By.CSS_SELECTOR, ".market button.outcome")
                    if not btns:
                        btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='outcome']")
                    return btns

                clicked = False
                # Re-fetch avant chaque tentative (DOM Stake rechargé après tab click ou scroll)
                outcome_btns = _fetch_sgm_buttons()

                for idx, btn in enumerate(outcome_btns):
                    try:
                        btn_label = (btn.text or "").strip().lower().split("\n")[0].strip()
                        if any(v in btn_label for v in search_variants):
                            driver.execute_script(
                                "arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                            _human_wait(0.3, 0.5)
                            btn.click()
                            clicked = True
                            selections_clicked += 1
                            log(f"[Stake] ✅ SGM sélection: '{btn_label[:50]}'", "info")
                            _human_wait(0.6, 1.0)
                            break
                    except Exception:
                        # Stale element — re-fetch et réessayer depuis le début
                        outcome_btns = _fetch_sgm_buttons()
                        for btn2 in outcome_btns:
                            try:
                                lbl = (btn2.text or "").strip().lower().split("\n")[0].strip()
                                if any(v in lbl for v in search_variants):
                                    driver.execute_script(
                                        "arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn2)
                                    _human_wait(0.3, 0.5)
                                    btn2.click()
                                    clicked = True
                                    selections_clicked += 1
                                    log(f"[Stake] ✅ SGM sélection (re-fetch): '{lbl[:50]}'", "info")
                                    _human_wait(0.6, 1.0)
                                    break
                            except Exception:
                                continue
                        break

                if not clicked:
                    # Fallback IA — re-fetch pour avoir des éléments frais
                    outcome_btns = _fetch_sgm_buttons()
                    all_texts = []
                    for b in outcome_btns:
                        try:
                            t = (b.text or "").strip()
                            if t:
                                all_texts.append(t)
                        except Exception:
                            continue
                    if all_texts:
                        # Enrichir l'event avec les équipes pour que l'IA comprenne 1X/X2
                        enriched_event = dict(event)
                        if equipe_1:
                            enriched_event["equipe_1"] = equipe_1
                        if equipe_2:
                            enriched_event["equipe_2"] = equipe_2
                        ai_label = _ai_resolve_outcome(all_texts, enriched_event)
                        if ai_label:
                            ai_lower = ai_label.lower()
                            # Re-fetch encore une fois avant de cliquer
                            outcome_btns = _fetch_sgm_buttons()
                            for btn in outcome_btns:
                                try:
                                    btn_label = (btn.text or "").strip().lower().split("\n")[0].strip()
                                    if ai_lower in btn_label or btn_label in ai_lower:
                                        driver.execute_script(
                                            "arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                                        _human_wait(0.3, 0.5)
                                        btn.click()
                                        clicked = True
                                        selections_clicked += 1
                                        log(f"[Stake] ✅ SGM IA sélection: '{btn.text.strip()[:50]}'", "info")
                                        _human_wait(0.6, 1.0)
                                        break
                                except Exception:
                                    continue

                if not clicked:
                    log(f"[Stake] ❌ Sélection SGM non trouvée: {selection} / {intitule}", "error")

            if selections_clicked < 2:
                log(f"[Stake] ❌ Seulement {selections_clicked} sélection(s) SGM — minimum 2 requis", "error")
                return False

            _human_wait(0.8, 1.2)

            # ── 3. Cliquer "Ajouter un pari" pour envoyer au betslip ──────
            # Utilise dispatchEvent pour compatibilité Svelte
            ajouter_clicked = False
            for btn in driver.find_elements(By.CSS_SELECTOR, "button"):
                if "ajouter un pari" in (btn.text or "").lower():
                    btn.click()  # vrai clic nécessaire pour déclencher l'état Svelte
                    ajouter_clicked = True
                    log("[Stake] ✅ 'Ajouter un pari' cliqué", "info")
                    _human_wait(2.0, 2.5)
                    break

            if not ajouter_clicked:
                log("[Stake] ❌ Bouton 'Ajouter un pari' non trouvé", "error")
                return False

            # ── 4. Saisir la mise dans le betslip de droite ───────────────
            # Polling 8s — betslip Stake se charge de façon async
            mise_input = None
            for _ in range(16):
                time.sleep(0.5)
                for sel in ['[data-testid="input-bet-amount"]',
                            'input[type="number"][class*="spacing"]',
                            'input[type="number"]']:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    if els and els[0].is_displayed():
                        mise_input = els[0]
                        break
                if mise_input:
                    break

            if not mise_input:
                log("[Stake] ❌ Input de mise SGM non trouvé après 8s", "error")
                return False

            driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", mise_input)
            _human_wait(0.3, 0.5)
            mise_input.click()
            time.sleep(0.3)
            # Sélectionner tout + taper la mise
            from selenium.webdriver.common.keys import Keys
            mise_input.send_keys(Keys.CONTROL + "a")
            mise_input.send_keys(str(mise))
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, mise_input)
            log(f"[Stake] ✅ Mise saisie: {mise}€", "info")
            _human_wait(0.5, 1.0)

            # ── 5. Cliquer "Parier" — re-chercher après saisie (DOM mis à jour) ──
            _human_wait(0.8, 1.2)
            parier_clicked = False
            for _ in range(3):
                try:
                    parier_btns = driver.find_elements(By.CSS_SELECTOR, "button")
                    for btn in parier_btns:
                        try:
                            txt = (btn.text or "").strip().lower()
                            if txt == "parier" and btn.is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", btn)
                                _human_wait(0.3, 0.5)
                                btn.click()
                                parier_clicked = True
                                break
                        except Exception:
                            continue
                    if parier_clicked:
                        break
                except Exception:
                    _human_wait(0.5, 0.8)

            if parier_clicked:
                _human_wait(2.0, 3.5)
                log(f"[Stake] ✅ Pari SGM confirmé ({selections_clicked} sélections @ {mise}€)", "info")
                return True

            log("[Stake] ❌ Bouton 'Parier' non trouvé ou désactivé", "error")
            return False

        except Exception as e:
            log(f"[Stake] Erreur place_same_game_multi: {e}", "error")
            return False

    # ── Interface router ─────────────────────────────────────────────────

    async def run(self, bet: Dict) -> Dict:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._run_sync, bet)

    async def fetch_odds(self, bet: Dict) -> Dict:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._fetch_odds_sync, bet)

    def _run_sync(self, bet: Dict) -> Dict:
        result = {"bookmaker": self.name, "odds": None, "success": False,
                  "challenge_activated": False, "error": None}
        try:
            driver = self._get_driver()
            if not driver:
                result["error"] = "driver_unavailable"
                return result
            if not self.is_logged_in(driver):
                result["error"] = "session_expired"
                log("[Stake] ❌ Session inactive", "error")
                return result
            match_url = self.search_match(driver, bet.get("equipe_1", ""), bet.get("equipe_2", ""),
                                          str(bet.get("sport", "")), bet.get("date", ""))
            if not match_url:
                result["error"] = "match_not_found"
                return result

            combined_events = bet.get("combined_events")
            mise = float(bet.get("mise", 10))

            if combined_events:
                # Pari combiné sur le même match → MyMatch Stake
                log(f"[Stake] Mode MyMatch ({len(combined_events)} événements): {bet.get('combined_label', '')}", "info")
                result["odds"] = bet.get("odds")
                success = self.place_same_game_multi(
                    driver, match_url, combined_events, mise,
                    equipe_1=bet.get("equipe_1", ""), equipe_2=bet.get("equipe_2", "")
                )
            else:
                odds = self.get_odds(driver, match_url, bet.get("selection", ""), bet.get("categorie", ""))
                result["odds"] = odds
                success = self.place_bet(driver, match_url, bet.get("selection", ""),
                                         bet.get("categorie", ""), mise)

            result["success"] = success
        except Exception as e:
            result["error"] = str(e)
            log(f"[Stake] Erreur run: {e}", "error")
        return result

    def _fetch_odds_sync(self, bet: Dict) -> Dict:
        result = {"bookmaker": self.name, "odds": None, "match_url": None,
                  "challenge_activated": False, "error": None}
        try:
            driver = self._get_driver()
            if not driver:
                result["error"] = "driver_unavailable"
                return result
            if not self.is_logged_in(driver):
                result["error"] = "session_expired"
                return result
            match_url = self.search_match(driver, bet.get("equipe_1", ""), bet.get("equipe_2", ""),
                                          str(bet.get("sport", "")), bet.get("date", ""))
            if not match_url:
                result["error"] = "match_not_found"
                return result
            result["match_url"] = match_url
            result["odds"] = self.get_odds(driver, match_url, bet.get("selection", ""), bet.get("categorie", ""))
        except Exception as e:
            result["error"] = str(e)
            log(f"[Stake] Erreur fetch_odds: {e}", "error")
        return result

    def get_challenges(self, driver=None) -> List[Dict]:
        return []

    def activate_challenge(self, driver=None, challenge: Dict = None) -> bool:
        return False

    def _match_challenge(self, bet: Dict, challenges: List[Dict]):
        return None


def _detect_sport_from_url(url: str) -> str:
    url = url.lower()
    if "tennis" in url:
        return "2"
    if "soccer" in url or "football" in url:
        return "3"
    if "basketball" in url:
        return "4"
    if "rugby" in url:
        return "5"
    return "3"
