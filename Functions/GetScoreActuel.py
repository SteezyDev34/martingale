import os
import sys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetSetActuel import GetSetActuel


# from ChromeDriver.SetDriver1 import driver


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    tentative = 0
    first = True
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
            else:
                if config.saved_score != config.score_actuel:
                    if not first:
                        first = False
                        record_scores(driver)
                    else:
                        first = False
                        time.sleep(2)
                        continue
                else:
                    get_score = True
                config.saved_score = config.score_actuel
    return True


# Correspondance score tennis → nombre de points marqués
_SCORE_VERS_POINTS = {'0': 0, '15': 1, '30': 2, '40': 3, 'A': 4, 'AD': 4, 'ADV': 4}


def _compter_deuces_jeu(set_actuel: str, jeu_actuel: str) -> int:
    """
    Compte le nombre de deuces (scores '40:40') dans l'historique du jeu en cours,
    en incluant le score actuel s'il est également un déuce.

    Args:
        set_actuel (str): Identifiant du set en cours.
        jeu_actuel (str): Identifiant du jeu en cours.

    Returns:
        int: Nombre total de deuces dans le jeu (historique + courant si applicable).
    """
    nb = sum(
        1 for entry in config.all_scores.values()
        if entry.get('set') == set_actuel
        and entry.get('jeu') == jeu_actuel
        and str(entry.get('score', '')).upper() == '40:40'
    )
    if str(config.score_actuel).upper() == '40:40':
        nb += 1
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

    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    print("Démarrage de la récupération du score actuel...")
    GetScoreActuel(driver)
