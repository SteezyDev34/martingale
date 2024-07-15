print('START')

import Functions_40a
import Functions_40a_proba
from SetDriver2 import driver
import config
import Functions_gsheets

config.script_num = 2

while (config.win < 100):
    config.init_variable()
    Functions_40a_proba.all_script(driver)
    driver.get('https://1xbet.com/fr/live/Tennis/')
    if config.perte > 0:
        perte = config.perte
        while perte > 2:
            config.perte = 2
            config.wantwin = 0
            config.mise = 1
            Functions_gsheets.suivi_lost()
            perte = perte - 2
            if perte > 1:
                config.ligue_name = 'random'
                config.perte = 1
                config.wantwin = 0
                config.mise = 0.61
                Functions_gsheets.suivi_lost30()
                perte = perte - 1

        config.mise = (float(config.wantwin) + float(perte)) / (float(config.cote) - 1)
        config.mise = round(config.mise, 2)
        config.perte = perte
        Functions_gsheets.suivi_lost()
print('TOTAL WIN : '+str(config.win))