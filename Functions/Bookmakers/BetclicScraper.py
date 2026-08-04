# -*- coding: utf-8 -*-
"""
Scraper Selenium pour Betclic — fenêtre 10 du driver partagé (port 43151).
DOM Angular standard (pas de shadow root).
"""
import os
import re
import time
import random
from typing import Optional, List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Functions.BetLabelsDB import get_label, clear_challenges, insert_challenge
from Functions.Logs.Logger import log

BETCLIC_URL    = "https://www.betclic.fr"
LOGIN_URL      = f"{BETCLIC_URL}/connexion"
BETCLIC_WINDOW = 10

SPORTS_MAP = {
    "1": "football-sfootball",
    "2": "tennis-stennis",
    "3": "football-sfootball",
    "4": "basketball-sbasketball",
    "5": "rugby-srugby",
    "8": "handball-shandball",
    "9": "hockey-sur-glace-shockey",
}

SEL_SESSION   = ["[class*='balance']", "[class*='userAccount']", "[data-automation-id='user-balance']",
                 "[class*='accountMenu']", "betclic-header-user", "[data-cy='header-balance']",
                 "[class*='headerUser']", "[class*='balanceAmount']"]
SEL_SEARCH    = "input[placeholder*='Joueur']"
SEL_CARD      = "a.cardEvent"
SEL_ODD_BTN   = "button.btn.is-odd"
SEL_MARKET    = "[class*='market']"
SEL_MKT_LABEL = ".marketBox_label"
SEL_STAKE_INP = "input[placeholder='Mise']"


def _norm(s: str) -> str:
    return re.sub(r"\s*-\s*", "-", s.lower().strip())


def _human_wait(a: float = 0.8, b: float = 1.5):
    import random
    time.sleep(a + random.random() * (b - a))


class BetclicScraper:
    name = "Betclic"
    requires_vpn = False

    def _get_driver(self):
        import config
        from ChromeDriver.SetDriver import get_script_driver
        return get_script_driver(BETCLIC_WINDOW)

    # ── Session ──────────────────────────────────────────────────────────

    def is_logged_in(self, driver) -> bool:
        try:
            driver.get(BETCLIC_URL)
            _human_wait(1.5, 2.5)
            for sel in SEL_SESSION:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    if el.text.strip():
                        log(f"[Betclic] ✅ Session active ({sel}) → '{el.text.strip()[:30]}'", "info")
                        return True
            return False
        except Exception as e:
            log(f"[Betclic] Erreur is_logged_in: {e}", "error")
            return False

    # ── Login automatique ────────────────────────────────────────────────

    def login(self, driver) -> bool:
        """Connexion automatique Betclic — frappe humaine caractere par caractere."""
        try:
            username = os.getenv("BETCLIC_USERNAME", "")
            password = os.getenv("BETCLIC_PASSWORD", "")
            if not username or not password:
                log("[Betclic] Credentials manquants (BETCLIC_USERNAME / BETCLIC_PASSWORD)", "error")
                return False

            log(f"[Betclic] Connexion avec {username}...", "info")
            driver.get(LOGIN_URL)
            _human_wait(3.0, 4.5)

            # Fermer banniere cookies Betclic (TC Privacy)
            for cookie_sel in ["#popin_tc_privacy_button_2",   # "Tout accepter"
                                "#popin_tc_privacy_button_3",   # "Continuer sans accepter"
                                "#tc-privacy-button-accept", ".tc-button-accept"]:
                els = driver.find_elements(By.CSS_SELECTOR, cookie_sel)
                if els:
                    try:
                        driver.execute_script("arguments[0].click();", els[0])
                        _human_wait(0.8, 1.2)
                    except Exception:
                        pass
                    break
            else:
                # Fallback : masquer le wrapper si bouton non trouve
                driver.execute_script("""
                    var el = document.getElementById('tc-privacy-wrapper');
                    if (el) el.style.display = 'none';
                """)
            _human_wait(0.3, 0.5)

            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[autocomplete='username']")
            if not text_inputs:
                text_inputs = [inp for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                               if inp.get_attribute("name") != "query"]
            pwd_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")

            if not text_inputs or not pwd_inputs:
                log("[Betclic] Champs login/password introuvables", "error")
                return False

            login_inp = text_inputs[0]
            pwd_inp = pwd_inputs[0]

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_inp)
            _human_wait(0.3, 0.5)

            self._clear_type(driver, login_inp, username)
            _human_wait(0.4, 0.7)

            self._clear_type(driver, pwd_inp, password)
            _human_wait(0.3, 0.5)

            # Soumettre via le bouton ou Enter
            connexion_btn = None
            for btn in driver.find_elements(By.CSS_SELECTOR, "button.btn.is-primary"):
                if "connexion" in btn.text.strip().lower():
                    connexion_btn = btn
                    break
            if connexion_btn:
                driver.execute_script("arguments[0].click();", connexion_btn)
            else:
                pwd_inp.send_keys(Keys.RETURN)

            _human_wait(5.0, 7.0)

            # Verif sans re-naviguer (is_logged_in() fait driver.get → risque de boucle)
            for sel in ["[class*='balance']", "[class*='userAccount']", "betclic-header-user",
                        "[data-cy='header-balance']", "[class*='headerUser']"]:
                for el in driver.find_elements(By.CSS_SELECTOR, sel):
                    if el.text.strip():
                        log(f"[Betclic] Connexion reussie", "info")
                        return True

            log("[Betclic] Echec connexion — session non active apres login", "error")
            return False

        except Exception as e:
            log(f"[Betclic] Erreur login: {e}", "error")
            return False

    @staticmethod
    def _clear_type(driver, element, text: str):
        """execCommand insertText — identique a l'autofill navigateur, Angular-compatible."""
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].select();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, arguments[1]);
            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));
        """, element, text)
        time.sleep(0.2)

    # ── Recherche de match ───────────────────────────────────────────────

    def search_match(self, driver, equipe_1: str, equipe_2: str, sport: str, date: str) -> Optional[str]:
        try:
            sport_slug = SPORTS_MAP.get(str(sport), "football-sfootball")
            driver.get(f"{BETCLIC_URL}/{sport_slug}")
            _human_wait(1.5, 2.0)

            e1, e2 = equipe_1.lower(), equipe_2.lower()

            search_els = driver.find_elements(By.CSS_SELECTOR, SEL_SEARCH)
            if not search_els:
                log("[Betclic] Barre de recherche introuvable", "error")
                return None

            search_els[0].click()
            _human_wait(0.3, 0.5)
            search_els[0].send_keys(equipe_1)
            _human_wait(1.5, 2.0)

            url = self._pick_card(driver, e1, e2)
            if url:
                return url

            # fallback equipe_2
            search_els = driver.find_elements(By.CSS_SELECTOR, SEL_SEARCH)
            if search_els:
                search_els[0].clear()
                search_els[0].send_keys(equipe_2)
                _human_wait(1.5, 2.0)
                return self._pick_card(driver, e1, e2)

            log(f"[Betclic] Match non trouvé: {equipe_1} vs {equipe_2}", "warning")
            return None
        except Exception as e:
            log(f"[Betclic] Erreur search_match: {e}", "error")
            return None

    def _pick_card(self, driver, e1: str, e2: str) -> Optional[str]:
        cards = driver.find_elements(By.CSS_SELECTOR, SEL_CARD)
        for card in cards:
            try:
                text = card.text.lower()
                if e1 in text and e2 in text:
                    log(f"[Betclic] ✅ Match trouvé: {card.text[:60]}", "info")
                    card.click()
                    _human_wait(1.5, 2.5)
                    return driver.current_url
            except Exception:
                continue
        return None

    # ── Cotes ────────────────────────────────────────────────────────────

    def get_odds(self, driver, match_url: str, selection: str, categorie: str) -> Optional[float]:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)

            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Betclic", sport_id, selection)
            search_label = _norm(label_bk or selection)
            cat_norm = _norm(categorie)

            markets = driver.find_elements(By.CSS_SELECTOR, SEL_MARKET)
            for market in markets:
                market_text = _norm(market.text)
                if cat_norm not in market_text and search_label not in market_text:
                    continue
                label_els = market.find_elements(By.CSS_SELECTOR, SEL_MKT_LABEL)
                for label_el in label_els:
                    if search_label not in _norm(label_el.text):
                        continue
                    # Cherche le bouton is-odd le plus proche via JS
                    btn = driver.execute_script("""
                        var el = arguments[0];
                        for (var i = 0; i < 6; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            var btn = el.querySelector('button.btn.is-odd');
                            if (btn) return btn;
                        }
                        return null;
                    """, label_el)
                    if btn:
                        raw = btn.text.strip().replace(",", ".")
                        try:
                            return float(raw)
                        except ValueError:
                            pass

            log(f"[Betclic] Cote non trouvée pour: {selection}", "warning")
            return None
        except Exception as e:
            log(f"[Betclic] Erreur get_odds: {e}", "error")
            return None

    # ── Placement ────────────────────────────────────────────────────────

    def place_bet(self, driver, match_url: str, selection: str, categorie: str, mise: float) -> bool:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)

            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Betclic", sport_id, selection)
            search_label = _norm(label_bk or selection)
            cat_norm = _norm(categorie)

            self._clear_betslip(driver)

            clicked = False
            markets = driver.find_elements(By.CSS_SELECTOR, SEL_MARKET)
            for market in markets:
                market_text = _norm(market.text)
                if cat_norm not in market_text and search_label not in market_text:
                    continue
                label_els = market.find_elements(By.CSS_SELECTOR, SEL_MKT_LABEL)
                for label_el in label_els:
                    if search_label not in _norm(label_el.text):
                        continue
                    btn = driver.execute_script("""
                        var el = arguments[0];
                        for (var i = 0; i < 6; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            var btn = el.querySelector('button.btn.is-odd');
                            if (btn) return btn;
                        }
                        return null;
                    """, label_el)
                    if btn:
                        log(f"[Betclic] Clic cote '{btn.text.strip()}' — label: '{label_el.text}'", "info")
                        driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                        break
                if clicked:
                    break

            if not clicked:
                log(f"[Betclic] ❌ Bouton cote introuvable: cat='{categorie}' sel='{selection}'", "error")
                return False

            _human_wait(1.5, 2.5)

            if not self._verify_betslip(driver, selection):
                return False

            # Saisir la mise
            stake_inputs = driver.find_elements(By.CSS_SELECTOR, SEL_STAKE_INP)
            if stake_inputs:
                inp = stake_inputs[0]
                driver.execute_script("arguments[0].click();", inp)
                inp.send_keys(Keys.CONTROL + "a")
                inp.send_keys(f"{mise:.2f}".replace(".", ","))
            _human_wait(0.5, 1.0)

            # Cliquer Parier
            confirm = None
            for sel in ["sports-betting-slip button", "betting-slip-footer button", "button"]:
                for btn in driver.find_elements(By.CSS_SELECTOR, sel):
                    if btn.text.strip().lower().startswith("parier"):
                        confirm = btn
                        break
                if confirm:
                    break

            if not confirm:
                log("[Betclic] ❌ Bouton Parier introuvable", "error")
                return False

            disabled = confirm.get_attribute("disabled")
            if disabled:
                log("[Betclic] ❌ Bouton Parier désactivé", "error")
                return False

            driver.execute_script("arguments[0].click();", confirm)
            _human_wait(1.5, 2.5)

            # Détecter confirmation
            for txt in ["Ton pari est validé", "pari est validé", "Super !"]:
                els = driver.find_elements(By.XPATH, f"//*[contains(text(), '{txt}')]")
                if els:
                    log("[Betclic] ✅ Pari validé", "info")
                    return True

            error_els = driver.find_elements(By.CSS_SELECTOR, "[class*='is-negative'], [class*='error']")
            if not error_els:
                log("[Betclic] ⚠️  Confirmation non détectée mais pas d'erreur", "warning")
                return False

            log("[Betclic] ❌ Erreur après clic Parier", "error")
            return False
        except Exception as e:
            log(f"[Betclic] Erreur place_bet: {e}", "error")
            return False

    def _clear_betslip(self, driver) -> None:
        delete_sels = [
            "betting-slip-selection-card button[class*='delete']",
            "betting-slip-selection-card button[class*='remove']",
            "betting-slip-selection-card button[class*='close']",
            "sports-betting-slip [aria-label*='upprimer']",
            "sports-betting-slip [aria-label*='emove']",
            "[class*='betslip'] [class*='delete']",
        ]
        deleted = 0
        for sel in delete_sels:
            for btn in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    _human_wait(0.3, 0.5)
                    deleted += 1
                except Exception:
                    pass
        if deleted:
            log(f"[Betclic] Betslip nettoyé ({deleted} sélection(s))", "info")
            _human_wait(0.5, 0.8)

    def _verify_betslip(self, driver, selection: str) -> bool:
        expected = _norm(selection)
        for sel in ["sports-betting-slip", "[class*='betslip']", "[class*='bet-slip']"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                text = _norm(el.text)
                if text and expected in text:
                    log(f"[Betclic] ✅ Coupon vérifié: '{selection}' présent", "info")
                    return True
        log(f"[Betclic] ❌ '{selection}' absent du coupon", "error")
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
                log("[Betclic] ❌ Session inactive", "error")
                return result
            match_url = self.search_match(driver, bet.get("equipe_1", ""), bet.get("equipe_2", ""),
                                          str(bet.get("sport", "")), bet.get("date", ""))
            if not match_url:
                result["error"] = "match_not_found"
                return result
            odds = self.get_odds(driver, match_url, bet.get("selection", ""), bet.get("categorie", ""))
            result["odds"] = odds
            success = self.place_bet(driver, match_url, bet.get("selection", ""),
                                     bet.get("categorie", ""), float(bet.get("mise", 10)))
            result["success"] = success
        except Exception as e:
            result["error"] = str(e)
            log(f"[Betclic] Erreur run: {e}", "error")
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
            log(f"[Betclic] Erreur fetch_odds: {e}", "error")
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
    if "basketball" in url:
        return "4"
    if "rugby" in url:
        return "5"
    if "handball" in url:
        return "8"
    if "hockey" in url:
        return "9"
    return "1"
