from Functions import Functions_15a

print('START')

from ChromeDriver.SetDriver1 import driver
import config

config.script_num = 1

while (config.win < 100):
    Functions_15a.all_script(driver)
    try:
        driver.get('https://1xlite-989182.top/fr/live/tennis')
    except:
        driver.get('https://1xlite-989182.top/fr/live/tennis')
print('TOTAL WIN : '+str(config.win))