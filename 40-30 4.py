print('START 40 30 4')

import Functions_403015_proba
from SetDriver12 import driver
import config4030 as config

config.script_num = 4

while (config.win < 100):
    try:
        Functions_403015_proba.all_script(driver)
    except:
        pass
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))
