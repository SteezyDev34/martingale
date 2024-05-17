print('START')
import re
import threading
import time

import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import Functions_30a
##DEFINITION DES FONCTIONS
##
##FIN DEFINITION DES FONCTIONS

from selenium.webdriver.chrome.options import Options
opt = Options()
opt.add_experimental_option("debuggerAddress", "localhost:7971")
service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=opt)


##CONDITIONS DE DEPART
##
script_num = 4
setaffiche=[]
error=0
win = 0
mise = 0.71
perte = 0
wantwin = 1
increment = 0
cote = 2.4
lose =0
firstgame = 1
jeu = firstgame
set_actuel='1 Set'
set='1 Set'
score_actuel=False
passageset = 0
x=-1
rattrape_perte = 0

##
##FIN DES CONDITIONS DE DEPART

##START
match_list = []
matchlist_file_name = 'matchlist30A'
running_file_name = 'running30A'
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
while (win< 999):
    infos = False
    try:
        infos = Functions_30a.all_script(driver, script_num, setaffiche, error, win, mise, perte, wantwin, increment, cote,
                                     lose, firstgame,
                                     jeu, set_actuel, set, score_actuel, passageset, x, match_list, match_done_key,
                                     match_found, rattrape_perte,matchlist_file_name,running_file_name)
    except:
        print(infos)
    if infos != False:
        win = infos[0]
        perte = infos[1]
        wantwin = infos[2]
        mise = infos[3]
        x = infos[4]
    cote = 2.4
    increment = 0
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
