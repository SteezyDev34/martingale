# -*- coding: utf-8 -*-
"""
Scraper Playwright pour france-pronos.com
- Se connecte automatiquement si nécessaire (profil persistant)
- Extrait les pronostics du jour directement depuis le DOM (pas d'OCR)
- Retourne une liste de dicts prêts à envoyer à l'API
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions.Logs.Logger import log

FRANCEPRONOS_URL = "https://www.france-pronos.com"
PRONOS_URL = f"{FRANCEPRONOS_URL}/pronostics"
LOGIN_URL = f"{FRANCEPRONOS_URL}/login"
TIPSTER_NAME = "FrancePronos"


class FrancePronosScraper:

    def __init__(self):
        self.email = os.getenv("FRANCEPRONOS_EMAIL", "")
        self.password = os.getenv("FRANCEPRONOS_PASSWORD", "")
        self.profile_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ChromeDriver",
            "francepronos_profile",
        )
        Path(self.profile_dir).mkdir(parents=True, exist_ok=True)

    async def _is_logged_in(self, page) -> bool:
        try:
            await page.goto(PRONOS_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            # Si redirigé vers /login = pas connecté
            if "/login" in page.url:
                log("[FrancePronos] Session inactive — redirigé vers login", "info")
                return False
            # Vérifier la présence des cards
            card = await page.query_selector("div.app-prono-preview")
            if card:
                log("[FrancePronos] ✅ Session active — pronostics détectés", "info")
                return True
            log("[FrancePronos] Session active (page chargée sans cards)", "info")
            return True
        except Exception as e:
            log(f"[FrancePronos] Erreur vérification session: {e}", "error")
            return False

    async def _login(self, page) -> bool:
        if not self.email or not self.password:
            log("[FrancePronos] ❌ FRANCEPRONOS_EMAIL ou FRANCEPRONOS_PASSWORD non définis", "error")
            return False
        try:
            log(f"[FrancePronos] Connexion sur {LOGIN_URL} avec {self.email}...", "info")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            # App Angular — utiliser evaluate pour déclencher les events natifs
            await page.evaluate('''(args) => {
                const inputs = document.querySelectorAll("input");
                const emailInput = Array.from(inputs).find(i => i.type === "email");
                const passInput = Array.from(inputs).find(i => i.type === "password");
                function setVal(el, val) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event("input", { bubbles: true }));
                    el.dispatchEvent(new Event("change", { bubbles: true }));
                }
                if (emailInput) setVal(emailInput, args.email);
                if (passInput) setVal(passInput, args.password);
            }''', {"email": self.email, "password": self.password})

            await page.wait_for_timeout(500)

            # Cliquer sur le bouton submit
            await page.click("button[type='submit']")
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            if "/login" in page.url:
                log("[FrancePronos] ❌ Échec login — toujours sur la page de connexion", "error")
                return False

            log("[FrancePronos] ✅ Connexion réussie", "info")
            return True
        except Exception as e:
            log(f"[FrancePronos] ❌ Erreur lors de la connexion: {e}", "error")
            return False

    async def _extract_pronos(self, page) -> List[Dict]:
        """
        Extrait les pronostics du jour depuis div.app-prono-preview.
        Retourne une liste de dicts avec equipe_1, equipe_2, selection, odds, date, sport.
        """
        try:
            # Fermer une éventuelle popup
            try:
                close_btn = await page.query_selector("button.close, .mat-dialog-container button, [aria-label='Close']")
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            pronos = await page.evaluate('''() => {
                const cards = document.querySelectorAll("div.app-prono-preview");
                const result = [];
                cards.forEach(card => {
                    const get = sel => {
                        const el = card.querySelector(sel);
                        return el ? el.innerText.trim() : "";
                    };
                    const matchRaw = get(".title-3");
                    // Séparer equipe_1 et equipe_2 sur le premier " - "
                    const dashIdx = matchRaw.indexOf(" - ");
                    const equipe_1 = dashIdx >= 0 ? matchRaw.slice(0, dashIdx).trim() : matchRaw;
                    const equipe_2_raw = dashIdx >= 0 ? matchRaw.slice(dashIdx + 3) : "";
                    // Retirer la mention entre parenthèses à la fin (ex: "(Coupe du monde)")
                    const equipe_2 = equipe_2_raw.replace(/\s*\(.*?\)\s*$/, "").trim();

                    const odds_raw = get(".cote-value.bold");

                    result.push({
                        equipe_1: equipe_1,
                        equipe_2: equipe_2,
                        intitule: matchRaw,
                        selection: get(".description"),
                        odds: odds_raw,
                        date: get(".date.bold") || get(".hidden-mobile.date.bold"),
                        sport: get(".sport-label"),
                        tipster: "FrancePronos",
                    });
                });
                return result;
            }''')

            # Filtrer les entrées sans match valide
            valid = [p for p in pronos if p.get("equipe_1") and p.get("selection")]
            log(f"[FrancePronos] {len(valid)} pronostic(s) extrait(s) sur {len(pronos)} card(s)", "info")
            return valid

        except Exception as e:
            log(f"[FrancePronos] Erreur extraction pronos: {e}", "error")
            return []

    async def scrape_pronos(self) -> List[Dict]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("[FrancePronos] ❌ Playwright non installé", "error")
            return []

        results = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                locale="fr-FR",
                viewport={"width": 1280, "height": 900},
            )
            page = browser.pages[0] if browser.pages else await browser.new_page()
            try:
                if not await self._is_logged_in(page):
                    if not await self._login(page):
                        log("[FrancePronos] ❌ Impossible de se connecter, abandon", "error")
                        return []
                    await page.goto(PRONOS_URL, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)

                results = await self._extract_pronos(page)
            finally:
                await browser.close()

        log(f"[FrancePronos] Total: {len(results)} pronostic(s) récupéré(s)", "info")
        return results


def scrape_francepronos() -> List[Dict]:
    """
    Wrapper synchrone pour appel depuis le handler Telegram.
    Retourne une liste de dicts prêts à envoyer à l'API.
    """
    import subprocess
    import json as _json
    import sys as _sys

    runner_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_francepronos_runner.py"
    )
    result = subprocess.run(
        [_sys.executable, runner_script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        log(f"[FrancePronos] ❌ Processus scraper échoué:\n{result.stderr}", "error")
        return []
    try:
        output = result.stdout.strip()
        last_line = [l for l in output.splitlines() if l.strip().startswith("[")]
        if last_line:
            return _json.loads(last_line[-1])
    except Exception as e:
        log(f"[FrancePronos] Erreur parsing résultat: {e}\nStdout: {result.stdout[:500]}", "error")
    return []
