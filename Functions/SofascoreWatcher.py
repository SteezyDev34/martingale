"""
Watcher Sofascore en tâche de fond, découplé du driver Selenium utilisé pour parier.

Contexte (voir AUDIT_MARTINGALE_TENNIS.md §7) : le site de paris peut mettre jusqu'à
10s à afficher un point gagné, alors que Sofascore l'a déjà. Un onglet Sofascore était
déjà ouvert par match mais jamais lu (GetSofaScoreActuel n'était jamais appelée) car
le lire depuis le MÊME driver que celui qui place les paris aurait pu entrer en
collision avec un clic de pari en cours (changement de fenêtre pendant une action).

Solution retenue : un second objet driver Selenium, entièrement indépendant, attaché
au même port de debug Chrome (donc au même navigateur/process) mais ciblant
uniquement l'onglet Sofascore. Les deux drivers sont des sessions CDP distinctes :
faire évoluer l'un (changement de fenêtre, lecture du DOM) n'affecte jamais l'état
de "fenêtre courante" de l'autre. Ce watcher tourne dans un thread dédié et alimente
`config.sofascore_score_hint` (avec horodatage) — une simple indication utilisée
pour le diagnostic de latence, JAMAIS pour valider un pari : la source de vérité pour
placer une mise reste exclusivement le DOM du bookmaker (cf. règle utilisateur
« ne jamais se fier à une info non confirmée pour une action irréversible »).
"""

import re
import threading
import time

from selenium.webdriver.common.by import By

import config
from ChromeDriver.SetDriver import init_driver

_watcher_thread = None
_stop_event = None
sofascore_hint_lock = threading.Lock()

# Nœud du score Sofascore, identique à celui utilisé (mais jamais exploité) par
# l'ancienne fonction GetSofaScoreActuel dans GetScoreActuel.py.
_SOFASCORE_SCORE_XPATH = '//*[@id="__next"]/main/div/div[2]/div/div[1]/div[3]/div[1]/div/div[2]/div/div/div[2]/div'

_VALID_TENNIS_TOKENS = {'0', '15', '30', '40', 'A', 'AD', 'ADV'}
_VALID_TENNIS_SCORES = {
    f"{a}:{b}"
    for a in _VALID_TENNIS_TOKENS
    for b in _VALID_TENNIS_TOKENS
}


def _poll_loop(stop_event, interval):
    watcher_driver = None
    try:
        watcher_driver = init_driver(config.localhost, config.sofascore_tab_handle)
    except Exception as e:
        config.log(f"[SofascoreWatcher] Impossible d'attacher un driver dédié: {e}", 'error', False)
        return

    if not watcher_driver:
        config.log("[SofascoreWatcher] driver dédié introuvable, watcher non démarré", 'error', False)
        return

    config.log("[SofascoreWatcher] démarré (driver dédié, indépendant du driver de pari)", 'info', False)

    while not stop_event.is_set():
        try:
            root = watcher_driver.find_element(By.XPATH, _SOFASCORE_SCORE_XPATH)
            # Chercher un score tennis valide directement dans le texte (ex: "40:A", "15:30").
            # re.findall(r'\d+') attraperait aussi les scores de set (ex: "3"), produisant
            # des scores parasites comme "3:40". On cherche d'abord un pattern score tennis.
            text = root.text.upper().replace(' ', '')
            score = None
            # Pattern : token tennis : token tennis (ex: 40:A, 15:30, 0:0)
            m = re.search(r'((?:AD?V?|A|\d+)):((?:AD?V?|A|\d+))', text)
            if m:
                candidate = m.group(1).rstrip('V').rstrip('D') + ':' + m.group(2).rstrip('V').rstrip('D')
                # Normaliser ADV/AD → A
                candidate = candidate.replace('ADV', 'A').replace('AD', 'A')
                if candidate in _VALID_TENNIS_SCORES:
                    score = candidate
            if score:
                with sofascore_hint_lock:
                    config.sofascore_score_hint = score
                    config.sofascore_score_hint_ts = time.time()
        except Exception:
            # Onglet fermé, page non chargée, nœud absent... on retentera au tour suivant.
            pass
        stop_event.wait(interval)

    # Pas de driver.quit() : en mode attach (debuggerAddress), certaines versions de
    # Selenium/chromedriver ferment le navigateur entier plutôt que la seule session
    # attachée. Le reste du projet évite systématiquement .quit() pour cette raison
    # (cf. Functions_15V1.py qui utilise driver.close() sur l'onglet, jamais .quit()).
    config.log("[SofascoreWatcher] arrêté", 'info', False)


def start_sofascore_watcher(interval: float = 1.0) -> bool:
    """
    Démarre le watcher Sofascore en tâche de fond pour le match courant.

    Nécessite que `config.sofascore_tab_handle` soit déjà défini (onglet Sofascore
    ouvert). Ne fait rien si un watcher tourne déjà (appel idempotent).
    """
    global _watcher_thread, _stop_event

    if not hasattr(config, 'sofascore_tab_handle') or not config.sofascore_tab_handle:
        return False

    if _watcher_thread is not None and _watcher_thread.is_alive():
        return True

    config.sofascore_score_hint = False
    config.sofascore_score_hint_ts = 0.0

    _stop_event = threading.Event()
    _watcher_thread = threading.Thread(
        target=_poll_loop, args=(_stop_event, interval), daemon=True, name="SofascoreWatcher"
    )
    _watcher_thread.start()
    return True


def stop_sofascore_watcher(timeout: float = 3.0) -> None:
    """Arrête le watcher Sofascore en tâche de fond, si actif."""
    global _watcher_thread, _stop_event

    if _stop_event is not None:
        _stop_event.set()
    if _watcher_thread is not None:
        _watcher_thread.join(timeout=timeout)
    _watcher_thread = None
    _stop_event = None


def get_score_hint(max_age_seconds: float = 5.0):
    """
    Retourne `(score, age_seconds)` le plus récent connu de Sofascore, ou `(None, None)`
    si aucune donnée n'est disponible ou si elle est trop ancienne (onglet bloqué,
    watcher arrêté, page non chargée...).

    Usage prévu : diagnostic de latence uniquement (comparer avec le score détecté
    côté bookmaker). Ne jamais utiliser cette valeur pour décider seule d'un pari.
    """
    with sofascore_hint_lock:
        score = getattr(config, 'sofascore_score_hint', False)
        ts = getattr(config, 'sofascore_score_hint_ts', 0.0)
    if not score or not ts:
        return None, None
    age = time.time() - ts
    if age > max_age_seconds:
        return None, None
    return score, age
