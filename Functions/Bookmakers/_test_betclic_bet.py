# -*- coding: utf-8 -*-
"""
Test end-to-end Betclic : session → recherche match → cote → placement 0.10€
Pronos : Sinner vs Kecmanovic, score exact 3-0
"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

REAL_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR = os.path.join(project_root, "ChromeDriver", "betclic_profile")

TEST_BET = {
    "equipe_1":  "Sinner",
    "equipe_2":  "Kecmanovic",
    "sport":     "2",
    "date":      "2026-06-26",
    "selection": "3-0",
    "categorie": "Score exact",
    "mise":      0.10,
}


async def main():
    from playwright.async_api import async_playwright
    from Functions.Bookmakers.BetclicScraper import BetclicScraper

    scraper = BetclicScraper()

    print("="*55)
    print("TEST BETCLIC — Sinner vs Kecmanovic  Score exact 3-0")
    print("="*55)
    print(f"Profil: {PROFILE_DIR}")

    async with async_playwright() as pw:
        launch_kwargs = dict(
            user_data_dir=PROFILE_DIR,
            executable_path=REAL_CHROME,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        browser = await pw.chromium.launch_persistent_context(**launch_kwargs)
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Appliquer playwright-stealth (anti-Cloudflare)
        try:
            from playwright_stealth import Stealth as _Stealth
            await _Stealth().apply_stealth_async(page)
            print("✅ playwright-stealth appliqué")
        except Exception as e:
            print(f"⚠️  playwright-stealth non disponible: {e}")

        # ── 1. Vérifier la session ─────────────────────────────────────
        print("\n[1/4] Vérification session...")
        logged = await scraper.is_logged_in(page)
        if not logged:
            print("❌ Session inactive — connecte-toi dans la fenêtre Chrome")
            print("   (attente 5 min max)")
            for _ in range(100):
                await asyncio.sleep(3)
                logged = await scraper.is_logged_in(page)
                if logged:
                    break
            else:
                print("❌ Timeout — fermeture")
                await browser.close()
                return

        print("✅ Session active")

        # ── 2. Recherche du match ─────────────────────────────────────
        print(f"\n[2/4] Recherche {TEST_BET['equipe_1']} vs {TEST_BET['equipe_2']}...")
        match_url = await scraper.search_match(
            page, TEST_BET["equipe_1"], TEST_BET["equipe_2"],
            TEST_BET["sport"], TEST_BET["date"]
        )
        if not match_url:
            print("❌ Match non trouvé")
            await browser.close()
            return
        print(f"✅ Match: {match_url}")

        # ── 3. Récupération de la cote ─────────────────────────────────
        print(f"\n[3/4] Récupération cote pour '{TEST_BET['selection']}'...")
        odds = await scraper.get_odds(page, match_url, TEST_BET["selection"], TEST_BET["categorie"])
        if not odds:
            print("❌ Cote non trouvée")
            await browser.close()
            return
        print(f"✅ Cote: {odds}")

        # ── 4. Placement du pari ───────────────────────────────────────
        print(f"\n[4/4] Placement dans 10s (Ctrl+C pour annuler)...")
        print(f"      Mise: {TEST_BET['mise']}€ — Sélection: {TEST_BET['selection']}")
        await asyncio.sleep(10)

        success = await scraper.place_bet(
            page, match_url, TEST_BET["selection"], TEST_BET["categorie"], TEST_BET["mise"]
        )

        if success:
            print("\n✅ PARI PLACÉ SUR BETCLIC")
        else:
            print("\n❌ ÉCHEC DU PLACEMENT")

        await asyncio.sleep(8)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
