# -*- coding: utf-8 -*-
"""
Classe abstraite pour tous les scrapers de bookmakers.
Chaque bookmaker hérite de cette classe et implémente les méthodes abstraites.
"""
import asyncio
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict

from Functions.Logs.Logger import log


class BookmakerScraper(ABC):

    name: str = "Bookmaker"

    def __init__(self):
        self.profile_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "ChromeDriver",
            f"{self.__class__.__name__.lower().replace('scraper', '')}_profile",
        )
        Path(self.profile_dir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Méthodes abstraites — à implémenter par chaque bookmaker            #
    # ------------------------------------------------------------------ #

    @abstractmethod
    async def login(self, page) -> bool:
        """Se connecte au bookmaker. Retourne True si succès."""

    @abstractmethod
    async def is_logged_in(self, page) -> bool:
        """Vérifie si la session est active sans naviguer."""

    @abstractmethod
    async def search_match(self, page, equipe_1: str, equipe_2: str, sport: str, date: str) -> Optional[str]:
        """
        Cherche le match sur le bookmaker.
        Retourne l'URL de la page du match ou None si non trouvé.
        """

    @abstractmethod
    async def get_odds(self, page, match_url: str, selection: str, categorie: str) -> Optional[float]:
        """
        Récupère la cote pour une sélection donnée sur la page du match.
        Retourne la cote (float) ou None si non trouvée.
        """

    @abstractmethod
    async def place_bet(self, page, match_url: str, selection: str, categorie: str, mise: float) -> bool:
        """
        Place le pari. Retourne True si succès.
        """

    @abstractmethod
    async def get_challenges(self, page) -> List[Dict]:
        """
        Récupère la liste des défis/boosts actifs.
        Retourne une liste de dicts : {title, description, condition, bookmaker, url}
        """

    @abstractmethod
    async def activate_challenge(self, page, challenge: Dict) -> bool:
        """Active un défi avant de placer le pari."""

    # ------------------------------------------------------------------ #
    # Méthodes communes                                                    #
    # ------------------------------------------------------------------ #

    async def fetch_odds(self, bet: Dict) -> Dict:
        """
        Récupère uniquement la cote sans placer le pari.
        Retourne un dict avec : bookmaker, odds, match_url, challenge_activated
        """
        result = {"bookmaker": self.name, "odds": None, "match_url": None, "challenge_activated": False, "error": None}
        try:
            import os
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                launch_kwargs = dict(
                    user_data_dir=self.profile_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                    locale="fr-FR",
                    viewport={"width": 1280, "height": 900},
                )
                real_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if getattr(self, "use_real_chrome", False) and os.path.exists(real_chrome):
                    launch_kwargs["executable_path"] = real_chrome
                browser = await pw.chromium.launch_persistent_context(**launch_kwargs)
                page = browser.pages[0] if browser.pages else await browser.new_page()
                if getattr(self, "use_real_chrome", False):
                    try:
                        from playwright_stealth import Stealth as _Stealth
                        await _Stealth().apply_stealth_async(page)
                    except Exception:
                        pass
                try:
                    if not await self.is_logged_in(page):
                        result["error"] = "session_expired"
                        try:
                            from Functions.Functions_telegram import send_telegram, alertGroup
                            send_telegram(alertGroup, f"⚠️ #SESSION_EXPIRÉE\nLa session {self.name} est inactive.")
                        except Exception:
                            pass
                        return result
                    match_url = await self.search_match(
                        page, bet.get("equipe_1", ""), bet.get("equipe_2", ""),
                        str(bet.get("sport", "")), bet.get("date", "")
                    )
                    if not match_url:
                        result["error"] = "match_not_found"
                        return result
                    result["match_url"] = match_url
                    result["odds"] = await self.get_odds(page, match_url, bet.get("selection", ""), bet.get("categorie", ""))
                    challenges = await self.get_challenges(page)
                    matched = self._match_challenge(bet, challenges)
                    if matched:
                        result["challenge_activated"] = True
                finally:
                    await browser.close()
        except Exception as e:
            result["error"] = str(e)
            log(f"[{self.name}] Erreur fetch_odds: {e}", "error")
        return result

    async def run(self, bet: Dict) -> Dict:
        """
        Point d'entrée principal pour un pari.
        Retourne un dict avec : bookmaker, odds, success, challenge_activated
        """
        result = {
            "bookmaker": self.name,
            "odds": None,
            "success": False,
            "challenge_activated": False,
            "error": None,
        }
        try:
            import os
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                launch_kwargs = dict(
                    user_data_dir=self.profile_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                    locale="fr-FR",
                    viewport={"width": 1280, "height": 900},
                )
                real_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if getattr(self, "use_real_chrome", False) and os.path.exists(real_chrome):
                    launch_kwargs["executable_path"] = real_chrome
                browser = await pw.chromium.launch_persistent_context(**launch_kwargs)
                page = browser.pages[0] if browser.pages else await browser.new_page()
                if getattr(self, "use_real_chrome", False):
                    try:
                        from playwright_stealth import Stealth as _Stealth
                        await _Stealth().apply_stealth_async(page)
                    except Exception:
                        pass
                try:
                    if not await self.is_logged_in(page):
                        log(f"[{self.name}] ❌ Session inactive — relancer le script pour se reconnecter", "error")
                        result["error"] = "session_expired"
                        try:
                            from Functions.Functions_telegram import send_telegram, alertGroup
                            send_telegram(alertGroup, f"⚠️ #SESSION_EXPIRÉE\nLa session {self.name} est inactive.\nRelance le script pour te reconnecter.")
                        except Exception:
                            pass
                        return result

                    equipe_1 = bet.get("equipe_1", "")
                    equipe_2 = bet.get("equipe_2", "")
                    sport = str(bet.get("sport", ""))
                    date = bet.get("date", "")
                    selection = bet.get("selection", "")
                    categorie = bet.get("categorie", "")
                    mise = float(bet.get("mise", 10))

                    match_url = await self.search_match(page, equipe_1, equipe_2, sport, date)
                    if not match_url:
                        result["error"] = "match_not_found"
                        return result

                    odds = await self.get_odds(page, match_url, selection, categorie)
                    result["odds"] = odds

                    # Vérifier les défis actifs
                    challenges = await self.get_challenges(page)
                    matched_challenge = self._match_challenge(bet, challenges)
                    if matched_challenge:
                        activated = await self.activate_challenge(page, matched_challenge)
                        result["challenge_activated"] = activated
                        log(f"[{self.name}] 🎯 Défi activé: {matched_challenge.get('title')}", "info")

                    success = await self.place_bet(page, match_url, selection, categorie, mise)
                    result["success"] = success

                finally:
                    await browser.close()
        except Exception as e:
            result["error"] = str(e)
            log(f"[{self.name}] ❌ Erreur run(): {e}", "error")

        return result

    def _match_challenge(self, bet: Dict, challenges: List[Dict]) -> Optional[Dict]:
        """
        Vérifie si un pari correspond à un défi actif.
        Comparaison naïve sur les noms d'équipes et la sélection.
        Le matching sémantique fin est fait par l'IA dans le router.
        """
        if not challenges:
            return None
        equipe_1 = bet.get("equipe_1", "").lower()
        equipe_2 = bet.get("equipe_2", "").lower()
        for challenge in challenges:
            cond = challenge.get("condition", "").lower()
            if equipe_1 in cond or equipe_2 in cond:
                return challenge
        return None

    async def get_browser(self, pw):
        """Ouvre le navigateur avec profil persistant."""
        return await pw.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            locale="fr-FR",
            viewport={"width": 1280, "height": 900},
        )
