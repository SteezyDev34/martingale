# -*- coding: utf-8 -*-
"""
Test de placement d'un pari réel sur Winamax.
Pari simulé : Uruguay vs Espagne — Nombre de buts Plus de 1,5
"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

# Pari reçu (simulé depuis screenshot)
TEST_BET = {
    "equipe_1":  "Sinner",
    "equipe_2":  "Kecmanovic",
    "sport":     "2",        # tennis
    "date":      "2026-06-26",
    "selection": "3-0",
    "categorie": "Score exact",
    "mise":      0.10,
    "tipster":   "test",
}


LOGGED_IN_SELECTORS = [
    "[data-test='account-menu']", ".account-menu", ".user-logged",
    "a[href*='compte']", "[class*='UserMenu']", "[class*='userMenu']",
    "[class*='AccountMenu']", "button[class*='account']",
]


async def run_test():
    from playwright.async_api import async_playwright
    from Functions.Bookmakers.WinamaxScraper import WinamaxScraper
    from Functions.Logs.Logger import log

    scraper = WinamaxScraper()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=scraper.profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("\n=== VÉRIFICATION SESSION ===")
        await page.goto("https://www.winamax.fr/", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        logged = False
        for sel in LOGGED_IN_SELECTORS:
            el = await page.query_selector(sel)
            if el:
                logged = True
                print(f"✅ Session active (sélecteur: {sel})")
                break

        if not logged:
            print("🔓 Session inactive — connecte-toi manuellement dans la fenêtre...")
            await page.goto("https://www.winamax.fr/account/login.php?redir=/", wait_until="domcontentloaded", timeout=20000)
            # Attendre la connexion (polling 300s max)
            for _ in range(100):
                await asyncio.sleep(3)
                for sel in LOGGED_IN_SELECTORS:
                    el = await page.query_selector(sel)
                    if el:
                        logged = True
                        print(f"✅ Connecté ! (sélecteur: {sel})")
                        break
                if logged:
                    break
                # Vérifier aussi via URL
                if "login" not in page.url and "account" not in page.url.split("?")[0]:
                    logged = True
                    print(f"✅ Redirigé vers {page.url}")
                    break

        if not logged:
            print("❌ Timeout connexion")
            await browser.close()
            return

        # ── DEBUG : inspecter la page CDM 2026 directement ──────────────
        print("\n=== DEBUG CDM 2026 ===")
        await page.goto("https://www.winamax.fr/paris-sportifs/sports/1/4/900001750", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path="/tmp/wina_cdm.png")

        # Scroller pour charger les matchs lazy-loaded
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(1)
        await asyncio.sleep(2)

        all_links = await page.evaluate('''() => {
            const seen = new Set();
            const results = [];
            document.querySelectorAll("a[href], [onclick], [class*='match'], [class*='event'], [class*='Match'], [class*='Event']").forEach(el => {
                const href = el.href || el.getAttribute("href") || "";
                const text = el.innerText?.trim().slice(0, 100);
                if (!seen.has(href + text)) {
                    seen.add(href + text);
                    if (text) results.push({href: href.slice(0,150), text, classes: el.className?.slice(0,60)});
                }
            });
            return results.slice(0, 50);
        }''')
        print("Éléments matchs sur CDM 2026 (après scroll):")
        import json
        for l in all_links:
            t = l['text'].replace('\n',' ')
            if any(kw in l['href'].lower() for kw in ['match', 'event', 'sports/1']) or \
               any(team in t.lower() for team in ['uruguay', 'espagne', 'spain', 'france', 'brésil']):
                print(f"  [{l['classes'][:30]}] {t[:60]:60s} → {l['href'][:80]}")

        print(f"\n=== RECHERCHE MATCH: {TEST_BET['equipe_1']} vs {TEST_BET['equipe_2']} ===")
        match_url = await scraper.search_match(
            page,
            TEST_BET["equipe_1"],
            TEST_BET["equipe_2"],
            TEST_BET["sport"],
            TEST_BET["date"],
        )
        print(f"URL match: {match_url}")
        await page.screenshot(path="/tmp/wina_test_search.png")

        if not match_url:
            print("❌ Match non trouvé")
            await asyncio.sleep(30)
            await browser.close()
            return

        print(f"\n=== RÉCUPÉRATION COTE: {TEST_BET['selection']} ===")
        odds = await scraper.get_odds(page, match_url, TEST_BET["selection"], TEST_BET["categorie"])
        print(f"Cote trouvée: {odds}")
        await page.screenshot(path="/tmp/wina_test_odds.png")

        if not odds:
            print("❌ Cote non trouvée — vérifie /tmp/wina_test_odds.png")
            # Dump les containers pour debug
            from playwright.async_api import async_playwright as _
            containers = await page.query_selector_all(".bet-group-outcome-odd")
            print(f"Nombre de .bet-group-outcome-odd trouvés: {len(containers)}")
            for i, c in enumerate(containers[:10]):
                txt = await c.inner_text()
                print(f"  [{i}] {txt.strip()[:60]}")
            await asyncio.sleep(60)
            await browser.close()
            return

        print(f"\n=== PLACEMENT PARI: mise={TEST_BET['mise']}€ @ {odds} ===")
        print("⚠️  Tu as 10 secondes pour annuler (Ctrl+C)...")
        await asyncio.sleep(10)

        success = await scraper.place_bet(
            page,
            match_url,
            TEST_BET["selection"],
            TEST_BET["categorie"],
            TEST_BET["mise"],
        )
        await page.screenshot(path="/tmp/wina_test_placed.png")
        print(f"Résultat: {'✅ Pari placé' if success else '❌ Échec placement'}")
        print("Screenshot: /tmp/wina_test_placed.png")

        # Notifier l'API du résultat
        if success:
            try:
                from Functions.TelegramBetsAPI import telegram_bets_api
                # En test on n'a pas d'ID réel — on simule juste l'appel
                print("📡 [API] Pari marqué comme traité (simulation test — pas d'ID réel)")
                # En production : telegram_bets_api.mark_bet_as_processed(bet_id)
            except Exception as e:
                print(f"❌ Erreur API: {e}")

        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())
