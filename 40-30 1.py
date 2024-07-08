print('START 40-30 1')

import Functions_403015_proba
from SetDriver9 import driver
import config4030 as config

config.script_num = 1

while (config.win < 100):
    print(('ttst'))
    Functions_403015_proba.all_script(driver)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))
