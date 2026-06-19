import itertools
import json
import threading
import time

import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pyautogui.FAILSAFE = False  # évite l'arrêt si la souris touche un coin

API_URL = (
    "https://ca.1xbet.com/service-api/main-line-feed/v1/expressDay"
    "?cfView=3&country=85&gr=828&lng=fr&ref=1"
)
CLOUDFLARE_MARKER = "Vérification de sécurité"
MAX_ATTEMPTS = 5

# Coordonnées écran de la case Cloudflare Turnstile (calibrées manuellement)
_checkbox_coords: tuple[int, int] | None = (1549, 1102)


# ---------------------------------------------------------------------------
# Calibration manuelle
# ---------------------------------------------------------------------------

def calibrate_checkbox(driver) -> tuple[int, int] | None:
    """
    Charge la page captcha, demande à l'utilisateur de positionner sa souris
    sur la case à cocher puis d'appuyer sur Entrée.
    Enregistre et retourne les coordonnées écran (x, y).
    """
    global _checkbox_coords

    print("\n" + "=" * 60)
    print("[Calibration] Chargement de la page captcha...")
    driver.get(API_URL)
    time.sleep(2)

    if not _is_captcha_page(driver):
        print("[Calibration] ℹ️  Pas de captcha détecté sur la page — calibration ignorée.")
        return _checkbox_coords

    print("[Calibration] ✅ Page captcha détectée.")
    print("[Calibration] 👉 Placez votre souris SUR LA CASE À COCHER du widget Cloudflare.")
    print("[Calibration]    Appuyez sur ENTRÉE quand la souris est bien positionnée...")
    print("=" * 60)

    # Countdown de 3s pour laisser le temps de se positionner après Entrée
    input("[Calibration] → Appuyez sur ENTRÉE pour enregistrer la position : ")
    x, y = pyautogui.position()
    _checkbox_coords = (x, y)

    print(f"[Calibration] ✅ Coordonnées enregistrées : x={x}, y={y}")
    print("=" * 60 + "\n")
    return _checkbox_coords


# ---------------------------------------------------------------------------
# Popup rouge
# ---------------------------------------------------------------------------

def _show_red_popup(driver, message: str = "⚠️ Vérification Cloudflare en cours...") -> None:
    try:
        driver.execute_script("""
        (function(msg) {
            var el = document.getElementById('__captcha_popup__');
            if (!el) {
                el = document.createElement('div');
                el.id = '__captcha_popup__';
                el.style.cssText = [
                    'position:fixed', 'top:0', 'left:0', 'width:100%',
                    'background:#cc0000', 'color:#fff', 'font-size:20px',
                    'font-weight:bold', 'text-align:center', 'padding:12px 0',
                    'z-index:2147483647', 'letter-spacing:1px'
                ].join(';');
                document.body.appendChild(el);
            }
            el.innerText = msg;
        })(arguments[0]);
        """, message)
    except Exception:
        pass


def _remove_red_popup(driver) -> None:
    try:
        driver.execute_script("""
        var el = document.getElementById('__captcha_popup__');
        if (el) el.parentNode.removeChild(el);
        """)
    except Exception:
        pass


def _bring_chrome_to_front() -> None:
    """Met la fenêtre Chrome au premier plan via AppleScript (macOS)."""
    try:
        import subprocess
        subprocess.call(['osascript', '-e', 'tell application "Google Chrome" to activate'])
        time.sleep(0.4)
        print("[Captcha] ✅ Chrome mis au premier plan.")
    except Exception as e:
        print(f"[Captcha] ⚠️ Impossible de mettre Chrome au premier plan: {e}")


TENNIS_URL = "https://ca.1xbet.com/fr/live/tennis"


# ---------------------------------------------------------------------------
# Détection réseau 403 via CDP
# ---------------------------------------------------------------------------

def enable_network_logging(driver) -> None:
    """No-op — performance logs non disponibles sur cette instance Chrome."""
    print("[CDP] Capture réseau via fetch JS (performance logs non disponibles).")


def check_403_on_tennis_page(driver) -> bool:
    """
    Navigue sur la page tennis live puis exécute un fetch JS vers l'API
    pour vérifier le status HTTP réel (utilise les cookies de session du navigateur).

    Retourne True si le status est 403 (Cloudflare bloque), False sinon.
    """
    print(f"[CDP] Navigation vers {TENNIS_URL}")
    driver.get(TENNIS_URL)
    time.sleep(2)

    print(f"[CDP] Fetch JS vers l'API: {API_URL}")
    try:
        status = driver.execute_async_script("""
            var callback = arguments[arguments.length - 1];
            fetch(arguments[0], {method: 'GET', credentials: 'include'})
                .then(function(r) { callback(r.status); })
                .catch(function(e) { callback(-1); });
        """, API_URL)
        print(f"[CDP] Status HTTP reçu: {status}")
        if status == 403:
            print("[CDP] 🔒 403 détecté — Cloudflare bloque.")
            return True
        print(f"[CDP] ✅ Pas de blocage (status={status}).")
        return False
    except Exception as e:
        print(f"[CDP] Erreur fetch JS: {e}")
        return False


# ---------------------------------------------------------------------------
# Détection page
# ---------------------------------------------------------------------------

def _is_json_page(driver) -> bool:
    """Retourne True si le contenu visible de la page est un JSON valide."""
    for selector in ("pre", "body"):
        try:
            text = driver.find_element(By.TAG_NAME, selector).text.strip()
            json.loads(text)
            return True
        except Exception:
            continue
    return False


def _is_captcha_page(driver) -> bool:
    try:
        return CLOUDFLARE_MARKER in driver.page_source
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Clic sur la case Cloudflare Turnstile
# ---------------------------------------------------------------------------

def _click_captcha_checkbox(driver) -> bool:
    """
    Attend l'apparition du widget Cloudflare Turnstile puis clique sur la case.
    Retourne True si le clic a pu être effectué, False sinon.
    """
    print("[Captcha] Recherche du shadow host...")

    # 1. Attendre le shadow host direct
    shadow_host = None
    for selector in ("#BbLB6 > div > div", "div[style*='display: grid'] > div > div"):
        try:
            shadow_host = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            print(f"[Captcha] Shadow host trouvé avec selector: {selector}")
            break
        except Exception:
            print(f"[Captcha] Selector '{selector}' non trouvé, essai suivant...")
            continue

    if shadow_host is None:
        print("[Captcha] ❌ Shadow host introuvable, abandon.")
        return False

    # 2. Attendre que le shadow host ait des dimensions >= 60px (iframe rendu)
    print("[Captcha] Attente des dimensions du widget (iframe en cours de chargement)...")
    found = False
    for i in range(40):
        try:
            rect = driver.execute_script(
                "var r = arguments[0].getBoundingClientRect();"
                "return {w: r.width, h: r.height};",
                shadow_host
            )
            h = rect.get('h', 0) if rect else 0
            w = rect.get('w', 0) if rect else 0
            print(f"[Captcha] Cycle {i+1}/40 — dimensions: {w}x{h}px")
            if h >= 60:
                print(f"[Captcha] ✅ Widget présent ({w}x{h}px)")
                found = True
                break
        except Exception as e:
            print(f"[Captcha] Erreur getBoundingClientRect: {e}")
        time.sleep(0.5)

    if not found:
        print("[Captcha] ❌ Widget jamais apparu (timeout 20s), abandon.")
        return False

    # 3. Attendre la stabilité de la hauteur (case rendue dans l'iframe)
    print("[Captcha] Attente stabilité de la hauteur (rendu JS interne)...")
    prev_h = 0
    for i in range(20):
        try:
            h = driver.execute_script(
                "return arguments[0].getBoundingClientRect().height;", shadow_host
            )
            print(f"[Captcha] Stabilité {i+1}/20 — height={h} (prev={prev_h})")
            if h == prev_h and h >= 60:
                print("[Captcha] ✅ Hauteur stable, case probablement rendue.")
                break
            prev_h = h
        except Exception:
            pass
        time.sleep(0.3)

    # Marge supplémentaire pour le rendu JS interne à l'iframe
    print("[Captcha] Pause 1s avant clic...")
    time.sleep(1.0)

    # 4. Scroller pour que le widget soit visible
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", shadow_host)
    time.sleep(0.3)

    # 5. Récupérer la position absolue pour le log
    try:
        pos = driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};",
            shadow_host
        )
        print(f"[Captcha] Position widget à l'écran: x={pos['x']} y={pos['y']} ({pos['w']}x{pos['h']})")
        print(f"[Captcha] Clic à offset (25, 32) depuis le coin haut-gauche du widget")
    except Exception:
        pass

    # 6. Clic réel via pyautogui — switch_to.window obligatoire avant le clic physique
    try:
        driver.switch_to.window(driver.current_window_handle)
        print(f"[Captcha] switch_to.window effectué (handle: {driver.current_window_handle})")
    except Exception as e:
        print(f"[Captcha] ⚠️ switch_to.window échoué: {e}")

    if _checkbox_coords is not None:
        x, y = _checkbox_coords
        print(f"[Captcha] Clic via coordonnées calibrées: x={x} y={y}")
        _bring_chrome_to_front()
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click(x, y)
        print("[Captcha] ✅ Clic physique effectué (coordonnées calibrées)")
        return True

    # Fallback : calcul automatique depuis la position de la fenêtre Chrome
    try:
        win = driver.get_window_position()
        print(f"[Captcha] Position fenêtre Chrome: x={win['x']} y={win['y']}")

        vp = driver.execute_script(
            "return {oh: window.outerHeight, ih: window.innerHeight};"
        )
        chrome_h = vp['oh'] - vp['ih']
        print(f"[Captcha] Hauteur chrome navigateur: {chrome_h}px")

        rect = driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {x: r.x, y: r.y, w: r.width, h: r.height};",
            shadow_host
        )
        print(f"[Captcha] Élément viewport: x={rect['x']} y={rect['y']} ({rect['w']}x{rect['h']})")

        screen_x = int(win['x'] + rect['x'] + 25)
        screen_y = int(win['y'] + chrome_h + rect['y'] + 32)
        print(f"[Captcha] Clic automatique à: x={screen_x} y={screen_y}")

        _bring_chrome_to_front()
        pyautogui.moveTo(screen_x, screen_y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click(screen_x, screen_y)
        print("[Captcha] ✅ Clic physique effectué (calcul automatique)")
        return True

    except Exception as e:
        print(f"[Captcha] ❌ Clic échoué: {e}")
        return False


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def check_api_available(driver) -> bool:
    """
    Vérifie que l'API 1xbet répond avec du JSON.

    - Si la réponse est du JSON valide → return True immédiatement.
    - Si une page Cloudflare est détectée → affiche un bandeau rouge,
      tente de cocher la case, attend 10 s, puis réessaie (jusqu'à MAX_ATTEMPTS fois).
    - Return False si le captcha n'est jamais résolu.

    Args:
        driver: instance Selenium positionnée sur la fenêtre 12.

    Returns:
        bool: True si l'API est accessible, False sinon.
    """
    print(f"[Captcha] Chargement de l'URL: {API_URL}")
    driver.get(API_URL)
    time.sleep(1.5)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[Captcha] === Tentative {attempt}/{MAX_ATTEMPTS} ===")

        if _is_json_page(driver):
            print("[Captcha] ✅ JSON détecté — API disponible.")
            _remove_red_popup(driver)
            return True

        if _is_captcha_page(driver):
            print("[Captcha] 🔒 Page Cloudflare détectée.")
            # calibrate_checkbox(driver)  # désactivé — coordonnées fixes (1549, 1102)
            _show_red_popup(
                driver,
                f"⚠️ Captcha Cloudflare — tentative {attempt}/{MAX_ATTEMPTS}. Cocher la case..."
            )
            clicked = _click_captcha_checkbox(driver)

            # Attendre jusqu'à 15s que le captcha se résolve sans recharger la page
            print("[Captcha] Attente résolution captcha (max 15s)...")
            for tick in range(15):
                time.sleep(1)
                if _is_json_page(driver):
                    print(f"[Captcha] ✅ JSON apparu après {tick+1}s — captcha résolu !")
                    _remove_red_popup(driver)
                    return True
                print(f"[Captcha] ... {tick+1}s écoulée(s), pas encore de JSON")

            # Toujours sur la page captcha → réessayer le clic sans recharger
            if _is_captcha_page(driver):
                print("[Captcha] Toujours sur la page captcha — nouveau clic sans rechargement.")
                _click_captcha_checkbox(driver)
                for tick in range(10):
                    time.sleep(1)
                    if _is_json_page(driver):
                        print(f"[Captcha] ✅ JSON apparu après 2e clic ({tick+1}s)")
                        _remove_red_popup(driver)
                        return True
                    print(f"[Captcha] ... {tick+1}s après 2e clic, toujours captcha")

            # Toujours bloqué → recharger pour la prochaine tentative
            print("[Captcha] Rechargement de la page pour la tentative suivante.")
            driver.get(API_URL)
            time.sleep(1.5)
        else:
            print(f"[Captcha] ⚠️ Page inconnue (ni JSON ni captcha) — rechargement.")
            time.sleep(2)
            driver.get(API_URL)
            time.sleep(1.5)

    print("[Captcha] ❌ Échec après toutes les tentatives.")
    return False


# ---------------------------------------------------------------------------
# Surveillance continue (thread background)
# ---------------------------------------------------------------------------

_monitor_thread: threading.Thread | None = None
_monitor_stop = threading.Event()
_cdp_identifier: str | None = None


def _ensure_403_interceptor(driver) -> None:
    """Injecte via CDP un intercepteur fetch/XHR pour collecter les URLs 403. Une seule fois."""
    global _cdp_identifier
    if _cdp_identifier is not None:
        return
    try:
        result = driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                window.__403_urls = [];
                (function() {
                    var _f = window.fetch;
                    window.fetch = function(url, opts) {
                        var u = typeof url === 'string' ? url : (url && url.url) || String(url);
                        return _f.apply(this, arguments).then(function(r) {
                            if (r.status === 403 && u && !window.__403_urls.includes(u))
                                window.__403_urls.push(u);
                            return r;
                        });
                    };
                    var _open = XMLHttpRequest.prototype.open;
                    XMLHttpRequest.prototype.open = function(m, u) {
                        this.__url = u; return _open.apply(this, arguments);
                    };
                    var _send = XMLHttpRequest.prototype.send;
                    XMLHttpRequest.prototype.send = function() {
                        this.addEventListener('load', function() {
                            if (this.status === 403 && this.__url && !window.__403_urls.includes(this.__url))
                                window.__403_urls.push(this.__url);
                        });
                        return _send.apply(this, arguments);
                    };
                })();
            """
        })
        _cdp_identifier = result.get("identifier", "ok")
        print(f"[Monitor] ✅ Intercepteur 403 CDP actif (id={_cdp_identifier})")
    except Exception as e:
        print(f"[Monitor] ⚠️ CDP non dispo, fallback JS fetch: {e}")
        _cdp_identifier = "unavailable"


def _get_403_urls(driver) -> list[str]:
    """
    Navigue sur la page tennis, attend que les requêtes soient émises,
    puis collecte les URLs qui ont retourné 403.
    Retourne [API_URL] en fallback si l'intercepteur CDP n'est pas disponible.
    """
    _ensure_403_interceptor(driver)

    print(f"[Monitor] Navigation → {TENNIS_URL}")
    driver.get(TENNIS_URL)
    time.sleep(4)

    if _cdp_identifier and _cdp_identifier != "unavailable":
        try:
            urls = driver.execute_script("return window.__403_urls || [];") or []
            # Réinitialiser pour le prochain cycle
            driver.execute_script("window.__403_urls = [];")
            if urls:
                print(f"[Monitor] {len(urls)} URL(s) 403 collectée(s) depuis la page tennis")
                return list(set(urls))
            print(f"[Monitor] Aucune URL 403 collectée par CDP")
            return []
        except Exception as e:
            print(f"[Monitor] Erreur lecture URLs CDP: {e}")

    # Fallback : fetch JS vers API_URL
    print(f"[Monitor] Fetch JS → {API_URL[:70]}...")
    try:
        status = driver.execute_async_script("""
            var cb = arguments[arguments.length - 1];
            fetch(arguments[0], {method: 'GET', credentials: 'include'})
                .then(function(r) { cb(r.status); })
                .catch(function() { cb(-1); });
        """, API_URL)
        print(f"[Monitor] Status HTTP: {status}")
        if status == 403:
            print("[Monitor] 🔒 403 confirmé (fallback JS fetch)")
            return [API_URL]
    except Exception as e:
        print(f"[Monitor] Erreur fetch JS: {e}")

    return []


def start_api_monitor(driver, interval: int = 10) -> None:
    """
    Lance un thread qui vérifie l'API toutes les `interval` secondes.
    Si un captcha est détecté, il le résout automatiquement.
    Appeler stop_api_monitor() pour arrêter.

    Args:
        driver: instance Selenium (fenêtre 12 recommandée)
        interval: secondes entre chaque vérification (défaut 10)
    """
    global _monitor_thread, _monitor_stop

    if _monitor_thread is not None and _monitor_thread.is_alive():
        print("[Monitor] ⚠️ Surveillance déjà en cours.")
        return

    _monitor_stop.clear()

    def _loop():
        print(f"[Monitor] ▶ Surveillance démarrée (intervalle {interval}s)")
        while not _monitor_stop.is_set():
            try:
                current_url = driver.current_url

                # Collecte les URLs 403 depuis la page tennis (CDP ou fetch JS)
                urls_403 = _get_403_urls(driver)

                if not urls_403:
                    print(f"[Monitor] ✅ API OK — {time.strftime('%H:%M:%S')}")
                    _remove_red_popup(driver)
                else:
                    print(f"[Monitor] 🔒 {len(urls_403)} URL(s) bloquée(s) — résolution captcha...")
                    _show_red_popup(driver, "⚠️ Captcha Cloudflare en cours de résolution...")

                    resolved = False
                    url_iter = itertools.cycle(urls_403)  # rotation sur les URLs 403 réelles

                    for click_attempt in range(1, 11):
                        captcha_url = next(url_iter)
                        print(f"[Monitor] Clic #{click_attempt}/10 → {captcha_url[:70]}...")
                        driver.get(captcha_url)

                        print(f"[Monitor] Attente 10s pour l'apparition de la case...")
                        time.sleep(10)

                        _bring_chrome_to_front()
                        driver.switch_to.window(driver.current_window_handle)
                        _click_captcha_checkbox(driver)

                        for tick in range(5):
                            time.sleep(1)
                            if _is_json_page(driver):
                                print(f"[Monitor] ✅ Captcha résolu — clic #{click_attempt}, {tick+1}s")
                                _remove_red_popup(driver)
                                resolved = True
                                break
                            print(f"[Monitor] ... clic #{click_attempt} — {tick+1}s")
                        if resolved:
                            break
                        print(f"[Monitor] Clic #{click_attempt} sans effet → URL suivante")

                    if not resolved:
                        print("[Monitor] ❌ Captcha non résolu après 10 clics.")

                if driver.current_url != current_url:
                    try:
                        driver.get(current_url)
                    except Exception:
                        pass

            except Exception as e:
                print(f"[Monitor] ❌ Erreur: {e}")

            _monitor_stop.wait(interval)

        print("[Monitor] ⏹ Surveillance arrêtée.")

    _monitor_thread = threading.Thread(target=_loop, daemon=True, name="ApiMonitor")
    _monitor_thread.start()


def stop_api_monitor() -> None:
    """Arrête le thread de surveillance."""
    global _monitor_thread
    _monitor_stop.set()
    if _monitor_thread is not None:
        _monitor_thread.join(timeout=5)
        _monitor_thread = None
    print("[Monitor] ⏹ Surveillance arrêtée.")


# ---------------------------------------------------------------------------
# Utilisation directe (fenêtre 12)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import config as _config
    _config.localhost = 43151  # port Chrome debug — à ajuster si besoin

    from ChromeDriver.SetDriver import get_script_driver

    _driver = get_script_driver(12)

    # Vérification initiale + calibration si captcha présent
    check_api_available(_driver)

    # Surveillance continue toutes les 10 secondes
    start_api_monitor(_driver, interval=10)

    # Garder le script actif
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_api_monitor()
        print("Arrêt.")