# -*- coding: utf-8 -*-
"""
Inspection du DOM Lollybet pour trouver les vrais sélecteurs.
Lance ce script avec une session active (profil lollybet_profile).
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
SCREENSHOT  = "/tmp"

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

        # ── 1. Session ────────────────────────────────────────────────
        print("\n=== SESSION ===")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)
        await page.screenshot(path=f"{SCREENSHOT}/lolly_home.png")
        print(f"📸 {SCREENSHOT}/lolly_home.png  — URL: {page.url}")

        session_info = await page.evaluate("""() => {
            const cands = [
                "[class*='user']","[class*='account']","[class*='balance']","[class*='wallet']",
                "[class*='logged']","[class*='avatar']","[class*='profile']",
                "a[href*='deposit']","a[href*='account']","a[href*='profil']",
                "[data-testid*='user']","[class*='login']","[class*='header-user']"
            ];
            const r = [];
            cands.forEach(s => {
                try {
                    document.querySelectorAll(s).forEach(el => {
                        const t = el.innerText?.trim().slice(0,50);
                        if (t) r.push({sel: s, tag: el.tagName, text: t, cls: el.className?.slice(0,60)});
                    });
                } catch(e) {}
            });
            return r.slice(0, 20);
        }""")
        if session_info:
            print("Éléments session trouvés:")
            for s in session_info:
                print(f"  {s['sel']}  [{s['tag']}] .{s['cls'][:40]} → '{s['text']}'")
        else:
            print("❌ Aucun élément session — connecte-toi dans la fenêtre (5 min max)")
            await page.goto(f"{HOME_URL}/login", wait_until="domcontentloaded", timeout=20000)
            for _ in range(100):
                await asyncio.sleep(3)
                info = await page.evaluate("""() => {
                    const cands = ["[class*='balance']","[class*='user']","[class*='account']",
                                   "a[href*='deposit']","[class*='wallet']","[class*='logged']"];
                    for (const s of cands) {
                        const el = document.querySelector(s);
                        const t = el?.innerText?.trim();
                        if (t) return {sel: s, text: t.slice(0,50), cls: el.className?.slice(0,60)};
                    }
                    return null;
                }""")
                if info:
                    print(f"✅ Connecté! {info['sel']} → '{info['text']}'")
                    break
            else:
                print("❌ Timeout — fermeture")
                await browser.close()
                return

        # ── 2. Barre de recherche ─────────────────────────────────────
        print("\n=== BARRE DE RECHERCHE ===")
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        inputs = await page.evaluate("""() =>
            Array.from(document.querySelectorAll('input')).map(el => ({
                placeholder: el.placeholder, type: el.type,
                cls: el.className?.slice(0,80), id: el.id, name: el.name
            })).filter(i => i.placeholder || i.type === 'search')
        """)
        print("Inputs:")
        for i in inputs:
            print(f"  placeholder='{i['placeholder']}' type='{i['type']}' cls='{i['cls'][:50]}'")

        # ── 3. Chercher un match tennis via le sportsbook principal ──────
        print("\n=== NAVIGATION SPORTSBOOK ===")
        await page.goto(f"{HOME_URL}/fr/sportsbook", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)
        await page.screenshot(path=f"{SCREENSHOT}/lolly_sportsbook.png")
        print(f"📸 {SCREENSHOT}/lolly_sportsbook.png  (URL: {page.url})")

        # Lister les éléments cliquables (onglets sport / tournaments)
        clickables = await page.evaluate("""() => {
            const r = [];
            document.querySelectorAll("a, button, [class*='tab'], [class*='sport'], [class*='nav']").forEach(el => {
                const t = el.innerText?.trim();
                const h = el.href || '';
                if (t && t.length < 40 && (t.includes('Tennis') || t.includes('Wimbledon')
                    || t.includes('ATP') || t.includes('Pré') || t.includes('Pre') || t.includes('upcoming')))
                    r.push({tag: el.tagName, text: t, href: h.slice(0,80), cls: el.className?.slice(0,50)});
            });
            return r.slice(0, 20);
        }""")
        print("Éléments Tennis/Wimbledon/Pré-match:")
        for c in clickables:
            print(f"  <{c['tag']}> '{c['text']}' href={c['href']}")

        # Chercher tous les textes — dump brut
        body_text = (await page.inner_text("body"))[:3000]
        print(f"\nTexte page sportsbook (3000 chars):\n{body_text}")

        # Cliquer sur Tennis dans la navigation
        print("\nRecherche Tennis dans la nav...")
        tennis_link = None
        for sel in ["a[href*='tennis']", "[class*='tab'][class*='tennis']", "button"]:
            els = await page.query_selector_all(sel)
            for el in els:
                t = (await el.inner_text()).strip().lower()
                if "tennis" in t:
                    tennis_link = el
                    print(f"✅ Trouvé: '{t}' via {sel}")
                    break
            if tennis_link:
                break

        # ── Shadow DOM / web components ───────────────────────────────
        print("\n=== SHADOW DOM / WEB COMPONENTS ===")
        shadow_info = await page.evaluate("""() => {
            const r = [];
            // Chercher tous les éléments avec shadow root
            document.querySelectorAll("*").forEach(el => {
                if (el.shadowRoot) {
                    r.push({tag: el.tagName, cls: el.className?.slice(0,60),
                            shadowText: el.shadowRoot.innerHTML?.slice(0,200)});
                }
            });
            return r.slice(0, 10);
        }""")
        if shadow_info:
            print("Éléments avec Shadow DOM:")
            for s in shadow_info:
                print(f"  <{s['tag']}> .{s['cls'][:40]}")
                print(f"    shadow: {s['shadowText'][:100]}")
        else:
            print("Pas de shadow DOM trouvé")

        # Inspecter le HTML brut pour trouver le composant sportsbook
        html_structure = await page.evaluate("""() => {
            const main = document.querySelector('main, [class*="content"], [class*="page"], [role="main"], app-root, wlc-app');
            return main ? main.innerHTML.slice(0, 3000) : document.body.innerHTML.slice(0, 3000);
        }""")
        print(f"\nHTML structure principale (3000 chars):\n{html_structure}")

        # ── Cliquer le lien Live Tennis ───────────────────────────────
        print("\n=== NAVIGATION VERS LIVE TENNIS ===")
        await page.goto(f"{HOME_URL}/fr/sportsbook/live/events/tennis", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(8)
        await page.screenshot(path=f"{SCREENSHOT}/lolly_tennis.png")
        print(f"📸 {SCREENSHOT}/lolly_tennis.png  (URL: {page.url})")

        # Chercher le contenu dans les web components
        live_content = await page.evaluate("""() => {
            // Chercher profondément dans le DOM y compris les slot/templates
            const getAllText = (root) => {
                const texts = [];
                const walk = (node) => {
                    if (node.nodeType === 3 && node.textContent.trim())
                        texts.push(node.textContent.trim());
                    if (node.shadowRoot) walk(node.shadowRoot);
                    node.childNodes.forEach(walk);
                };
                walk(root);
                return texts.filter(t => t.length > 2 && t.length < 100);
            };
            return getAllText(document.body).slice(0, 100);
        }""")
        print("Textes dans le DOM (y compris shadow):")
        seen = set()
        for t in live_content:
            if t not in seen:
                seen.add(t)
                print(f"  '{t[:60]}'")

        # ── Accès au Shadow DOM du sportsbook ─────────────────────────
        print("\n=== SHADOW DOM SPORTSBOOK ===")
        sb_info = await page.evaluate("""() => {
            // Trouver SG-SB-ROOT
            const sbRoot = document.querySelector('[class*="sg-sb"], [id*="sg-sb"]')
                        || Array.from(document.querySelectorAll('*')).find(el => el.tagName.startsWith('SG-'));
            if (!sbRoot) return {error: 'SG-SB-ROOT non trouvé'};
            const sr = sbRoot.shadowRoot;
            if (!sr) return {error: 'pas de shadowRoot'};
            // Chercher Sinner/Wimbledon dans le shadow
            const texts = [];
            const walk = (root) => {
                root.querySelectorAll('*').forEach(el => {
                    const t = el.innerText?.trim();
                    if (t && t.length > 2 && t.length < 100
                        && (t.toLowerCase().includes('sinner') || t.toLowerCase().includes('wimbledon')
                            || t.toLowerCase().includes('tennis') || t.toLowerCase().includes('kecmanovic'))) {
                        texts.push({tag: el.tagName, cls: el.className?.slice(0,60), text: t.slice(0,80)});
                    }
                });
            };
            walk(sr);
            return {tag: sbRoot.tagName, texts, htmlSnippet: sr.innerHTML?.slice(0,2000)};
        }""")
        if 'error' in sb_info:
            print(f"❌ {sb_info['error']}")
            # Essai alternatif : chercher par tagName commençant par SG
            sb_tag = await page.evaluate("""() => {
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    if (el.tagName.startsWith('SG-') || el.tagName.startsWith('sg-')) {
                        return {tag: el.tagName, cls: el.className, hasShadow: !!el.shadowRoot};
                    }
                }
                return null;
            }""")
            print(f"Recherche SG-* tag: {sb_tag}")
        else:
            print(f"✅ SG-SB-ROOT trouvé: <{sb_info['tag']}>")
            if sb_info['texts']:
                print("Textes tennis/Sinner dans shadow:")
                for t in sb_info['texts']:
                    print(f"  <{t['tag']}> .{t['cls'][:40]} → '{t['text']}'")
            else:
                print("⚠️  Pas de texte Sinner/Wimbledon dans le shadow DOM")
                print(f"\nHTML shadow DOM (2000 chars):\n{sb_info['htmlSnippet']}")

        # ── Chercher les matchs tennis dans le shadow DOM ─────────────
        print("\n=== MATCHS TENNIS DANS SHADOW DOM ===")
        tennis_matches = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            const sr = el.shadowRoot;
            const results = [];
            // Chercher tous les éléments texte dans le shadow DOM
            const allEls = sr.querySelectorAll('[class*="match"], [class*="event"], [class*="game"], [class*="fixture"]');
            allEls.forEach(e => {
                const t = e.innerText?.trim();
                if (t && t.length > 3 && t.length < 200) {
                    results.push({cls: e.className?.slice(0,60), text: t.slice(0,120)});
                }
            });
            return results.slice(0, 30);
        }""")
        if tennis_matches:
            print("Matchs/events dans shadow:")
            for m in tennis_matches:
                print(f"  .{m['cls'][:50]} → {m['text'][:80]}")
        else:
            print("⚠️  Pas de matchs trouvés — cherchons les liens et boutons")

        # Chercher tout texte dans le shadow root directement (profondeur 1)
        all_shadow = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            const sr = el.shadowRoot;
            const seen = new Set();
            const r = [];
            sr.querySelectorAll('*').forEach(node => {
                const t = node.innerText?.trim();
                if (t && t.length > 2 && t.length < 150 && node.children.length < 4) {
                    if (!seen.has(t.slice(0,50))) {
                        seen.add(t.slice(0,50));
                        r.push({cls: node.className?.slice(0,60), text: t.slice(0,100),
                                href: node.closest('a')?.href || ''});
                    }
                }
            });
            return r.slice(0, 80);
        }""")
        print("\nTous les textes du shadow DOM:")
        for t in all_shadow:
            print(f"  .{t['cls'][:40]} → '{t['text'][:70]}'")

        # ── Chercher Wimbledon / Sinner dans tout le shadow ───────────
        print("\n=== RECHERCHE WIMBLEDON / SINNER ===")
        wimbledon = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            const sr = el.shadowRoot;
            const r = [];
            sr.querySelectorAll('*').forEach(node => {
                const t = node.innerText?.trim();
                if (t && (t.toLowerCase().includes('wimbledon') || t.toLowerCase().includes('sinner')
                         || t.toLowerCase().includes('kecmanovic'))) {
                    r.push({cls: node.className?.slice(0,60), text: t.slice(0,120)});
                }
            });
            return r.slice(0, 20);
        }""")
        if wimbledon:
            print("Wimbledon/Sinner trouvé:")
            for w in wimbledon:
                print(f"  .{w['cls'][:50]} → '{w['text'][:80]}'")
        else:
            print("⚠️  Wimbledon/Sinner absent de la page courante")

        # ── Toggler pré-match ─────────────────────────────────────────
        print("\n=== TOGGLE PRÉ-MATCH ===")
        togglers = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            const sr = el.shadowRoot;
            return Array.from(sr.querySelectorAll('[class*="toggler"], [class*="toggle"], button'))
                .map(b => ({text: b.innerText?.trim().slice(0,40), cls: b.className?.slice(0,60),
                            active: b.classList.contains('active')}))
                .filter(b => b.text);
        }""")
        print("Boutons/toggles:")
        for b in togglers:
            print(f"  {'[actif]' if b['active'] else '[inactif]'} '{b['text']}' .{b['cls'][:50]}")

        # Cliquer le toggler inactif (pré-match)
        clicked = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return false;
            const sr = el.shadowRoot;
            const toggls = sr.querySelectorAll('[class*="toggler"]');
            for (const t of toggls) {
                if (!t.classList.contains('active')) { t.click(); return t.innerText?.trim(); }
            }
            return false;
        }""")
        print(f"Clic sur: {clicked}")
        await asyncio.sleep(4)
        await page.screenshot(path=f"{SCREENSHOT}/lolly_prematch.png")
        print(f"📸 {SCREENSHOT}/lolly_prematch.png")

        # Lister tous les matchs disponibles maintenant
        all_matches = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            return Array.from(el.shadowRoot.querySelectorAll('[class*="match-team-name"], [class*="team-name"]'))
                .map(e => e.innerText?.trim()).filter(Boolean);
        }""")
        print(f"\nMatchs disponibles ({len(all_matches)}):")
        for m in all_matches[:30]:
            print(f"  '{m}'")

        # ── Cliquer "Matchs" (titre = pré-match) dans shadow DOM ────────
        print("\n=== CLIC MATCHS (PRÉ-MATCH) ===")
        clicked2 = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return false;
            const sr = el.shadowRoot;
            // Chercher .sb-live-matches__title ou tout élément texte "Matchs"
            const cands = sr.querySelectorAll('.sb-live-matches__title, [class*="matches__title"], [class*="match-title"]');
            for (const c of cands) {
                c.click();
                return 'clicked: ' + c.innerText?.trim();
            }
            // Chercher par texte "Matchs" dans les boutons/liens
            const all = sr.querySelectorAll('button, a, [class*="tab"], [class*="nav"]');
            for (const a of all) {
                const t = a.innerText?.trim();
                if (t === 'Matchs' || t === 'Pre-match' || t === 'Upcoming') {
                    a.click();
                    return 'text-click: ' + t;
                }
            }
            return false;
        }""")
        print(f"Résultat: {clicked2}")
        await asyncio.sleep(5)

        # Chercher Wimbledon dans la liste pré-match
        wb3 = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return [];
            const r = [];
            el.shadowRoot.querySelectorAll('*').forEach(n => {
                const t = n.innerText?.trim();
                if (t && (t.toLowerCase().includes('wimbledon') || t.toLowerCase().includes('sinner')))
                    r.push({cls: n.className?.slice(0,60), text: t.slice(0,100)});
            });
            return r.slice(0, 10);
        }""")
        if wb3:
            print("✅ Wimbledon/Sinner après clic Matchs:")
            for w in wb3: print(f"  .{w['cls'][:50]} → '{w['text'][:80]}'")

        # Essayer la navigation directe via #/sport/tennis dans le SG widget
        print("\n=== ESSAI URL PRÉ-MATCH DIRECTE ===")
        for test_url in [
            f"{HOME_URL}/fr/sportsbook/sports/tennis",
            f"{HOME_URL}/fr/sportsbook#/sport/tennis",
            f"{HOME_URL}/fr/sportsbook#/events/tennis",
        ]:
            await page.goto(test_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(6)
            wb4 = await page.evaluate("""() => {
                const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                if (!el || !el.shadowRoot) return [];
                const r = [];
                el.shadowRoot.querySelectorAll('[class*="team-name"], [class*="match-name"]').forEach(n => {
                    const t = n.innerText?.trim();
                    if (t) r.push(t);
                });
                return r.slice(0, 20);
            }""")
            print(f"\n{test_url}")
            print(f"  Équipes: {wb4[:10]}")
            if any('sinner' in t.lower() or 'wimbledon' in t.lower() for t in wb4):
                print("  ✅ SINNER TROUVÉ!")
                break

        # ── Navigation pré-match tennis + scroll ─────────────────────
        print("\n=== PRÉ-MATCH TENNIS COMPLET ===")
        await page.goto(f"{HOME_URL}/fr/sportsbook#/events/tennis", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(8)

        # Scroller plusieurs fois dans le shadow DOM pour charger plus de matchs
        for _ in range(5):
            await page.evaluate("""() => {
                const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                if (el && el.shadowRoot) {
                    const scrollable = el.shadowRoot.querySelector('[class*="scroll"], [class*="content"], [class*="list"]');
                    if (scrollable) scrollable.scrollTop += 800;
                }
                window.scrollBy(0, 800);
            }""")
            await asyncio.sleep(1)

        await page.screenshot(path=f"{SCREENSHOT}/lolly_tennis.png")
        print(f"📸 {SCREENSHOT}/lolly_tennis.png  (URL: {page.url})")

        # Chercher Wimbledon/Sinner dans le shadow DOM
        wimbledon_pm = await page.evaluate("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return {error: 'no SG'};
            const sr = el.shadowRoot;
            const found = [];
            sr.querySelectorAll('*').forEach(n => {
                const t = n.innerText?.trim();
                if (t && (t.toLowerCase().includes('wimbledon') || t.toLowerCase().includes('sinner')
                         || t.toLowerCase().includes('kecmanovic')))
                    found.push({cls: n.className?.slice(0,60), text: t.slice(0,100)});
            });
            const teams = Array.from(sr.querySelectorAll('[class*="team-name"], [class*="match-name"]'))
                .map(e => e.innerText?.trim()).filter(Boolean);
            const tournaments = Array.from(sr.querySelectorAll('[class*="tournament"], [class*="league"], [class*="competition"]'))
                .map(e => e.innerText?.trim().slice(0,80)).filter(Boolean);
            const inputs = Array.from(sr.querySelectorAll('input')).map(i => ({
                placeholder: i.placeholder, type: i.type, cls: i.className?.slice(0,60)
            }));
            return {found: found.slice(0,10), teams: teams.slice(0, 40), tournaments: tournaments.slice(0, 20), inputs};
        }""")
        print(f"\nWimbledon/Sinner trouvé: {wimbledon_pm.get('found', [])}")
        print(f"\nTournois ({len(wimbledon_pm.get('tournaments', []))}): {wimbledon_pm.get('tournaments', [])[:15]}")
        print(f"\nÉquipes ({len(wimbledon_pm.get('teams', []))}): {wimbledon_pm.get('teams', [])[:20]}")
        print(f"\nInputs shadow: {wimbledon_pm.get('inputs', [])}")

        # ── Utiliser la recherche interne du shadow DOM ───────────────
        print("\n=== RECHERCHE INTERNE SHADOW DOM ===")
        # Trouver et remplir l'input .sb-search-field__input dans le shadow
        search_handle = await page.evaluate_handle("""() => {
            const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
            if (!el || !el.shadowRoot) return null;
            return el.shadowRoot.querySelector('.sb-search-field__input');
        }""")
        search_el = search_handle.as_element() if search_handle else None
        if search_el:
            print("✅ Input recherche shadow trouvé")
            await search_el.click()
            await asyncio.sleep(0.5)
            await search_el.type("Sinner", delay=80)
            await asyncio.sleep(3)
            await page.screenshot(path=f"{SCREENSHOT}/lolly_shadow_search.png")
            print(f"📸 {SCREENSHOT}/lolly_shadow_search.png")

            # Lire les résultats de recherche dans le shadow DOM
            results = await page.evaluate("""() => {
                const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                if (!el || !el.shadowRoot) return [];
                const sr = el.shadowRoot;
                const r = [];
                sr.querySelectorAll('*').forEach(n => {
                    const t = n.innerText?.trim();
                    if (t && t.toLowerCase().includes('sinner') && n.children.length < 5)
                        r.push({cls: n.className?.slice(0,60), text: t.slice(0,100)});
                });
                return r.slice(0, 15);
            }""")
            print("Résultats pour 'Sinner':")
            for r in results:
                print(f"  .{r['cls'][:50]} → '{r['text'][:80]}'")

            # Cliquer sur le premier résultat de match
            clicked_match = await page.evaluate("""() => {
                const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                if (!el || !el.shadowRoot) return null;
                const sr = el.shadowRoot;
                const r = sr.querySelectorAll('[class*="result"], [class*="suggestion"], [class*="search-item"]');
                for (const item of r) {
                    if (item.innerText?.toLowerCase().includes('sinner')) {
                        item.click();
                        return item.innerText?.trim().slice(0,80);
                    }
                }
                // Chercher n'importe quel élément cliquable contenant Sinner
                const all = sr.querySelectorAll('[class*="match"], [class*="event"], a');
                for (const item of all) {
                    if (item.innerText?.toLowerCase().includes('sinner')) {
                        item.click();
                        return item.innerText?.trim().slice(0,80);
                    }
                }
                return null;
            }""")
            print(f"\nClic sur match: {clicked_match}")
            if clicked_match:
                await asyncio.sleep(4)
                await page.screenshot(path=f"{SCREENSHOT}/lolly_match.png")
                print(f"📸 Match page: {SCREENSHOT}/lolly_match.png")
                # Inspecter les marchés/cotes sur la page de match
                match_odds = await page.evaluate("""() => {
                    const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!el || !el.shadowRoot) return [];
                    const sr = el.shadowRoot;
                    const r = [];
                    sr.querySelectorAll('[class*="market"], [class*="outcome"]').forEach(n => {
                        const t = n.innerText?.trim();
                        if (t && t.length < 200) r.push({cls: n.className?.slice(0,60), text: t.slice(0,120)});
                    });
                    return r.slice(0, 20);
                }""")
                print("Marchés/cotes (premier scan):")
                for m in match_odds:
                    print(f"  .{m['cls'][:50]} → '{m['text'][:80]}'")

                # Inspecter tous les marchés + score exact
                await asyncio.sleep(3)
                full_markets = await page.evaluate("""() => {
                    const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!el || !el.shadowRoot) return [];
                    const sr = el.shadowRoot;
                    const r = [];
                    sr.querySelectorAll('[class*="market-name"], [class*="market-title"], [class*="market__name"], [class*="market-header"], [class*="market__title"]').forEach(n => {
                        r.push({type: 'market', cls: n.className?.slice(0,60), text: n.innerText?.trim().slice(0,80)});
                    });
                    sr.querySelectorAll('[class*="outcome-button"], button[class*="odd"], [class*="odds-btn"]').forEach(n => {
                        const t = n.innerText?.trim();
                        if (t && t.length < 30) r.push({type: 'btn', cls: n.className?.slice(0,60), text: t});
                    });
                    return r.slice(0, 60);
                }""")
                print("\nDétail marchés/boutons:")
                for m in full_markets:
                    print(f"  [{m['type']}] .{m['cls'][:50]} → '{m['text'][:60]}'")

                score_exact = await page.evaluate("""() => {
                    const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!el || !el.shadowRoot) return [];
                    const sr = el.shadowRoot;
                    const r = [];
                    sr.querySelectorAll('*').forEach(n => {
                        const t = n.innerText?.trim();
                        if (t && (t.toLowerCase().includes('score exact') || t.includes('3-0') || t.includes('3:0')
                                 || t.toLowerCase().includes('exact') || t.toLowerCase().includes('correct score')))
                            r.push({cls: n.className?.slice(0,60), text: t.slice(0,120)});
                    });
                    return r.slice(0, 15);
                }""")
                print("\nScore exact / 3-0:")
                for s in score_exact:
                    print(f"  .{s['cls'][:50]} → '{s['text'][:80]}'")

                print(f"\nURL match: {page.url}")

                # Cliquer sur une cote et inspecter le betslip
                print("\n=== BETSLIP LOLLYBET ===")
                betslip_clicked = await page.evaluate("""() => {
                    const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!el || !el.shadowRoot) return false;
                    const sr = el.shadowRoot;
                    const btns = sr.querySelectorAll('[class*="outcome-button"], [class*="odd-button"], button[class*="odd"]');
                    if (btns.length) { btns[0].click(); return btns[0].innerText?.trim(); }
                    return false;
                }""")
                print(f"Clic cote: {betslip_clicked}")
                await asyncio.sleep(2)
                await page.screenshot(path=f"{SCREENSHOT}/lolly_betslip.png")
                print(f"📸 {SCREENSHOT}/lolly_betslip.png")

                betslip_content = await page.evaluate("""() => {
                    const el = Array.from(document.querySelectorAll('*')).find(e => e.tagName.startsWith('SG-'));
                    if (!el || !el.shadowRoot) return [];
                    const sr = el.shadowRoot;
                    const r = [];
                    sr.querySelectorAll('[class*="betslip"], [class*="bet-slip"], [class*="coupon"], [class*="ticket"], input').forEach(n => {
                        const t = n.innerText?.trim() || n.placeholder || n.value || '';
                        if (t) r.push({cls: n.className?.slice(0,60), tag: n.tagName, text: t.slice(0,80)});
                    });
                    return r.slice(0, 20);
                }""")
                print("Betslip:")
                for b in betslip_content:
                    print(f"  [{b['tag']}] .{b['cls'][:50]} → '{b['text'][:60]}'")
        else:
            print("❌ Input recherche shadow non trouvé via handle — essai via page.locator")
            # Playwright peut piercer shadow DOM avec locator
            try:
                loc = page.locator(".sb-search-field__input")
                await loc.fill("Sinner", timeout=5000)
                await asyncio.sleep(3)
                print("✅ Fill via locator réussi")
            except Exception as e:
                print(f"❌ Locator: {e}")

        # Chercher les composants spécifiques au sportsbook (noms WLC / Angular)
        sportsbook_info = await page.evaluate("""() => {
            const r = [];
            const cands = [
                "[class*='sport']","[class*='Sport']","[class*='event']","[class*='Event']",
                "[class*='match']","[class*='Match']","[class*='league']","[class*='League']",
                "[class*='tournament']","[class*='Tournament']","[class*='competition']",
                "[class*='game']","[class*='Game']","[class*='fixture']","[class*='Fixture']",
                "wlc-sport","wlc-event","wlc-match","[class*='wlc-sb']","[class*='sb-']",
            ];
            cands.forEach(s => {
                const els = document.querySelectorAll(s);
                if (els.length) {
                    const sample = els[0].innerText?.trim().slice(0,80);
                    if (sample) r.push({sel: s, count: els.length, sample});
                }
            });
            return r;
        }""")
        if sportsbook_info:
            print("Composants sportsbook trouvés:")
            for c in sportsbook_info:
                print(f"  {c['sel']} ({c['count']}) → {c['sample']}")
        else:
            print("⚠️  Aucun composant sportsbook trouvé après 11s")

        # Chercher Wimbledon ou Sinner spécifiquement
        sinner_info = await page.evaluate("""() => {
            const r = [];
            document.querySelectorAll("*").forEach(el => {
                const t = el.innerText?.trim();
                if (t && (t.toLowerCase().includes('sinner') || t.toLowerCase().includes('wimbledon')
                         || t.toLowerCase().includes('kecmanovic'))
                    && el.children.length < 5) {
                    r.push({tag: el.tagName, cls: el.className?.slice(0,60), text: t.slice(0,80),
                            href: el.href || el.closest('a')?.href || ''});
                }
            });
            return r.slice(0, 15);
        }""")
        if sinner_info:
            print("\n✅ Sinner/Wimbledon trouvé:")
            for s in sinner_info:
                print(f"  <{s['tag']}> .{s['cls'][:40]} → '{s['text'][:60]}'")
                if s['href']: print(f"    href: {s['href']}")
        else:
            print("⚠️  Sinner/Wimbledon non trouvé dans la page principale")

        # ── Chercher les iframes ──────────────────────────────────────
        print("\n=== IFRAMES ===")
        frames = page.frames
        print(f"{len(frames)} frame(s) trouvée(s):")
        for i, frame in enumerate(frames):
            print(f"  [{i}] url={frame.url}")

        # Inspecter chaque iframe non-principale
        for i, frame in enumerate(frames[1:], 1):
            if not frame.url or frame.url == "about:blank":
                continue
            print(f"\n--- Contenu frame [{i}] ({frame.url[:80]}) ---")
            try:
                frame_text = await frame.evaluate("""() => document.body?.innerText?.slice(0,500)""")
                print(f"Texte: {frame_text}")

                sinner_in_frame = await frame.evaluate("""() => {
                    const r = [];
                    document.querySelectorAll("*").forEach(el => {
                        const t = el.innerText?.trim();
                        if (t && (t.toLowerCase().includes('sinner') || t.toLowerCase().includes('wimbledon'))
                            && el.children.length < 5) {
                            r.push({tag: el.tagName, cls: el.className?.slice(0,60), text: t.slice(0,80),
                                    href: el.href || el.closest('a')?.href || ''});
                        }
                    });
                    return r.slice(0, 10);
                }""")
                if sinner_in_frame:
                    print("✅ Sinner/Wimbledon dans cette iframe:")
                    for s in sinner_in_frame:
                        print(f"  <{s['tag']}> .{s['cls'][:40]} → '{s['text']}'")
                        if s['href']: print(f"    href: {s['href']}")
            except Exception as e:
                print(f"  Erreur: {e}")

        # ── 4. Essayer la barre de recherche ─────────────────────────
        print("\n=== RECHERCHE 'Sinner' ===")
        search_sels = [
            "input[placeholder*='Recherch']", "input[placeholder*='Search']",
            "input[type='search']", "input[placeholder*='Joueur']",
            "input[placeholder*='équipe']", "input[class*='search']",
            "[class*='search-input'] input", "[class*='SearchInput'] input",
        ]
        for sel in search_sels:
            el = await page.query_selector(sel)
            if el:
                print(f"✅ Barre de recherche: {sel}")
                await el.click()
                await asyncio.sleep(0.3)
                await el.type("Sinner", delay=80)
                await asyncio.sleep(2)
                await page.screenshot(path=f"{SCREENSHOT}/lolly_search.png")
                print(f"📸 {SCREENSHOT}/lolly_search.png")

                suggestions = await page.evaluate("""() => {
                    const r = [];
                    document.querySelectorAll("*").forEach(el => {
                        const t = el.innerText?.trim();
                        if (t && t.toLowerCase().includes('sinner') && el.children.length < 5) {
                            r.push({tag: el.tagName, cls: el.className?.slice(0,60),
                                    text: t.slice(0,80), href: el.closest('a')?.href || ''});
                        }
                    });
                    return r.slice(0, 10);
                }""")
                print("Suggestions:")
                for s in suggestions:
                    print(f"  <{s['tag']}> .{s['cls'][:40]} → '{s['text'][:60]}'")
                break
        else:
            print("❌ Barre de recherche non trouvée")

        # ── 5. Naviguer vers un match et inspecter les cotes ─────────
        print("\n=== PAGE DE MATCH ===")
        # Chercher un lien contenant Sinner
        match_url = None
        all_links = await page.query_selector_all("a[href]")
        for link in all_links:
            t = (await link.inner_text()).lower()
            h = await link.get_attribute("href")
            if "sinner" in t and h:
                match_url = h if h.startswith("http") else HOME_URL + h
                print(f"✅ Match Sinner: {match_url}")
                break

        if match_url:
            await page.goto(match_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            await page.screenshot(path=f"{SCREENSHOT}/lolly_match.png")
            print(f"📸 {SCREENSHOT}/lolly_match.png  — URL: {page.url}")

            # Inspecter les marchés / cotes
            odds_info = await page.evaluate("""() => {
                const r = [];
                const seen = new Set();
                document.querySelectorAll("*").forEach(el => {
                    const t = el.innerText?.trim();
                    if (!t || seen.has(el.className)) return;
                    const n = parseFloat(t.replace(",","."));
                    if (!isNaN(n) && n > 1.01 && n < 200 && t.length < 10 && el.children.length === 0) {
                        seen.add(el.className);
                        const par = el.closest("button, [class*='odd'], [class*='market'], [class*='bet']");
                        r.push({tag: el.tagName, cls: el.className?.slice(0,60), text: t,
                                parCls: par?.className?.slice(0,60)||'', parTag: par?.tagName||''});
                    }
                });
                return r.slice(0, 20);
            }""")
            print("Éléments de cotes:")
            for o in odds_info:
                print(f"  <{o['tag']}> .{o['cls'][:40]} = {o['text']}  (parent <{o['parTag']}> .{o['parCls'][:40]})")

            markets_info = await page.evaluate("""() => {
                const cands = ["[class*='market']","[class*='Market']","[class*='outcome']",
                               "[class*='bet-group']","[class*='event']","[class*='section']"];
                const r = [];
                cands.forEach(s => {
                    const els = document.querySelectorAll(s);
                    if (els.length) r.push({sel: s, count: els.length,
                        sample: els[0].innerText?.trim().slice(0,80)});
                });
                return r;
            }""")
            print("\nGroupes de marché:")
            for m in markets_info:
                print(f"  {m['sel']} ({m['count']}) → {m['sample']}")

        # ── 6. Betslip après clic sur une cote ───────────────────────
        print("\n=== BETSLIP ===")
        if match_url:
            # Cliquer sur la première cote disponible
            btn = await page.query_selector("button[class*='odd'], [class*='odd'] button, [class*='bet'] button")
            if btn:
                await btn.click()
                await asyncio.sleep(2)
                await page.screenshot(path=f"{SCREENSHOT}/lolly_betslip.png")
                print(f"📸 {SCREENSHOT}/lolly_betslip.png")

            betslip_info = await page.evaluate("""() => {
                const cands = [
                    "[class*='betslip']","[class*='bet-slip']","[class*='ticket']",
                    "[class*='coupon']","[class*='panier']","[class*='basket']",
                    "input[class*='stake']","input[class*='mise']","input[class*='amount']",
                    "input[placeholder*='mise']","input[placeholder*='Mise']","input[placeholder*='€']",
                ];
                const r = [];
                cands.forEach(s => {
                    document.querySelectorAll(s).forEach(el => {
                        const t = el.innerText?.trim() || el.placeholder || el.value || '';
                        if (t) r.push({sel: s, tag: el.tagName, cls: el.className?.slice(0,60), text: t.slice(0,80)});
                    });
                });
                return r;
            }""")
            if betslip_info:
                print("Betslip:")
                for b in betslip_info:
                    print(f"  {b['sel']} [{b['tag']}] .{b['cls'][:40]} → '{b['text']}'")

            buttons_info = await page.evaluate("""() =>
                Array.from(document.querySelectorAll('button')).map(b => ({
                    text: b.innerText.trim().slice(0,40),
                    cls: b.className.slice(0,60), disabled: b.disabled
                })).filter(b => b.text)
            """)
            print("\nBoutons:")
            for b in buttons_info:
                print(f"  {'[disabled]' if b['disabled'] else '[actif]  '} '{b['text']}'  .{b['cls'][:50]}")

        print("\n=== FIN INSPECTION LOLLYBET ===")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
