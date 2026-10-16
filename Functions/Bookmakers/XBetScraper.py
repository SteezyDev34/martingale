# -*- coding: utf-8 -*-
"""
XBetScraper — bookmaker 1xBet pour le router, basé sur l'extension Chrome
(websocket_server.ExtensionBridge) au lieu de Playwright/Selenium.
Interface compatible avec le router : run(bet) -> dict, fetch_odds(bet) -> dict.
"""
import asyncio

from Functions.OneXBetBridge import find_and_prepare_bet
from Functions.Logs import BetTrace
from Functions.Logs.Logger import log


def _matches_from_bet(bet):
    if bet.get('is_combined'):
        return bet['matches_list']
    return [bet]


class XBetScraper:
    name = "1xBet"
    requires_vpn = False

    def _fetch_odds_sync(self, bet):
        matches = _matches_from_bet(bet)
        # Reutilise l'URL deja connue si ce bet a deja ete recherche (voir
        # commentaire _run_sync ci-dessous pour le pourquoi).
        prepared = find_and_prepare_bet(matches, cached_url=bet.get('_xbet_match_url'))
        if prepared.get('match_url'):
            bet['_xbet_match_url'] = prepared['match_url']
        from websocket_server import bridge
        bridge.delete_bet()
        if not prepared.get('success'):
            m = matches[0] if matches else {}
            log(f"[1xBet] Échec recherche/sélection pour {m.get('equipe_1')} vs {m.get('equipe_2')}: {prepared.get('error')}", "warning")
            return {"bookmaker": self.name, "odds": None, "error": prepared.get('error')}
        return {"bookmaker": self.name, "odds": prepared.get('cote')}

    def _run_sync(self, bet):
        trace_dir = bet.get('trace_dir')
        from websocket_server import bridge

        matches = _matches_from_bet(bet)
        # Reutilise l'URL du match deja trouvee par un fetch_odds precedent sur
        # ce meme bet (router.py appelle fetch_odds puis run sur le MEME dict
        # bet, cf. priorite 1xBet dans place_best_bet) -- une 2e recherche
        # independante quelques secondes apres la 1ere echouait parfois en
        # match_not_found alors que la 1ere venait de reussir (constate en
        # conditions reelles le 2026-10-16, cause jamais identifiee avec
        # certitude -- probablement un effet de l'etat laisse par la 1ere
        # recherche sur la page). Naviguer directement vers l'URL deja connue
        # evite completement cette 2e recherche redondante et peu fiable.
        prepared = find_and_prepare_bet(matches, cached_url=bet.get('_xbet_match_url'))
        if prepared.get('match_url'):
            bet['_xbet_match_url'] = prepared['match_url']
        if not prepared.get('success'):
            BetTrace.capture_failure(trace_dir, prepared.get('error'), bridge=bridge, tag="find_prepare")
            return {"bookmaker": self.name, "success": False, "error": prepared.get('error')}

        mise = bet.get('mise', 1.0)
        stake_result = bridge.set_stake(mise)
        if not stake_result.get('success'):
            BetTrace.capture_failure(trace_dir, "stake_failed", bridge=bridge, tag="stake_failed")
            return {"bookmaker": self.name, "success": False, "error": "stake_failed"}

        validation = bridge.validate_bet(confirm=True)
        if not validation.get('validated'):
            BetTrace.capture_failure(trace_dir, "validation_failed", bridge=bridge, tag="validation_failed")
            return {"bookmaker": self.name, "success": False, "error": "validation_failed"}

        return {"bookmaker": self.name, "success": True, "odds": prepared.get('cote')}

    async def run(self, bet):
        return await asyncio.get_event_loop().run_in_executor(None, self._run_sync, bet)

    async def fetch_odds(self, bet):
        return await asyncio.get_event_loop().run_in_executor(None, self._fetch_odds_sync, bet)
