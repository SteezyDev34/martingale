import time

import GetIfMatchPage
import GetScoreActuel


def main(driver,saved_score):
    #driver.switch_to.window(driver.window_handles[0])
    gamestart = 0
    error = 0
    printext = 0
    while (gamestart <= 0 and error == 0):
        #driver.switch_to.window(driver.window_handles[0])
        score_actuel = GetScoreActuel.main(driver,saved_score)
        saved_score = saved_score
        if score_actuel == '0:0':
            if score_actuel == False:
                error = 1
            if printext == 0:
                print('GAME NOT START')
                printext = 1
                if GetIfMatchPage.main(driver)!=True:
                    error = 1
            time.sleep(1)#attente 20 sec que le jeu commence
            # END GET SCORE
        elif score_actuel == '15:0' or score_actuel == '0:15' or score_actuel == '15:15' or score_actuel == '30:15' or score_actuel == '15:30' or score_actuel == '40:15' or score_actuel == '15:40' or score_actuel == '0:30' or score_actuel == '30:0' or score_actuel == '30:30' or score_actuel == '30:40' or score_actuel == '40:30' or score_actuel == '0:40' or score_actuel == '40:0' or score_actuel == '40:40' or score_actuel == 'A:40' or score_actuel == '40:A':
            print('GAME START')
            gamestart = 1
        else:
            gamestart = 0
            if GetIfMatchPage.main(driver) != True:
                error = 1
