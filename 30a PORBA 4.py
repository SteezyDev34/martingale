import Functions_30a

print('START')

from SetDriver8 import driver
import config as config

config.script_num = 4

while (config.win < 100):
    try:
        Functions_30a.all_script(driver)
    except:
        print("ERROR SCRIIPT")
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))