import os
import sys
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.BridgeAdapter import bridge_active, bridge_get_score_actuel, bridge_wait_score_change


# Remplacée par Functions/SofascoreWatcher.py : lire l'onglet SofaScore depuis le
# MÊME driver que celui qui place les paris (comme le faisait cette fonction) risquait
# une collision de fenêtre pendant un clic de pari en cours. Le watcher utilise un
# driver Selenium dédié, complètement indépendant.


def GetScoreActuel(driver):
    # ── Bridge Chrome Extension (sans Selenium) ──
    if bridge_active():
        ok = bridge_get_score_actuel()
        if ok:
            dom_debounce = getattr(config, '_dom_debounce', None)
            if config.saved_score != config.score_actuel and config.score_actuel != dom_debounce:
                config._dom_debounce = None
                _appliquer_transition(driver, config.score_actuel, source='bridge')
            else:
                # Attendre un vrai changement de score
                bridge_wait_score_change()
                if config.score_actuel and config.score_actuel != config.saved_score:
                    _appliquer_transition(driver, config.score_actuel, source='bridge')
            config.saved_score = config.score_actuel
        return ok
    # ── Selenium fallback ──────────────────────────────────────────────────────
    config.score_actuel = False
    get_score = False
    tentative = 0
    while not get_score:
        try:

            score_teams = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  config.classes['score_container'][config.site_type]))
            )
            score_teams = driver.find_elements(By.CLASS_NAME, config.classes['score_container'][config.site_type])
        except Exception as e:
            score_container_selector = config.classes['score_container'][config.site_type]
            print(f"#E0020\nUne erreur est survenue : {score_container_selector}")
            config.log_clear_line()
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            tentative = tentative + 1
            time.sleep(1)
            if tentative == 5:
                config.error = True
                return False
        else:
            try:
                if config.site_type == 'mobile_site':
                    block_score_teams = score_teams[0]
                    team1_elements = block_score_teams.find_elements(By.CLASS_NAME, 'scoreboard-scores__item--team-1')
                    team2_elements = block_score_teams.find_elements(By.CLASS_NAME, 'scoreboard-scores__item--team-2')
                    if team1_elements and team2_elements:
                        config.score_actuel = team1_elements[0].text + ':' + team2_elements[0].text
                    else:
                        raise Exception("Impossible de trouver les scores des équipes en mode mobile_site")
                else:
                    config.score_actuel = score_teams[0].text + ':' + score_teams[1].text
            except Exception as e:
                print(f"#E0021\nUne erreur est survenue lors de la récupération du score : {e}")
                continue

        dom_debounce = getattr(config, '_dom_debounce', None)
        if config.saved_score != config.score_actuel and config.score_actuel != dom_debounce:
            config._dom_debounce = None
            _appliquer_transition(driver, config.score_actuel, source='dom')
        else:
            # DOM inchangé : vérifier si Redis/hint a déjà acté une transition plus récente
            try:
                from Functions import RedisIPC
                etat_redis = RedisIPC.get_match_score(getattr(config, 'newmatch', ''))
                if etat_redis and etat_redis['score'] != str(config.saved_score):
                    redis_np = int(etat_redis.get('numero_point', -1))
                    local_np = get_numero_point(config.saved_score) if config.saved_score else -1
                    if redis_np > local_np:
                        _appliquer_transition(driver, etat_redis['score'], source='redis_hint')
            except Exception:
                pass
            get_score = True
        config.saved_score = config.score_actuel
    return True


def _appliquer_transition(driver, candidat_score, source):
    """
    Calcule le numéro de point associé à `candidat_score` et tente de le faire
    valider comme LA transition faisant foi via `RedisIPC.try_claim_score_update`,
    partagée entre tous les process qui suivent ce match (15V1, 15V2, 1530A_V2...).

    - Si cet appel gagne la course (premier à voir cette transition évolutive,
      qu'elle vienne du DOM 1xBet ou du hint Sofascore) : elle est enregistrée dans
      `config.all_scores` et le traitement (mise, etc.) peut se poursuivre normalement.
    - Si cet appel perd (transition déjà actée par un autre process/tour précédent,
      ou régression/duplication) : l'état local est resynchronisé sur l'état partagé
      faisant foi, SANS dupliquer l'enregistrement ni le pari.
    """
    if source == 'dom':
        GetSetActuel(driver)
        GetJeuActuel(driver)
    elif source in ('redis_hint', 'bridge'):
        # Score depuis Redis hint ou Extension Chrome : adopter set/jeu depuis Redis ou bridge
        if source == 'redis_hint':
            from Functions import RedisIPC
            etat = RedisIPC.get_match_score(getattr(config, 'newmatch', ''))
            if etat:
                config.set_actuel = etat['set_actuel']
                config.jeu_actuel = etat['jeu_actuel']
        else:
            from Functions.BridgeAdapter import bridge_get_jeu_actuel, bridge_get_set_actuel
            bridge_get_set_actuel()
            bridge_get_jeu_actuel()
    # En mode hint Sofascore, 1xBet n'a pas bougé : on réutilise le set/jeu actuel déjà
    # connus (ils n'ont aucune raison d'avoir changé puisque le bookmaker est en retard).

    numero_point = get_numero_point(candidat_score)
    vainqueur = get_vainqueur_point_precedent(config.saved_score, candidat_score)

    from Functions import RedisIPC
    gagne, etat = RedisIPC.try_claim_score_update(
        getattr(config, 'newmatch', ''), candidat_score, numero_point,
        config.set_actuel, config.jeu_actuel, vainqueur, source=source,
    )

    if gagne:
        nouveau_score = {
            'set': config.set_actuel,
            'jeu': config.jeu_actuel,
            'score': candidat_score,
            'numero_point': numero_point,
            'vainqueur_point': vainqueur,
        }
        config.vainqueur_point_precedent = vainqueur
        config.point_actuel = numero_point + 1  # +1 car le point actuel vient d'être joué
        config._dom_debounce = None  # transition actée → débloquer le prochain DOM
        config._dom_debounce = None
        config.log(nouveau_score, clear=False, indent=2)
        config.log_clear_line()
        config.all_scores.update({len(config.all_scores): nouveau_score})
        config.score_actuel = candidat_score

        if source == 'dom':
            # Diagnostic de latence uniquement (jamais utilisé pour décider d'un pari) :
            # comparer le score bookmaker qu'on vient de confirmer avec le dernier score
            # connu de Sofascore, pour objectiver le délai réel entre les deux sources.
            try:
                from Functions.SofascoreWatcher import get_score_hint
                hint_score, hint_age = get_score_hint()
                if hint_score is not None:
                    statut = "identique" if hint_score == candidat_score else "différent"
                    config.log(
                        f"[Sofascore] hint={hint_score} (âge {hint_age:.1f}s) vs bookmaker={candidat_score} ({statut})",
                        'debug', False,
                    )
            except Exception:
                pass
        else:
            config.log(
                f"[Sofascore] transition {candidat_score} actée en premier via hint Sofascore "
                f"(bookmaker encore en retard)", 'warning', False,
            )
    elif etat is not None:
        # Un autre process (ou ce process à un tour précédent) a déjà acté cette
        # transition, ou celle-ci est une régression/duplication : on adopte l'état
        # partagé faisant foi sans rien ré-enregistrer ni re-parier.
        config.log(
            f"[Sofascore] transition {candidat_score} déjà actée ailleurs "
            f"(état partagé={etat['score']}), resynchronisation locale", 'debug', False,
        )
        config.score_actuel = etat['score']
        # Ne pas rétrograder jeu/set locaux si Redis a des données plus anciennes :
        # évite que 1530A (déjà à jeu 7) recule à jeu 6 à cause d'une entrée Redis périmée,
        # ce qui déclencherait "set du paris supérieur!" et un DeleteBet incorrect.
        try:
            etat_set = int(etat['set_actuel'])
            etat_jeu = int(etat['jeu_actuel'])
            local_set = int(config.set_actuel) if config.set_actuel else 0
            local_jeu = int(config.jeu_actuel) if config.jeu_actuel else 0
            redis_plus_avance = (etat_set > local_set) or (etat_set == local_set and etat_jeu >= local_jeu)
        except Exception:
            redis_plus_avance = True
        if redis_plus_avance:
            config.set_actuel = etat['set_actuel']
            config.jeu_actuel = etat['jeu_actuel']
        config.vainqueur_point_precedent = etat['vainqueur_point']
        config.point_actuel = int(etat['numero_point']) + 1
        # Enregistrer dans all_scores local même si c'est un autre process qui a gagné
        # la course : nécessaire pour que GetResult puisse retrouver l'historique du jeu
        # et éviter un LOSE incorrect quand les transitions sont actées par 15V2/1530A.
        # Ne sync que si le jeu/set de Redis est au moins aussi avancé que le local.
        if redis_plus_avance:
            already_recorded = any(
                str(v.get('set')) == str(etat['set_actuel'])
                and str(v.get('jeu')) == str(etat['jeu_actuel'])
                and str(v.get('numero_point')) == str(etat['numero_point'])
                for v in config.all_scores.values()
            )
            if not already_recorded:
                synced_score = {
                    'set': etat['set_actuel'],
                    'jeu': etat['jeu_actuel'],
                    'score': etat['score'],
                    'numero_point': int(etat['numero_point']),
                    'vainqueur_point': etat['vainqueur_point'],
                }
                config.all_scores.update({len(config.all_scores): synced_score})
        # Si l'état partagé est en retard sur le hint (ex: Redis=40:40, hint=A:40),
        # on pose un debounce dédié pour ne pas re-tenter le même hint en boucle
        # jusqu'à ce que Redis avance ou que 1xBet affiche le score.
        if etat['score'] != candidat_score:
            # Redis en retard sur candidat_score : enregistrer quand même l'état observé localement
            # pour que GetResult retrouve l'entrée (ex: A:40 réclamé par 1530A mais 15V1 l'avait vu en premier).
            np_candidat = get_numero_point(candidat_score)
            already_local = any(
                str(v.get('set')) == str(config.set_actuel)
                and str(v.get('jeu')) == str(config.jeu_actuel)
                and str(v.get('numero_point')) == str(np_candidat)
                for v in config.all_scores.values()
            )
            if not already_local:
                config.all_scores.update({len(config.all_scores): {
                    'set': config.set_actuel,
                    'jeu': config.jeu_actuel,
                    'score': candidat_score,
                    'numero_point': np_candidat,
                    'vainqueur_point': vainqueur,
                }})
            # Avancer saved_score pour éviter que la prochaine transition calcule
            # get_vainqueur_point_precedent depuis un score trop vieux ET pour arrêter
            # la boucle DOM (saved_score == score_actuel après la prochaine lecture).
            config.saved_score = candidat_score
            config._dom_debounce = candidat_score
        else:
            # Redis a maintenant ce score (gagné par un autre process entre-temps) : débloquer.
            config.saved_score = candidat_score
            config._dom_debounce = None
    else:
        # etat est None uniquement en cas d'erreur RedisIPC (voir try_claim_score_update) :
        # comportement de repli identique à l'ancien fonctionnement local, sans table
        # partagée, pour ne jamais bloquer le bot sur une panne de la BDD de secours.
        config.score_actuel = candidat_score

    return gagne


# Correspondance score tennis → nombre de points marqués
_SCORE_VERS_POINTS = {'0': 0, '15': 1, '30': 2, '40': 3, 'A': 4, 'AD': 4, 'ADV': 4}


def _compter_deuces_jeu(set_actuel: str, jeu_actuel: str) -> int:
    """
    Compte le nombre de deuces (scores '40:40') dans l'historique du jeu en cours,
    en incluant le score actuel s'il est également un déuce.

    Quand all_scores est vide ou incomplet (script démarré en cours de jeu),
    utilise le numero_point Redis pour rétro-calculer le nombre de deuces réels.
    """
    nb = sum(
        1 for entry in config.all_scores.values()
        if entry.get('set') == set_actuel
        and entry.get('jeu') == jeu_actuel
        and str(entry.get('score', '')).upper() == '40:40'
    )
    if str(config.score_actuel).upper() == '40:40':
        nb += 1

    # Si l'historique local est vide ou incomplet, vérifier Redis pour éviter
    # de sous-compter les deuces quand le script a démarré en cours de jeu.
    if nb <= 1:
        try:
            from Functions import RedisIPC
            shared = RedisIPC.get_match_score(getattr(config, 'newmatch', ''))
            if (shared
                    and str(shared.get('set_actuel', '')) == str(set_actuel)
                    and str(shared.get('jeu_actuel', '')) == str(jeu_actuel)
                    and shared.get('numero_point') is not None):
                redis_np = int(shared['numero_point'])
                redis_score = str(shared.get('score', '')).upper()
                # Rétro-calcul depuis numero_point Redis :
                #   40:40 Nème déuce  → numero_point = 6 + (N-1)*2  → N = (np-4)//2
                #   A:40 / 40:A       → numero_point = 7 + (N-1)*2  → N = (np-5)//2
                if redis_score == '40:40' and redis_np >= 6:
                    nb_redis = (redis_np - 4) // 2
                elif redis_score in ('A:40', '40:A') and redis_np >= 7:
                    nb_redis = (redis_np - 5) // 2
                else:
                    nb_redis = 0
                if nb_redis > nb:
                    nb = nb_redis
        except Exception:
            pass

    return nb


def get_numero_point(score: str) -> int:
    """
    Retourne le nombre de points joués dans le jeu à partir du score tennis.

    En zone déuce/avantage, l'historique de config.all_scores est utilisé pour
    compter les cycles déuce déjà joués et calculer le bon numéro de point.

    Exemples :
        '0:0'   → 0  (aucun point joué)
        '15:15' → 2  (2 points joués)
        '40:40' → 6  (premier déuce, 6 points joués)
        'A:40'  → 7  (avantage après premier déuce)
        '40:40' → 8  (deuxième déuce, si un 40:40 précédent existe en historique)

    Args:
        score (str): Score du jeu au format 'X:Y' (ex. '15:30', '40:A').

    Returns:
        int: Nombre de points joués dans ce jeu (0 si score = '0:0').
    """
    if not score or ':' not in str(score):
        return 0
    parties = str(score).upper().split(':')
    p1 = _SCORE_VERS_POINTS.get(parties[0], 0)
    p2 = _SCORE_VERS_POINTS.get(parties[1], 0)
    # Cas standard : avant la zone déuce (au moins un joueur a moins de 40)
    if not (p1 >= 3 and p2 >= 3):
        return p1 + p2
    # Zone déuce/avantage : utiliser l'historique pour détecter les cycles répétés
    nb_deuces = _compter_deuces_jeu(config.set_actuel, config.jeu_actuel)
    if parties[0] == '40' and parties[1] == '40':
        # Nième déuce : 6 points de base + 2 points par cycle supplémentaire
        return 6 + (nb_deuces - 1) * 2
    else:
        # Avantage après le Nième déuce
        return 7 + (nb_deuces - 1) * 2


def get_vainqueur_point_precedent(score_precedent: str, score_actuel: str) -> int:
    """
    Détermine le vainqueur du point précédent en comparant deux scores consécutifs.

    Gère correctement les transitions déuce ↔ avantage répétées :
        '40:A' → '40:40' : le joueur 1 a cassé l'avantage du joueur 2 → retourne 1
        'A:40' → '40:40' : le joueur 2 a cassé l'avantage du joueur 1 → retourne 2

    Args:
        score_precedent (str): Score avant le point joué (ex. '15:15').
        score_actuel (str): Score après le point joué (ex. '30:15').

    Returns:
        int: 1 si le joueur 1 a gagné le point, 2 si le joueur 2 a gagné, 0 si indéterminé.
    """
    if not score_precedent or not score_actuel:
        return 0
    if ':' not in str(score_precedent) or ':' not in str(score_actuel):
        return 0
    prec_upper = str(score_precedent).upper()
    act_upper = str(score_actuel).upper()
    # Transitions avantage → déuce : le joueur sans avantage a gagné le point
    if prec_upper == '40:A' and act_upper == '40:40':
        return 1  # Joueur 1 casse l'avantage du joueur 2
    if prec_upper == 'A:40' and act_upper == '40:40':
        return 2  # Joueur 2 casse l'avantage du joueur 1
    parties_prec = prec_upper.split(':')
    parties_act = act_upper.split(':')
    p1_prec = _SCORE_VERS_POINTS.get(parties_prec[0], 0)
    p2_prec = _SCORE_VERS_POINTS.get(parties_prec[1], 0)
    p1_act = _SCORE_VERS_POINTS.get(parties_act[0], 0)
    p2_act = _SCORE_VERS_POINTS.get(parties_act[1], 0)
    # Fin de jeu → remise à 0:0 : déterminer le vainqueur depuis le score précédent
    if act_upper == '0:0' and prec_upper != '0:0':
        # Après un avantage, c'est le joueur avantagé qui a remporté le jeu
        if prec_upper == 'A:40':
            return 1
        if prec_upper == '40:A':
            return 2
        # Score normal : le joueur à 40 (p=3) et dont l'adversaire n'est pas à 40 a gagné
        if p1_prec >= 3 and p2_prec < 3:
            return 1
        if p2_prec >= 3 and p1_prec < 3:
            return 2
        return 0
    if p1_act > p1_prec:
        return 1
    if p2_act > p2_prec:
        return 2
    return 0


def record_scores(driver):
    GetSetActuel(driver)
    GetJeuActuel(driver)
    # Calcul du numéro du point en cours et du vainqueur du point précédent
    config.point_actuel = get_numero_point(config.score_actuel)
    config.vainqueur_point_precedent = get_vainqueur_point_precedent(
        config.saved_score, config.score_actuel
    )
    nouveau_score = {
        'set': config.set_actuel,
        'jeu': config.jeu_actuel,
        'score': config.score_actuel,
        'numero_point': config.point_actuel,
        'vainqueur_point': config.vainqueur_point_precedent,
    }
    config.point_actuel = config.point_actuel + 1  # +1 car le point actuel vient d'être joué
    config.log(nouveau_score, clear=False, indent=2)
    config.log_clear_line()
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})

    # Diagnostic de latence uniquement (jamais utilisé pour décider d'un pari) :
    # comparer le score bookmaker qu'on vient de confirmer avec le dernier score connu
    # de Sofascore, pour objectiver le délai réel entre les deux sources.
    try:
        from Functions.SofascoreWatcher import get_score_hint
        hint_score, hint_age = get_score_hint()
        if hint_score is not None:
            statut = "identique" if hint_score == config.score_actuel else "différent"
            config.log(
                f"[Sofascore] hint={hint_score} (âge {hint_age:.1f}s) vs bookmaker={config.score_actuel} ({statut})",
                'debug', False,
            )
    except Exception:
        pass


def GetQTScoreActuel(driver):
    config.score_actuel = []
    tentative = 0
    while not config.score_actuel:
        try:
            config.score_actuel = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-table__col')
        except Exception as e:
            config.log(f"#E0009\nUne erreur est survenue : {e}")
            config.log("erreur : c-scorebdfdfvdoard-player-score__row")
            tentative = tentative + 1
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            else:
                tentative = tentative + 1
                if tentative == 5:
                    config.error = True
                    return False
        else:
            try:
                if config.qt_actuel == 1:
                    score_actuel_player1 = \
                        config.score_actuel[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 2:
                    score_actuel_player1 = \
                        config.score_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 3:
                    score_actuel_player1 = \
                        config.score_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 4:
                    score_actuel_player1 = \
                        config.score_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                else:
                    return False
            except Exception as e:
                continue
            else:
                get_score = True
                if config.saved_score != config.score_actuel:
                    record_scores()
                config.saved_score = config.score_actuel
    return True


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    config.sofascore_tab_handle = 1
    config.original_tab_handle = 1
    config.sofascore_link = 'https://www.sofascore.com/fr/tennis/atp-miami-open-2024/568422'
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    print("Démarrage de la récupération du score actuel...")
    GetScoreActuel(driver)
