# Function_GetMatchScore
from selenium.webdriver.common.by import By

import config


def main(div_bet_score: object, score_to_start: list[str]) -> bool:
    get_bet_score = False
    try:
        config.log('Récupération du score', 'info', True, 4)
        config.log_clear_line()
        get_if_icon_ball = div_bet_score.find_elements(By.CLASS_NAME,
                                                       'ui-game-scores__item--inning')

        bet_score = div_bet_score.text
        bet_score = bet_score.replace(
            '\n', '')
    except:
        config.log('Impossible de lire le score du match!', 'warning', False, 3)
        get_bet_score = False
    else:
        config.log('Score en cours : ' + bet_score, 'warning', True, 4)
        config.log_clear_line()
        if any(score_ok == bet_score
               for score_ok in
               score_to_start) and len(get_if_icon_ball) > 0:
            get_bet_score = True
            config.log('Score eOKOK : ' + bet_score, 'warning', True, 4)
            config.log_clear_line()
    return get_bet_score


def set1main(div_bet_score: object, score_to_start: list[str]) -> bool:
    get_bet_score = False
    try:
        config.log('Récupération du score', 'info', True, 4)
        config.log_clear_line()

        bet_score = div_bet_score.text
        bet_score = bet_score.replace(
            '\n', '')
    except:
        config.log('Impossible de lire le score du match!', 'warning', False, 3)
        get_bet_score = False
    else:
        config.log('Score en cours : ' + bet_score, 'warning', True, 4)
        config.log_clear_line()
        if not any(score_ok == bet_score
                   for score_ok in
                   score_to_start):
            get_bet_score = True
            config.log('Score eOKOK : ' + bet_score, 'warning', True, 4)
            config.log_clear_line()
    return get_bet_score
