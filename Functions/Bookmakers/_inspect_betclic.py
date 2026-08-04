# -*- coding: utf-8 -*-
"""
Inspection du DOM Betclic pour trouver les vrais sélecteurs.
Lance ce script avec une session active (profil betclic_profile).
"""
import asyncio
import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

REAL_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR = os.path.join(project_root, "ChromeDriver", "betclic_profile")
HOME_URL     = "https://www.betclic.fr"
SEARCH_URL   = "https://www.betclic.fr/tennis-s4"


async def inspect():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth as _Stealth

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            executable_path=REAL_CHROME,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await _Stealth().apply_stealth_async(page)

        # ── 1. Vérifier la session ────────────────────────────────────────
        print("\n=== SESSION ===")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        session_info = await page.evaluate('''() => {
            const candidates = [
                "[class*='userAccount']", "[class*='userName']", "[class*='accountMenu']",
                "[class*='balanceAmount']", "[class*='headerUser']", "[class*='HeaderUser']",
                "betclic-header-user", "[data-cy='header-balance']",
                "[data-automation-id='user-balance']", "a[href*='/mon-compte']",
                "[class*='myAccount']", "[class*='balance']", "[class*='logged']"
            ];
            const results = [];
            candidates.forEach(sel => {
                try {
                    const el = document.querySelector(sel);
                    if (el) results.push({selector: sel, text: el.innerText?.trim().slice(0,50), tag: el.tagName});
                } catch(e) {}
            });
            return results;
        }''')
        if session_info:
            print("✅ Session active — sélecteurs trouvés :")
            for s in session_info:
                print(f"  {s['selector']}  →  {s['text']}")
        else:
            print("❌ Session inactive — connecte-toi dans la fenêtre Chrome puis attends...")
            await page.goto("https://www.betclic.fr/connexion", wait_until="domcontentloaded", timeout=20000)
            # Attendre jusqu'à 5 minutes
            for _ in range(100):
                await asyncio.sleep(3)
                info = await page.evaluate('''() => {
                    const candidates = [
                        "[class*='userAccount']","[class*='userName']","[class*='accountMenu']",
                        "[class*='balanceAmount']","[class*='headerUser']","betclic-header-user",
                        "[data-cy='header-balance']","[data-automation-id='user-balance']",
                        "a[href*='/mon-compte']","[class*='balance']"
                    ];
                    for (const sel of candidates) {
                        const el = document.querySelector(sel);
                        if (el) return {selector: sel, text: el.innerText?.trim().slice(0,50)};
                    }
                    return null;
                }''')
                if info:
                    print(f"✅ Connecté ! sélecteur: {info['selector']} → {info['text']}")
                    session_info = [info]
                    break
            else:
                print("❌ Timeout — fermeture")
                await browser.close()
                return

        # ── 2. Inspecter la barre de recherche ───────────────────────────
        print("\n=== BARRE DE RECHERCHE ===")
        await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        search_info = await page.evaluate('''() => {
            const inputs = Array.from(document.querySelectorAll("input"));
            return inputs.map(el => ({
                tag: el.tagName,
                type: el.type,
                placeholder: el.placeholder,
                name: el.name,
                id: el.id,
                classes: el.className?.slice(0,80),
                ariaLabel: el.getAttribute("aria-label") || ""
            })).filter(i => i.placeholder || i.ariaLabel);
        }''')
        print("Inputs trouvés :")
        for i in search_info:
            print(f"  placeholder='{i['placeholder']}' aria='{i['ariaLabel']}' classes='{i['classes'][:60]}'")

        # ── 3. Taper dans la recherche et inspecter les suggestions ───────
        print("\n=== SUGGESTIONS DE MATCH ===")
        search_sel = None
        for candidate in [
            "input[placeholder*='Joueur']", "input[placeholder*='équipe']",
            "input[placeholder*='Recherch']", "input[placeholder*='Search']",
            "input[aria-label*='Recherch']", "input[type='search']",
            "input[class*='search']", "input[class*='Search']",
            "input[class*='forms_inputText']",
        ]:
            el = await page.query_selector(candidate)
            if el:
                search_sel = candidate
                print(f"✅ Barre de recherche: {candidate}")
                break

        if search_sel:
            await page.click(search_sel)
            await asyncio.sleep(0.5)
            await page.type(search_sel, "Sinner", delay=80)
            await asyncio.sleep(2)
            await page.screenshot(path="/tmp/betclic_search.png")
            print("📸 Screenshot: /tmp/betclic_search.png")

            suggestion_info = await page.evaluate('''() => {
                const seen = new Set();
                const results = [];
                document.querySelectorAll("*").forEach(el => {
                    const text = el.innerText?.trim();
                    if (!text || text.length > 200 || seen.has(el.className)) return;
                    if ((text.toLowerCase().includes("sinner") || text.toLowerCase().includes("tennis"))
                        && el.children.length < 5) {
                        seen.add(el.className);
                        results.push({
                            tag: el.tagName,
                            classes: el.className?.slice(0,80),
                            text: text.slice(0,80),
                            href: el.href || ""
                        });
                    }
                });
                return results.slice(0, 20);
            }''')
            print("Éléments contenant 'Sinner' :")
            for s in suggestion_info:
                print(f"  <{s['tag']}> .{s['classes'][:50]}  →  {s['text'][:60]}")
        else:
            print("❌ Barre de recherche non trouvée")

        # ── 4. Naviguer vers une page de match et inspecter les cotes ─────
        print("\n=== PAGE DE MATCH (cotes) ===")
        # Chercher un match Sinner dans les suggestions
        links = await page.query_selector_all("a[href*='/tennis'], a[href*='/match'], a[href*='/sport']")
        match_url = None
        for link in links:
            text = (await link.inner_text()).lower()
            if "sinner" in text:
                match_url = await link.get_attribute("href")
                if match_url and not match_url.startswith("http"):
                    match_url = HOME_URL + match_url
                print(f"✅ Match trouvé: {match_url}")
                break

        if match_url:
            await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/betclic_match.png")
            print("📸 Screenshot: /tmp/betclic_match.png")

            odds_info = await page.evaluate('''() => {
                const seen = new Set();
                const results = [];
                document.querySelectorAll("*").forEach(el => {
                    const text = el.innerText?.trim();
                    if (!text || seen.has(el.className)) return;
                    // Chercher les éléments qui ressemblent à des cotes (nombre entre 1 et 100)
                    const num = parseFloat(text.replace(",", "."));
                    if (!isNaN(num) && num > 1.01 && num < 100 && text.length < 10
                        && el.children.length === 0) {
                        seen.add(el.className);
                        const parent = el.closest("[class*='odd'], [class*='Odd'], [class*='market'], [class*='Market'], [class*='bet'], [class*='Bet'], [class*='outcome'], [class*='Outcome']");
                        results.push({
                            tag: el.tagName,
                            classes: el.className?.slice(0,80),
                            text: text,
                            parentClasses: parent?.className?.slice(0,80) || "",
                            parentText: parent?.innerText?.trim().slice(0,60) || ""
                        });
                    }
                });
                return results.slice(0, 20);
            }''')
            print("Éléments ressemblant à des cotes :")
            for o in odds_info:
                print(f"  <{o['tag']}> .{o['classes'][:50]} = {o['text']}  (parent: .{o['parentClasses'][:40]})")
                if o['parentText']:
                    print(f"    contexte: {o['parentText']}")

            # Inspecter aussi les groupes de marché
            markets_info = await page.evaluate('''() => {
                const results = [];
                const candidates = [
                    "[class*='market']", "[class*='Market']",
                    "[class*='outcomes']", "[class*='Outcomes']",
                    "[class*='bet-group']", "[class*='betGroup']",
                    "betclic-market", "betclic-outcome"
                ];
                candidates.forEach(sel => {
                    const els = document.querySelectorAll(sel);
                    if (els.length > 0) {
                        results.push({selector: sel, count: els.length,
                            sample: els[0]?.innerText?.trim().slice(0,80)});
                    }
                });
                return results;
            }''')
            print("\nGroupes de marché / conteneurs de cotes :")
            for m in markets_info:
                print(f"  {m['selector']} ({m['count']} éléments) → {m['sample']}")

        # ── 5. Cliquer sur une cote pour ouvrir le betslip ───────────────
        print("\n=== BETSLIP (après clic sur une cote) ===")
        # Cliquer sur le bouton de cote "Vainqueur du match - Sinner"
        odd_btn = await page.query_selector("bcdk-bet-button-odds-animated, .btn.is-odd, [class*='is-odd']")
        if odd_btn:
            box = await odd_btn.bounding_box()
            if box:
                await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                await asyncio.sleep(2)
                await page.screenshot(path="/tmp/betclic_betslip.png")
                print("📸 Screenshot betslip: /tmp/betclic_betslip.png")

        betslip_info = await page.evaluate('''() => {
            const candidates = [
                "[class*='betslip']", "[class*='Betslip']", "[class*='bet-slip']",
                "betclic-betslip", "[id*='betslip']",
                "input[class*='stake']", "input[class*='amount']", "input[class*='wager']",
                "input[placeholder*='mise']", "input[placeholder*='Mise']",
                "input[placeholder*='€']", "input[placeholder*='Montant']",
                "input[class*='forms_inputText']"
            ];
            const results = [];
            candidates.forEach(sel => {
                try {
                    const els = document.querySelectorAll(sel);
                    els.forEach(el => results.push({
                        selector: sel,
                        tag: el.tagName,
                        classes: el.className?.slice(0,80),
                        text: el.innerText?.trim().slice(0,50) || el.placeholder || el.value || ""
                    }));
                } catch(e) {}
            });
            return results;
        }''')
        if betslip_info:
            print("Éléments betslip trouvés :")
            for b in betslip_info:
                print(f"  {b['selector']}  [{b['tag']}]  .{b['classes'][:50]} → '{b['text']}'")
        else:
            print("⚠️  Betslip non visible")

        # Chercher aussi les boutons de confirmation
        print("\nBoutons de confirmation :")
        confirm_info = await page.evaluate('''() => {
            const results = [];
            document.querySelectorAll("button").forEach(btn => {
                const text = btn.innerText?.trim();
                if (text && text.length < 60) results.push({
                    text, classes: btn.className?.slice(0,80),
                    disabled: btn.disabled
                });
            });
            return results.slice(0, 20);
        }''')
        for b in confirm_info:
            print(f"  {'[disabled]' if b['disabled'] else '[actif]  '} '{b['text']}'  .{b['classes'][:50]}")

        print("\n=== FIN INSPECTION ===")
        print("Captures : /tmp/betclic_search.png  /tmp/betclic_match.png")
        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect())
