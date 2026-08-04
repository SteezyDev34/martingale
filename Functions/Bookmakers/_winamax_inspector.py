# -*- coding: utf-8 -*-
"""
Script d'inspection du DOM Winamax.
Lance un navigateur visible, navigue sur /connexion et dump les sélecteurs réels.
Exécuter manuellement : python Functions/Bookmakers/_winamax_inspector.py
"""
import asyncio
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

PROFILE_DIR = os.path.join(project_root, "ChromeDriver", "winamax_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

EMAIL = os.getenv("WINAMAX_EMAIL", "")
PASSWORD = os.getenv("WINAMAX_PASSWORD", "")
DOB = os.getenv("WINAMAX_DOB", "")


async def inspect_login():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("\n=== HOMEPAGE ===")
        await page.goto("https://www.winamax.fr/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Fermer la bannière cookies si présente
        for cookie_btn in ["#tarteaucitronAllAllowed", "#tarteaucitronPersonalize2",
                           "button.tarteaucitronAllow", "[id*='accept-all']"]:
            try:
                btn = await page.query_selector(cookie_btn)
                if btn and await btn.is_visible():
                    await btn.click()
                    print(f"✅ Cookie banner fermée: {cookie_btn}")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass

        await asyncio.sleep(1)
        await page.screenshot(path="/tmp/winamax_home.png")
        print("Screenshot homepage: /tmp/winamax_home.png")

        # Trouver et cliquer le bouton connexion
        print("\n=== BOUTON CONNEXION ===")
        login_btns = await page.evaluate('''() => {
            const result = [];
            document.querySelectorAll("a, button").forEach(el => {
                const t = (el.innerText || el.textContent || "").toLowerCase().trim();
                const cls = el.className || "";
                const href = el.href || "";
                if (t.includes("connect") || t.includes("login") || t.includes("compte")
                    || cls.includes("login") || cls.includes("signin") || href.includes("login")) {
                    result.push({tag: el.tagName, text: t.slice(0,40), classes: cls.slice(0,80), href: href.slice(0,80)});
                }
            });
            return result.slice(0, 10);
        }''')
        print(json.dumps(login_btns, ensure_ascii=False, indent=2))

        # Test login réel via WinamaxScraper
        print("\n=== TEST LOGIN WINAMAX SCRAPER ===")
        from Functions.Bookmakers.WinamaxScraper import WinamaxScraper
        scraper = WinamaxScraper()
        logged_in = await scraper.is_logged_in(page)
        print(f"Déjà connecté: {logged_in}")
        if not logged_in:
            result = await scraper.login(page)
            print(f"Login résultat: {result}")
        await asyncio.sleep(2)
        await page.screenshot(path="/tmp/winamax_after_login.png")
        print(f"URL finale: {page.url}")
        print("Screenshot: /tmp/winamax_after_login.png")
        # Inspecter les iframes
        print("\n=== IFRAMES ===")
        frames = page.frames
        for i, frame in enumerate(frames):
            print(f"Frame {i}: url={frame.url}")
            try:
                inputs = await frame.evaluate('''() => {
                    return Array.from(document.querySelectorAll("input")).map(el => ({
                        type: el.type, name: el.name, id: el.id,
                        placeholder: el.placeholder, classes: el.className?.slice(0,60),
                        visible: el.offsetParent !== null
                    })).filter(el => el.visible || el.type !== 'hidden');
                }''')
                if inputs:
                    print(f"  → Inputs: {json.dumps(inputs, ensure_ascii=False)}")
            except Exception as e:
                print(f"  → Erreur: {e}")

        print("\n=== INPUTS VISIBLES APRÈS LOGIN ===")


        # Dump tous les inputs et boutons
        elements = await page.evaluate('''() => {
            const result = [];
            document.querySelectorAll("input, button, [role='button']").forEach(el => {
                result.push({
                    tag: el.tagName,
                    type: el.type || "",
                    name: el.name || "",
                    id: el.id || "",
                    placeholder: el.placeholder || "",
                    classes: el.className?.slice(0, 80) || "",
                    text: el.innerText?.slice(0, 50) || "",
                    visible: el.offsetParent !== null
                });
            });
            return result;
        }''')
        print(json.dumps(elements, ensure_ascii=False, indent=2))

        print("\n=== TENTATIVE LOGIN ===")
        # Remplir email
        try:
            await page.wait_for_selector("input[type='email'], input[name='email'], input[name='login']", timeout=8000)
            await page.fill("input[type='email'], input[name='email'], input[name='login']", EMAIL)
            await asyncio.sleep(0.5)
            await page.fill("input[type='password']", PASSWORD)
            await asyncio.sleep(0.5)
            await page.screenshot(path="/tmp/winamax_before_submit.png")
            print("Screenshot avant submit: /tmp/winamax_before_submit.png")

            # Cliquer submit
            submit = await page.query_selector("button[type='submit']")
            if submit:
                await submit.click()
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                print(f"URL après submit: {page.url}")
                await page.screenshot(path="/tmp/winamax_after_submit.png")
                print("Screenshot après submit: /tmp/winamax_after_submit.png")

                # Vérifier si DOB demandée
                dob_field = await page.query_selector("input[name='birthDate'], input[placeholder*='naissance'], input[placeholder*='date']")
                if dob_field:
                    print("→ Champ date de naissance détecté")
                    dob_html = await page.evaluate('''() => {
                        const fields = document.querySelectorAll("input");
                        return Array.from(fields).map(f => ({
                            name: f.name, id: f.id, type: f.type,
                            placeholder: f.placeholder, classes: f.className?.slice(0,80)
                        }));
                    }''')
                    print(json.dumps(dob_html, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Erreur: {e}")

        print("\n=== URL FINALE ===", page.url)
        print("\nNavigateur ouvert — inspecte manuellement puis ferme la fenêtre.")
        await asyncio.sleep(60)  # Laisser 60s pour inspection manuelle
        await browser.close()


async def inspect_challenges():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Test page défis (si déjà connecté)
        for url in ["https://www.winamax.fr/compte/defis",
                    "https://www.winamax.fr/compte/missions",
                    "https://www.winamax.fr/promotions"]:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            print(f"\n=== {url} ===")
            print(f"URL réelle: {page.url}")
            items = await page.evaluate('''() => {
                const result = [];
                document.querySelectorAll("[class*='challenge'],[class*='defi'],[class*='mission'],[class*='promo']").forEach(el => {
                    if (el.children.length > 0) {
                        result.push({classes: el.className?.slice(0,80), text: el.innerText?.slice(0, 150)});
                    }
                });
                return result.slice(0, 10);
            }''')
            print(json.dumps(items, ensure_ascii=False, indent=2))

        await asyncio.sleep(30)
        await browser.close()


async def inspect_sports():
    """Inspecte la page sports, un match, les cotes et le panier."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # ── 1. Page sports/tennis ──────────────────────────────────────────
        print("\n=== PAGE SPORTS/TENNIS ===")
        await page.goto("https://www.winamax.fr/paris-sportifs/sports/2", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path="/tmp/wina_sports.png")

        # Recherche barre de recherche
        search_els = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll("input")).map(el => ({
                type: el.type, placeholder: el.placeholder, id: el.id,
                classes: el.className?.slice(0,80), visible: el.offsetParent !== null
            })).filter(el => el.visible);
        }''')
        print("Inputs visibles:", json.dumps(search_els, ensure_ascii=False, indent=2))

        # Liens de matchs
        match_links = await page.evaluate('''() => {
            const links = [];
            document.querySelectorAll("a[href*='/paris-sportifs/']").forEach(el => {
                const href = el.href;
                const text = el.innerText?.trim().slice(0, 80);
                if (href && text && !links.find(l => l.href === href))
                    links.push({href, text});
            });
            return links.slice(0, 10);
        }''')
        print("Liens matchs:", json.dumps(match_links, ensure_ascii=False, indent=2))

        if not match_links:
            print("Aucun match trouvé sur /sports/2 — essai football")
            await page.goto("https://www.winamax.fr/paris-sportifs/sports/3", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            match_links = await page.evaluate('''() => {
                const links = [];
                document.querySelectorAll("a[href*='/paris-sportifs/']").forEach(el => {
                    const href = el.href;
                    const text = el.innerText?.trim().slice(0, 80);
                    if (href && text && !links.find(l => l.href === href))
                        links.push({href, text});
                });
                return links.slice(0, 10);
            }''')
            print("Liens matchs football:", json.dumps(match_links, ensure_ascii=False, indent=2))

        # ── 2. Page d'un match ─────────────────────────────────────────────
        if match_links:
            match_url = match_links[0]["href"]
            print(f"\n=== PAGE MATCH: {match_url} ===")
            await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/wina_match.png")

            # Sélecteurs cotes
            odds_els = await page.evaluate('''() => {
                const result = [];
                document.querySelectorAll("[class*='odd'],[class*='Odd'],[class*='cote'],[class*='Cote'],[data-test*='odd']").forEach(el => {
                    if (el.offsetParent !== null) {
                        const parent = el.closest("[class*='market'],[class*='Market'],[class*='bet'],[class*='Bet']");
                        result.push({
                            tag: el.tagName,
                            text: el.innerText?.trim().slice(0,20),
                            classes: el.className?.slice(0,80),
                            dataTest: el.dataset?.test || "",
                            parentClasses: parent?.className?.slice(0,80) || "",
                            parentText: parent?.innerText?.trim().slice(0,60) || ""
                        });
                    }
                });
                return result.slice(0, 20);
            }''')
            print("Éléments cotes:", json.dumps(odds_els, ensure_ascii=False, indent=2))

            # data-test attributes présents
            data_tests = await page.evaluate('''() => {
                const s = new Set();
                document.querySelectorAll("[data-test]").forEach(el => s.add(el.dataset.test));
                return Array.from(s).slice(0, 30);
            }''')
            print("data-test présents:", json.dumps(data_tests, ensure_ascii=False))

            # ── 3. Cliquer sur une cote et inspecter le panier ──────────────
            print("\n=== CLIC SUR UNE COTE ===")
            # Essayer de cliquer sur le premier bouton de cote visible
            cote_btn = await page.query_selector(".odd-button-wrapper, .bet-group-outcome-odd")

            if cote_btn:
                await cote_btn.click()
                await asyncio.sleep(2)
                await page.screenshot(path="/tmp/wina_betslip.png")
                print("Screenshot panier: /tmp/wina_betslip.png")

                # Inspecter le panier / betslip
                betslip = await page.evaluate('''() => {
                    const result = [];
                    document.querySelectorAll("[class*='betslip'],[class*='Betslip'],[class*='slip'],[class*='panier'],[data-test*='betslip'],[data-test*='slip']").forEach(el => {
                        if (el.offsetParent !== null) {
                            result.push({
                                classes: el.className?.slice(0,80),
                                dataTest: el.dataset?.test || "",
                                text: el.innerText?.trim().slice(0,100)
                            });
                        }
                    });
                    return result.slice(0, 10);
                }''')
                print("Betslip:", json.dumps(betslip, ensure_ascii=False, indent=2))

                # Champ mise
                stake_inputs = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll("input")).map(el => ({
                        type: el.type, placeholder: el.placeholder, id: el.id,
                        classes: el.className?.slice(0,80), dataTest: el.dataset?.test || "",
                        visible: el.offsetParent !== null
                    })).filter(el => el.visible);
                }''')
                print("Inputs visibles après clic cote:", json.dumps(stake_inputs, ensure_ascii=False, indent=2))

                # Bouton validation
                confirm_btns = await page.evaluate('''() => {
                    const result = [];
                    document.querySelectorAll("button,[role='button']").forEach(el => {
                        const t = el.innerText?.trim().toLowerCase();
                        if (el.offsetParent !== null && (t.includes("parier") || t.includes("valider") || t.includes("placer") || t.includes("confirmer") || t.includes("bet"))) {
                            result.push({tag: el.tagName, text: t.slice(0,40), classes: el.className?.slice(0,80), dataTest: el.dataset?.test || ""});
                        }
                    });
                    return result;
                }''')
                print("Boutons confirmation:", json.dumps(confirm_btns, ensure_ascii=False, indent=2))
            else:
                print("Aucun bouton cote trouvé")

        print("\n=== RECHERCHE MATCH URUGUAY vs ESPAGNE ===")
        await page.goto("https://www.winamax.fr/paris-sportifs/sports/1", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        search_box = await page.query_selector("input[placeholder='Rechercher']")
        if search_box:
            await search_box.click()
            await asyncio.sleep(0.5)
            await search_box.type("Uruguay", delay=80)
            await asyncio.sleep(2)
            await page.screenshot(path="/tmp/wina_search_uruguay.png")
            print("Screenshot recherche: /tmp/wina_search_uruguay.png")

            # Dump tout ce qui apparaît après frappe
            visible = await page.evaluate('''() => {
                const result = [];
                document.querySelectorAll("a, li, [role='option'], [role='listitem'], [class*='result'], [class*='suggestion'], [class*='autocomplete'], [class*='search']").forEach(el => {
                    if (el.offsetParent !== null) {
                        const t = el.innerText?.trim().slice(0, 80);
                        const href = el.href || "";
                        if (t) result.push({tag: el.tagName, text: t, href: href.slice(0,100), classes: el.className?.slice(0,60)});
                    }
                });
                return result.slice(0, 30);
            }''')
            print("Éléments visibles après 'Uruguay':", json.dumps(visible, ensure_ascii=False, indent=2))

        print("\n=== FIN — fenêtre ouverte 60s pour inspection manuelle ===")
        await page.screenshot(path="/tmp/wina_final.png")
        await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "login"
    if mode == "challenges":
        asyncio.run(inspect_challenges())
    elif mode == "sports":
        asyncio.run(inspect_sports())
    else:
        asyncio.run(inspect_login())
