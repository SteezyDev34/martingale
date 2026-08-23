"""
BridgeAdapter — couche d'abstraction entre le code martingale et le WebSocket bridge.

Usage dans chaque fonction :
    from Functions.BridgeAdapter import bridge_active, ext

    if bridge_active():
        return ext.get_score()      # chemin extension Chrome
    # ... chemin Selenium existant
"""

import threading
import time
import config


def bridge_active() -> bool:
    """True si le bridge WebSocket est disponible et connecté à l'extension."""
    try:
        from websocket_server import bridge
        return bridge.connected
    except Exception:
        return False


def _bridge():
    from websocket_server import bridge
    return bridge


# ─── Score ────────────────────────────────────────────────────────────────────

# File d'attente pour les scores poussés par MutationObserver
_score_event = threading.Event()
_latest_score = {'score': None, 'jeu': None, 'set': None}


def _on_score(score, raw):
    _latest_score['score'] = score
    _score_event.set()


def _on_game(jeu, set_actuel, raw):
    _latest_score['jeu'] = jeu
    _latest_score['set'] = set_actuel
    _score_event.set()


def setup_score_callbacks():
    """Branche les callbacks MutationObserver sur le bridge. À appeler au démarrage."""
    try:
        b = _bridge()
        b.on_score(_on_score)
        b.on_game(_on_game)
    except Exception:
        pass


def wait_for_new_score(current_score, timeout=30) -> str | None:
    """
    Bloque jusqu'à ce que le score change vs current_score.
    Retourne le nouveau score ou None si timeout.
    """
    deadline = time.time() + timeout
    _score_event.clear()
    while time.time() < deadline:
        remaining = deadline - time.time()
        _score_event.wait(timeout=min(1.0, remaining))
        _score_event.clear()
        new = _latest_score['score']
        if new and new != str(current_score):
            return new
    return None


def get_state_from_bridge() -> dict:
    """Retourne l'état complet depuis l'extension (score, jeu, set, players)."""
    try:
        return _bridge().get_state() or {}
    except Exception:
        return {}


# ─── Score actuel ─────────────────────────────────────────────────────────────

def bridge_get_score_actuel():
    """
    Équivalent de GetScoreActuel via bridge.
    Met à jour config.score_actuel et retourne True/False.
    """
    state = get_state_from_bridge()
    score = state.get('score') or _latest_score.get('score')
    if score:
        config.score_actuel = score
        return True
    return False


def bridge_wait_score_change():
    """
    Attend un changement de score (équivalent de la boucle GetScoreActuel).
    Retourne True quand un nouveau score est disponible.
    """
    current = getattr(config, 'saved_score', None)
    new_score = wait_for_new_score(current, timeout=60)
    if new_score:
        config.score_actuel = new_score
        return True
    return False


# ─── Jeu / Set ────────────────────────────────────────────────────────────────

def bridge_get_jeu_actuel():
    """Met à jour config.jeu_actuel depuis le bridge. Retourne True/False."""
    state = get_state_from_bridge()
    jeu_data = state.get('jeu_actuel') or _latest_score.get('jeu')
    if jeu_data:
        # jeu_data est {jeu1, jeu2, col} — on prend le max (jeu actuel = dernier col non vide)
        if isinstance(jeu_data, dict):
            try:
                j1 = int(jeu_data.get('jeu1', 0) or 0)
                j2 = int(jeu_data.get('jeu2', 0) or 0)
                config.jeu_actuel = j1 + j2 + 1  # approximation
            except Exception:
                config.jeu_actuel = jeu_data.get('col', 1)
        else:
            config.jeu_actuel = jeu_data
        return True
    return False


def bridge_get_set_actuel():
    """Met à jour config.set_actuel depuis le bridge. Retourne True/False."""
    state = get_state_from_bridge()
    set_val = state.get('set_actuel') or _latest_score.get('set')
    if set_val is not None:
        try:
            config.set_actuel = str(int(set_val))
        except Exception:
            config.set_actuel = str(set_val)
        return True
    return False


# ─── Joueurs ──────────────────────────────────────────────────────────────────

def bridge_get_players():
    """Retourne (p1, p2) depuis le bridge."""
    try:
        return _bridge().get_players()
    except Exception:
        return None, None


# ─── Paris ────────────────────────────────────────────────────────────────────

def bridge_place_and_validate_bet(market: str, mise: float) -> bool:
    """
    Place et valide un pari via l'extension.
    Met à jour config.validated_bet et retourne True si réussi.
    """
    b = _bridge()

    # 1) Placer le pari (cliquer + remplir mise)
    result = b.place_bet(market=market, mise=mise)
    if not result or not result.get('success'):
        config.log(f'[Bridge] place_bet échec: {result}', 'error')
        return False

    cote = result.get('cote')
    config.log(f'[Bridge] Pari placé marché={market} cote={cote} mise={mise}')

    # 2) Confirmer
    val_result = b.validate_bet(confirm=True)
    if not val_result or not val_result.get('validated'):
        config.log(f'[Bridge] validate_bet échec: {val_result}', 'error')
        return False

    # 3) Stocker dans validated_bet
    import datetime
    config.validated_bet = {
        'jeu':        config.jeu_actuel,
        'set':        config.set_actuel,
        'url':        getattr(config, 'ligue_name', ''),
        'montant':    str(mise),
        'cote':       str(cote) if cote else str(getattr(config, 'cote', 0)),
        'match':      getattr(config, 'newmatch', ''),
        'script':     getattr(config, 'scriptType', ''),
        'timestamp':  datetime.datetime.now().isoformat(),
        'numero_point': getattr(config, 'point_actuel', 0),
        'result':     None,
        'api_bet_id': None,
    }
    config.log(f'[Bridge] validated_bet: {config.validated_bet}')
    return True


def bridge_delete_bet() -> bool:
    """Supprime tous les paris du betslip via l'extension."""
    try:
        result = _bridge().delete_bet()
        deleted = result.get('deleted', 0) if result else 0
        config.log(f'[Bridge] DeleteBet: {deleted} paris supprimés')
        return True
    except Exception as e:
        config.log(f'[Bridge] DeleteBet erreur: {e}', 'error')
        return False


def bridge_get_result() -> str | None:
    """
    Lit WIN/LOSE depuis l'extension.
    Met à jour config.validated_bet['result'] et retourne 'WIN'/'LOSE'/None.
    """
    try:
        resp = _bridge().get_result()
        result = resp.get('result') if resp else None
        if result and hasattr(config, 'validated_bet') and config.validated_bet:
            config.validated_bet['result'] = result
        return result
    except Exception as e:
        config.log(f'[Bridge] GetResult erreur: {e}', 'error')
        return None
