# -*- coding: utf-8 -*-
"""
Scraper Playwright pour france-pronos.com
- Se connecte automatiquement si nécessaire (profil persistant)
- Extrait les pronostics du jour via l'API https://api.france-pronos.fr/api/bets
  (capture réseau, pas de lecture du DOM ni d'OCR -- le rendu DOM peut être
  bloqué par une modale non fermable, cf. _start_bets_capture)
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
API_BASE = "https://api.france-pronos.fr"
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
            await page.wait_for_timeout(3000)
            # Si redirigé vers /login = pas connecté
            if "/login" in page.url:
                log("[FrancePronos] Session inactive — redirigé vers login", "info")
                return False
            # Vérifier la présence des cards
            card = await page.query_selector("div.app-prono-preview")
            if card:
                log("[FrancePronos] ✅ Session active — pronostics détectés", "info")
                return True
            # Pas de cards ne suffit PAS à conclure à une session active : la page
            # "Pronostics du jour" s'affiche aussi (vide) quand on est déconnecté
            # (bug constaté le 2026-10-18 — _login() n'était jamais appelé, la
            # session persistante n'a donc jamais été établie). Le menu affiche
            # "SE CONNECTER" uniquement quand on n'est pas authentifié -- signal
            # fiable pour distinguer "vraiment connecté, pas de pronos aujourd'hui"
            # de "pas connecté du tout".
            body_text = await page.evaluate("() => document.body.innerText")
            if "SE CONNECTER" in body_text.upper():
                log("[FrancePronos] Session inactive — bouton 'Se connecter' détecté", "info")
                return False
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
            log(f"[FrancePronos] Connexion avec {self.email}...", "info")
            # Naviguer directement vers LOGIN_URL affiche une page blanche (route
            # Angular cote-client qui ne s'initialise pas correctement en deep-link
            # direct, constate le 2026-10-18) -- on passe par PRONOS_URL (pas la page
            # d'accueil : le clic depuis l'accueil ne déclenche pas la navigation,
            # probablement une popup différente qui intercepte le clic) et on clique
            # sur "SE CONNECTER" comme un vrai utilisateur.
            await page.goto(PRONOS_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            clicked = await page.evaluate('''() => {
                // Deux éléments "SE CONNECTER" coexistent dans le DOM (nav desktop
                // visible + duplicata mobile caché via CSS) -- ne cliquer que le
                // visible, sinon le clic sur l'élément caché ne déclenche pas la
                // navigation (constaté le 2026-10-18, échec intermittent).
                const els = Array.from(document.querySelectorAll("button, a, span, div"));
                const target = els.find(e =>
                    e.innerText && e.innerText.trim().toUpperCase() === "SE CONNECTER" &&
                    (e.offsetWidth || e.offsetHeight)
                );
                if (target) { target.click(); return true; }
                return false;
            }''')
            if not clicked:
                log("[FrancePronos] ❌ Bouton 'Se connecter' introuvable sur la page d'accueil", "error")
                return False
            await page.wait_for_timeout(1500)
            await page.wait_for_selector("input[type='email']", timeout=10000)

            # App Angular — utiliser evaluate pour déclencher les events natifs.
            # Comme pour "SE CONNECTER", le site duplique ses éléments (versions
            # desktop/mobile) : ne cibler que les champs/bouton VISIBLES, sinon on
            # remplit/clique une copie cachée qui n'affecte pas le vrai formulaire.
            filled = await page.evaluate('''(args) => {
                const visible = el => !!(el.offsetWidth || el.offsetHeight);
                const inputs = Array.from(document.querySelectorAll("input"));
                const emailInput = inputs.find(i => i.type === "email" && visible(i));
                const passInput = inputs.find(i => i.type === "password" && visible(i));
                function setVal(el, val) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event("input", { bubbles: true }));
                    el.dispatchEvent(new Event("change", { bubbles: true }));
                }
                if (emailInput) setVal(emailInput, args.email);
                if (passInput) setVal(passInput, args.password);
                return !!(emailInput && passInput);
            }''', {"email": self.email, "password": self.password})
            if not filled:
                log("[FrancePronos] ❌ Champs email/mot de passe visibles introuvables", "error")
                return False

            # Cliquer sur le bouton submit visible (JS, pas page.click() -- le
            # sélecteur CSS seul peut matcher la copie cachée en premier). En
            # Filtrer sur la PROPRIÉTÉ JS .type (pas le sélecteur CSS [type='submit'],
            # qui ne matche que l'attribut HTML littéral -- un <button> sans attribut
            # type explicite vaut "submit" par défaut pour le navigateur mais pas pour
            # ce sélecteur, constaté le 2026-10-18 : le bouton était bien visible et
            # cliquable à l'écran mais jamais trouvé par l'attribut).
            submitted = False
            for _ in range(10):
                submitted = await page.evaluate('''() => {
                    const visible = el => !!(el.offsetWidth || el.offsetHeight);
                    const btn = Array.from(document.querySelectorAll("button")).find(b => b.type === "submit" && visible(b));
                    if (btn) { btn.click(); return true; }
                    return false;
                }''')
                if submitted:
                    break
                await page.wait_for_timeout(300)
            if not submitted:
                log("[FrancePronos] ❌ Bouton de connexion visible introuvable", "error")
                return False
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

    def _start_bets_capture(self, page):
        """
        Les pronos du jour sont servis par l'API https://api.france-pronos.fr/api/bets
        (pagination chronologique, la plus ancienne en premier), chargée en arrière-plan
        par l'app -- MÊME quand le rendu DOM est bloqué par une modale non fermable
        (constaté le 2026-10-18 : composant "app-member-is-out", abonnement en échec
        d'après le site alors que la page Profil dit "Premium jusqu'au 01/11/2026" --
        incohérence côté site, mais les données sont bien là). On capture ces réponses
        réseau au lieu de lire le DOM. L'archive remonte à plusieurs mois ; il faut
        attendre que la pagination arrive jusqu'à aujourd'hui (~1600+ paris, jusqu'à 60s).
        """
        self._bets_by_id = {}

        async def _on_response(response):
            if "/api/bets?page=" in response.url:
                try:
                    data = await response.json()
                    for b in data:
                        self._bets_by_id[b.get("id")] = b
                except Exception:
                    pass

        page.on("response", _on_response)

    async def _wait_for_today_bets(self, page, max_wait_s: int = 60, poll_every_s: int = 3, stable_needed_s: int = 6) -> None:
        """
        Poll self._bets_by_id (alimenté par _start_bets_capture) jusqu'à ce que des
        paris datés d'aujourd'hui soient présents ET que plus aucun nouveau pari
        n'arrive depuis `stable_needed_s` (la pagination en arrière-plan a fini de
        remonter jusqu'à aujourd'hui), ou jusqu'à `max_wait_s` en dernier recours.
        """
        import datetime
        today_str = datetime.date.today().isoformat()
        elapsed = 0
        last_count = -1
        stable_for = 0
        while elapsed < max_wait_s:
            await page.wait_for_timeout(poll_every_s * 1000)
            elapsed += poll_every_s
            has_today = any((b.get("startAt") or "").startswith(today_str) for b in self._bets_by_id.values())
            count = len(self._bets_by_id)
            stable_for = stable_for + poll_every_s if count == last_count else 0
            last_count = count
            log(f"[FrancePronos] Chargement en arrière-plan... {count} paris reçus ({elapsed}s)", "info")
            if has_today and stable_for >= stable_needed_s:
                break

    def _resolve_image_url(self, media_path: str) -> str:
        """
        Le champ "image" d'un pari (ex: "/api/media_objects/<uuid>") pointe vers une
        ressource JSON-LD (métadonnées), pas vers l'image elle-même -- le vrai
        fichier est dans son champ "contentUrl" (ex: "/media/xxx_capture.png").
        Les deux endpoints sont publics, pas besoin de cookie de session (vérifié
        le 2026-10-18). Retourne l'URL finale directement utilisable (ex: pour
        Telegram sendPhoto), ou "" si indisponible.
        """
        if not media_path:
            return ""
        try:
            import requests
            from urllib.parse import quote
            r = requests.get(f"{API_BASE}{media_path}", timeout=10, verify=False)
            r.raise_for_status()
            content_url = r.json().get("contentUrl") or ""
            if not content_url:
                return ""
            return f"{API_BASE}{quote(content_url, safe='/')}"
        except Exception as e:
            log(f"[FrancePronos] Erreur résolution image {media_path}: {e}", "warning")
            return ""

    def _extract_todays_pending_pronos(self) -> List[Dict]:
        """
        Filtre self._bets_by_id sur la date du jour ET status=None (pari pas encore
        résolu = à venir/en cours, par opposition à "won"/"lost"/"refunded" qui sont
        des résultats déjà connus plus tôt dans la journée). Retourne le même format
        de dict que l'ancienne extraction DOM (equipe_1, equipe_2, intitule, selection,
        odds, date, sport, tipster) pour rester compatible avec le reste du pipeline
        (extraire_pari_depuis_texte côté appelant).
        """
        import datetime
        today_str = datetime.date.today().isoformat()
        pending_today = [
            b for b in self._bets_by_id.values()
            if (b.get("startAt") or "").startswith(today_str) and b.get("status") is None
        ]
        pending_today.sort(key=lambda b: b.get("startAt") or "")

        results = []
        for b in pending_today:
            items = b.get("betItems") or []
            if items:
                equipe_1 = items[0].get("teamA") or ""
                equipe_2 = items[0].get("teamB") or ""
                sport = items[0].get("displaySport") or ""
            else:
                equipe_1 = b.get("teamA") or ""
                equipe_2 = b.get("teamB") or ""
                sport = b.get("displaySport") or ""
            results.append({
                "equipe_1": equipe_1,
                "equipe_2": equipe_2,
                "intitule": b.get("displayName") or "",
                "selection": b.get("displayChoice") or "",
                "image": self._resolve_image_url(b.get("image")),
                "odds": b.get("odds"),
                "date": (b.get("startAt") or "")[:10],
                "sport": sport,
                "tipster": "FrancePronos",
            })

        log(f"[FrancePronos] {len(results)} pronostic(s) du jour en attente (sur {len(self._bets_by_id)} paris reçus au total)", "info")
        return results

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
            # Attaché AVANT toute navigation (y compris celle de _is_logged_in) pour
            # ne rater aucune des premières pages /api/bets?page=N chargées au login.
            self._start_bets_capture(page)
            try:
                if not await self._is_logged_in(page):
                    if not await self._login(page):
                        log("[FrancePronos] ❌ Impossible de se connecter, abandon", "error")
                        return []
                    await page.goto(PRONOS_URL, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)

                await self._wait_for_today_bets(page)
                results = self._extract_todays_pending_pronos()
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
