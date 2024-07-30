
print('START 40-30 1')

from Functions import Functions_403015_proba, Functions_gsheets
from ChromeDriver.SetDriver9 import driver
import config

config.script_num = 1

while (config.win < 100):
    try:
        config.init_variable()
        Functions_403015_proba.all_script(driver)
    except Exception as e:
        print(f"ERROR SCRIPT : {e}")
        print('perte = '+str(config.perte))
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
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : ' + str(config.win))
