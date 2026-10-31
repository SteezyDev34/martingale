# -*- coding: utf-8 -*-
"""
StakeBridge — pont WebSocket dédié à Stake.bet (port distinct du bridge 1xBet :
Functions/Bookmakers/StakeBridge.STAKE_WS_PORT = 9101, cf. service_worker.js
WS_PORTS), utilisé par StakeScraper quand l'extension Chrome est connectée.

Même mécanisme que websocket_server.ExtensionBridge pour 1xBet (port dédié,
onglet dédié ouvert au premier navigate() puis réutilisé) — instance séparée
car Stake a son propre onglet/port, pour pouvoir tourner en parallèle du
bridge 1xBet dans le même process (router.py compare les cotes des deux
bookmakers).
"""
from websocket_server import ExtensionBridge

STAKE_WS_PORT = 9101


class StakeExtensionBridge(ExtensionBridge):
    def get_state(self):
        """Retourne {loggedIn, url}."""
        resp = self._send_and_wait({'action': 'stake_get_state'}, timeout=10)
        return resp.get('data') or {}

    def search_match(self, equipe1: str, timeout: int = 20) -> dict:
        """Tape equipe1 dans la recherche Stake. Retourne {found, candidates: [{text, url}]}."""
        return self._send_and_wait({'action': 'stake_search_match', 'equipe1': equipe1}, timeout=timeout)

    def get_odds(self, search_labels: list, timeout: int = 10) -> dict:
        """Retourne {found, odds} pour la première variante de label trouvée."""
        return self._send_and_wait({'action': 'stake_get_odds', 'search_labels': search_labels}, timeout=timeout)

    def get_dnb_odds(self, team_idx: int, timeout: int = 10) -> dict:
        """Cote Draw No Bet (Handicap X (0)) pour l'équipe 1 ou 2."""
        return self._send_and_wait({'action': 'stake_get_odds', 'dnb_team_idx': team_idx}, timeout=timeout)

    def get_table_market_odds(self, handicap_market: dict, timeout: int = 10) -> dict:
        """Cote d'un marché "table à 2 colonnes" (tennis) -- Handicap de sets/jeux,
        Total de jeux (global ou par joueur) -- le nom de colonne n'est pas dans le
        bouton (cf. stake.js _findTableMarketButton). handicap_market: dict avec
        marketLabel (nom exact) OU marketSubstrings (liste), + targetName + handicapValue."""
        return self._send_and_wait({
            'action': 'stake_get_odds',
            'handicap_market': handicap_market,
        }, timeout=timeout)

    def place_bet(self, search_labels: list = None, mise: float = None, dnb_team_idx: int = None,
                  handicap_market: dict = None, dry_run: bool = False, timeout: int = 15) -> dict:
        """Clique la sélection (par label, DNB, ou handicap de sets/jeux), saisit la
        mise, confirme. Retourne {success, error?}.
        dry_run=True : s'arrête juste avant le clic de confirmation finale (aucun pari réel) —
        retourne {success: True, simulated: True} si tout le reste s'est bien déroulé."""
        return self._send_and_wait({
            'action': 'stake_place_bet',
            'search_labels': search_labels,
            'mise': mise,
            'dnb_team_idx': dnb_team_idx,
            'handicap_market': handicap_market,
            'dry_run': dry_run,
        }, timeout=timeout)

    def place_same_game_multi(self, combined_legs: list, mise: float, dry_run: bool = False, timeout: int = 40) -> dict:
        """
        combined_legs: [{'search_labels': [...]} | {'handicap_market': {...}}, ...] --
        handicap_market pour les marchés "table à 2 colonnes" (Total, Handicap de
        sets/jeux -- cf. StakeScraper._match_table_market), search_labels sinon.
        Place un pari combiné sur le même match (onglet "Pari Multiple sur un Même Match").
        dry_run=True : s'arrête juste avant le clic "Parier" final (aucun pari réel).
        """
        return self._send_and_wait({
            'action': 'stake_place_sgm',
            'combined_legs': combined_legs,
            'mise': mise,
            'dry_run': dry_run,
        }, timeout=timeout)

    def reset_betslip(self, timeout: int = 10) -> dict:
        """Vide le betslip. À appeler UNE fois avant la 1ère jambe d'un combiné
        multi-matchs (les jambes suivantes ne doivent PAS reset, cf. add_combo_leg)."""
        return self._send_and_wait({'action': 'stake_reset_betslip'}, timeout=timeout)

    def add_combo_leg(self, search_labels: list = None, dnb_team_idx: int = None,
                      handicap_market: dict = None, timeout: int = 15) -> dict:
        """Ajoute UNE jambe d'un combiné multi-matchs (accumulateur, matchs
        différents) sans vider le betslip -- appeler stake_bridge.navigate() vers le
        match de cette jambe juste avant. Stake accumule automatiquement une section
        "Pari multiple" dans le betslip dès 2 jambes de matchs différents ajoutées.
        Retourne {clicked: bool}."""
        return self._send_and_wait({
            'action': 'stake_add_combo_leg',
            'search_labels': search_labels,
            'dnb_team_idx': dnb_team_idx,
            'handicap_market': handicap_market,
        }, timeout=timeout)

    def confirm_combo(self, mise: float, dry_run: bool = False, timeout: int = 15) -> dict:
        """Saisit la mise du combiné (section "Pari multiple" du betslip, pas les
        paris simples individuels) et confirme. dry_run=True : s'arrête avant le clic
        de confirmation finale (aucun pari réel)."""
        return self._send_and_wait({
            'action': 'stake_confirm_combo',
            'mise': mise,
            'dry_run': dry_run,
        }, timeout=timeout)


stake_bridge = StakeExtensionBridge(port=STAKE_WS_PORT)
_stake_bridge_started = False


def start_stake_bridge(wait_timeout: int = 0):
    """Démarre le serveur WebSocket dédié Stake. Idempotent (sans effet si déjà démarré)."""
    global _stake_bridge_started
    if _stake_bridge_started:
        return
    stake_bridge.start()
    _stake_bridge_started = True
    if wait_timeout > 0:
        print(f'[WS:{STAKE_WS_PORT}] Attente connexion extension Chrome (Stake, {wait_timeout}s max)...')
        stake_bridge.wait_connected(timeout=wait_timeout)
        print(f'[WS:{STAKE_WS_PORT}] Extension connectée (Stake) ✓')
    else:
        print(f'[WS:{STAKE_WS_PORT}] Serveur WebSocket démarré (Stake) — en attente de l\'extension Chrome...')


def is_connected() -> bool:
    return stake_bridge.connected
