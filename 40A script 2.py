import Functions_1XBET

script_num = 2
print('INIT SCRIPT '+str(script_num))
import config_40A
import Functions_40a


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
opt = Options()
opt.add_experimental_option("debuggerAddress", "localhost:7911")
service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=opt)

win = 0
while (win< 10):
    infos = Functions_40a.all_script(driver, script_num, win, config_40A.matchlist_file_name, config_40A.running_file_name, False)

    if infos:
        win = infos[0]
        Functions_1XBET.del_running(script_num, config_40A.running_file_name)
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(win))