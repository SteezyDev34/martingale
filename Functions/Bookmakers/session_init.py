# -*- coding: utf-8 -*-
"""
Initialisation des sessions bookmakers via Selenium (driver partagé, port 43151).
Navigue vers chaque bookmaker sur la MÊME fenêtre, attend la connexion manuelle,
puis passe au suivant uniquement une fois connecté.
"""
import time
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from selenium.webdriver.common.by import By
from Functions.Logs.Logger import log

LOGIN_URLS = {
    "Stake":    "https://stake.bet/fr",
    "Lollybet": "https://lolly-bet99.com/login",
}

HOME_URLS = {
    "Stake":    "https://stake.bet",
    "Lollybet": "https://lolly-bet99.com",
}

LOGGED_IN_SELECTORS = {
    "Stake":    ["[class*='authenticated']"],
    "Lollybet": ["[class*='balance']", "[class*='wallet']", "[class*='user-balance']",
                 "a[href*='deposit']", "[class*='logged']"],
}

WINDOW_NUMBER = 8   # fenêtre unique utilisée pour toutes les vérifications

POLL_INTERVAL = 3    # secondes entre vérifications
MAX_WAIT      = 300  # secondes max d'attente par bookmaker


def _is_logged_in_selenium(driver, selectors: list) -> bool:
    for sel in selectors:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                if el.text.strip():
                    return True
        except Exception:
            pass
    return False


def _wait_for_login_selenium(driver, name: str, login_url: str,
                              home_url: str, selectors: list) -> bool:
    """
    Sur le driver donné, navigue vers le bookmaker et attend la connexion manuelle.
    Retourne True dès que connecté, False en cas de timeout.
    """
    # Vérifier session existante
    try:
        driver.get(home_url)
        time.sleep(2.5)
        if _is_logged_in_selenium(driver, selectors):
            log(f"[{name}] ✅ Session déjà active", "info")
            return True
    except Exception as e:
        log(f"[{name}] Erreur vérification session: {e}", "warning")

    # Naviguer vers la page de login et attendre connexion manuelle
    log(f"[{name}] 🔓 Connecte-toi sur {login_url} (max {MAX_WAIT}s)...", "info")
    try:
        driver.get(login_url)
    except Exception as e:
        log(f"[{name}] Erreur navigation login: {e}", "warning")

    elapsed = 0
    while elapsed < MAX_WAIT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        try:
            if _is_logged_in_selenium(driver, selectors):
                log(f"[{name}] ✅ Connecté !", "info")
                return True
        except Exception:
            pass

    log(f"[{name}] ⚠️  Timeout connexion ({MAX_WAIT}s)", "warning")
    try:
        from Functions.Functions_telegram import send_telegram, alertGroup
        send_telegram(alertGroup,
            f"⚠️ #SESSION_TIMEOUT\nConnexion {name} non détectée.\nRelance le script.")
    except Exception:
        pass
    return False


def _init_all_sessions(driver) -> dict:
    results = {}
    for name in LOGIN_URLS:
        ok = _wait_for_login_selenium(
            driver=driver,
            name=name,
            login_url=LOGIN_URLS[name],
            home_url=HOME_URLS[name],
            selectors=LOGGED_IN_SELECTORS[name],
        )
        results[name] = ok
    return results


def init_bookmaker_sessions() -> dict:
    """
    Point d'entrée — à appeler au démarrage du script principal.
    Utilise une seule fenêtre et vérifie chaque bookmaker séquentiellement.
    Retourne un dict {bookmaker_name: bool} indiquant les sessions actives.
    """
    import config
    config.localhost = 43151

    from ChromeDriver.SetDriver import get_script_driver

    log("🔑 Initialisation des sessions bookmakers...", "info")

    driver = get_script_driver(WINDOW_NUMBER)
    if not driver:
        log("❌ Driver indisponible — Chrome lancé sur le port 43151 ?", "error")
        return {name: False for name in LOGIN_URLS}

    statuses = _init_all_sessions(driver)
    for name, ok in statuses.items():
        icon = "✅" if ok else "❌"
        log(f"  {icon} {name}: {'connecté' if ok else 'non connecté'}", "info")
    return statuses


if __name__ == "__main__":
    import config
    config.localhost = 43151
    init_bookmaker_sessions()
