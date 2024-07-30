from Functions import Functions_gsheets, Functions_30a

print('START')

from ChromeDriver.SetDriver5 import driver
import config as config

config.script_num = 1

while (config.win < 100):
    config.init_variable()
    try:
        Functions_30a.all_script(driver)
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
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : ' + str(config.win))
