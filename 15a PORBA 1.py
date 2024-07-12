import Functions_15a

print('START')

from SetDriver1 import driver
import config

config.script_num = 1

while (config.win < 100):
    Functions_15a.all_script(driver)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))