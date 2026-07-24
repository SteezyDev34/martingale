# -*- coding: utf-8 -*-
"""
Inspecte la modal de suggestions de recherche Winamax.
"""
import asyncio, json, os, sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

PROFILE_DIR = os.path.join(project_root, "ChromeDriver", "winamax_profile")

async def inspect():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR, headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR", viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://www.winamax.fr/paris-sportifs", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Taper dans la barre recherche
        search_box = await page.query_selector("input[placeholder='Rechercher']")
        await search_box.click()
        await asyncio.sleep(0.5)
        await search_box.type("Uruguay", delay=100)
        await asyncio.sleep(2)
        await page.screenshot(path="/tmp/wina_suggest.png")

        # Dump TOUT le DOM nouvellement apparu (éléments avec position fixed/absolute ou modal)
        print("\n=== ÉLÉMENTS MODAL/DROPDOWN APRÈS FRAPPE ===")
        suggestions = await page.evaluate('''() => {
            const results = [];
            // Chercher tout ce qui ressemble à une suggestion/modal/dropdown
            const selectors = [
                "[class*='suggest']", "[class*='Suggest']",
                "[class*='autocomplete']", "[class*='Autocomplete']",
                "[class*='dropdown']", "[class*='Dropdown']",
                "[class*='modal']", "[class*='Modal']",
                "[class*='search-result']", "[class*='SearchResult']",
                "[class*='result']", "[role='listbox']",
                "[role='option']", "[role='dialog']",
                "[class*='overlay']", "[class*='popup']",
                "[class*='Popup']", "[class*='layer']"
            ];
            const seen = new Set();
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    if (el.offsetParent !== null && !seen.has(el)) {
                        seen.add(el);
                        results.push({
                            tag: el.tagName,
                            classes: el.className?.slice(0,80),
                            role: el.getAttribute("role") || "",
                            text: el.innerText?.trim().slice(0,100),
                            href: el.href || "",
                            children: el.children.length
                        });
                    }
                });
            });
            return results.slice(0, 40);
        }''')
        for el in suggestions:
            print(f"  [{el['tag']}][{el['role']}] {el['text'][:60]:60s} classes={el['classes'][:50]}")

        print("\n=== TOUS LES ÉLÉMENTS VISIBLES AVEC 'uruguay' OU 'espagne' ===")
        team_els = await page.evaluate('''() => {
            const results = [];
            document.querySelectorAll("*").forEach(el => {
                if (el.offsetParent !== null && el.children.length === 0) {
                    const t = el.innerText?.toLowerCase() || "";
                    if (t.includes("uruguay") || t.includes("espagne") || t.includes("spain")) {
                        const parent = el.closest("a") || el;
                        results.push({
                            text: el.innerText?.trim().slice(0,80),
                            tag: el.tagName,
                            classes: el.className?.slice(0,80),
                            href: parent.href || "",
                            parentClasses: parent.className?.slice(0,80)
                        });
                    }
                }
            });
            return results.slice(0, 20);
        }''')
        if team_els:
            for el in team_els:
                print(f"  [{el['tag']}] {el['text'][:60]:60s} href={el['href'][:80]}")
        else:
            print("  Aucun élément trouvé avec ces termes")

        print("\n=== SCREENSHOT: /tmp/wina_suggest.png ===")
        print("Fenêtre ouverte 60s — inspecte manuellement")
        await asyncio.sleep(60)
        await browser.close()

asyncio.run(inspect())
