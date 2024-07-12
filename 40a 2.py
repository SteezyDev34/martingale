print('START')
import re
import threading
import time


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import Functions_40a
##DEFINITION DES FONCTIONS
##
##FIN DEFINITION DES FONCTIONS

from selenium.webdriver.chrome.options import Options
opt = Options()
opt.add_experimental_option("debuggerAddress", "localhost:7977")
service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=opt)


##CONDITIONS DE DEPART
##
script_num = 2
setaffiche=[]
error=0
win = 0
mise = 0.2
perte = 0
wantwin = 0.2
increment = 0.2
cote = 3
lose =0
firstgame = 1
jeu = firstgame
set_actuel='1 Set'
set='1 Set'
score_actuel=False
passageset = 0
x=-1
rattrape_perte = 0
def put_mise(jeu, mise):
    error = 0
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
            jeu) + ' : 40:40 - Oui")]'))
        )
    except:
        print("btn 40A not visible")
        error = "btn 40A not visible"
    else:
        try:
            list_of_bet_type = driver.find_elements_by_xpath(
        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
            jeu) + ' : 40:40 - Oui")]')
        except:
            print("btn 40A not reachable")
            error = "btn 40A not reachable"
        else:
            if len(list_of_bet_type) > 0:
                print(list_of_bet_type[0].text)
                try:
                    element = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
            jeu) + ' : 40:40 - Oui")]')))
                except:
                    print("btn 40A not clicable retry ")
                else:
                    list_of_bet_type[0].click()
                    try:
                        element = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="sports_right"]/div/div[2]/div/div[2]/div[1]/div/div[3]/div[2]/div[1]/div/div[3]/div/input')))
                    except:
                        print("erreur ajout mise")
                    else:
                        driver.find_element_by_xpath(
                    '//*[@id="sports_right"]/div/div[2]/div/div[2]/div[1]/div/div[3]/div[2]/div[1]/div/div[3]/div/input').send_keys(
                    str(mise))
    if error == 0:
        return True
    else:
        return error
def get_score_actuel():
    score_actuel = 0
    get_score =0
    while get_score==0:
        try:
            score_actuel = driver.find_element_by_class_name('c-scoreboard-score__content').text
        except:
            print('erreur recup score')
        else:
            get_score =1
            score_actuel= score_actuel.replace("\n", "")
            return score_actuel
def get_set_actuel():
    try:
        set_actuel = driver.find_elements_by_class_name('c-scoreboard-score__heading')[0].text
    except:
        return False
    else:
        return set_actuel
def delete_bet():
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "c-bet-box__del"))
        )
    except:
        print("cross no found")
    else:
        #driver.switch_to.window(driver.window_handles[0])
        driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
        time.sleep(2)
        #driver.switch_to.window(driver.window_handles[0])
        element = driver.find_element_by_class_name('c-bet-box__del')
        element.click()
        return 0

##
##FIN DES CONDITIONS DE DEPART

##START
match_list = []
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
while (win< 999):
    infos = False
    try:
        infos = Functions_40a.all_script(driver, script_num, setaffiche, error, win, mise, perte, wantwin, increment, cote, lose, firstgame,
                   jeu, set_actuel, set, score_actuel, passageset, x,match_list,match_done_key,match_found,rattrape_perte)
    except Exception as e:
        print(f"#START0001\nUne erreur est survenue : {e}")
        try:
            driver.get('https://1xbet.com/fr/live/Tennis/')
        except:
            driver.get('https://1xbet.com/fr/live/Tennis/')

    print(infos)
    if infos != False:
        win = infos[0]
        perte = infos[1]
        wantwin = infos[2]
        mise = infos[3]
        x = infos[4]
    cote = 3
    increment = 0.2
    jeu = 1
    setaffiche=[]
    erreur=0
    set_actuel='1 SET'
    set='1 SET'
    score_actuel=False
    passageset = 0
    validate=0
    match_found = 0
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
