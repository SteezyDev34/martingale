"""
Serveur WebSocket Python ↔ Extension Chrome 1xBet.

Lance un serveur asyncio sur ws://localhost:9999.
Les fonctions Selenium existantes (GetScoreActuel, GetAndPlaceBet, etc.)
appellent les méthodes de ExtensionBridge au lieu de driver.find_element.

Usage :
    bridge = ExtensionBridge()
    bridge.start()          # lance le thread WS en arrière-plan
    # ... puis dans le code martingale :
    state  = bridge.get_state()
    result = bridge.place_bet(market='15A', mise=2.5)
    bridge.delete_bet()
"""

import asyncio
import json
import queue
import threading
import time
import websockets
import websockets.server

WS_PORT = 9999
WS_HOST = 'localhost'

# ─── Bridge singleton ─────────────────────────────────────────────────────────

class ExtensionBridge:
    def __init__(self):
        self._loop = None
        self._thread = None
        self._ws_client = None          # connexion WebSocket active avec l'extension
        self._response_queues = {}      # action_id → queue.Queue(1)
        self._score_callback = None     # appelé à chaque push de score
        self._game_callback = None
        self._connected = False
        self._lock = threading.Lock()
        self._req_counter = 0

    # ─── Démarrage serveur ────────────────────────────────────────────────────

    def start(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f'[WS] Serveur WebSocket démarré sur ws://{WS_HOST}:{WS_PORT}')

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        async with websockets.serve(self._handler, WS_HOST, WS_PORT):
            await asyncio.Future()  # tourne indéfiniment

    async def _handler(self, websocket):
        self._ws_client = websocket
        self._connected = True
        print('[WS] Extension Chrome connectée')
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                await self._handle_message(msg)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._ws_client = None
            self._connected = False
            print('[WS] Extension Chrome déconnectée')

    async def _handle_message(self, msg):
        action = msg.get('action')

        # Push score depuis MutationObserver → callback Python
        if action == 'score_update':
            if self._score_callback:
                self._score_callback(msg.get('score'), msg)
            return

        if action == 'game_update':
            if self._game_callback:
                self._game_callback(msg.get('jeu'), msg.get('set_actuel'), msg)
            return

        # Réponse à une commande envoyée par Python (identifiée par req_id)
        req_id = msg.get('req_id')
        if req_id and req_id in self._response_queues:
            self._response_queues[req_id].put_nowait(msg)
            return

        # extension_ready : log seulement
        if action == 'extension_ready':
            print(f"[WS] Extension prête — version {msg.get('version')}")

    # ─── Envoi synchrone avec attente de réponse ─────────────────────────────

    def _send_and_wait(self, msg, timeout=10):
        """Envoie msg à l'extension et attend la réponse. Thread-safe."""
        if not self._connected or not self._ws_client:
            raise RuntimeError('Extension Chrome non connectée')

        with self._lock:
            self._req_counter += 1
            req_id = f'req_{self._req_counter}'

        msg['req_id'] = req_id
        resp_queue = queue.Queue(1)
        self._response_queues[req_id] = resp_queue

        # Envoyer depuis le loop asyncio
        asyncio.run_coroutine_threadsafe(
            self._ws_client.send(json.dumps(msg)),
            self._loop
        )

        try:
            resp = resp_queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f'Timeout attente réponse action={msg.get("action")}')
        finally:
            self._response_queues.pop(req_id, None)

        return resp

    # ─── API publique (appelée par le code martingale) ────────────────────────

    def wait_connected(self, timeout=30):
        """Bloque jusqu'à ce que l'extension se connecte."""
        start = time.time()
        while not self._connected:
            if time.time() - start > timeout:
                raise TimeoutError('Extension Chrome non connectée après %ds' % timeout)
            time.sleep(0.5)

    def get_state(self):
        """Retourne {score, set_actuel, jeu_actuel, players, url}."""
        return self._send_and_wait({'action': 'get_state'})

    def get_players(self):
        """Retourne {p1, p2}."""
        resp = self._send_and_wait({'action': 'get_players'})
        return resp.get('p1'), resp.get('p2')

    def navigate(self, url):
        """Navigue l'onglet 1xBet vers url."""
        return self._send_and_wait({'action': 'navigate', 'url': url}, timeout=15)

    def place_bet(self, market, mise, tab_index=None):
        """Clique sur le marché et remplit la mise. Retourne {success, cote, error}."""
        return self._send_and_wait({
            'action': 'place_bet',
            'market': market,
            'mise': mise,
            'tab_index': tab_index,
        })

    def validate_bet(self, confirm=True):
        """Confirme (ou annule) le pari. Retourne {validated, accepted}."""
        return self._send_and_wait({'action': 'validate_bet', 'confirm': confirm})

    def delete_bet(self):
        """Supprime tous les paris du betslip."""
        return self._send_and_wait({'action': 'delete_bet'})

    def get_result(self):
        """Lit WIN/LOSE dans le betslip. Retourne {result: 'WIN'|'LOSE'|None}."""
        return self._send_and_wait({'action': 'get_result'})

    def on_score(self, callback):
        """callback(score_str, raw_msg) appelé à chaque changement de score."""
        self._score_callback = callback

    def on_game(self, callback):
        """callback(jeu_dict, set_actuel, raw_msg) appelé à chaque changement de jeu."""
        self._game_callback = callback

    @property
    def connected(self):
        return self._connected


# ─── Instance globale ─────────────────────────────────────────────────────────

bridge = ExtensionBridge()

_bridge_started = False


def start_bridge(wait_timeout: int = 0):
    """
    Démarre le serveur WebSocket et branche les callbacks score.
    À appeler au début du script principal (avant all_script).

    Args:
        wait_timeout: si > 0, bloque jusqu'à ce que l'extension se connecte (secondes).
                      0 = démarrage sans attente (l'extension peut se connecter plus tard).
    """
    global _bridge_started
    if _bridge_started:
        return
    bridge.start()
    _bridge_started = True
    # Brancher les callbacks score du BridgeAdapter
    try:
        from Functions.BridgeAdapter import setup_score_callbacks
        setup_score_callbacks()
    except Exception:
        pass
    if wait_timeout > 0:
        print(f'[WS] Attente connexion extension Chrome ({wait_timeout}s max)...')
        bridge.wait_connected(timeout=wait_timeout)
        print('[WS] Extension connectée ✓')
    else:
        print('[WS] Serveur WebSocket démarré — en attente de l\'extension Chrome...')


if __name__ == '__main__':
    start_bridge(wait_timeout=30)
    print('Extension connectée, état:', bridge.get_state())
