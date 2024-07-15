import Functions_30a

print('START')

from SetDriver7 import driver
import config as config

config.script_num = 3

while (config.win < 100):
    Functions_30a.all_script(driver)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))