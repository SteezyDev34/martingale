# -*- coding: utf-8 -*-
"""
Inspecte la modal de confirmation Betclic après un placement de pari.
Capture le DOM et screenshot pour trouver les sélecteurs exacts.
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
MATCH_URL    = "https://www.betclic.fr/tennis-stennis/wimbledon-h-c24/jannik-sinner-miomir-kecmanovic-m1152891277660160"
SCREENSHOT_DIR = "/tmp"


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
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await _Stealth().apply_stealth_async(page)

        # ── 1. Aller sur la page du match ─────────────────────────────
        print(f"Navigation vers {MATCH_URL}")
        await page.goto(MATCH_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Fermer les modals éventuelles
        for close_sel in ["[class*='modal'] button[class*='close']",
                          "[class*='popin'] button[class*='close']",
                          "button[aria-label*='ermer']",
                          "[class*='overlay'] button"]:
            try:
                btn = await page.query_selector(close_sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

        # ── 2. Nettoyer le betslip ────────────────────────────────────
        print("Nettoyage betslip...")
        for del_sel in ["sports-betting-slip [class*='delete']",
                        "sports-betting-slip [class*='close']",
                        "sports-betting-slip [class*='remove']",
                        "betting-slip-selection-card [class*='delete']",
                        "betting-slip-selection-card button"]:
            btns = await page.query_selector_all(del_sel)
            for btn in btns:
                try:
                    await btn.click()
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

        # ── 3. Cliquer sur la cote "3-0" ──────────────────────────────
        print("Recherche label '3 - 0' dans les marchés...")
        import re
        def _norm(s): return re.sub(r'\s*-\s*', '-', s.lower().strip())

        markets = await page.query_selector_all("[class*='market']")
        clicked = False
        for market in markets:
            market_text = _norm(await market.inner_text())
            if "score" not in market_text and "3-0" not in market_text:
                continue
            labels = await market.query_selector_all(".marketBox_label")
            for label_el in labels:
                if "3-0" not in _norm(await label_el.inner_text()):
                    continue
                btn_handle = await label_el.evaluate_handle("""(el) => {
                    let node = el;
                    for (let i = 0; i < 6; i++) {
                        node = node.parentElement;
                        if (!node) break;
                        const btn = node.querySelector('button.btn.is-odd');
                        if (btn) return btn;
                    }
                    return null;
                }""")
                btn_el = btn_handle.as_element() if btn_handle else None
                if btn_el:
                    text = (await btn_el.inner_text()).strip()
                    print(f"✅ Clic sur cote '{text}' — label '3 - 0'")
                    await btn_el.click()
                    clicked = True
                    break
            if clicked:
                break

        if not clicked:
            print("❌ Cote 3-0 non trouvée")
            await browser.close()
            return

        await asyncio.sleep(2)

        # ── 4. Saisir la mise (0,10) ─────────────────────────────────
        print("Saisie mise 0,10...")
        stake_input = await page.query_selector("input[placeholder='Mise']")
        if stake_input:
            await stake_input.click(click_count=3)
            await asyncio.sleep(0.2)
            await stake_input.type("0,10", delay=80)
            await asyncio.sleep(1)
        else:
            print("⚠️  Input mise non trouvé")

        await page.screenshot(path=f"{SCREENSHOT_DIR}/betclic_before_parier.png")
        print(f"📸 Screenshot avant Parier: {SCREENSHOT_DIR}/betclic_before_parier.png")

        # ── 5. Inspecter et cliquer sur "Parier" ─────────────────────
        print("\n=== INSPECTION DU BOUTON PARIER ===")

        # Lister tous les boutons visibles sur la page
        all_buttons = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button')).map(btn => ({
                text: btn.innerText.trim().slice(0, 40),
                classes: btn.className.slice(0, 80),
                disabled: btn.disabled,
                visible: btn.offsetParent !== null,
                inBetslip: !!btn.closest('sports-betting-slip, betting-slip-footer, [class*=betslip]'),
                rect: btn.getBoundingClientRect()
            })).filter(b => b.text.length > 0);
        }""")
        print("Tous les boutons trouvés:")
        for b in all_buttons:
            tag = "✅" if "parier" in b['text'].lower() else "  "
            print(f"  {tag} '{b['text']}' | classes={b['classes'][:50]} | disabled={b['disabled']} | betslip={b['inBetslip']}")

        # Chercher le bouton Parier par texte dans le betslip
        confirm = None
        buttons = await page.query_selector_all("sports-betting-slip button, betting-slip-footer button")
        for btn in buttons:
            txt = (await btn.inner_text()).strip().lower()
            if txt.startswith("parier"):
                print(f"\n✅ Bouton Parier trouvé dans betslip: '{txt[:40]}'")
                confirm = btn
                break
        if not confirm:
            for btn in await page.query_selector_all("button"):
                txt = (await btn.inner_text()).strip().lower()
                if txt.startswith("parier"):
                    print(f"\n✅ Bouton Parier trouvé (global): '{txt[:40]}'")
                    confirm = btn
                    break

        if not confirm:
            print("❌ Bouton Parier non trouvé")
            await browser.close()
            return

        # Infos sur le bouton trouvé
        btn_info = await confirm.evaluate("""(el) => ({
            tag: el.tagName,
            classes: el.className,
            disabled: el.disabled,
            text: el.innerText,
            visible: el.offsetParent !== null,
            rect: el.getBoundingClientRect(),
            parent: el.parentElement?.tagName + ' ' + el.parentElement?.className?.slice(0,50)
        })""")
        print(f"\nBouton Parier trouvé:")
        print(f"  tag={btn_info['tag']} | classes={btn_info['classes']}")
        print(f"  disabled={btn_info['disabled']} | visible={btn_info['visible']}")
        print(f"  text='{btn_info['text']}' | parent={btn_info['parent']}")
        print(f"  rect={btn_info['rect']}")

        disabled = await confirm.get_attribute("disabled")
        if disabled:
            print(f"❌ Bouton Parier désactivé")
            await browser.close()
            return

        # Scroll vers le bouton pour s'assurer qu'il est visible
        await confirm.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/betclic_before_click.png")
        print(f"📸 Avant clic: {SCREENSHOT_DIR}/betclic_before_click.png")

        # Tenter 3 méthodes de clic différentes
        print("\nTentative clic natif Playwright...")
        await confirm.click(force=True)
        await asyncio.sleep(1)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/betclic_after_click1.png")

        # Vérifier si quelque chose a changé
        betslip_text = await page.inner_text("sports-betting-slip")
        print(f"Betslip après clic natif: {betslip_text[:100]}")

        if "parier" in betslip_text.lower():
            print("Betslip inchangé — essai JS click...")
            await page.evaluate("(el) => el.click()", confirm)
            await asyncio.sleep(1)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/betclic_after_click2.png")
            betslip_text = await page.inner_text("sports-betting-slip")
            print(f"Betslip après JS click: {betslip_text[:100]}")

        if "parier" in betslip_text.lower():
            print("Betslip inchangé — essai dispatch MouseEvent...")
            await page.evaluate("""(el) => {
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }""", confirm)
            await asyncio.sleep(1)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/betclic_after_click3.png")
            betslip_text = await page.inner_text("sports-betting-slip")
            print(f"Betslip après MouseEvent: {betslip_text[:100]}")

        print(f"\n✅ Parier cliqué — attente confirmation...")

        # ── 6. Capturer le DOM toutes les 500ms pendant 10s ─────────
        for tick in range(20):
            await asyncio.sleep(0.5)
            screenshot_path = f"{SCREENSHOT_DIR}/betclic_confirm_{tick:02d}.png"
            await page.screenshot(path=screenshot_path)

            # Dump tous les textes visibles nouveaux (modals, overlays, etc.)
            dom_info = await page.evaluate("""() => {
                const results = [];
                // Chercher modals / overlays / notifications
                const candidates = [
                    "[class*='modal']", "[class*='popin']", "[class*='overlay']",
                    "[class*='notification']", "[class*='toast']", "[class*='confirm']",
                    "[class*='success']", "[class*='valid']", "[class*='receipt']",
                    "[class*='ticket']", "[class*='bet-placed']", "[class*='betPlaced']",
                    "sports-betting-slip", "[class*='betslip']",
                    "[role='dialog']", "[role='alert']", "[role='status']",
                    "[aria-live]", "[class*='message']",
                ];
                candidates.forEach(sel => {
                    try {
                        document.querySelectorAll(sel).forEach(el => {
                            const text = el.innerText?.trim();
                            if (text && text.length > 3 && text.length < 500) {
                                results.push({selector: sel, text: text.slice(0, 200)});
                            }
                        });
                    } catch(e) {}
                });
                return results;
            }""")

            if dom_info:
                print(f"\n--- Tick {tick} ({tick*0.5:.1f}s) ---")
                seen = set()
                for item in dom_info:
                    key = item['text'][:80]
                    if key not in seen:
                        seen.add(key)
                        print(f"  [{item['selector']}]\n    {item['text'][:200]}")

            # Détecter les textes de confirmation habituels
            page_text = (await page.inner_text("body")).lower()
            for keyword in ["validé", "enregistré", "confirmé", "placé", "gagner", "ticket", "reçu", "receipt", "accepted", "placed"]:
                if keyword in page_text:
                    print(f"\n🎯 Mot-clé détecté dans la page: '{keyword}'")
                    # Trouver l'élément contenant ce mot
                    el_info = await page.evaluate(f"""() => {{
                        const results = [];
                        document.querySelectorAll("*").forEach(el => {{
                            const t = el.innerText?.trim().toLowerCase();
                            if (t && t.includes("{keyword}") && el.children.length < 4 && t.length < 300) {{
                                results.push({{
                                    tag: el.tagName,
                                    classes: el.className?.slice(0, 80),
                                    text: el.innerText.trim().slice(0, 150)
                                }});
                            }}
                        }});
                        return results.slice(0, 10);
                    }}""")
                    for e in el_info:
                        print(f"    <{e['tag']}> .{e['classes'][:60]}")
                        print(f"    → {e['text']}")

        print(f"\n📸 Screenshots: {SCREENSHOT_DIR}/betclic_confirm_*.png")
        print("=== FIN INSPECTION ===")
        await asyncio.sleep(15)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
