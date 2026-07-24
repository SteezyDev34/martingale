# -*- coding: utf-8 -*-
"""
Inspection ciblée Lollybet : une seule navigation, viewport large.
Cherche Sinner via la recherche interne du shadow DOM.
"""
import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

REAL_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR = os.path.join(project_root, "ChromeDriver", "lollybet_profile")
HOME_URL    = "https://lolly-bet99.com"
SS = "/tmp"

# Snippet JS réutilisable pour accéder au shadow root du widget sportsbook
GET_SR = """
    (function() {
        var el = Array.from(document.querySelectorAll('*')).find(function(e) {
            return e.tagName.startsWith('SG-');
        });
        return el ? el.shadowRoot : null;
    })()
"""

async def eval_sr(page, body):
    """Évalue du JS dans le contexte du shadow root."""
    return await page.evaluate("(function() { var sr = " + GET_SR + "; " + body + " })()")


async def main():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth as _Stealth

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            executable_path=REAL_CHROME,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1600, "height": 950},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await _Stealth().apply_stealth_async(page)

        # ── 1. Aller sur la section pré-match tennis ──────────────────
        print("Navigation pré-match tennis...")
        await page.goto(HOME_URL + "/fr/sportsbook#/events/tennis",
                        wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)

        # ── 2. Trouver l'input de recherche dans le shadow DOM ────────
        print("Recherche input shadow DOM...")
        search_handle = await page.evaluate_handle(
            "(function() { var sr = " + GET_SR + "; return sr ? sr.querySelector('.sb-search-field__input') : null; })()"
        )
        search_el = search_handle.as_element()

        if not search_el:
            # Playwright peut piercer shadow DOM avec locator
            try:
                search_el = await page.query_selector(".sb-search-field__input")
            except Exception:
                pass

        if not search_el:
            print("❌ Input recherche non trouvé dans shadow DOM")
            await page.screenshot(path=SS + "/lolly2_debug.png")
            print("📸 " + SS + "/lolly2_debug.png")
            await asyncio.sleep(30)
            await browser.close()
            return

        print("✅ Input trouvé — frappe 'Sinner'...")
        await search_el.click()
        await asyncio.sleep(0.3)
        await search_el.type("Sinner", delay=80)
        await asyncio.sleep(3)
        await page.screenshot(path=SS + "/lolly2_search.png")
        print("📸 " + SS + "/lolly2_search.png")

        # ── 3. Lire les résultats de recherche ────────────────────────
        print("\n=== RÉSULTATS RECHERCHE ===")
        results = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "var r = []; "
            "sr.querySelectorAll('*').forEach(function(n) { "
            "    var t = n.innerText ? n.innerText.trim() : ''; "
            "    if (t && t.toLowerCase().indexOf('sinner') >= 0 && n.children.length < 5) "
            "        r.push({cls: (n.className||'').slice(0,60), text: t.slice(0,100)}); "
            "}); "
            "return r.slice(0,15); })()"
        )
        for r in results:
            print("  ." + r['cls'][:50] + " → '" + r['text'][:80] + "'")

        # ── 4. Cliquer sur le résultat Sinner ────────────────────────
        print("\nClic sur résultat Sinner...")
        clicked = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return null; "
            "var items = sr.querySelectorAll('.sb-search-results-item, [class*=\"search-result\"]'); "
            "for (var i = 0; i < items.length; i++) { "
            "    if (items[i].innerText && items[i].innerText.toLowerCase().indexOf('sinner') >= 0) { "
            "        items[i].click(); return items[i].innerText.trim().slice(0, 80); "
            "    } "
            "} return null; })()"
        )
        print("Match: " + str(clicked))
        await asyncio.sleep(5)
        await page.screenshot(path=SS + "/lolly2_match.png")
        print("📸 " + SS + "/lolly2_match.png  URL: " + page.url)

        # ── 5. Tous les marchés ───────────────────────────────────────
        print("\n=== MARCHÉS DE LA PAGE ===")
        market_titles = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "var r = []; var seen = {}; "
            "var sels = ['[class*=\"market-name\"]','[class*=\"market-title\"]','[class*=\"market__name\"]',"
            "'[class*=\"market__title\"]','.sb-market-title','.sb-market-name',"
            "'[class*=\"group-name\"]','[class*=\"group-title\"]','[class*=\"sb-market\"]']; "
            "sels.forEach(function(s) { "
            "    sr.querySelectorAll(s).forEach(function(el) { "
            "        var t = el.innerText ? el.innerText.trim() : ''; "
            "        if (t && t.length < 80 && !seen[t]) { seen[t]=1; "
            "            r.push({cls: (el.className||'').slice(0,60), text: t}); } "
            "    }); "
            "}); return r; })()"
        )
        for m in market_titles:
            print("  ." + m['cls'][:45] + " → '" + m['text'] + "'")

        # ── 6. Chercher "Score exact" et "3-0" ───────────────────────
        print("\n=== SCORE EXACT / 3-0 ===")
        score_items = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "var r = []; "
            "sr.querySelectorAll('*').forEach(function(n) { "
            "    var t = n.innerText ? n.innerText.trim() : ''; "
            "    if (!t || n.children.length > 8) return; "
            "    var tl = t.toLowerCase(); "
            "    if (tl.indexOf('score exact')>=0 || tl.indexOf('correct score')>=0 "
            "        || t.indexOf('3-0')>=0 || t.indexOf('3:0')>=0 || t.indexOf('3 - 0')>=0) "
            "        r.push({cls: (n.className||'').slice(0,60), text: t.slice(0,120)}); "
            "}); return r.slice(0,15); })()"
        )
        if score_items:
            for s in score_items:
                print("  ." + s['cls'][:50] + " → '" + s['text'][:80] + "'")
        else:
            print("  ⚠️  Score exact non trouvé — affichage de TOUS les marchés texte")
            all_market_text = await page.evaluate(
                "(function() { var sr = " + GET_SR + "; if (!sr) return ''; "
                "return sr.innerText ? sr.innerText.slice(0,3000) : ''; })()"
            )
            print(all_market_text[:2000])

        # ── 7. Tous les boutons ───────────────────────────────────────
        print("\n=== BOUTONS (cotes + actions) ===")
        all_btns = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "var r = []; var seen = {}; "
            "sr.querySelectorAll('button, [class*=\"outcome\"], [class*=\"odd\"]').forEach(function(el) { "
            "    var t = el.innerText ? el.innerText.trim() : ''; "
            "    if (t && t.length < 40 && !seen[t.slice(0,20)]) { "
            "        seen[t.slice(0,20)] = 1; "
            "        r.push({cls: (el.className||'').slice(0,60), tag: el.tagName, text: t.slice(0,40)}); "
            "    } "
            "}); return r.slice(0,40); })()"
        )
        for b in all_btns:
            print("  [" + b['tag'] + "] ." + b['cls'][:50] + " → '" + b['text'] + "'")

        # ── 8. Cliquer une cote → betslip ────────────────────────────
        print("\n=== BETSLIP (après clic cote) ===")
        first_btn_text = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return false; "
            "var btns = sr.querySelectorAll('[class*=\"outcome-button\"], [class*=\"odd-button\"], [class*=\"bet-btn\"]'); "
            "if (btns[0]) { btns[0].click(); return btns[0].innerText ? btns[0].innerText.trim() : 'ok'; } "
            "return false; })()"
        )
        print("Clic cote: " + str(first_btn_text))
        await asyncio.sleep(2)
        await page.screenshot(path=SS + "/lolly2_betslip.png")
        print("📸 " + SS + "/lolly2_betslip.png")

        betslip_data = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "var r = []; "
            "sr.querySelectorAll('[class*=\"betslip\"], [class*=\"bet-slip\"], [class*=\"coupon\"], [class*=\"ticket\"], [class*=\"slip\"]').forEach(function(el) { "
            "    var t = el.innerText ? el.innerText.trim() : ''; "
            "    if (t) r.push({cls: (el.className||'').slice(0,60), tag: el.tagName, text: t.slice(0,100)}); "
            "}); "
            "sr.querySelectorAll('input').forEach(function(el) { "
            "    r.push({cls: (el.className||'').slice(0,60), tag: 'INPUT', text: el.placeholder||el.value||'(vide)'}); "
            "}); "
            "return r.slice(0,20); })()"
        )
        for b in betslip_data:
            print("  [" + b['tag'] + "] ." + b['cls'][:50] + " → '" + b['text'][:60] + "'")

        print("\nBoutons après clic:")
        btns_after = await page.evaluate(
            "(function() { var sr = " + GET_SR + "; if (!sr) return []; "
            "return Array.from(sr.querySelectorAll('button')).map(function(b) { "
            "    return {text: b.innerText ? b.innerText.trim().slice(0,40) : '', "
            "            cls: (b.className||'').slice(0,60), disabled: b.disabled}; "
            "}).filter(function(b) { return b.text; }); })()"
        )
        for b in btns_after:
            status = "[disabled]" if b['disabled'] else "[actif]  "
            print("  " + status + " '" + b['text'] + "' ." + b['cls'][:50])

        print("\n=== FIN ===")
        await asyncio.sleep(30)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
