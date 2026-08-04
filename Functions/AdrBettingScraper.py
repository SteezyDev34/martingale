# -*- coding: utf-8 -*-
"""
Scraper Playwright pour adr-betting.fr
- Se connecte automatiquement si nécessaire
- Récupère les coupons de paris depuis l'espace VIP
- Prend des screenshots des zones coupons et les passe à l'OCR
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions.Logs.Logger import log

ADRBETTING_URL = "https://adr-betting.fr"
VIP_URL = f"{ADRBETTING_URL}/espace-vip/"
LOGIN_URL = f"{ADRBETTING_URL}/login/"

# Sélecteurs CSS extraits du HTML réel de adr-betting.fr
# Login : plugin "Theme My Login" — champs name="log" et name="pwd"
SELECTORS = {
    "login_user": "input[name='log']",       # identifiant/email
    "login_pass": "input[name='pwd']",       # mot de passe
    "login_submit": "button[name='submit']", # bouton Se connecter
    "login_error": ".tml-alerts",            # zone d'erreur
    # Grille de tickets VIP (CSS custom du site)
    "tickets_grid": ".vip-tickets-grid",
    "ticket_card": ".vip-ticket-card",
    "ticket_thumb": ".vip-thumb img",        # image miniature dans la card
    "ticket_content": ".vip-full-content",  # contenu texte du coupon
    "ticket_link": ".vip-btn",              # bouton "Voir le coupon"
}


class AdrBettingScraper:
    """
    Scraper asynchrone pour adr-betting.fr.
    Utilise Playwright en mode non-headless (navigateur visible) avec un profil
    persistant pour réutiliser la session de connexion.
    """

    def __init__(self, output_dir: str = None):
        self.email = os.getenv("ADRBETTING_EMAIL", "")
        self.password = os.getenv("ADRBETTING_PASSWORD", "")
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "telegram_media",
            "adrbetting_coupons",
        )
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Répertoire du profil persistant (conserve la session de connexion)
        self.profile_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ChromeDriver",
            "adrbetting_profile",
        )
        Path(self.profile_dir).mkdir(parents=True, exist_ok=True)

    async def _is_logged_in(self, page) -> bool:
        """
        Vérifie si la session est active.
        Navigue sur la page VIP et teste la présence de la grille de tickets.
        Si on voit la grille `.vip-tickets-grid` = connecté.
        Si on voit le formulaire de login = pas connecté.
        """
        try:
            await page.goto(VIP_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            # Présence de la grille de tickets = accès VIP confirmé
            grid = await page.query_selector(SELECTORS["tickets_grid"])
            if grid:
                log("[AdrBetting] ✅ Session active — grille VIP détectée", "info")
                return True

            # Présence du formulaire de login = session expirée
            login_form = await page.query_selector(SELECTORS["login_user"])
            if login_form:
                log("[AdrBetting] Session inactive — formulaire de login détecté", "info")
                return False

            # Contenu restreint sans formulaire (message "abonnement requis")
            content = await page.content()
            if any(p in content.lower() for p in ["abonnement", "devenir vip", "pmpro-no-access"]):
                log("[AdrBetting] Session inactive — contenu restreint détecté", "info")
                return False

            log("[AdrBetting] ✅ Session active (aucune restriction détectée)", "info")
            return True

        except Exception as e:
            log(f"[AdrBetting] Erreur vérification session: {e}", "error")
            return False

    async def _login(self, page) -> bool:
        """
        Connexion via https://adr-betting.fr/login/
        Plugin Theme My Login : champs name='log' et name='pwd'
        """
        if not self.email or not self.password:
            log("[AdrBetting] ❌ ADRBETTING_EMAIL ou ADRBETTING_PASSWORD non définis dans .env", "error")
            return False

        try:
            log(f"[AdrBetting] Connexion sur {LOGIN_URL} avec {self.email}...", "info")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1000)

            # Attendre que le formulaire soit présent
            await page.wait_for_selector(SELECTORS["login_user"], timeout=10000)

            # Remplir identifiant et mot de passe
            await page.fill(SELECTORS["login_user"], self.email)
            await page.fill(SELECTORS["login_pass"], self.password)

            # Cocher "Se souvenir de moi"
            try:
                await page.check("input[name='rememberme']")
            except Exception:
                pass

            # Soumettre
            await page.click(SELECTORS["login_submit"])
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            # Vérifier le résultat
            current_url = page.url
            log(f"[AdrBetting] URL après soumission: {current_url}", "info")

            # Si toujours sur /login/ = erreur de credentials
            if "/login" in current_url:
                error_el = await page.query_selector(SELECTORS["login_error"])
                error_msg = (await error_el.inner_text()).strip() if error_el else "Erreur inconnue"
                log(f"[AdrBetting] ❌ Échec login: {error_msg}", "error")
                return False

            log("[AdrBetting] ✅ Connexion réussie", "info")
            return True

        except Exception as e:
            log(f"[AdrBetting] ❌ Erreur lors de la connexion: {e}", "error")
            return False

    def _tipster_from_title(self, title: str) -> str:
        """
        Déduit le nom du tipster depuis le titre de la card VIP.
        H3.vip-ticket-title contient "TICKET SAFE VIP" ou "TICKET FUN VIP".
        """
        t = title.upper()
        if "SAFE" in t:
            return "ADR SAFE"
        if "FUN" in t:
            return "ADR FUN"
        return "AdrBetting"

    async def _scrape_vip_page(self, page) -> List[tuple]:
        """
        Récupère les images de coupons depuis la page VIP avec leur tipster.
        Retourne une liste de tuples (filepath, tipster_name).
        Le tipster est déduit du H3.vip-ticket-title de chaque card :
          "TICKET SAFE VIP" -> "ADR SAFE"
          "TICKET FUN VIP"  -> "ADR FUN"
        """
        downloaded = []
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        try:
            await page.goto(VIP_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # Extraire URL image + titre de chaque card
            coupon_data = await page.evaluate('''() => {
                const cards = document.querySelectorAll(".vip-ticket-card");
                const result = [];
                cards.forEach(card => {
                    const titleEl = card.querySelector("h3.vip-ticket-title, .vip-ticket-title");
                    const title = titleEl ? titleEl.innerText.trim() : "";
                    const imgs = card.querySelectorAll("img");
                    let imgUrl = null;
                    for (const img of imgs) {
                        if (
                            img.naturalWidth >= 400 &&
                            img.src &&
                            !img.src.includes("s.w.org")
                        ) {
                            imgUrl = img.src;
                            break;
                        }
                    }
                    if (imgUrl) {
                        result.push({ url: imgUrl, title: title });
                    }
                });
                return result;
            }''')

            log(f"[AdrBetting] {len(coupon_data)} image(s) de coupon trouvée(s)", "info")

            import requests as _req
            cookies = await page.context.cookies()
            session_cookies = {c["name"]: c["value"] for c in cookies}

            for i, item in enumerate(coupon_data):
                url = item["url"]
                tipster = self._tipster_from_title(item.get("title", ""))
                try:
                    filepath = os.path.join(self.output_dir, f"adrbetting_coupon_{timestamp}_{i}.jpg")
                    resp = _req.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0", "Referer": VIP_URL},
                        cookies=session_cookies,
                        verify=False,
                        timeout=15,
                    )
                    resp.raise_for_status()
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    downloaded.append((filepath, tipster))
                    log(f"[AdrBetting] ✅ [{tipster}] Coupon téléchargé ({len(resp.content)//1024}KB): {os.path.basename(filepath)}", "info")
                except Exception as e:
                    log(f"[AdrBetting] Erreur téléchargement {url}: {e}", "warning")

            # Fallback : screenshot de l'img wp-content dans chaque card
            if not downloaded:
                log("[AdrBetting] Fallback screenshot des cards", "warning")
                cards = await page.query_selector_all(SELECTORS["ticket_card"])
                for i, card in enumerate(cards):
                    try:
                        title_el = await card.query_selector("h3.vip-ticket-title, .vip-ticket-title")
                        title = (await title_el.inner_text()).strip() if title_el else ""
                        tipster = self._tipster_from_title(title)
                        img_el = await card.query_selector("img[src*='wp-content']")
                        if img_el:
                            filepath = os.path.join(self.output_dir, f"adrbetting_coupon_{timestamp}_{i}.jpg")
                            await img_el.screenshot(path=filepath)
                            downloaded.append((filepath, tipster))
                            log(f"[AdrBetting] ✅ [{tipster}] Screenshot coupon: {os.path.basename(filepath)}", "info")
                    except Exception as e:
                        log(f"[AdrBetting] Erreur screenshot fallback card #{i}: {e}", "warning")

        except Exception as e:
            log(f"[AdrBetting] Erreur scraping page VIP: {e}", "error")

        return downloaded

    async def _follow_ticket_links(self, page) -> List[str]:
        """
        Optionnel : suit les liens .vip-btn de chaque card pour capturer
        la page détail du coupon (utile si l'image haute-résolution y est).
        """
        screenshots = []
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        try:
            await page.goto(VIP_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            btn_links = await page.query_selector_all(SELECTORS["ticket_link"])
            hrefs = []
            for btn in btn_links:
                href = await btn.get_attribute("href")
                if href and href.startswith("http"):
                    hrefs.append(href)

            log(f"[AdrBetting] {len(hrefs)} lien(s) de détail trouvé(s)", "info")

            for i, href in enumerate(hrefs):
                try:
                    await page.goto(href, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(1500)

                    # Chercher les images dans la page détail
                    imgs = await page.query_selector_all(".entry-content img, .vip-full-content img, article img")
                    captured = False
                    for j, img in enumerate(imgs):
                        box = await img.bounding_box()
                        if not box or box["width"] < 150:
                            continue
                        filepath = os.path.join(self.output_dir, f"adrbetting_detail_{timestamp}_{i}_{j}.jpg")
                        await img.screenshot(path=filepath)
                        screenshots.append(filepath)
                        captured = True
                        log(f"[AdrBetting] ✅ Détail capturé: {os.path.basename(filepath)}", "info")

                    if not captured:
                        # Screenshot de la zone contenu principal
                        content_el = await page.query_selector(".entry-content, .vip-full-content")
                        if content_el:
                            filepath = os.path.join(self.output_dir, f"adrbetting_detail_{timestamp}_{i}.jpg")
                            await content_el.screenshot(path=filepath)
                            screenshots.append(filepath)
                            log(f"[AdrBetting] ✅ Contenu détail capturé: {os.path.basename(filepath)}", "info")

                except Exception as e:
                    log(f"[AdrBetting] Erreur page détail {href}: {e}", "warning")

        except Exception as e:
            log(f"[AdrBetting] Erreur follow_ticket_links: {e}", "error")

        return screenshots

    async def scrape_coupons(self) -> List[tuple]:
        """
        Point d'entrée principal.
        Se connecte si nécessaire, récupère tous les coupons du jour et retourne
        la liste des chemins d'images à passer à l'OCR.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log("[AdrBetting] ❌ Playwright non installé. Exécuter: pip install playwright && playwright install chromium", "error")
            return []

        all_screenshots = []

        async with async_playwright() as pw:
            # Utiliser un profil persistant pour conserver la session
            browser = await pw.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
                locale="fr-FR",
                viewport={"width": 1280, "height": 900},
            )

            page = browser.pages[0] if browser.pages else await browser.new_page()

            try:
                # Vérifier la session et se connecter si nécessaire
                if not await self._is_logged_in(page):
                    success = await self._login(page)
                    if not success:
                        log("[AdrBetting] ❌ Impossible de se connecter, abandon", "error")
                        return []
                    # Aller sur la page VIP après connexion
                    await page.goto(VIP_URL, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)

                # 1. Screenshot direct des cards/images sur la page VIP
                shots = await self._scrape_vip_page(page)
                all_screenshots.extend(shots)

                # 2. Si les cards n'ont pas d'images suffisantes, suivre les liens détail
                if not shots:
                    detail_shots = await self._follow_ticket_links(page)
                    all_screenshots.extend(detail_shots)

            finally:
                await browser.close()

        log(f"[AdrBetting] Total: {len(all_screenshots)} screenshot(s) récupéré(s)", "info")
        return all_screenshots


def scrape_adrbetting_coupons() -> List[tuple]:
    """
    Wrapper synchrone — appelable depuis le handler Telegram (non-async).
    Lance le scraper dans un processus séparé pour éviter les conflits
    avec l'event loop Telethon et garantir l'affichage du navigateur sur macOS.
    Retourne une liste de tuples (filepath, tipster_name).
    """
    import subprocess
    import json as _json
    import sys as _sys

    runner_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_adrbetting_runner.py"
    )

    result = subprocess.run(
        [_sys.executable, runner_script],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        log(f"[AdrBetting] ❌ Processus scraper échoué:\n{result.stderr}", "error")
        return []

    try:
        # Le runner imprime un JSON sur stdout : [["path1", "ADR SAFE"], ["path2", "ADR FUN"]]
        output = result.stdout.strip()
        last_line = [l for l in output.splitlines() if l.strip().startswith("[")]
        if last_line:
            data = _json.loads(last_line[-1])
            return [tuple(item) for item in data]
    except Exception as e:
        log(f"[AdrBetting] Erreur parsing résultat runner: {e}\nStdout: {result.stdout[:500]}", "error")

    return []
