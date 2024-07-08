import Functions_30a

print('START')

from SetDriver5 import driver
import config_30A as config

config.script_num = 1

while (config.win < 100):
    try:
        Functions_30a.all_script(driver)
    except Exception as e:
        print("ERROR SCRIIPT",e)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))