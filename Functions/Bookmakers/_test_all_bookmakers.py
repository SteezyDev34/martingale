# -*- coding: utf-8 -*-
"""
Test de session + placement de pari pour tous les bookmakers.
Mise : 0.10€ sur chaque.
"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

REAL_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CLOUDFLARE_BOOKMAKERS = {"Betclic", "Lollybet", "Stake"}

# Pari de test (tennis, score exact 3-0 sur Wimbledon)
TEST_BET = {
    "equipe_1":  "Sinner",
    "equipe_2":  "Kecmanovic",
    "sport":     "2",
    "date":      "2026-06-26",
    "selection": "3-0",
    "categorie": "Score exact",
    "mise":      0.10,
}

LOGGED_IN_SELECTORS = {
    "Winamax":  ["[data-test='account-menu']", ".account-menu", "a[href*='compte']", "[class*='UserMenu']"],
    "Betclic":  ["[class*='userAccount']", "[class*='userName']", "[class*='accountMenu']",
                 "[data-cy='header-balance']", "[class*='balanceAmount']", "[class*='headerUser']",
                 "a[href*='/mon-compte']", "[data-automation-id='user-balance']"],
    "Lollybet": ["[class*='user-menu']", "[class*='userMenu']", ".user-balance", "[class*='balance']",
                 "[class*='avatar']", "a[href*='/deposit']", "a[href*='/withdraw']"],
    "Stake":    ["[class*='userBalance']", "[class*='user-balance']", "[data-test='balance']",
                 "[class*='HeaderUser']", "[class*='walletBalance']"],
}

HOME_URLS = {
    "Winamax":  "https://www.winamax.fr",
    "Betclic":  "https://www.betclic.fr",
    "Lollybet": "https://lolly-bet99.com",
    "Stake":    "https://stake.bet",
}


async def check_session(name: str, profile_dir: str) -> bool:
    """Vérifie si la session est active via Playwright."""
    from playwright.async_api import async_playwright
    try:
        launch_kwargs = dict(
            user_data_dir=profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        if name in CLOUDFLARE_BOOKMAKERS and os.path.exists(REAL_CHROME):
            launch_kwargs["executable_path"] = REAL_CHROME

        async with async_playwright() as pw:
            browser = await pw.chromium.launch_persistent_context(**launch_kwargs)
            page = browser.pages[0] if browser.pages else await browser.new_page()
            await page.goto(HOME_URLS[name], wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)
            for sel in LOGGED_IN_SELECTORS[name]:
                el = await page.query_selector(sel)
                if el:
                    await browser.close()
                    return True
            await browser.close()
            return False
    except Exception as e:
        print(f"[{name}] Erreur check_session: {e}")
        return False


async def test_bookmaker(name: str, scraper_cls, profile_dir: str):
    """Lance un test de placement sur un bookmaker."""
    from playwright.async_api import async_playwright

    print(f"\n{'='*50}")
    print(f"TEST {name.upper()}")
    print(f"{'='*50}")

    launch_kwargs = dict(
        user_data_dir=profile_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        locale="fr-FR",
        viewport={"width": 1280, "height": 900},
    )
    if name in CLOUDFLARE_BOOKMAKERS and os.path.exists(REAL_CHROME):
        launch_kwargs["executable_path"] = REAL_CHROME
        print(f"→ Utilisation de Google Chrome (anti-Cloudflare)")

    scraper = scraper_cls()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(**launch_kwargs)
        page = browser.pages[0] if browser.pages else await browser.new_page()

        if name in CLOUDFLARE_BOOKMAKERS:
            try:
                from playwright_stealth import Stealth as _Stealth
                await _Stealth().apply_stealth_async(page)
            except Exception:
                pass

        # Vérif session
        logged = False
        await page.goto(HOME_URLS[name], wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)
        for sel in LOGGED_IN_SELECTORS[name]:
            el = await page.query_selector(sel)
            if el:
                logged = True
                print(f"✅ Session active ({sel})")
                break

        if not logged:
            print(f"❌ Session inactive — connecte-toi manuellement...")
            await browser.close()
            return False

        # Recherche match
        print(f"🔍 Recherche: {TEST_BET['equipe_1']} vs {TEST_BET['equipe_2']}...")
        match_url = await scraper.search_match(
            page, TEST_BET["equipe_1"], TEST_BET["equipe_2"],
            TEST_BET["sport"], TEST_BET["date"]
        )
        if not match_url:
            print(f"❌ Match non trouvé")
            await browser.close()
            return False
        print(f"✅ Match: {match_url}")

        # Cote
        odds = await scraper.get_odds(page, match_url, TEST_BET["selection"], TEST_BET["categorie"])
        if not odds:
            print(f"❌ Cote non trouvée pour {TEST_BET['selection']}")
            await browser.close()
            return False
        print(f"✅ Cote: {odds}")

        # Placement
        print(f"⚠️  Placement dans 10s (Ctrl+C pour annuler)...")
        await asyncio.sleep(10)

        success = await scraper.place_bet(
            page, match_url, TEST_BET["selection"], TEST_BET["categorie"], TEST_BET["mise"]
        )
        print(f"{'✅ Pari placé' if success else '❌ Échec placement'}")
        await asyncio.sleep(5)
        await browser.close()
        return success


async def main():
    from Functions.Bookmakers.WinamaxScraper import WinamaxScraper
    from Functions.Bookmakers.BetclicScraper import BetclicScraper
    from Functions.Bookmakers.LollybetScraper import LollybetScraper
    from Functions.Bookmakers.StakeScraper import StakeScraper

    bookmakers = [
        ("Winamax",  WinamaxScraper),
        ("Betclic",  BetclicScraper),
        ("Lollybet", LollybetScraper),
        ("Stake",    StakeScraper),
    ]

    results = {}
    for name, cls in bookmakers:
        scraper = cls()
        try:
            ok = await test_bookmaker(name, cls, scraper.profile_dir)
            results[name] = ok
        except KeyboardInterrupt:
            print(f"\n⏭️  {name} ignoré")
            results[name] = None
        except Exception as e:
            print(f"❌ Erreur {name}: {e}")
            results[name] = False

    print(f"\n{'='*50}")
    print("RÉSUMÉ")
    print(f"{'='*50}")
    for name, ok in results.items():
        icon = "✅" if ok else ("⏭️" if ok is None else "❌")
        print(f"  {icon} {name}")


if __name__ == "__main__":
    asyncio.run(main())
