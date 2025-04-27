import time

import config
from Functions.GetScoreActuel import GetQTScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetResult(driver):
    ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
    RetourTpsReg(driver)
    txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"

    print('validated_bet = ', config.validated_bet)
    config.log(txtlog, config.newmatch)
    config.saved_set = ""
    timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
    result = False
    while not result and not config.error:
        time.sleep(timesleep)
        config.qt_actuel = int(config.validated_bet.get('qt'))
        GetQTScoreActuel(driver)
        if config.validated_bet.get('win') == 'V1' and config.score_actuel[0] > \
                config.score_actuel[1]:
            result = 'WIN'
            config.log(f"Result: {result}", 'success', False, 2)
        elif config.validated_bet.get('win') == 'V2' and config.score_actuel[0] < \
                config.score_actuel[1]:
            result = 'WIN'
            config.log(f"Result: {result}", 'success', False, 2)
        else:
            result = 'LOSE'
            config.log(result, 'error', False, 2)

        return result


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.validated_bet = {
        'qt': 3,
        'win': 'V2'
    }
    config.scriptType = 'QT'
    GetResult(driver)
