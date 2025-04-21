import inspect
import time

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetScoreActuel import GetScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetIfGameStart(driver):
    gamestart = False
    printext = False
    driver.switch_to.window(driver.window_handles[0])
    RetourTpsReg(driver)
    while not gamestart and not config.error:
        driver.switch_to.window(driver.window_handles[0])
        GetScoreActuel(driver)
        config.saved_score = config.saved_score
        if config.score_actuel == '0:0':
            if not config.score_actuel:
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
            if not printext:
                config.log('GAME NOT START')
                printext = True
            time.sleep(1)  # attente 20 sec que le jeu commence
            # END GET SCORE
        elif config.score_actuel == '15:0' or config.score_actuel == '0:15' or config.score_actuel == '15:15' or config.score_actuel == '30:15' or config.score_actuel == '15:30' or config.score_actuel == '40:15' or config.score_actuel == '15:40' or config.score_actuel == '0:30' or config.score_actuel == '30:0' or config.score_actuel == '30:30' or config.score_actuel == '30:40' or config.score_actuel == '40:30' or config.score_actuel == '0:40' or config.score_actuel == '40:0':
            print('GAME START')
            gamestart = True
        elif not config.score_actuel:
            gamestart = False
            if not GetIfMatchPage(driver):
                print('Ce n\'est pas une page de match')
                config.error = True
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
        else:
            gamestart = False

    return gamestart


def GetIfGameStart30A(driver):
    gamestart = False
    printext = False
    config.log('ATTENTE DEBUT DE JEU', 'info', False, 4)
    while not gamestart and not config.error:
        GetScoreActuel(driver)
        if config.score_actuel == '0:0':
            config.log('GAME START', 'info', False, 4)
            config.log_clear_line()
            gamestart = True
        else:
            gamestart = False
            if not GetIfMatchPage(driver):
                config.error = True
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
    return gamestart


def GetIfGameEnd(driver):
    gameeend = False
    printext = False
    RetourTpsReg(driver)
    config.log('ATTENTE FIN DE JEU', 'info', False, 4)
    while not gameeend and not config.error:
        GetScoreActuel(driver)
        if config.score_actuel == '0:0':
            config.log('FIN DE JEU', 'info', False, 4)
            config.log_clear_line()
            gameeend = True
        else:
            gameeend = False
            if not GetIfMatchPage(driver):
                config.error = True
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
    return gameeend


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    GetIfGameStart(driver)
