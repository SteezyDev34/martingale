# -*- coding: utf-8 -*-
"""
Test de connexion automatique pour Winamax, Betclic, Lollybet.
Prérequis : Chrome lancé sur le port 43151.

    venv/bin/python -m Functions.Bookmakers._test_session_login
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

import config
config.localhost = 43151

from selenium.webdriver.common.by import By
from ChromeDriver.SetDriver import get_script_driver


def test_bookmaker(name, window_num, scraper_class):
    print(f"\n{'='*50}")
    print(f"=== {name.upper()} (fenêtre {window_num}) ===")
    print(f"{'='*50}")

    driver = get_script_driver(window_num)
    if not driver:
        print(f"❌ Driver indisponible")
        return False

    scraper = scraper_class()

    print(f"\n--- 1. Vérification session existante ---")
    if scraper.is_logged_in(driver):
        print(f"✅ Déjà connecté — pas besoin de login")
        return True

    print(f"⚠️  Session inactive — tentative de connexion automatique...")

    print(f"\n--- 2. Connexion automatique ---")
    ok = scraper.login(driver)
    print(f"{'✅ Connexion réussie' if ok else '❌ Connexion échouée'}")

    if ok:
        print(f"\n--- 3. Vérification post-login ---")
        logged = scraper.is_logged_in(driver)
        print(f"{'✅ Session confirmée' if logged else '⚠️  Session non confirmée après login'}")
        return logged

    return False


def main():
    from Functions.Bookmakers.WinamaxScraper import WinamaxScraper
    from Functions.Bookmakers.BetclicScraper import BetclicScraper
    from Functions.Bookmakers.LollybetScraper import LollybetScraper

    results = {}

    # Tester les bookmakers sans VPN
    for name, window, cls in [
        ("Winamax",  9,  WinamaxScraper),
        ("Betclic",  10, BetclicScraper),
        ("Lollybet", 8,  LollybetScraper),
    ]:
        try:
            results[name] = test_bookmaker(name, window, cls)
        except Exception as e:
            print(f"❌ Erreur inattendue {name}: {e}")
            import traceback; traceback.print_exc()
            results[name] = False

    print(f"\n{'='*50}")
    print("=== RÉSUMÉ ===")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}: {'connecté' if ok else 'échec'}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
