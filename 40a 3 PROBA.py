print('START')

import Functions_40a
import Functions_40a_proba
from SetDriver3 import driver
import config

config.script_num = 3

while (config.win < 100):
    Functions_40a_proba.all_script(driver)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))