
print('START 40 15 4')

import Functions_4015_proba
from ChromeDriver.SetDriver8 import driver
import config as config
import Functions_gsheets

config.script_num = 4

while (config.win < 100):
    try:
        config.init_variable()
        Functions_4015_proba.all_script(driver)
    except Exception as e:
        print(f"ERROR SCRIPT : {e}")
    if config.perte > 0:
        perte = config.perte
        while perte > 2:
            config.perte = 2
            config.wantwin = 0
            config.mise = 1
            Functions_gsheets.suivi_lost30()
            perte = perte - 2
        config.mise = (float(config.wantwin) + float(perte)) / (float(config.cote) - 1)
        config.mise = round(config.mise, 2)
        config.perte = perte
        Functions_gsheets.suivi_lost30()
    try:
        driver.get('https://ca.1x001.com/fr/live/tennis')
    except:
        driver.get('https://ca.1x001.com/fr/live/tennis')
print('TOTAL WIN : ' + str(config.win))

