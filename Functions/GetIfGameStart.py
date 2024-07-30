import time

from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetScoreActuel import GetScoreActuel

import config
def GetIfGameStart(driver):
    gamestart = False
    printext = False
    while not gamestart and not config.error:
        GetScoreActuel(driver)
        config.saved_score = config.saved_score
        if config.score_actuel == '0:0':
            if not config.score_actuel:
                config.error = True
            if not printext:
                config.saveLog('GAME NOT START')
                printext = True
                if not GetIfMatchPage(driver):
                    config.error = True
            time.sleep(1)#attente 20 sec que le jeu commence
            # END GET SCORE
        elif config.score_actuel == '15:0' or config.score_actuel == '0:15' or config.score_actuel == '15:15' or config.score_actuel == '30:15' or config.score_actuel == '15:30' or config.score_actuel == '40:15' or config.score_actuel == '15:40' or config.score_actuel == '0:30' or config.score_actuel == '30:0' or config.score_actuel == '30:30' or config.score_actuel == '30:40' or config.score_actuel == '40:30' or config.score_actuel == '0:40' or config.score_actuel == '40:0':
            print('GAME START')
            gamestart = True
        elif not config.score_actuel:
            gamestart = False
            if not GetIfMatchPage(driver):
                config.error = True
        else:
            gamestart = False

    return gamestart
def GetIfGameStart30A(driver):
    gamestart = False
    printext = False
    while not gamestart and not config.error:
        GetScoreActuel(driver)
        config.saved_score = config.saved_score
        if config.score_actuel == '0:0' or config.score_actuel == '15:0' or config.score_actuel == '0:15' or config.score_actuel == '15:15' or config.score_actuel == '30:15' or config.score_actuel == '15:30' or config.score_actuel == '0:30' or config.score_actuel == '30:0' or config.score_actuel == '30:30':
            print('GAME START')
            gamestart = True
        else:
            gamestart = False
            if not GetIfMatchPage(driver):
                config.error = True

    return gamestart
