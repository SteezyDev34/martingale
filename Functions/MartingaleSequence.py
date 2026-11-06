"""
Consolidation des séquences martingale envoyées à AuxoTracker (2026-11-04).

Avant : chaque jeu/tentative d'une séquence (jeu 1, jeu 2 à mise doublée...)
était envoyé comme un pari séparé à AuxoTracker, polluant le tracker. Ce
module accumule les jeux d'une séquence (via record_leg, appelé depuis
Functions/ValidationDuParis.py à chaque jeu validé) et n'envoie qu'UN SEUL
pari consolidé à la fin de la séquence (gain -> finalize_sequence_win,
abandon -> finalize_sequence_lost).

Formule validée explicitement par l'utilisateur (ne pas dévier) :
    total_mise_reelle = somme des mises de TOUS les jeux de la séquence
    gain_reel         = mise_dernier_jeu_gagnant * cote_dernier_jeu_gagnant
    benefice_reel     = gain_reel - total_mise_reelle
    cote_moyenne      = moyenne arithmétique de TOUTES les cotes jouées
    mise_envoyee      = benefice_reel / (cote_moyenne - 1)
    gain_affiche      = mise_envoyee * cote_moyenne
Pour une séquence perdue : mise_envoyee = total_mise_reelle (somme réelle),
cote_moyenne identique, result='lost'.
"""
import json
import os
from datetime import datetime

import config
from Functions import RedisIPC
from Functions.TelegramBetsAPI import send_bet_to_auxotracker

_FAILED_SENDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'martingale_failed_sends.json')


def _save_failed_send(script_type, bet_dict: dict) -> None:
    """Append-only : garde une trace locale des paris consolidés jamais créés côté AuxoTracker."""
    try:
        try:
            with open(_FAILED_SENDS_PATH, 'r') as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = []
        existing.append({
            'script_type': script_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bet_dict': bet_dict,
        })
        with open(_FAILED_SENDS_PATH, 'w') as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass

# 255, pas 500 : la validation Laravel du endpoint auxobot/bets autorise 500
# caractères pour events.*.description, mais la colonne SQL réelle qui la
# stocke (events.type / events.market, cf. BetController::storeAuxobot) est
# en varchar(255) -- au-delà, MySQL renvoie "1406 Data too long for column"
# (constaté le 2026-11-06, erreur 500 sur un pari consolidé réel).
_DESCRIPTION_MAX_LEN = 255
_DESCRIPTION_RESERVE = 60  # marge pour la ligne récap si troncature


def record_leg(script_type, *, jeu, mise, cote, equipe_1, equipe_2, win_type, timestamp) -> None:
    """Enregistre un jeu dans l'historique persisté de la séquence en cours (aucun appel HTTP)."""
    leg = {
        'jeu': jeu,
        'mise': float(mise),
        'cote': float(cote),
        'equipe_1': equipe_1,
        'equipe_2': equipe_2,
        'win_type': win_type,
        'timestamp': timestamp,
    }
    RedisIPC.append_martingale_leg(script_type, leg)


def _fmt_eur(value: float) -> str:
    """31.64 -> '31€64' (format demandé explicitement par l'utilisateur)."""
    sign = '-' if value < 0 else ''
    value = round(abs(float(value)), 2)
    euros = int(value)
    centimes = round((value - euros) * 100)
    if centimes == 100:
        euros += 1
        centimes = 0
    return f"{sign}{euros}€{centimes:02d}"


def _build_description(script_type, legs: list, mode: str) -> str:
    header = f"Bot {script_type}"

    # Perte cumulée réelle à travers chaque jeu (index i = somme legs[0..i]).
    cum = []
    running = 0.0
    for leg in legs:
        running += leg['mise']
        cum.append(running)

    lines = []
    n = len(legs)
    for idx in range(n - 1, -1, -1):
        leg = legs[idx]
        is_last_and_win = (mode == 'win' and idx == n - 1)
        if is_last_and_win:
            gain = leg['mise'] * leg['cote']
            lines.append(
                f"jeu {leg['jeu']} | mise : {_fmt_eur(leg['mise'])} | "
                f"cote : {leg['cote']} | gain : {_fmt_eur(gain)}"
            )
        else:
            lines.append(
                f"jeu {leg['jeu']} | mise : {_fmt_eur(leg['mise'])} | "
                f"cote : {leg['cote']} | perte cumulée : {_fmt_eur(cum[idx])}"
            )

    kept = []
    total_len = len(header)
    cutoff_idx = None  # index (dans `lines`, ordre du plus récent au plus ancien) où la troncature a eu lieu
    for i, line in enumerate(lines):
        candidate_len = total_len + 1 + len(line)
        if candidate_len > _DESCRIPTION_MAX_LEN - _DESCRIPTION_RESERVE:
            cutoff_idx = i
            break
        kept.append(line)
        total_len = candidate_len

    text = header + "\n" + "\n".join(kept)
    if cutoff_idx is not None:
        n_dropped = n - len(kept)
        # Le jeu le plus récent parmi ceux coupés correspond à legs[idx] où
        # idx = n - 1 - cutoff_idx (lines est dans l'ordre inverse de legs).
        dropped_newest_idx = n - 1 - cutoff_idx
        text += f"\n... + {n_dropped} jeux précédents (perte cumulée {_fmt_eur(cum[dropped_newest_idx])})"

    return text[:_DESCRIPTION_MAX_LEN]


def _send_consolidated(script_type, legs: list, *, stake: float, odds: float, result: str) -> None:
    last = legs[-1]
    description = _build_description(script_type, legs, mode='win' if result == 'win' else 'lost')
    bet_dict = {
        "tipster": "AutoBot",
        "bet_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "global_odds": round(odds, 4),
        "bet_code": f"autobot-{str(script_type).lower()}",
        "stake": round(stake, 2),
        "stake_type": "currency",
        "result": result,
        "bankroll_id": 2,
        "event_list": [{
            "equipe_1": last.get('equipe_1', ''),
            "equipe_2": last.get('equipe_2', ''),
            "selection": description,
            "odds": round(odds, 4),
            "sport_id": 2,
        }],
    }
    try:
        api_bet_id = send_bet_to_auxotracker(bet_dict)
    except Exception as e:
        api_bet_id = None
        config.log(f"Erreur envoi pari consolidé AuxoTracker ({script_type}): {e}", 'warning', False)

    if not api_bet_id:
        # send_bet_to_auxotracker avale déjà les erreurs HTTP (ne lève pas
        # d'exception sur un 4xx/5xx, retourne juste None) -- sans ce log,
        # un échec d'envoi passait inaperçu ET l'historique de la séquence
        # était quand même vidé juste après par l'appelant (finalize_*),
        # perdant le pari définitivement (constaté le 2026-11-06, erreur 500
        # "Data too long for column" sur un pari consolidé réel). Conservé
        # ici pour reconstruction manuelle a posteriori.
        config.log(f"Échec envoi pari consolidé AuxoTracker ({script_type}), sauvegarde locale pour récupération manuelle", 'warning', False)
        _save_failed_send(script_type, bet_dict)


def finalize_sequence_win(script_type, final_mise, final_cote) -> None:
    """
    Calcule et envoie le pari consolidé d'une séquence gagnante, puis vide
    l'historique persisté. `final_mise`/`final_cote` sont ceux du jeu gagnant
    (passés explicitement, pas relus depuis l'historique -- voir garde-fou
    ci-dessous).
    """
    legs = RedisIPC.get_martingale_legs(script_type)
    if not legs:
        config.log(f"[MartingaleSequence] win: aucun jeu enregistré pour {script_type}, envoi annulé", 'warning', False)
        return

    final_mise = float(final_mise)
    final_cote = float(final_cote)
    last = legs[-1]
    # Garde-fou : si record_leg avait silencieusement échoué pour le jeu
    # gagnant (son propre except avale l'erreur), l'historique persisté
    # pourrait ne pas le contenir -- l'ajouter en mémoire pour ne pas
    # sous-compter total_mise_reelle/cote_moyenne.
    if abs(last['mise'] - final_mise) > 0.001 or abs(last['cote'] - final_cote) > 0.001:
        legs = legs + [{
            'jeu': getattr(config, 'looking_game', None), 'mise': final_mise, 'cote': final_cote,
            'equipe_1': last.get('equipe_1', ''), 'equipe_2': last.get('equipe_2', ''),
            'win_type': last.get('win_type', ''), 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }]

    total_mise_reelle = sum(l['mise'] for l in legs)
    gain_reel = final_mise * final_cote
    benefice_reel = gain_reel - total_mise_reelle
    cote_moyenne = sum(l['cote'] for l in legs) / len(legs)

    if cote_moyenne <= 1:
        config.log(f"[MartingaleSequence] cote_moyenne<=1 pour {script_type}, envoi annulé", 'warning', False)
        RedisIPC.clear_martingale_legs(script_type)
        return

    mise_envoyee = benefice_reel / (cote_moyenne - 1)
    _send_consolidated(script_type, legs, stake=mise_envoyee, odds=cote_moyenne, result='win')
    RedisIPC.clear_martingale_legs(script_type)


def finalize_sequence_lost(script_type) -> None:
    """Calcule et envoie le pari consolidé d'une séquence abandonnée (perte), puis vide l'historique."""
    legs = RedisIPC.get_martingale_legs(script_type)
    if not legs:
        return

    total_mise_reelle = sum(l['mise'] for l in legs)
    cote_moyenne = sum(l['cote'] for l in legs) / len(legs)
    _send_consolidated(script_type, legs, stake=total_mise_reelle, odds=cote_moyenne, result='lost')
    RedisIPC.clear_martingale_legs(script_type)
