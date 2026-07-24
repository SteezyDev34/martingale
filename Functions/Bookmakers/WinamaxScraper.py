# -*- coding: utf-8 -*-
"""
Scraper Selenium pour Winamax — fenêtre 9 du driver partagé (port 43151).
DOM standard (pas de shadow root).
"""
import os
import re
import time
import random
from typing import Optional, List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Functions.BetLabelsDB import get_label, upsert_label, clear_challenges, insert_challenge
from Functions.Logs.Logger import log

WINAMAX_URL    = "https://www.winamax.fr"
SPORTS_URL     = "https://www.winamax.fr/paris-sportifs/sports"
LOGIN_URL      = "https://www.winamax.fr/account/login.php?redir=/"
WINAMAX_WINDOW = 9

SPORTS_MAP = {
    "1": "1",   # football
    "2": "5",   # tennis
    "3": "1",
    "4": "4",   # basketball
    "5": "6",   # rugby
    "8": "8",   # handball
    "9": "9",   # hockey
}

SEL_SESSION   = ["a[href*='account/dashboard']", "div.name",
                 "a[href*='/account/']", "[class*='UserMenu']", "[class*='userBalance']"]
SEL_SEARCH    = "input[placeholder='Rechercher']"
SEL_RESULT    = ".search-row-result"
SEL_ODD_WRAP  = ".bet-group-outcome-odd"
SEL_ODD_BTN   = ".odd-button-wrapper"
SEL_ODD_VAL   = "span.odd-button-value"
SEL_STAKE_INP = "input.sc-bSoiow"


def _norm(s: str) -> str:
    return re.sub(r"\s*-\s*", "-", s.lower().strip())


def _human_wait(a: float = 0.8, b: float = 1.5):
    import random
    time.sleep(a + random.random() * (b - a))


class WinamaxScraper:
    name = "Winamax"
    requires_vpn = False

    def _get_driver(self):
        import config
        from ChromeDriver.SetDriver import get_script_driver
        return get_script_driver(WINAMAX_WINDOW)

    # ── Session ──────────────────────────────────────────────────────────

    def is_logged_in(self, driver) -> bool:
        try:
            driver.get("https://www.winamax.fr/account/dashboard")
            _human_wait(2.5, 3.5)
            # URL doit contenir dashboard sans redirection vers login
            if "login" in driver.current_url or "dashboard" not in driver.current_url:
                return False
            # Verifier qu'un element authentifie est present (pas juste l'URL)
            for sel in ["[class*='userBalance']", "[class*='UserMenu']",
                        "[class*='accountMenu']", "div.name", "[class*='balance']"]:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    if el.is_displayed() and el.text.strip():
                        log(f"[Winamax] Session active ({sel})", "info")
                        return True
            # Si bouton "Se connecter" visible → non connecte
            for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
                if "se connecter" in (el.text or "").lower() and el.is_displayed():
                    log("[Winamax] Bouton 'Se connecter' visible — non connecte", "info")
                    return False
            return False
        except Exception as e:
            log(f"[Winamax] Erreur is_logged_in: {e}", "error")
            return False

    # ── Login automatique ────────────────────────────────────────────────

    # ── CDP Stealth ──────────────────────────────────────────────────────

    _CDP_STEALTH = """
        /* --- webdriver --- */
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        /* --- plugins realistes --- */
        const makePlugin = (name, filename, desc, mimetypes) => {
            const p = Object.create(Plugin.prototype);
            Object.defineProperties(p, {
                name: {value: name}, filename: {value: filename}, description: {value: desc},
                length: {value: mimetypes.length}
            });
            mimetypes.forEach((mt, i) => { p[i] = mt; });
            return p;
        };
        const makeMime = (type, suf, desc) => {
            const m = Object.create(MimeType.prototype);
            Object.defineProperties(m, {
                type: {value: type}, suffixes: {value: suf}, description: {value: desc}
            });
            return m;
        };
        const pdfPlugin = makePlugin('PDF Viewer','internal-pdf-viewer','Portable Document Format',
            [makeMime('application/pdf','pdf','Portable Document Format')]);
        Object.defineProperty(navigator, 'plugins', {get: () => {
            const arr = [pdfPlugin];
            arr.refresh = () => {};
            return arr;
        }});

        /* --- langues --- */
        Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR','fr','en-US','en']});

        /* --- platform --- */
        Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});

        /* --- hardwareConcurrency --- */
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});

        /* --- deviceMemory --- */
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});

        /* --- chrome runtime complet --- */
        window.chrome = {
            app: {isInstalled: false, InstallState: {DISABLED:'disabled',INSTALLED:'installed',NOT_INSTALLED:'not_installed'}, RunningState: {CANNOT_RUN:'cannot_run',READY_TO_RUN:'ready_to_run',RUNNING:'running'}},
            runtime: {
                OnInstalledReason: {CHROME_UPDATE:'chrome_update',INSTALL:'install',SHARED_MODULE_UPDATE:'shared_module_update',UPDATE:'update'},
                OnRestartRequiredReason: {APP_UPDATE:'app_update',OS_UPDATE:'os_update',PERIODIC:'periodic'},
                PlatformArch: {ARM:'arm',ARM64:'arm64',MIPS:'mips',MIPS64:'mips64',X86_32:'x86-32',X86_64:'x86-64'},
                PlatformNaclArch: {ARM:'arm',MIPS:'mips',MIPS64:'mips64',X86_32:'x86-32',X86_64:'x86-64'},
                PlatformOs: {ANDROID:'android',CROS:'cros',LINUX:'linux',MAC:'mac',OPENBSD:'openbsd',WIN:'win'},
                RequestUpdateCheckStatus: {NO_UPDATE:'no_update',THROTTLED:'throttled',UPDATE_AVAILABLE:'update_available'}
            },
            loadTimes: function() { return {commitLoadTime: Date.now()/1000 - 0.3, connectionInfo: 'h2', finishDocumentLoadTime: 0, finishLoadTime: 0, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now()/1000 - 0.1, navigationType: 'Other', npnNegotiatedProtocol: 'h2', requestTime: Date.now()/1000 - 0.5, startLoadTime: Date.now()/1000 - 0.4, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: true, wasNpnNegotiated: true}; },
            csi: function() { return {onloadT: Date.now(), pageT: Math.random()*1000+500, startE: Date.now()-1000, tran: 15}; }
        };

        /* --- permissions spoofing --- */
        const _query = window.Permissions && Permissions.prototype.query;
        if (_query) {
            Permissions.prototype.query = function(params) {
                return params && params.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : _query.apply(this, arguments);
            };
        }

        /* --- iFrame contentWindow spoofing (hCaptcha check) --- */
        const _iFrame = HTMLIFrameElement.prototype;
        const _desc = Object.getOwnPropertyDescriptor(_iFrame, 'contentWindow');
        if (_desc) {
            Object.defineProperty(_iFrame, 'contentWindow', {
                get: function() {
                    const win = _desc.get.apply(this);
                    if (!win) return win;
                    try {
                        Object.defineProperty(win.navigator, 'webdriver', {get: () => undefined});
                    } catch(e) {}
                    return win;
                }
            });
        }
    """

    @staticmethod
    def _get_chrome_h(driver):
        """Hauteur de la barre Chrome (onglets+adresse). Appeler depuis le contexte principal."""
        try:
            inner_h = driver.execute_script("return window.innerHeight;")
            return driver.get_window_size()["height"] - inner_h
        except Exception:
            return 72

    @staticmethod
    def _screen_coords(driver, element, chrome_h=72):
        """Coordonnées écran réelles. chrome_h doit être calculé hors iframe."""
        win_pos = driver.get_window_position()
        # Position de l'élément dans le viewport (fonctionne même en iframe via getBoundingClientRect)
        # + traversée des iframes parentes pour obtenir la position dans le doc top-level
        coords = driver.execute_script("""
            var el = arguments[0];
            var r = el.getBoundingClientRect();
            var cx = r.left + r.width  * 0.5;
            var cy = r.top  + r.height * 0.5;
            var frame = window.frameElement;
            while (frame) {
                var fr = frame.getBoundingClientRect();
                cx += fr.left;
                cy += fr.top;
                try { frame = frame.ownerDocument.defaultView.frameElement; }
                catch(e) { break; }
            }
            return {x: cx, y: cy};
        """, element)
        ox = random.randint(-5, 5)
        oy = random.randint(-3, 3)
        return int(win_pos["x"] + coords["x"] + ox), int(win_pos["y"] + chrome_h + coords["y"] + oy)

    @staticmethod
    def _human_move_click(driver, element, chrome_h=72):
        """Vraie souris OS : trajectoire courbe puis clic. Aucun fallback Selenium."""
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            tx, ty = WinamaxScraper._screen_coords(driver, element, chrome_h)
            log(f"[Winamax] Mouse click → ({tx}, {ty})", "info")
            cx, cy = pyautogui.position()
            steps = random.randint(4, 7)
            for i in range(1, steps + 1):
                t = i / steps
                mx = cx + (tx - cx) * t + random.randint(-8, 8)
                my = cy + (ty - cy) * t + random.randint(-6, 6)
                pyautogui.moveTo(int(mx), int(my), duration=random.uniform(0.03, 0.09))
            pyautogui.moveTo(tx, ty, duration=random.uniform(0.05, 0.12))
            time.sleep(random.uniform(0.08, 0.18))
            pyautogui.click()
            time.sleep(random.uniform(0.12, 0.28))
        except Exception as e:
            log(f"[Winamax] ERREUR mouse click: {e}", "error")

    @staticmethod
    def _human_type(text: str):
        """Frappe irrégulière via presse-papier (layout-agnostic, AZERTY-safe)."""
        try:
            import pyautogui
            import subprocess
            pyautogui.FAILSAFE = False
            # Sauvegarder le presse-papier original
            try:
                original = subprocess.check_output(['pbpaste']).decode('utf-8')
            except Exception:
                original = ''
            for char in text:
                # Copier le caractère dans le presse-papier
                subprocess.run(['pbcopy'], input=char.encode('utf-8'), check=False)
                time.sleep(0.03)
                # Coller via Cmd+V (indépendant du layout clavier)
                pyautogui.hotkey('command', 'v')
                # Délai irrégulier humain
                time.sleep(random.uniform(0.06, 0.20))
                if random.random() < 0.07:
                    time.sleep(random.uniform(0.2, 0.6))
            # Restaurer le presse-papier
            try:
                subprocess.run(['pbcopy'], input=original.encode('utf-8'), check=False)
            except Exception:
                pass
        except Exception:
            pass  # Fallback géré par l'appelant

    @staticmethod
    def _clear_type(driver, element, text: str, chrome_h=72):
        """Clic souris sur le champ, effacement, frappe irrégulière AZERTY-safe."""
        WinamaxScraper._human_move_click(driver, element, chrome_h)
        time.sleep(0.25)
        try:
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            element.send_keys(Keys.DELETE)
            time.sleep(0.15)
        except Exception:
            pass
        WinamaxScraper._human_type(text)

    def login(self, driver) -> bool:
        """Connexion via modal homepage avec 3 retries (rechargement page entre chaque)."""
        email    = os.getenv("WINAMAX_EMAIL", "")
        password = os.getenv("WINAMAX_PASSWORD", "")
        if not email or not password:
            log("[Winamax] Credentials manquants (WINAMAX_EMAIL / WINAMAX_PASSWORD)", "error")
            return False

        driver.set_window_size(1440, 900)
        _human_wait(0.5, 1.0)
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                                   {"source": self._CDP_STEALTH})
        except Exception:
            pass

        for attempt in range(1, 4):
            log(f"[Winamax] Tentative {attempt}/3 avec {email}...", "info")
            try:
                if self._attempt_login(driver, email, password):
                    return True
            except Exception as e:
                log(f"[Winamax] Erreur tentative {attempt}: {e}", "error")
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
            if attempt < 3:
                log("[Winamax] Rechargement avant retry...", "info")
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
                driver.get(WINAMAX_URL)
                _human_wait(3.0, 4.0)

        log("[Winamax] Echec apres 3 tentatives", "error")
        return False

    def _attempt_login(self, driver, email: str, password: str) -> bool:
        """Flux complet : homepage → modal → email → password → submit → DOB → validation."""
        dob = os.getenv("WINAMAX_DOB", "")

        # 1. Page d'accueil
        driver.get(WINAMAX_URL)
        _human_wait(3.5, 5.0)

        # Fermer banniere cookies avec la souris
        for sel in ["#tarteaucitronPersonalize2", "#tarteaucitronAllAllowed"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].is_displayed():
                self._human_move_click(driver, els[0])
                _human_wait(0.8, 1.5)
                break

        # 2. Clic "Se connecter" (bouton visible avec ce texte exact)
        se_connecter = None
        for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
            try:
                if not el.is_displayed():
                    continue
                txt = (el.text or "").lower().strip()
                if txt in ("se connecter", "connexion", "se connecter / s'inscrire",
                           "se connecter/s'inscrire"):
                    se_connecter = el
                    break
            except Exception:
                continue
        if not se_connecter:
            log("[Winamax] Bouton 'Se connecter' introuvable", "error")
            return False

        # Calculer chrome_h ici (contexte principal, pas d'iframe)
        chrome_h = self._get_chrome_h(driver)
        log(f"[Winamax] chrome_h={chrome_h}px | Clic '{se_connecter.text.strip()}'", "info")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", se_connecter)
        time.sleep(0.4)
        self._human_move_click(driver, se_connecter, chrome_h)
        _human_wait(3.0, 4.5)

        # 3. Attente apparition de la modal (iframe avec champ email)
        login_frame = None
        EMAIL_SELS = [
            "input[placeholder='Email ou numéro de mobile']",
            "input[type='email']",
            "input[autocomplete*='email']",
            "input[autocomplete='username']",
        ]
        for _ in range(20):
            for frame in driver.find_elements(By.CSS_SELECTOR, "iframe"):
                try:
                    driver.switch_to.frame(frame)
                    for sel in EMAIL_SELS:
                        if driver.find_elements(By.CSS_SELECTOR, sel):
                            login_frame = frame
                            break
                    if login_frame:
                        break
                    driver.switch_to.default_content()
                except Exception:
                    driver.switch_to.default_content()
            if login_frame:
                break
            driver.switch_to.default_content()
            time.sleep(0.6)

        if not login_frame:
            log("[Winamax] Modal de login non trouvee", "error")
            driver.switch_to.default_content()
            return False

        # On est dans l'iframe
        email_inp, pwd_inp = None, None
        for sel in EMAIL_SELS:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                email_inp = els[0]
                break
        for sel in ["input[placeholder='Mot de passe']", "input[type='password']"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                pwd_inp = els[0]
                break

        if not email_inp or not pwd_inp:
            driver.switch_to.default_content()
            log("[Winamax] Champs email/password introuvables", "error")
            return False

        # 4. Clic champ email + remplissage (chrome_h calculé hors iframe)
        self._clear_type(driver, email_inp, email, chrome_h)
        _human_wait(0.5, 1.0)

        # 5. Clic champ mot de passe + remplissage
        self._clear_type(driver, pwd_inp, password, chrome_h)
        _human_wait(0.6, 1.2)

        # 6. Clic bouton "Se connecter" du formulaire (celui dans l'iframe, pas la navbar)
        submit = None
        for btn in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button"):
            try:
                if btn.is_displayed():
                    submit = btn
                    break
            except Exception:
                pass
        if not submit:
            driver.switch_to.default_content()
            log("[Winamax] Bouton submit du formulaire introuvable", "error")
            return False
        log(f"[Winamax] Clic submit formulaire: {submit.text.strip()!r}", "info")
        self._human_move_click(driver, submit, chrome_h)

        driver.switch_to.default_content()
        _human_wait(4.0, 6.0)

        # 7. Attente et remplissage du champ DOB (date de naissance)
        if dob:
            dob_filled = False
            for _ in range(15):
                # Chercher le champ DOB dans la page ou dans une iframe
                dob_inp = self._find_dob_field(driver)
                if dob_inp:
                    log(f"[Winamax] Champ DOB trouve, remplissage: {dob}", "info")
                    self._clear_type(driver, dob_inp["element"], dob)
                    if dob_inp["in_frame"]:
                        driver.switch_to.default_content()
                    _human_wait(0.5, 1.0)
                    # Clic bouton de validation DOB
                    val_btn = self._find_dob_submit(driver)
                    if val_btn:
                        log("[Winamax] Clic validation DOB", "info")
                        self._human_move_click(driver, val_btn["element"])
                        if val_btn["in_frame"]:
                            driver.switch_to.default_content()
                    dob_filled = True
                    break
                time.sleep(0.8)
            if not dob_filled:
                log("[Winamax] Champ DOB non apparu — peut-etre pas requis", "warning")

        _human_wait(4.0, 6.0)

        # 8. Verification connexion reussie
        for sel in ["[class*='userBalance']", "[class*='UserMenu']",
                    "[class*='accountMenu']", "div.name", "[class*='balance']"]:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if el.is_displayed() and el.text.strip():
                        log(f"[Winamax] Connexion reussie ({sel})", "info")
                        return True
                except Exception:
                    pass
        for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
            try:
                if "se connecter" in (el.text or "").lower() and el.is_displayed():
                    log("[Winamax] Echec — bouton Se connecter encore visible", "error")
                    return False
            except Exception:
                pass
        log("[Winamax] Statut inconnu apres soumission", "warning")
        return False

    def _find_dob_field(self, driver):
        """Cherche le champ DOB dans la page ou dans les iframes."""
        DOB_SELS = [
            "input[placeholder*='naissance']", "input[placeholder*='birth']",
            "input[placeholder*='JJ/MM/AAAA']", "input[placeholder*='DD/MM']",
            "input[name*='birth']", "input[name*='dob']", "input[id*='birth']",
            "input[id*='dob']", "input[autocomplete*='bday']",
        ]
        # Page principale
        for sel in DOB_SELS:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els and els[0].is_displayed():
                return {"element": els[0], "in_frame": False}
        # Dans les iframes
        for frame in driver.find_elements(By.CSS_SELECTOR, "iframe"):
            try:
                driver.switch_to.frame(frame)
                for sel in DOB_SELS:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    if els and els[0].is_displayed():
                        return {"element": els[0], "in_frame": True}
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()
        return None

    def _find_dob_submit(self, driver):
        """Cherche le bouton de validation apres saisie DOB."""
        for el in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button"):
            try:
                if el.is_displayed() and el.text.strip():
                    return {"element": el, "in_frame": False}
            except Exception:
                pass
        for frame in driver.find_elements(By.CSS_SELECTOR, "iframe"):
            try:
                driver.switch_to.frame(frame)
                for el in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button"):
                    if el.is_displayed() and el.text.strip():
                        return {"element": el, "in_frame": True}
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()
        return None

    # ── Recherche de match ───────────────────────────────────────────────

    def search_match(self, driver, equipe_1: str, equipe_2: str, sport: str, date: str) -> Optional[str]:
        try:
            sport_id = SPORTS_MAP.get(str(sport), "1")
            driver.get(f"{SPORTS_URL}/{sport_id}")
            _human_wait(1.5, 2.5)

            e1, e2 = equipe_1.lower(), equipe_2.lower()

            search_box = driver.find_elements(By.CSS_SELECTOR, SEL_SEARCH)
            if not search_box:
                log("[Winamax] Barre de recherche introuvable", "error")
                return None

            search_box = search_box[0]
            search_box.click()
            _human_wait(0.3, 0.5)
            search_box.send_keys(equipe_1)
            _human_wait(1.5, 2.5)

            url = self._pick_result(driver, e1, e2)
            if url:
                return url

            # fallback equipe_2
            search_box.clear()
            search_box.send_keys(equipe_2)
            _human_wait(1.5, 2.5)
            return self._pick_result(driver, e1, e2)

        except Exception as e:
            log(f"[Winamax] Erreur search_match: {e}", "error")
            return None

    def _pick_result(self, driver, e1: str, e2: str) -> Optional[str]:
        results = driver.find_elements(By.CSS_SELECTOR, SEL_RESULT)
        for r in results:
            try:
                text = r.text.lower()
                if e1 in text and e2 in text:
                    log(f"[Winamax] ✅ Match trouvé: {r.text[:60]}", "info")
                    r.click()
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
            label_bk = get_label("Winamax", sport_id, selection)
            search_label = _norm(label_bk or selection)

            containers = driver.find_elements(By.CSS_SELECTOR, SEL_ODD_WRAP)
            for c in containers:
                if search_label in _norm(c.text):
                    val_els = c.find_elements(By.CSS_SELECTOR, SEL_ODD_VAL)
                    if val_els:
                        raw = val_els[0].text.strip().replace(",", ".")
                        try:
                            return float(raw)
                        except ValueError:
                            pass

            log(f"[Winamax] Cote non trouvée pour: {selection}", "warning")
            return None
        except Exception as e:
            log(f"[Winamax] Erreur get_odds: {e}", "error")
            return None

    # ── Placement ────────────────────────────────────────────────────────

    def place_bet(self, driver, match_url: str, selection: str, categorie: str, mise: float) -> bool:
        try:
            driver.get(match_url)
            _human_wait(1.5, 2.5)

            sport_id = _detect_sport_from_url(match_url)
            label_bk = get_label("Winamax", sport_id, selection)
            search_label = _norm(label_bk or selection)

            clicked = False
            containers = driver.find_elements(By.CSS_SELECTOR, SEL_ODD_WRAP)
            for c in containers:
                if search_label in _norm(c.text):
                    btns = c.find_elements(By.CSS_SELECTOR, SEL_ODD_BTN)
                    if btns:
                        driver.execute_script("arguments[0].click();", btns[0])
                        clicked = True
                        break

            if not clicked:
                log(f"[Winamax] ❌ Bouton cote non trouvé pour: {selection}", "error")
                return False

            _human_wait(0.8, 1.5)

            # Saisir la mise
            stake_inputs = driver.find_elements(By.CSS_SELECTOR, SEL_STAKE_INP)
            if not stake_inputs:
                stake_inputs = driver.find_elements(By.CSS_SELECTOR,
                    "[class*='betslip'] input, [class*='Betslip'] input")
            if stake_inputs:
                inp = stake_inputs[0]
                driver.execute_script("arguments[0].click();", inp)
                inp.send_keys(Keys.CONTROL + "a")
                inp.send_keys(f"{mise:.2f}".replace(".", ","))
            _human_wait(0.5, 1.0)

            # Cliquer "Parier"
            confirm = None
            for btn in driver.find_elements(By.CSS_SELECTOR, "button"):
                if "parier" in btn.text.lower():
                    confirm = btn
                    break

            if confirm:
                driver.execute_script("arguments[0].click();", confirm)
                _human_wait(2.0, 3.5)
                for txt in ["Ton pari est validé", "pari validé", "validé"]:
                    els = driver.find_elements(By.XPATH, f"//*[contains(text(), '{txt}')]")
                    if els:
                        log("[Winamax] ✅ Pari validé", "info")
                        return True
                log("[Winamax] ⚠️  Confirmation non détectée — pari peut-être placé", "warning")
                return True

            log("[Winamax] ❌ Bouton Parier non trouvé", "error")
            return False
        except Exception as e:
            log(f"[Winamax] Erreur place_bet: {e}", "error")
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
                log("[Winamax] ❌ Session inactive", "error")
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
            log(f"[Winamax] Erreur run: {e}", "error")
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
            log(f"[Winamax] Erreur fetch_odds: {e}", "error")
        return result

    def get_challenges(self, driver=None) -> List[Dict]:
        return []

    def activate_challenge(self, driver=None, challenge: Dict = None) -> bool:
        return False

    def _match_challenge(self, bet: Dict, challenges: List[Dict]):
        return None


def _detect_sport_from_url(url: str) -> str:
    url = url.lower()
    if "tennis" in url or "/5" in url:
        return "2"
    if "basket" in url or "/4" in url:
        return "4"
    if "rugby" in url or "/6" in url:
        return "5"
    if "handball" in url or "/8" in url:
        return "8"
    if "hockey" in url or "/9" in url:
        return "9"
    return "1"
