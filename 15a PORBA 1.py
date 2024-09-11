from Functions import Functions_15a

print('START')

from ChromeDriver.SetDriver1 import driver
import config

config.script_num = 1

while (config.win < 100):
    Functions_15a.all_script(driver)
    try:
        driver.get('https://ca.1x001.com/fr/live/tennis')
    except:
        driver.get('https://ca.1x001.com/fr/live/tennis')
print('TOTAL WIN : '+str(config.win))