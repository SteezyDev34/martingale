# -*- coding: utf-8 -*-
"""
Scraper Selenium pour Lollybet — fenêtre 8 du driver partagé.
Utilise le driver Selenium existant (get_script_driver(8)) + shadow root natif Selenium 4.

Sélecteurs validés par inspection DOM réelle :
  - Composant SG-* : shadow root du sportsbook
  - Recherche       : input[placeholder='Rechercher...']  (.sb-search-field__input)
  - Résultat        : .sb-search-results-item
  - Label sélection : .sb-game-event__name
  - Bouton cote     : parent .sb-game-event-content.sb-bet-button
  - Input mise      : input[placeholder='Mise']  (.sb-betslip-bet-input_buttons__input)
  - Bouton Parier   : button .sb-bet-slip-footer-v2__btn_submit
  - Cote value      : texte numérique dans le parent .sb-bet-button
"""
import os
import re
import time
import random
from typing import Optional, List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Functions.Logs.Logger import log

LOLLYBET_URL = "https://lolly-bet99.com"
LOLLYBET_WINDOW = 8


# ── Résolution IA (Claude) ────────────────────────────────────────────────────

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


def _ai_resolve_match(candidates: List[Dict], equipe_1: str, equipe_2: str) -> Optional[int]:
    """
    Demande à Claude quel résultat de recherche correspond au match.
    candidates = [{"text": "...", "index": 0}, ...]
    Retourne l'index du bon candidat ou None.
    """
    client = _get_anthropic_client()
    if not client or not candidates:
        return None
    try:
        lines = "\n".join(f"{i+1}. {c['text'].strip()[:60]}" for i, c in enumerate(candidates))
        prompt = (
            f"Je cherche le match de sport entre '{equipe_1}' et '{equipe_2}'.\n"
            f"Voici les résultats trouvés :\n{lines}\n\n"
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
                log(f"[Lollybet AI] ✅ Match résolu: {candidates[idx]['text'].strip()[:50]}", "info")
                return idx
    except Exception as e:
        log(f"[Lollybet AI] Erreur résolution match: {e}", "warning")
    return None


def _ai_resolve_outcome(available_labels: List[str], selection: str, intitule: str = "") -> Optional[str]:
    """
    Demande à Claude quel bouton de cote correspond à la sélection.
    available_labels = ["Victoire Angleterre", "Match nul", ...]
    Retourne le label correspondant ou None.
    """
    client = _get_anthropic_client()
    if not client or not available_labels:
        return None
    try:
        lines = "\n".join(f"{i+1}. {l}" for i, l in enumerate(available_labels))
        glossary = (
            "=== LABELS LOLLYBET RÉELS ===\n"
            "\nFOOTBALL 1x2:\n"
            "  Victoire domicile = nom de l'équipe domicile (ex: 'Colombie')\n"
            "  Nul = 'Match nul'\n"
            "  Victoire extérieur = nom de l'équipe extérieure (ex: 'Portugal')\n"
            "\nDOUBLE CHANCE:\n"
            "  1X = 'Colombie ou Match nul' (domicile OU nul)\n"
            "  X2 = 'Match nul ou Portugal' (nul OU extérieur)\n"
            "  12 = 'Colombie ou Portugal' (domicile OU extérieur)\n"
            "\nBTTS (les deux équipes marquent):\n"
            "  Oui = 'oui' | Non = 'non'\n"
            "\nTOTAL BUTS:\n"
            "  Over = 'Plus de 0.5' / 'Plus de 1.5' / 'Plus de 2.5' etc.\n"
            "  Under = 'Moins de 0.5' / 'Moins de 1.5' / 'Moins de 2.5' etc.\n"
            "\nHANDICAP ASIATIQUE:\n"
            "  Format: 'Équipe (+1.5)' ou 'Équipe (-1.5)'\n"
            "  Positif = l'équipe reçoit des buts d'avance\n"
            "  Négatif = l'équipe doit gagner par X buts\n"
            "\nTENNIS:\n"
            "  Vainqueur = nom du joueur (ex: 'Djokovic, Novak')\n"
            "  Total jeux match = 'Plus de 31.5' / 'Moins de 31.5' / 'Plus de 40.5' etc. — 'plus de X.5' ou 'moins de X.5' → label: 'Plus de X.5' / 'Moins de X.5'\n"
            "  Handicap jeux = 'Wu, Yibing (+7.5)' / 'Djokovic, Novak (-7.5)'\n"
            "  1er set total = 'Plus de 11.5' / 'Moins de 11.5'\n"
            "  Joueur total jeux = 'Plus de 19.5' / 'Moins de 19.5'\n"
            "  Total sets match = 'Plus de 2.5' / 'Moins de 2.5' / 'Plus de 3.5' / 'Moins de 3.5' — 'total de sets plus de X.5' → label: 'Plus de X.5'\n"
            "  HANDICAP NUMÉROTÉ: 'v1' = joueur 1 (domicile/équipe_1) gagne, 'v2' = joueur 2 gagne\n"
            "  'handicap 1 (+X.5)' = joueur 1 avec avantage → label Lollybet: 'NomJ1, PrenomJ1 (+X.5)'\n"
            "  'handicap 2 (+X.5)' = joueur 2 avec avantage → label Lollybet: 'NomJ2, PrenomJ2 (+X.5)'\n"
            "  'handicap 1 (-X.5)' = joueur 1 doit gagner d'écart → label: 'NomJ1, PrenomJ1 (-X.5)'\n"
            "  'handicap 2 (-X.5)' = joueur 2 doit gagner d'écart → label: 'NomJ2, PrenomJ2 (-X.5)'\n"
            "\nBASKETBALL:\n"
            "  Vainqueur = nom de l'équipe (ex: 'Indiana Fever')\n"
            "  Nul (rare) = 'Match nul'\n"
            "  Total = 'Plus de 180.5' / 'Moins de 180.5'\n"
            "  Handicap = 'Indiana Fever (-8.5)' / 'Los Angeles Sparks (+8.5)'\n"
            "  Demi handicap entier = 'Indiana Fever (-8)' / 'Los Angeles Sparks (+8)'\n"
            "================================\n\n"
        )
        context_line = ""
        if intitule and " vs " in intitule.lower():
            context_line = f"Contexte du match: '{intitule}' (joueur 1 = premier nom, joueur 2 = second nom).\n"
        prompt = (
            f"{glossary}"
            f"{context_line}"
            f"Je veux parier sur : '{intitule or selection}' (sélection: '{selection}').\n\n"
            f"Voici les boutons disponibles sur Lollybet :\n{lines}\n\n"
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
            if 0 <= idx < len(available_labels):
                log(f"[Lollybet AI] ✅ Outcome résolu: '{available_labels[idx]}'", "info")
                return available_labels[idx]
    except Exception as e:
        log(f"[Lollybet AI] Erreur résolution outcome: {e}", "warning")
    return None

SPORTS_MAP = {
    "1": "football",
    "2": "tennis",
    "3": "football",
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
    "18": "darts",
    "19": "snooker",
    "20": "futsal",
    "21": "padel",
    "22": "badminton",
    "23": "waterpolo",
}


def _norm(s: str) -> str:
    """Normalise un label : minuscule, espaces autour du séparateur supprimés."""
    return re.sub(r"\s*[:\-]\s*", "-", s.lower().strip())


def _human_wait(a: float = 0.8, b: float = 1.5):
    import random
    time.sleep(a + random.random() * (b - a))


# ── Accès au Shadow Root ─────────────────────────────────────────────────────

def _get_shadow_root(driver):
    """Retourne le ShadowRoot natif Selenium 4 du composant SG-*."""
    sg_el = driver.execute_script(
        "return Array.from(document.querySelectorAll('*'))"
        ".find(function(e){ return e.tagName.startsWith('SG-'); });"
    )
    return sg_el.shadow_root if sg_el else None


def _wait_shadow_root(driver, timeout: float = 15.0):
    """Attend que le shadow root SG-* soit disponible et le retourne."""
    elapsed = 0.0
    while elapsed < timeout:
        sr = _get_shadow_root(driver)
        if sr:
            return sr
        time.sleep(0.8)
        elapsed += 0.8
    return None


def _scroll_to_load_markets(driver):
    """Scrolle la page du match pour forcer le chargement de tous les marchés (total sets, etc.)."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(0.6)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.4)
    except Exception:
        pass


# ── Scraper ──────────────────────────────────────────────────────────────────

class LollybetScraper:
    """
    Scraper Lollybet basé sur Selenium (fenêtre 8 du driver partagé).
    Interface compatible avec le router : run(bet) → dict, fetch_odds(bet) → dict.
    """
    name = "Lollybet"
    requires_vpn = False

    def _get_driver(self):
        import config
        from ChromeDriver.SetDriver import get_script_driver
        return get_script_driver(LOLLYBET_WINDOW)

    # ── Session ──────────────────────────────────────────────────────────

    def login(self, driver) -> bool:
        """Connexion automatique Lollybet : clic Connexion → formulaire → submit (3 retries)."""
        email    = os.getenv("LOLLYBET_EMAIL", "")
        password = os.getenv("LOLLYBET_PASSWORD", "")
        if not email or not password:
            log("[Lollybet] Credentials manquants (LOLLYBET_EMAIL / LOLLYBET_PASSWORD)", "error")
            return False

        for attempt in range(1, 4):
            log(f"[Lollybet] Tentative {attempt}/3...", "info")
            try:
                if self._attempt_login(driver, email, password):
                    return True
            except Exception as e:
                log(f"[Lollybet] Erreur tentative {attempt}: {e}", "error")
            if attempt < 3:
                driver.get(LOLLYBET_URL + "/fr")
                _human_wait(3.0, 4.0)

        log("[Lollybet] Echec apres 3 tentatives", "error")
        return False

    def _attempt_login(self, driver, email: str, password: str) -> bool:
        driver.set_window_size(1280, 900)
        driver.get(LOLLYBET_URL + "/fr")
        _human_wait(3.5, 5.0)

        # Clic sur le bouton "Connexion" dans la navbar
        connexion_btn = None
        for btn in driver.find_elements(By.CSS_SELECTOR, "button.wlc-btn"):
            if btn.text.strip() == "Connexion":
                connexion_btn = btn
                break
        if not connexion_btn:
            log("[Lollybet] Bouton 'Connexion' introuvable", "error")
            return False

        driver.execute_script("arguments[0].click();", connexion_btn)
        _human_wait(2.0, 3.0)

        # Champs du formulaire
        email_inp = driver.find_elements(By.CSS_SELECTOR,
            "input[id='email'], input[placeholder='E-mail'], input[type='email']")
        pwd_inp   = driver.find_elements(By.CSS_SELECTOR,
            "input[id='password'], input[placeholder='Mot de passe'], input[type='password']")

        if not email_inp or not pwd_inp:
            log("[Lollybet] Champs email/password introuvables", "error")
            return False

        driver.execute_script("arguments[0].click();", email_inp[0])
        time.sleep(0.2)
        try: email_inp[0].clear()
        except Exception: pass
        driver.execute_script("arguments[0].value='';", email_inp[0])
        for char in email:
            email_inp[0].send_keys(char)
            time.sleep(random.uniform(0.06, 0.15))
        _human_wait(0.4, 0.7)

        driver.execute_script("arguments[0].click();", pwd_inp[0])
        time.sleep(0.2)
        try: pwd_inp[0].clear()
        except Exception: pass
        driver.execute_script("arguments[0].value='';", pwd_inp[0])
        for char in password:
            pwd_inp[0].send_keys(char)
            time.sleep(random.uniform(0.06, 0.15))
        _human_wait(0.4, 0.7)

        # Submit
        submit = driver.find_elements(By.CSS_SELECTOR, "button.wlc-btn--submit")
        if submit:
            driver.execute_script("arguments[0].click();", submit[0])
        else:
            from selenium.webdriver.common.keys import Keys
            pwd_inp[0].send_keys(Keys.RETURN)

        _human_wait(4.0, 6.0)

        if self.is_logged_in(driver):
            log("[Lollybet] Connexion reussie", "info")
            return True

        log("[Lollybet] Echec — session non active apres login", "error")
        return False

    def is_logged_in(self, driver) -> bool:
        try:
            driver.get(LOLLYBET_URL + "/fr")
            _human_wait(2.0, 3.0)
            # Bouton Depot visible = connecte
            for el in driver.find_elements(By.CSS_SELECTOR, "button.wlc-btn--deposit"):
                if el.is_displayed():
                    log("[Lollybet] Session active (bouton Depot present)", "info")
                    return True
            # Bouton Connexion visible = pas connecte
            for btn in driver.find_elements(By.CSS_SELECTOR, "button.wlc-btn"):
                if btn.text.strip() == "Connexion" and btn.is_displayed():
                    return False
            # Fallback balance/wallet
            for sel in ["[class*='balance']", "[class*='wallet']", "[class*='user-balance']"]:
                for el in driver.find_elements(By.CSS_SELECTOR, sel):
                    if el.text.strip():
                        log(f"[Lollybet] Session active ({sel})", "info")
                        return True
            return False
        except Exception as e:
            log(f"[Lollybet] Erreur is_logged_in: {e}", "error")
            return False

    # ── Recherche de match ───────────────────────────────────────────────

    def _open_search_field(self, sr, driver) -> bool:
        """Clique sur l'icône/bouton de recherche pour rendre le champ interactable."""
        search_toggles = [
            ".sb-search-field__toggle",
            ".sb-header__search",
            "[class*='search-icon']",
            "[class*='search-toggle']",
            "[class*='search-btn']",
            "button[aria-label*='earch']",
            ".sb-search",
            ".sb-search-field",
        ]
        for sel in search_toggles:
            els = sr.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                try:
                    driver.execute_script("arguments[0].click();", el)
                    _human_wait(0.5, 0.9)
                    return True
                except Exception:
                    continue
        return False

    def _type_in_search(self, sr, driver, text: str) -> bool:
        """Remplit le champ de recherche via JS (shadow root)."""
        # Injection JS via le shadow host — seule méthode fiable pour les shadow root
        try:
            result = driver.execute_script("""
                var sg = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                if (!sg || !sg.shadowRoot) return 'no_shadow';
                var sr = sg.shadowRoot;
                // Essayer de cliquer le toggle de recherche d'abord
                var toggle = sr.querySelector('.sb-search-field__toggle, .sb-header__search, [class*="search-toggle"], [class*="search-btn"], [class*="search-icon"]');
                if (toggle) { try { toggle.click(); } catch(e) {} }
                var inp = sr.querySelector('.sb-search-field__input, input[placeholder*="echerch"], input[type="search"], input[class*="search"]');
                if (!inp) {
                    // Chercher récursivement dans les shadow roots imbriqués
                    var all = Array.from(sr.querySelectorAll('*'));
                    for (var el of all) {
                        if (el.shadowRoot) {
                            var nested = el.shadowRoot.querySelector('input[placeholder*="echerch"], input[type="search"], input[class*="search"]');
                            if (nested) { inp = nested; break; }
                        }
                    }
                }
                if (!inp) return 'no_input';
                inp.focus();
                inp.value = arguments[0];
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
                return 'ok';
            """, text)
            if result == 'ok':
                return True
            log(f"[Lollybet] _type_in_search JS: {result}", "warning")
            # Retry après une courte attente (timing)
            if result == 'no_input':
                time.sleep(1.5)
                result2 = driver.execute_script("""
                    var sg = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!sg || !sg.shadowRoot) return 'no_shadow';
                    var inp = sg.shadowRoot.querySelector('.sb-search-field__input, input[placeholder*="echerch"]');
                    if (!inp) return 'no_input';
                    inp.click(); inp.focus();
                    inp.value = arguments[0];
                    inp.dispatchEvent(new Event('input', {bubbles:true}));
                    inp.dispatchEvent(new Event('change', {bubbles:true}));
                    inp.dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
                    return 'ok';
                """, text)
                if result2 == 'ok':
                    return True
                log(f"[Lollybet] _type_in_search retry: {result2}", "warning")
        except Exception as e:
            log(f"[Lollybet] _type_in_search erreur: {e}", "warning")
        return False

    def search_match(self, driver, equipe_1: str, equipe_2: str, sport: str, date: str) -> Optional[str]:
        try:
            sport_slug = SPORTS_MAP.get(str(sport), "football")
            url = f"{LOLLYBET_URL}/fr/sportsbook#/events/{sport_slug}"
            log(f"[Lollybet] Navigation vers {url}", "info")
            driver.get(url)
            _human_wait(2.5, 4.0)

            sr = _wait_shadow_root(driver, timeout=15)
            if not sr:
                log("[Lollybet] ❌ Shadow root non trouvé", "error")
                return None
            log("[Lollybet] Shadow root trouvé", "info")

            # Ouvrir le champ de recherche si nécessaire
            # Re-fetch sr depuis le DOM pour éviter stale shadow root
            sr = _get_shadow_root(driver) or sr
            opened = self._open_search_field(sr, driver)
            log(f"[Lollybet] Toggle recherche: {'cliqué' if opened else 'non trouvé (input peut-être déjà visible)'}", "info")
            _human_wait(0.5, 0.8)
            sr = _get_shadow_root(driver) or sr

            typed = self._type_in_search(sr, driver, equipe_1)
            log(f"[Lollybet] Frappe '{equipe_1}': {'OK' if typed else '❌ échec'}", "info")
            if not typed:
                log("[Lollybet] ❌ Impossible d'écrire dans le champ de recherche", "error")
                return None
            _human_wait(2.0, 3.0)

            match_url = self._pick_result(sr, driver, equipe_1, equipe_2)
            if match_url:
                return match_url

            log(f"[Lollybet] Aucun résultat pour '{equipe_1}', essai avec '{equipe_2}'", "info")
            sr = _get_shadow_root(driver) or sr
            self._open_search_field(sr, driver)
            _human_wait(0.3, 0.5)
            sr = _get_shadow_root(driver) or sr
            if self._type_in_search(sr, driver, equipe_2):
                _human_wait(2.0, 3.0)
                result = self._pick_result(sr, driver, equipe_1, equipe_2)
                if result:
                    return result

            # Fallback: essai avec nom de famille seul (Lollybet peut afficher noms inversés/abrégés)
            last_1 = equipe_1.split()[-1] if equipe_1 else equipe_1
            last_2 = equipe_2.split()[-1] if equipe_2 else equipe_2
            for last_name in [last_1, last_2]:
                log(f"[Lollybet] Essai nom de famille: '{last_name}'", "info")
                # Re-fetch sr frais à chaque tentative pour éviter detached shadow root
                sr = _wait_shadow_root(driver, timeout=10)
                if not sr:
                    continue
                self._open_search_field(sr, driver)
                _human_wait(0.3, 0.5)
                if self._type_in_search(sr, driver, last_name):
                    _human_wait(2.0, 3.0)
                    sr = _wait_shadow_root(driver, timeout=10)
                    if not sr:
                        continue
                    result = self._pick_result(sr, driver, equipe_1, equipe_2)
                    if result:
                        return result

            log(f"[Lollybet] ❌ Match '{equipe_1} vs {equipe_2}' non trouvé", "warning")
            return None

        except Exception as e:
            log(f"[Lollybet] Erreur search_match: {e}", "error")
            return None

    def _pick_result(self, sr, driver, equipe_1: str, equipe_2: str) -> Optional[str]:
        # Essai avec plusieurs sélecteurs au cas où la classe change
        result_selectors = [
            ".sb-search-results-item",
            "[class*='search-results-item']",
            "[class*='search-result']",
            "[class*='search-item']",
            "[class*='result-item']",
        ]
        items = []
        for sel in result_selectors:
            items = sr.find_elements(By.CSS_SELECTOR, sel)
            if items:
                log(f"[Lollybet] {len(items)} résultat(s) trouvé(s) avec '{sel}'", "info")
                break

        if not items:
            # Dump des éléments visibles dans le shadow root pour diagnostiquer
            try:
                all_texts = driver.execute_script(
                    "var sr = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));"
                    "if (!sr || !sr.shadowRoot) return 'no shadow root';"
                    "return Array.from(sr.shadowRoot.querySelectorAll('*')).filter(e => e.textContent.trim().length > 0 && e.children.length === 0).slice(0,20).map(e => e.tagName + '.' + e.className + ': ' + e.textContent.trim().slice(0,40)).join('\\n');"
                )
                log(f"[Lollybet] Shadow root (aucun résultat trouvé) :\n{all_texts}", "info")
            except Exception:
                pass
            log("[Lollybet] Aucun élément résultat dans le shadow root", "warning")
            return None

        for item in items:
            try:
                text = item.text.lower()
                if equipe_1.lower() in text and equipe_2.lower() in text:
                    log(f"[Lollybet] ✅ Match trouvé: {item.text[:60]}", "info")
                    driver.execute_script("arguments[0].click();", item)
                    _human_wait(2.5, 4.0)
                    return driver.current_url
                # Partiel: les deux équipes doivent avoir au moins un mot en commun avec le texte
                words_1 = [w for w in equipe_1.lower().split() if len(w) > 3]
                words_2 = [w for w in equipe_2.lower().split() if len(w) > 3]
                match_1 = any(w in text for w in words_1) if words_1 else equipe_1.lower() in text
                match_2 = any(w in text for w in words_2) if words_2 else equipe_2.lower() in text
                if match_1 and match_2 and (" v " in text or " vs " in text or " - " in text or "\n" in item.text):
                    log(f"[Lollybet] ✅ Match partiel: {item.text[:60]}", "info")
                    driver.execute_script("arguments[0].click();", item)
                    _human_wait(2.5, 4.0)
                    return driver.current_url
            except Exception:
                continue

        log(f"[Lollybet] Résultats présents mais aucun ne correspond à '{equipe_1}' / '{equipe_2}'", "warning")
        try:
            log(f"[Lollybet] Textes des résultats: {[i.text[:40] for i in items[:5]]}", "info")
        except Exception:
            pass

        # Fallback IA — demande à Claude de choisir le bon résultat
        candidates = []
        for item in items:
            try:
                t = item.text.strip()
                if t:
                    candidates.append({"text": t, "element": item})
            except Exception:
                continue
        if candidates:
            ai_idx = _ai_resolve_match(
                [{"text": c["text"]} for c in candidates], equipe_1, equipe_2
            )
            if ai_idx is not None:
                try:
                    driver.execute_script("arguments[0].click();", candidates[ai_idx]["element"])
                    _human_wait(2.5, 4.0)
                    return driver.current_url
                except Exception as e:
                    log(f"[Lollybet AI] Erreur clic résultat: {e}", "warning")

        return None

    # ── Récupération de cote ────────────────────────────────────────────

    def get_odds(self, driver, match_url: str, selection: str, categorie: str, intitule: str = "") -> Optional[float]:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)
            _scroll_to_load_markets(driver)

            sr = _wait_shadow_root(driver, timeout=15)
            if not sr:
                return None

            from Functions.BetLabelsDB import get_label
            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Lollybet", sport_id, selection)
            # Lollybet utilise ':' comme séparateur de score (ex: '3:0')
            search_label = _norm_lollybet(label_bk or selection)

            return self._find_odds_in_sr(sr, search_label, selection=selection, intitule=intitule)
        except Exception as e:
            log(f"[Lollybet] Erreur get_odds: {e}", "error")
            return None

    def _find_odds_in_sr(self, sr, search_label: str, selection: str = "", intitule: str = "") -> Optional[float]:
        """Cherche la cote pour search_label dans les boutons de cote du shadow root."""
        bet_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-game-event-content.sb-bet-button, [class*='sb-bet-button']")
        label_map = []  # [(raw_label, btn)]

        def _extract_odds(btn):
            odds_els = btn.find_elements(By.CSS_SELECTOR, ".sb-game-event__price, [class*='event__price'], [class*='event-price'], [class*='odds']")
            if odds_els:
                try:
                    v = float(odds_els[0].text.strip().replace(",", "."))
                    if 1.01 < v < 200:
                        return v
                except ValueError:
                    pass
            for line in btn.text.strip().split("\n"):
                try:
                    v = float(line.replace(",", "."))
                    if 1.01 < v < 200:
                        return v
                except ValueError:
                    pass
            return None

        for btn in bet_btns:
            try:
                label_els = btn.find_elements(By.CSS_SELECTOR, ".sb-game-event__name, [class*='event__name'], [class*='event-name']")
                if not label_els:
                    continue
                raw_label = label_els[0].text.strip()
                label_text = _norm_lollybet(raw_label)
                label_map.append((raw_label, btn))
                if search_label in label_text or label_text in search_label:
                    v = _extract_odds(btn)
                    if v:
                        return v
            except Exception:
                continue

        # Fallback IA
        if label_map:
            available = [lm[0] for lm in label_map]
            ai_label = _ai_resolve_outcome(available, selection or search_label, intitule=intitule)
            if ai_label:
                ai_norm = _norm_lollybet(ai_label)
                # Re-fetch buttons après appel IA (éléments potentiellement stale)
                fresh_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-game-event-content.sb-bet-button, [class*='sb-bet-button']")
                for btn in fresh_btns:
                    try:
                        label_els = btn.find_elements(By.CSS_SELECTOR, ".sb-game-event__name, [class*='event__name'], [class*='event-name']")
                        if not label_els:
                            continue
                        raw_label = label_els[0].text.strip()
                        if ai_norm in _norm_lollybet(raw_label) or _norm_lollybet(raw_label) in ai_norm:
                            v = _extract_odds(btn)
                            if v:
                                log(f"[Lollybet AI] ✅ Cote trouvée via IA: '{raw_label}' @ {v}", "info")
                                return v
                    except Exception:
                        continue

        if label_map:
            log(f"[Lollybet] Boutons disponibles ({len(label_map)}): {[lm[0] for lm in label_map[:20]]}", "warning")
        else:
            log(f"[Lollybet] Aucun bouton de cote trouvé sur la page", "warning")
        log(f"[Lollybet] Cote non trouvée pour '{search_label}'", "warning")
        return None

    # ── Placement de pari ───────────────────────────────────────────────

    def _clear_betslip(self, sr) -> None:
        # Bouton "Réinitialiser" du betslip Lollybet
        reset_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-bet-slip-footer-v2__btn_reset")
        for btn in reset_btns:
            try:
                btn.click()
                _human_wait(0.5, 0.8)
            except Exception:
                pass
        # Fallback: boutons delete individuels
        if not reset_btns:
            for sel in ["[class*='betslip'] [class*='delete']", "[class*='betslip'] [class*='remove']",
                        "[class*='betslip'] [class*='close']"]:
                btns = sr.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    try:
                        btn.click()
                        _human_wait(0.3, 0.5)
                    except Exception:
                        pass

    def _count_betslip_legs(self, driver_obj, sr) -> int:
        """Retourne le nombre de sélections dans le betslip (0 si vide) via JS."""
        try:
            count = driver_obj.execute_script(
                "var hosts = document.querySelectorAll('*');"
                "var sr = null;"
                "for (var i=0; i<hosts.length; i++) { if (hosts[i].shadowRoot) { sr = hosts[i].shadowRoot; break; } }"
                "if (!sr) return -1;"
                "var empty = sr.querySelector('.sb-betslip-empty');"
                "if (empty && empty.offsetParent !== null) return 0;"
                "var wrp = sr.querySelector('.sb-betslip-items-wrp');"
                "if (!wrp) return -1;"
                "var items = wrp.children;"
                "var count = 0;"
                "for (var i=0; i<items.length; i++) {"
                "  var cn = items[i].className || '';"
                "  if (typeof cn === 'string' && cn.indexOf('empty') < 0 && items[i].offsetParent !== null) count++;"
                "}"
                "return count;"
            )
            return int(count) if count is not None and count >= 0 else 0
        except Exception:
            return 0

    def _verify_betslip(self, sr, selection: str) -> bool:
        betslip_els = sr.find_elements(By.CSS_SELECTOR, "[class*='betslip'], [class*='bet-slip'], [class*='slip']")
        sel_norm = _norm_lollybet(selection)
        # Tokens significatifs (> 3 chars) pour une correspondance partielle
        sel_tokens = [t for t in sel_norm.split() if len(t) > 3]
        for el in betslip_els:
            if el.text.strip():
                slip_text = _norm_lollybet(el.text)
                # Correspondance exacte
                if sel_norm in slip_text:
                    log(f"[Lollybet] ✅ Betslip vérifié: '{selection}' présent", "info")
                    return True
                # Correspondance partielle : au moins 1 token significatif trouvé
                if sel_tokens and any(t in slip_text for t in sel_tokens):
                    log(f"[Lollybet] ✅ Betslip vérifié (partiel): '{selection}' présent", "info")
                    return True
        # Si le betslip est non vide (sélection ajoutée mais texte différent), on laisse passer
        for el in betslip_els:
            txt = el.text.strip()
            if txt and len(txt) > 10:
                log(f"[Lollybet] ✅ Betslip non vide, on continue", "info")
                return True
        log(f"[Lollybet] ⚠️  '{selection}' absent du betslip", "warning")
        return False

    def _click_outcome(self, sr, search_label: str, selection: str = "", intitule: str = "") -> bool:
        """Clique sur le bouton de cote correspondant à search_label, avec fallback IA."""
        bet_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-game-event-content.sb-bet-button, [class*='sb-bet-button']")
        label_map = []  # [(label_text, btn)]

        for btn in bet_btns:
            try:
                label_els = btn.find_elements(By.CSS_SELECTOR, ".sb-game-event__name, [class*='event__name'], [class*='event-name']")
                if not label_els:
                    continue
                raw_label = label_els[0].text.strip()
                label_text = _norm_lollybet(raw_label)
                label_map.append((raw_label, label_text, btn))
                if search_label in label_text or label_text in search_label:
                    btn.click()
                    log(f"[Lollybet] ✅ Clic cote: '{raw_label}'", "info")
                    return True
            except Exception:
                continue

        # Fallback IA
        if label_map:
            available = [lm[0] for lm in label_map]
            ai_label = _ai_resolve_outcome(available, selection or search_label, intitule)
            if ai_label:
                ai_norm = _norm_lollybet(ai_label)
                _human_wait(0.5, 0.8)
                # Re-fetch après appel IA pour éviter stale element (inclure boutons actifs)
                fresh_btns = sr.find_elements(By.CSS_SELECTOR,
                    ".sb-game-event-content.sb-bet-button, [class*='sb-bet-button']")
                log(f"[Lollybet] Re-fetch après IA: {len(fresh_btns)} bouton(s), ai_norm='{ai_norm}'", "info")
                for btn in fresh_btns:
                    try:
                        label_els = btn.find_elements(By.CSS_SELECTOR,
                            ".sb-game-event__name, [class*='event__name'], [class*='event-name']")
                        if not label_els:
                            continue
                        raw_label = label_els[0].text.strip()
                        label_text = _norm_lollybet(raw_label)
                        if ai_norm in label_text or label_text in ai_norm:
                            btn_classes = btn.get_attribute("class") or ""
                            # Si déjà actif/sélectionné → déjà dans le betslip, pas besoin de cliquer
                            if "active" in btn_classes or "selected" in btn_classes or "checked" in btn_classes:
                                log(f"[Lollybet] ✅ Cote déjà sélectionnée (active): '{raw_label}'", "info")
                                return True
                            btn.click()
                            log(f"[Lollybet] ✅ Clic cote (IA): '{raw_label}'", "info")
                            return True
                    except Exception:
                        continue
            log(f"[Lollybet] IA n'a pas trouvé de bouton pour '{search_label}', disponibles: {[lm[0] for lm in label_map[:20]]}", "warning")
        elif not label_map:
            log(f"[Lollybet] _click_outcome: aucun bouton visible pour '{search_label}'", "warning")
        return False

    def _check_confirmation(self, sr, driver) -> bool:
        for text in ["pari validé", "pari confirmé", "bet placed", "félicitations", "success"]:
            els = driver.find_elements(By.XPATH, f"//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{text}')]")
            if els:
                return True
        betslip_els = sr.find_elements(By.CSS_SELECTOR, "[class*='betslip'], [class*='slip']")
        for el in betslip_els:
            t = el.text.lower()
            if "validé" in t or "confirmé" in t or "placé" in t or "placed" in t:
                return True
        return False

    def place_bet(self, driver, match_url: str, selection: str, categorie: str, mise: float, intitule: str = "") -> bool:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)
            _scroll_to_load_markets(driver)

            sr = _wait_shadow_root(driver, timeout=15)
            if not sr:
                return False

            from Functions.BetLabelsDB import get_label
            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Lollybet", sport_id, selection)
            search_label = _norm_lollybet(label_bk or selection)

            self._clear_betslip(sr)
            _human_wait(0.4, 0.7)

            if not self._click_outcome(sr, search_label, selection=selection, intitule=intitule):
                log(f"[Lollybet] ❌ Bouton cote '{search_label}' non trouvé", "error")
                return False

            _human_wait(1.2, 2.0)

            if not self._verify_betslip(sr, selection):
                return False

            # Saisir la mise
            stake_inputs = sr.find_elements(By.CSS_SELECTOR, "input[placeholder='Mise'], .sb-betslip-bet-input_buttons__input")
            if stake_inputs:
                inp = stake_inputs[0]
                inp.clear()
                mise_str = f"{mise:.2f}".replace(".", ",")
                inp.send_keys(mise_str)
                log(f"[Lollybet] Mise saisie: {mise_str}", "info")
                _human_wait(0.4, 0.7)
            else:
                log("[Lollybet] ⚠️  Input mise non trouvé", "warning")

            # Cliquer sur Parier
            parier_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-bet-slip-footer-v2__btn_submit, button[class*='submit']")
            if not parier_btns:
                parier_btns = [b for b in sr.find_elements(By.CSS_SELECTOR, "button")
                               if b.text.strip().lower().startswith("parier")]
            if not parier_btns:
                log("[Lollybet] ❌ Bouton Parier non trouvé", "error")
                return False

            log(f"[Lollybet] Clic sur '{parier_btns[0].text.strip()}'", "info")
            parier_btns[0].click()
            _human_wait(2.0, 3.5)

            if self._check_confirmation(sr, driver):
                log("[Lollybet] ✅ Pari validé", "info")
                return True

            log("[Lollybet] ⚠️  Confirmation non détectée", "warning")
            return False

        except Exception as e:
            log(f"[Lollybet] Erreur place_bet: {e}", "error")
            return False

    # ── Interface router ─────────────────────────────────────────────────

    async def run(self, bet: Dict) -> Dict:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._run_sync, bet)

    async def fetch_odds(self, bet: Dict) -> Dict:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._fetch_odds_sync, bet)

    def place_accumulator(self, driver, matches_list: List[Dict], mise: float) -> bool:
        """
        Place un pari combiné (accumulateur) avec plusieurs sélections.
        Ajoute chaque match au betslip sans vider entre chaque, puis place.
        """
        try:
            # Vider le betslip avant de commencer (avec vérification)
            driver.get(LOLLYBET_URL + "/fr/sportsbook#/events/football")
            _human_wait(2.0, 3.0)
            sr = _wait_shadow_root(driver, timeout=15)
            if sr:
                self._clear_betslip(sr)
                _human_wait(0.8, 1.2)
                # Vérification que le betslip est bien vide
                remaining = self._count_betslip_legs(driver, sr)
                if remaining > 0:
                    log(f"[Lollybet] ⚠️  Betslip pas complètement vidé ({remaining} leg(s)), nouvelle tentative", "warning")
                    self._clear_betslip(sr)
                    _human_wait(1.0, 1.5)
                log(f"[Lollybet] Betslip vidé (legs restants: {self._count_betslip_legs(driver, sr)})", "info")

            for i, match in enumerate(matches_list):
                equipe_1 = match.get("equipe_1", "")
                equipe_2 = match.get("equipe_2", "")
                selection = match.get("selection", "")
                sport = str(match.get("sport", "1"))
                date = match.get("date", "")
                intitule = match.get("intitule", "")
                categorie = match.get("categorie", "")

                log(f"[Lollybet] Combiné leg {i+1}/{len(matches_list)}: {equipe_1} vs {equipe_2} | {selection}", "info")
                # Enrichir intitule avec les noms des équipes pour l'IA (handicap numéroté, etc.)
                if not intitule:
                    intitule = f"{equipe_1} vs {equipe_2}"

                match_url = self.search_match(driver, equipe_1, equipe_2, sport, date)
                if not match_url:
                    log(f"[Lollybet] ❌ Match non trouvé: {equipe_1} vs {equipe_2}", "error")
                    return False

                driver.get(match_url)
                _human_wait(1.5, 2.5)

                sr = _wait_shadow_root(driver, timeout=15)
                if not sr:
                    log(f"[Lollybet] ❌ Shadow root non trouvé pour leg {i+1}", "error")
                    return False

                from Functions.BetLabelsDB import get_label
                sport_id = _detect_sport_from_url(match_url)
                label_bk = get_label("Lollybet", sport_id, selection)
                search_label = _norm_lollybet(label_bk or selection)

                if not self._click_outcome(sr, search_label, selection=selection, intitule=intitule):
                    log(f"[Lollybet] ❌ Cote '{search_label}' non trouvée pour leg {i+1}", "error")
                    return False

                _human_wait(1.0, 1.8)
                log(f"[Lollybet] ✅ Leg {i+1} ajouté au betslip", "info")

            # Saisir la mise et placer
            sr = _wait_shadow_root(driver, timeout=15)
            if not sr:
                return False

            _human_wait(1.0, 1.5)

            # Chercher l'input mise du combiné
            stake_inputs = sr.find_elements(By.CSS_SELECTOR, "input[placeholder='Mise'], .sb-betslip-bet-input_buttons__input")
            if stake_inputs:
                # Prendre le dernier input (celui du combiné total)
                inp = stake_inputs[-1]
                inp.clear()
                mise_str = f"{mise:.2f}".replace(".", ",")
                inp.send_keys(mise_str)
                log(f"[Lollybet] Mise combiné saisie: {mise_str}", "info")
                _human_wait(0.4, 0.7)
            else:
                log("[Lollybet] ⚠️  Input mise combiné non trouvé", "warning")

            # Vérification du nombre de legs avant validation
            actual_legs = self._count_betslip_legs(driver, sr)
            expected_legs = len(matches_list)
            log(f"[Lollybet] Betslip: {actual_legs} leg(s) détecté(s), {expected_legs} attendu(s)", "info")
            if actual_legs != expected_legs and actual_legs > 0:
                log(f"[Lollybet] ❌ Coupon incorrect ({actual_legs} != {expected_legs}) — annulation", "error")
                self._clear_betslip(sr)
                return False

            parier_btns = sr.find_elements(By.CSS_SELECTOR, ".sb-bet-slip-footer-v2__btn_submit, button[class*='submit']")
            if not parier_btns:
                parier_btns = [b for b in sr.find_elements(By.CSS_SELECTOR, "button")
                               if b.text.strip().lower().startswith("parier")]
            if not parier_btns:
                log("[Lollybet] ❌ Bouton Parier combiné non trouvé", "error")
                return False

            log(f"[Lollybet] Clic Parier combiné: '{parier_btns[0].text.strip()}'", "info")
            parier_btns[0].click()
            _human_wait(2.0, 3.5)

            if self._check_confirmation(sr, driver):
                log(f"[Lollybet] ✅ Pari combiné validé ({len(matches_list)} legs)", "info")
                return True

            log("[Lollybet] ⚠️  Confirmation combiné non détectée", "warning")
            return False

        except Exception as e:
            log(f"[Lollybet] Erreur place_accumulator: {e}", "error")
            return False

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
                log("[Lollybet] ❌ Session inactive", "error")
                return result

            # Mode combiné (accumulateur)
            if bet.get("is_combined") and bet.get("matches_list"):
                success = self.place_accumulator(driver, bet["matches_list"], float(bet.get("mise", 10)))
                result["success"] = success
                return result

            equipe_1 = bet.get("equipe_1", "")
            equipe_2 = bet.get("equipe_2", "")
            intitule = bet.get("intitule", "") or f"{equipe_1} vs {equipe_2}"
            match_url = self.search_match(driver, equipe_1, equipe_2,
                                          str(bet.get("sport", "")), bet.get("date", ""))
            if not match_url:
                result["error"] = "match_not_found"
                return result
            odds = self.get_odds(driver, match_url, bet.get("selection", ""), bet.get("categorie", ""), intitule=intitule)
            result["odds"] = odds
            success = self.place_bet(driver, match_url, bet.get("selection", ""),
                                     bet.get("categorie", ""), float(bet.get("mise", 10)),
                                     intitule=intitule)
            result["success"] = success
        except Exception as e:
            result["error"] = str(e)
            log(f"[Lollybet] Erreur run: {e}", "error")
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
            result["odds"] = self.get_odds(driver, match_url, bet.get("selection", ""), bet.get("categorie", ""), intitule=bet.get("intitule", ""))
        except Exception as e:
            result["error"] = str(e)
            log(f"[Lollybet] Erreur fetch_odds: {e}", "error")
        return result

    def get_challenges(self, driver=None) -> List[Dict]:
        return []

    def activate_challenge(self, driver=None, challenge: Dict = None) -> bool:
        return False

    def _match_challenge(self, bet: Dict, challenges: List[Dict]):
        return None


# ── Utilitaires ──────────────────────────────────────────────────────────────

def _norm_lollybet(s: str) -> str:
    """Normalise en remplaçant ':' et '-' uniformément."""
    return re.sub(r"\s*[:\-]\s*", "-", s.lower().strip())


def _detect_sport_from_url(url: str) -> str:
    url = url.lower()
    if "tennis" in url:
        return "2"
    if "basket" in url:
        return "4"
    if "rugby" in url:
        return "5"
    if "handball" in url:
        return "8"
    if "hockey" in url:
        return "9"
    return "1"
