"""
Consolidation des paris martingale envoyés à AuxoTracker (2026-11-04, étendu
au niveau match le 2026-11-06).

Avant (2026-11-04) : chaque jeu/tentative d'une séquence (jeu 1, jeu 2 à mise
doublée...) était envoyé comme un pari séparé à AuxoTracker, polluant le
tracker. Un premier passage consolidait par SÉQUENCE (une série de mises
jusqu'à un gain ou un abandon) -- mais un scriptType comme 15V1/15V2/431a/456P
peut enchaîner PLUSIEURS séquences dans le même match (il continue de parier
tant que son objectif de gain match n'est pas atteint), donc plusieurs envois
par match. Demande explicite du 2026-11-06 : un seul envoi consolidé par
MATCH, à la toute fin (objectif de gain atteint, ou abandon du match).

record_leg() accumule chaque jeu (table settings, clé martingale_legs:<ST>) --
PLUS vidée entre deux séquences gagnantes : finalize_sequence_win/lost ne font
plus que garantir que le jeu courant est bien dans l'historique, sans envoyer
ni vider. Seul finalize_match() envoie et vide, au moment où le scriptType
termine son implication sur CE match (objectif atteint ou match abandonné).

Formule validée explicitement par l'utilisateur (ne pas dévier) :
    total_mise_reelle = somme des mises de TOUS les jeux du match (toutes séquences)
    benefice_reel     = net profit réel du match pour ce scriptType
                         (config.global_match_win[script_type], déjà calculé
                         jeu par jeu par le moteur -- gain du dernier jeu gagnant
                         de CHAQUE séquence gagnante moins la mise de CETTE
                         séquence, sommé sur tout le match -- recalculer ce total
                         depuis les legs seuls ne marche pas dès qu'il y a eu
                         plus d'une séquence gagnante dans le match)
    cote_moyenne      = moyenne arithmétique de TOUTES les cotes jouées sur le match
    mise_envoyee      = benefice_reel / (cote_moyenne - 1)
    gain_affiche      = mise_envoyee * cote_moyenne
Si le match se termine sans profit net (abandon) : mise_envoyee =
total_mise_reelle (somme réelle), cote_moyenne identique, result='lost'.
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
    Garantit que le jeu gagnant de cette séquence est bien dans l'historique
    persisté du match (pas d'envoi ni de vidage ici -- cf. finalize_match,
    une séquence gagnante n'est pas forcément la fin du match : le scriptType
    peut enchaîner une nouvelle séquence si son objectif de gain match n'est
    pas encore atteint). `final_mise`/`final_cote` sont ceux du jeu gagnant
    (passés explicitement, pas relus depuis l'historique -- voir garde-fou
    ci-dessous).
    """
    legs = RedisIPC.get_martingale_legs(script_type)
    if not legs:
        config.log(f"[MartingaleSequence] win: aucun jeu enregistré pour {script_type}", 'warning', False)
        return

    final_mise = float(final_mise)
    final_cote = float(final_cote)
    last = legs[-1]
    # Garde-fou : si record_leg avait silencieusement échoué pour le jeu
    # gagnant (son propre except avale l'erreur), l'historique persisté
    # pourrait ne pas le contenir -- l'ajouter pour ne pas sous-compter
    # total_mise_reelle/cote_moyenne au moment de finalize_match.
    if abs(last['mise'] - final_mise) > 0.001 or abs(last['cote'] - final_cote) > 0.001:
        RedisIPC.append_martingale_leg(script_type, {
            'jeu': getattr(config, 'looking_game', None), 'mise': final_mise, 'cote': final_cote,
            'equipe_1': last.get('equipe_1', ''), 'equipe_2': last.get('equipe_2', ''),
            'win_type': last.get('win_type', ''), 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })


def finalize_sequence_lost(script_type) -> None:
    """
    Aucune action : le(s) jeu(x) de la séquence perdue sont déjà dans
    l'historique persisté via record_leg (appelé à chaque jeu validé), et
    restent accumulés pour le prochain envoi (finalize_match, fin du match).
    Conservée pour la lisibilité des appelants (symétrique à
    finalize_sequence_win) et en cas de besoin de logique dédiée plus tard.
    """
    return


def finalize_match(script_type, net_profit) -> None:
    """
    Calcule et envoie LE pari consolidé du match pour ce scriptType (toutes
    séquences confondues), puis vide l'historique persisté. À appeler une
    fois que le scriptType a fini d'intervenir sur ce match -- objectif de
    gain atteint, ou match abandonné/terminé avant (filet de sécurité dans
    les scripts SCRIPTS_*/*.py, sinon des legs orphelins resteraient collés
    au prochain match pour ce même scriptType).

    `net_profit` : config.global_match_win[script_type] au moment de l'appel
    -- déjà le vrai bénéfice net du match (somme jeu par jeu par le moteur),
    pas recalculable depuis les seuls legs dès qu'il y a eu plus d'une
    séquence gagnante dans le match (le gain d'une séquence antérieure
    n'apparaît pas dans les legs, seulement sa mise) -- cf. note de formule
    en tête de fichier.
    """
    legs = RedisIPC.get_martingale_legs(script_type)
    if not legs:
        return

    net_profit = float(net_profit)
    total_mise_reelle = sum(l['mise'] for l in legs)
    cote_moyenne = sum(l['cote'] for l in legs) / len(legs)

    if cote_moyenne <= 1:
        config.log(f"[MartingaleSequence] cote_moyenne<=1 pour {script_type}, envoi annulé", 'warning', False)
        RedisIPC.clear_martingale_legs(script_type)
        return

    if net_profit > 0:
        mise_envoyee = net_profit / (cote_moyenne - 1)
        result = 'win'
    else:
        mise_envoyee = total_mise_reelle
        result = 'lost'

    _send_consolidated(script_type, legs, stake=mise_envoyee, odds=cote_moyenne, result=result)
    RedisIPC.clear_martingale_legs(script_type)
