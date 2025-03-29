import time

import config
from Functions.GetScoreActuel import GetScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetResult(driver):
    ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
    txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"
    config.log(txtlog, config.newmatch)
    config.saved_set = ""
    timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
    result = False
    RetourTpsReg(driver)
    while not result and not config.error:
        time.sleep(timesleep)
        previous_score = config.score_actuel
        GetScoreActuel(driver)
        if not config.score_actuel:
            config.error = True
            break
        if config.scriptType == "40A":
            if config.score_actuel == '40:A' or config.score_actuel == 'A:40' or config.score_actuel == '40:40':
                result = 'WIN'
                config.log(result, config.newmatch)
                while config.score_actuel == '40:A' or config.score_actuel == 'A:40' or config.score_actuel == '40:40':
                    GetScoreActuel(driver)
                return result
            elif config.score_actuel == '0:0':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
        elif config.scriptType == "30A":
            if config.score_actuel == '30:30':
                result = 'WIN'
                config.log(result, config.newmatch)
                while config.score_actuel == '30:30':
                    GetScoreActuel(driver)
                return result
            elif config.score_actuel == '40:0' or config.score_actuel == '0:40' or config.score_actuel == '40:15' or config.score_actuel == '15:40':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
        elif config.scriptType == "15A":
            if config.score_actuel == '15:15':
                result = 'WIN'
                config.log(result, config.newmatch)
                while config.score_actuel == '15:15':
                    GetScoreActuel(driver)
                return result
            elif config.score_actuel == '30:0' or config.score_actuel == '0:30':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
        elif config.scriptType == '4030' or config.scriptType == '4015':
            print('previous_score = ' + previous_score)
            print('xin score = ' + config.win_type)
            if config.score_actuel == '0:0' and previous_score == config.win_type:
                result = 'WIN'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '0:0' and previous_score != config.win_type:
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
        elif config.scriptType == '400':
            print('previous_score = ' + previous_score)
            print('xin score = ' + config.win_type)
            if config.score_actuel == '0:0' and previous_score == config.win_type:
                result = 'WIN'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '40:15' or config.score_actuel == '15:40' or config.score_actuel == '40:30' or config.score_actuel == '30:40':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '0:0' and previous_score != config.win_type:
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    GetResult(driver)
