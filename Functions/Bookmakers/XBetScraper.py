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
        prepared = find_and_prepare_bet(matches)
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
        prepared = find_and_prepare_bet(matches)
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
