# -*- coding: utf-8 -*-
"""
Test end-to-end Lollybet — Selenium (fenêtre 8 du driver partagé).
Prérequis : Chrome lancé sur le port 43151 avec le profil Lollybet.

    venv/bin/python -m Functions.Bookmakers._test_lollybet_bet
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

import config
config.localhost = 43151

BET = {
    "equipe_1": "Sinner",
    "equipe_2": "Kecmanovic",
    "sport": "2",
    "date": "2026-06-26",
    "selection": "3-0",
    "categorie": "Score exact",
    "mise": 0.10,
}


def main():
    from ChromeDriver.SetDriver import get_script_driver
    from Functions.Bookmakers.LollybetScraper import LollybetScraper

    print("\n=== INIT DRIVER ===")
    driver = get_script_driver(8)
    if not driver:
        print("❌ Impossible d'obtenir le driver — Chrome lancé sur le port 43151 ?")
        return

    scraper = LollybetScraper()

    # ── 1. Session ─────────────────────────────────────────────────────
    print("\n=== SESSION ===")
    logged = scraper.is_logged_in(driver)
    if not logged:
        print("⚠️  Session inactive — navigation vers login, attente 60s...")
        driver.get("https://lolly-bet99.com/login")
        for i in range(20):
            import time; time.sleep(3)
            logged = scraper.is_logged_in(driver)
            if logged:
                break
            print(f"  attente... {(i+1)*3}s")
    if not logged:
        print("❌ Session inactive après attente — arrêt")
        return
    print("✅ Session active")

    # ── 2. Recherche de match ───────────────────────────────────────────
    print("\n=== RECHERCHE MATCH ===")
    match_url = scraper.search_match(
        driver,
        BET["equipe_1"], BET["equipe_2"],
        BET["sport"], BET["date"]
    )
    if not match_url:
        print(f"❌ Match non trouvé: {BET['equipe_1']} vs {BET['equipe_2']}")
        return
    print(f"✅ Match: {match_url}")

    # ── 3. Récupération de la cote ──────────────────────────────────────
    print("\n=== COTE ===")
    odds = scraper.get_odds(driver, match_url, BET["selection"], BET["categorie"])
    if odds:
        print(f"✅ Cote: {odds}")
    else:
        print(f"⚠️  Cote non trouvée — placement quand même pour tester le flux")

    # ── 4. Placement du pari ────────────────────────────────────────────
    print("\n=== PLACEMENT PARI ===")
    success = scraper.place_bet(
        driver, match_url,
        BET["selection"], BET["categorie"],
        BET["mise"]
    )
    print("✅ Pari placé" if success else "❌ Placement échoué")

    print("\n=== FIN TEST ===")


if __name__ == "__main__":
    main()
