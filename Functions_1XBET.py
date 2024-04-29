from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

import time
import re
from datetime import datetime



#RÉCUPÉRER LES MATCHS EFFECTUÉS
def get_match_done(matchlist_file_name):
    get_matchlist_file = open(matchlist_file_name+".txt", "r")
    get_matchlist = get_matchlist_file.read()
    get_matchlist_file.close()
    match_list = get_matchlist.split('\n')
    return match_list
#VERRIFICATION DU MATCH TROUVÉ
def verification_match_trouve(bet_item,matchlist_file_name):
    try:
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'c-events__name')[
            0].get_attribute(
            "href")
        newmatch = newmatchtxt.split(
            '-')
        newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        print(f"#E0007\nUne erreur est survenue : {e}")
        print('Impossible de lire le lien du match!')
        return [False, newmatch]
    else:
        #print('newmatch : '+newmatch)
        match_list = get_match_done(matchlist_file_name)
        if not any( newmatch in x for x in match_list):
            #print('Le match n\'a pas encore été parié!')
            return [True,newmatch]
        else:
            print('Le match a déjà été parié!')
            return [False, newmatch]
#VERRIFICATION DU MATCH TROUVÉ PAR URL
def verification_match_trouve_url(driver,matchlist_file_name):
    try:
        newmatchtxt = driver.current_url
        newmatch = newmatchtxt.split(
            '-')
        newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        print(f"#E0007\nUne erreur est survenue : {e}")
        print('Impossible de lire le lien du match!')
        return [False, newmatch]
    else:
        #print('newmatch : '+newmatch)
        match_list = get_match_done(matchlist_file_name)
        if not any( newmatch in x for x in match_list):
            #print('Le match n\'a pas encore été parié!')
            return [True,newmatch]
        else:
            print('Le match a déjà été parié!')
            return [False, newmatch]
#MISE A JOUR DES MATCHS EFFECTUÉS
def update_match_done(action, values,matchlist_file_name):
    if action == "add":
        newmatch = values
        get_matchlist_file = open(matchlist_file_name+".txt", "a")
        get_matchlist_file.write(
            "\n" + str(newmatch))
        get_matchlist_file.close()
    elif action == "del":
        get_matchlist_file = open(matchlist_file_name+".txt", "r")
        get_matchlist = get_matchlist_file.read()
        get_matchlist_file.close()
        match_list = get_matchlist.replace("\n" + str(values), "")
        get_matchlist_file = open(matchlist_file_name+".txt", "w")
        get_matchlist_file.write(match_list)
        get_matchlist_file.close()
#MISE A JOUR DES MATCHS EFFECTUÉS
def update_mise_en_cours(action, values,mise_en_cours_file_name,matchlist_file_name):
    if action == "add":
        newmatch = values
        get_matchlist_file = open(mise_en_cours_file_name+".txt", "a")
        get_matchlist_file.write(
            "\n" + str(newmatch))
        get_matchlist_file.close()
    elif action == "del":
        get_matchlist_file = open(mise_en_cours_file_name+".txt", "r")
        get_matchlist = get_matchlist_file.read()
        get_matchlist_file.close()
        match_list = get_matchlist.replace("\n" + str(values), "")
        get_matchlist_file = open(matchlist_file_name+".txt", "w")
        get_matchlist_file.write(match_list)
        get_matchlist_file.close()
#EST CE QUE LE SCRIPT ESTT EN COURS

def get_if_running(script_num,running_file_name):
    dontgo = 0
    if script_num > 1:
        i = 1
        while i < script_num:
            get_running_file = open(running_file_name+".txt", "r")
            get_running = get_running_file.read()
            get_running_file.close()
            if len(re.findall(str(i), get_running)) <= 0:
                dontgo = dontgo + 1
            i = i + 1
    if dontgo != 0:
        time.sleep(10)
        return False
    else:
        #print("can go")
        return True
#INDIQUER QUE LE SCRIPT EST EN COURS
def add_running(script_num,running_file_name):
    if script_num == '#1#':
        script_num = 1
    get_running_file = open(running_file_name+".txt", "a")
    get_running_file.write(str(script_num))
    get_running_file.close()
#INDIQUER SCRIPT STOP
def del_running(script_num,running_file_name):
    get_running_file = open(running_file_name+".txt", "r")
    get_running = get_running_file.read()
    get_running_file.close()
    match_list = get_running.replace("#" + str(script_num) + "#", "")
    match_list = match_list.replace(str(script_num), "")
    get_running_file = open(running_file_name+".txt", "w")
    get_running_file.write(match_list)
    get_running_file.close()
#OBTENIR L'HEURE ACTUELLE
def current_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S")



##
##
##FONCTIONS 1XBET
##
##
#SUPPRRIMER PARIS EN COURS
def delete_bet(driver, error):
    #driver.switch_to.window(driver.window_handles[0])
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "cpn-bet__remove"))
        )
        driver.find_element(By.TAG_NAME,'body').send_keys(Keys.CONTROL + Keys.HOME)
        time.sleep(2)
        element = driver.find_element(By.CLASS_NAME,'cpn-bet__remove')
    except:
        print("cross no found")
        return False
    else:
        element.click()
        return 0
#VÉRIFIERR SI PAGE DE MATCH
def verification_page_de_match(driver):
    #driver.switch_to.window(driver.window_handles[0])
    print("verfication si page match...")
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'c-scoreboard-score__heading'))
        )
    except Exception as e:
        print('Tableau des scores introuvable!')
        try:
            print(f"verfication si page match terminé...{e}")
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'after-game-info__text'))
            )
        except Exception as e:
            print("vérificattion page de match impossible!")
            driver.get('https://1xbet.com/fr/live/tennis')
            return False
        else:
            print("MATCH TERMINÉ!")
            driver.get('https://1xbet.com/fr/live/tennis')
            return 0

    else:
        #print('Tableau des scores trouvé...')
        return True

def verification_liste_match_live(driver):
    #driver.switch_to.window(driver.window_handles[0])
    #print("verfication si liste de match live...")
    try:
        driver.find_element(By.CLASS_NAME, 'game_content_line')

    except Exception as e:
        print (f"#E0003\nUne erreur est survenue : {e}")
        print("Liste match live non visible!")
        return False
    else:
        #print('Liste de match live trouvé!')
        return True

def get_ligue_name(bet_ligue):
    ligue_name = ''
    try:
        div_ligue_name = bet_ligue.find_element(By.TAG_NAME, 'div')
    except Exception as e:
        print (f"#E0004\nUne erreur est survenue : {e}")
        print('Lecture nom ligue impossible!')
        ligue_name = False
    else:
        try:
            ligue_name = div_ligue_name.find_element(By.CLASS_NAME,
                                                     'c-events__name')
            ligue_name = ligue_name.text.lower()
            ligue_name = ligue_name.replace('.', '')
        except Exception as e:
            print(f"#E0005\nUne erreur est survenue : {e}")
            ligue_name = False
        #else:
            #print('a Nom de la ligue :'+ligue_name)
    return ligue_name

def get_ligue_name_from_url(driver):
    get_url = driver.current_url
    print(" url = "+get_url)
    get_url = get_url.split('tennis/')
    get_url = get_url[1].split('/')
    get_url = get_url[0]
    get_url = get_url.split('-')
    del get_url[0]
    get_url = (' ').join(get_url)
    ligue_name = get_url
    '''if len(re.findall("wta",get_url.lower())) >0:
        ligue_name ='wta'
    elif len(re.findall("atp",get_url.lower())) >0:
        ligue_name = 'atp'
    elif len(re.findall("itf", get_url.lower())) > 0:
        ligue_name = 'itf'
    else:
        ligue_name = '''''
    return ligue_name

def get_match_score(div_bet_score,score_to_start):
    bet_score = False
    try:
        bet_score = div_bet_score.text
        bet_score = bet_score.replace(
        '\n', '')
    except Exception as e:
        print(f"#E0006\nUne erreur est survenue : {e}")
        print('Impossible de lire le score du match!')
    else:
        #print('score en cours : '+bet_score)
        if any(
                score_ok in bet_score
                for score_ok in
                score_to_start):
            get_if_icon_ball = div_bet_score.find_elements(By.XPATH,
                                                           './/span[@class="c-events-scoreboard__ball"]/div[not(contains(@style,"display: none;"))]')
            if len(get_if_icon_ball) > 0:
                print('MATCH PRET')
                bet_score = True
    return bet_score

def ouverture_page_match(bet_item,script_num,newmatch,running_file_name,matchlist_file_name):
    print('test12154')
    try:
        add_running(script_num,running_file_name)
        update_match_done("add", newmatch,matchlist_file_name)
        bet_item.find_elements(By.CLASS_NAME,
                               'c-events__name')[
            0].click()
        print("OUVERTURE DU MATCH")
        time.sleep(5)
    except Exception as e:
        print(f"#E0008\nUne erreur est survenue : {e}")
        print('ERREUR LORS DE L\'OUVERTURE DU MATCH')
        return False
    else:
        return True
#OBTENIR LE SET ACTUEL
def get_set_actuel(driver, error,saved_set):
    #driver.switch_to.window(driver.window_handles[0])
    if error == 0:
        try:
            set_actuel = driver.find_elements(By.CLASS_NAME,'c-scoreboard-score__heading')[0].text
        except Exception as e:
            print(f"#E0009\nUne erreur est survenue : {e}")
            print("erreur : c-scoreboard-score__heading")
            return False
        else:
            try:
                numset = int(set_actuel.split(' ')[0])
            except Exception as e:
                print(f"#E0010\nUne erreur est survenue : {e}")
                print("erreur : numset")
                return False
            else:
                set = str(numset) + " Set"
                set_actuel = set
                if saved_set != set_actuel:
                    print('Récupération du set actuel : ' + set_actuel)
                return set_actuel
    else:
        print("erreur_get_set_actuel : " + str(error))
        return False

def get_jeu_actuel(driver):
    #driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = get_set_actuel(driver, error, '')
            if set_actuel == '1 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '2 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '3 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                numjeu = False
        except Exception as e:
            print(f"#JEU0010\nUne erreur est survenue : {e}")
            print("erreur : numjeu")
            return False
        else:
            jeu = "Jeu " + str(numjeu)
            print('Récupération du jeu actuel : ' + jeu)
            return numjeu

def get_jeu_actuel_30a(driver):
    #driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = get_set_actuel(driver, error, '')
            if set_actuel == '1 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '2 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '3 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                numjeu = False
        except Exception as e:
            print(f"#JEU0010\nUne erreur est survenue : {e}")
            print("erreur : numjeu")
            return False
        else:
            jeu = "Jeu " + str(numjeu)
            print('Récupération du jeu actuel : ' + jeu)
            score_actuel = get_score_actuel(driver,"")
            if score_actuel == "30:15" or score_actuel == "15:30" or score_actuel == "30:0" or score_actuel == "0:30" or score_actuel == "30:40" or score_actuel == "40:30" or score_actuel == "0:40" or score_actuel == "15:40" or score_actuel == "40:40" or score_actuel == "A:40" or score_actuel == "40:A" or score_actuel == "40:0" or score_actuel == "40:15":
                numjeu = numjeu +1
            return numjeu

def get_jeu_actuel_15a(driver):
    #driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = get_set_actuel(driver, error, '')
            if set_actuel == '1 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '2 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '3 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                numjeu = False
        except Exception as e:
            print(f"#JEU0010\nUne erreur est survenue : {e}")
            print("erreur : numjeu")
            return False
        else:
            jeu = "Jeu " + str(numjeu)
            print('Récupération du jeu actuel : ' + jeu)
            score_actuel = get_score_actuel(driver,"")
            if score_actuel == "0:15" or score_actuel == "15:0" or score_actuel == "30:15" or score_actuel == "15:30" or score_actuel == "30:0" or score_actuel == "0:30" or score_actuel == "30:40" or score_actuel == "40:30" or score_actuel == "0:40" or score_actuel == "15:40" or score_actuel == "40:40" or score_actuel == "A:40" or score_actuel == "40:A" or score_actuel == "40:0" or score_actuel == "40:15":
                numjeu = numjeu +1
            return numjeu

def validation_du_paris(driver, jeu,mise):
    #driver.switch_to.window(driver.window_handles[0])
    validation = 0
    tentative = 0
    error = 0
    while validation == 0 and tentative < 4:
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
            l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute("value")
            print("mise insérrer : " + str(l))
        except:
            print('erreur verification mise')
            break
        else:
            if str(l) == str(mise):
                sending_mise = 1
                print('RECHERCHE DU BOUTON PLACER UN PARIS')
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'cpn-settings'))
                    )
                except Exception as e:
                    print(f"#E0021\nUne erreur est survenue : {e}")
                    print('zone de bouton non trouvé!')
                    try:
                        # print('Vérification de validation déjà faite')
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]'))
                        )  ###vérifaction d'affichage pop up validation
                    except Exception as e:
                        print(f"#E0023\nUne erreur est survenue : {e}")
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            print('pas de fenetre alerte 0')
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        validation = driver.find_elements(By.XPATH,
                                                          '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]')[
                            0].text
                        if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                            print('PARI VALIDÉ!')
                            try:
                                element = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button'))
                                )
                            except:
                                print('impossible de cliqué sur ok')
                            else:
                                driver.find_element(By.XPATH,
                                                    '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button').click()

                        else:
                            print('impossible de récupérer les informations de validation')
                else:
                    try:
                        placer_mise(driver, mise)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
                        l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute(
                            "value")
                        print("mise insérrer : " + str(l))
                    except Exception as e:
                        print(f"#E005689\nUne erreur est survenue : {e}")
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            print('pas de fenetre alertte 1')
                            placer_mise(driver, mise)
                            tentative = tentative + 1
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        if str(l) == str(mise):
                            getbtn = driver.find_element(By.CLASS_NAME, 'cpn-settings')
                            getbtn = driver.find_element(By.CLASS_NAME, 'cpn-btns-group')
                            getbtn.click()
                            preloader = 1
                            printtext = 0
                            while preloader == 1:
                                try:
                                    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME,"cpn-preloader")))
                                except:
                                    print('pas de loader')
                                    preloader = 0
                                else:
                                    if printtext ==0:
                                        print('loading...')
                                        printtext = 1
                            fenetre_validation = 0
                            tentative = 1
                            while fenetre_validation == 0 and tentative <2:
                                tentative=tentative +1
                                try:
                                    print('Vérification de validation')
                                    element = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located(
                                            (By.CLASS_NAME,
                                             'c-coupon-modal__wrapper'))
                                    )  ###vérifaction d'affichage pop up validation
                                except:
                                    print('pas de fentre validation, vérification erreur')
                                    try:
                                        element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                            (By.XPATH, '//*[@id="swal2-title"]')))
                                    except:
                                        print('pas de fenetre alerte 2')
                                    else:
                                        alerttexte = driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text
                                        print('alert : '+alerttexte)
                                        if len(re.findall("Maximum",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            error=1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("modifiées",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            error=1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("déjà",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                            print("Paris déjà placé")
                                            delete_bet(driver, error)
                                            return True
                                        else:
                                            driver.find_element(By.CLASS_NAME,'swal2-confirm').click()
                                else:
                                    validation = driver.find_elements(By.CLASS_NAME,
                                        'c-coupon-modal__title')[
                                        0].text
                                    if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                        print('PARI VALIDÉ!')

                                        try:
                                            element = WebDriverWait(driver, 3).until(
                                                EC.presence_of_element_located(
                                                    (By.CLASS_NAME,
                                                     'o-btn-group__item'))
                                            )
                                        except:
                                            print('impossible de cliqué sur ok')
                                        else:
                                            modal_wrapper = driver.find_elements(By.CLASS_NAME,'c-coupon-modal__wrapper')[0]
                                            modal_wrapper.find_elements(By.TAG_NAME,
                                                'button')[0].click()
                                            fenetre_validation = 1
                                            validation = 1
                                            return True
                        else:
                            placer_mise(driver, mise)
                            tentative = tentative + 1
            else:
                placer_mise(driver,mise)
                tentative = tentative + 1

def first_validation_du_paris(driver, jeu,mise):
    #driver.switch_to.window(driver.window_handles[0])
    jeu = get_jeu_actuel(driver)
    validation = 0
    tentative = 0
    error = 0
    while validation == 0 and tentative < 4:
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
            l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute("value")
            print("mise insérrer : " + str(l))
        except:
            print('erreur verification mise')
            tentative = tentative + 1
        else:
            if str(l) == str(mise):
                accepter_changement_de_cote(driver)
                sending_mise = 1
                print('RECHERCHE DU BOUTON PLACER UN PARIS')
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'cpn-settings'))
                    )
                except Exception as e:
                    print(f"#E0021\nUne erreur est survenue : {e}")
                    print('zone de bouton non trouvé!')
                    try:
                        # print('Vérification de validation déjà faite')
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]'))
                        )  ###vérifaction d'affichage pop up validation
                    except Exception as e:
                        print(f"#E0023\nUne erreur est survenue : {e}")
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            print('pas de fenetre alerte 0')
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        validation = driver.find_elements(By.XPATH,
                                                          '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]')[
                            0].text
                        if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                            print('PARI VALIDÉ!')
                            try:
                                element = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button'))
                                )
                            except:
                                print('impossible de cliqué sur ok')
                            else:
                                driver.find_element(By.XPATH,
                                                    '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button').click()

                        else:
                            print('impossible de récupérer les informations de validation')
                else:
                    try:
                        getbtn = driver.find_element(By.CLASS_NAME, 'cpn-settings')
                        getbtn = driver.find_element(By.CLASS_NAME, 'cpn-btns-group')
                        getbtn.find_element(By.TAG_NAME, 'button').click()
                    except Exception as e:
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            print('pas de fenetre alertte 1')
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        preloader = 1
                        printtext = 0
                        while preloader == 1:
                            try:
                                WebDriverWait(driver, 3).until(
                                    EC.visibility_of_element_located((By.CLASS_NAME, "cpn-preloader")))
                            except:
                                print('pas de loader')
                                preloader = 0
                            else:
                                if printtext == 0:
                                    print('loading...')
                                    printtext = 1
                        fenetre_validation = 0
                        tentative = 1
                        while fenetre_validation == 0 and tentative < 2:
                            tentative = tentative + 1
                            try:
                                print('Vérification de validation')
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.CLASS_NAME,
                                         'c-coupon-modal__wrapper'))
                                )  ###vérifaction d'affichage pop up validation
                            except:
                                print('pas de fentre validation, vérification erreur')
                                try:
                                    element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="swal2-title"]')))
                                except:
                                    print('pas de fenetre alerte 2')
                                else:
                                    if len(re.findall("Maximum",
                                                      driver.find_elements(By.CLASS_NAME, 'swal2-content')[
                                                          0].text)) > 0:
                                        error = 1
                                        driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                    elif len(re.findall("déjà",
                                                        driver.find_elements(By.CLASS_NAME, 'swal2-content')[
                                                            0].text)) > 0:
                                        driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        print("Paris déjà placé")
                                        delete_bet(driver, error)
                                        return True
                                    else:
                                        driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                            else:
                                validation = driver.find_elements(By.CLASS_NAME,
                                                                  'c-coupon-modal__title')[
                                    0].text
                                if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                    print('PARI VALIDÉ!')

                                    try:
                                        element = WebDriverWait(driver, 3).until(
                                            EC.presence_of_element_located(
                                                (By.CLASS_NAME,
                                                 'o-btn-group__item'))
                                        )
                                    except:
                                        print('impossible de cliqué sur ok')
                                    else:
                                        modal_wrapper = driver.find_elements(By.CLASS_NAME, 'c-coupon-modal__wrapper')[0]
                                        modal_wrapper.find_elements(By.TAG_NAME,
                                                                    'button')[0].click()
                                        fenetre_validation = 1
                                        validation = 1
                                        return True

            else:
                placer_mise(driver, mise)
                tentative = tentative + 1

def get_score_actuel(driver,saved_score):
    #driver.switch_to.window(driver.window_handles[0])
    score_actuel = False
    get_score = 0
    error = 0
    saved = ''
    while get_score == 0 and error == 0:
        try:
            score_actuel = driver.find_element(By.CLASS_NAME,'c-scoreboard-score__content').text
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            verification_page_de_match(driver)
            error = 1
        else:
            get_score = 1
            score_actuel = score_actuel.replace("\n", "")
            if saved_score != score_actuel:
                print("Score actuel = "+score_actuel)
                print("saved actuel = " + saved_score)
            saved_score = score_actuel
    return score_actuel

def selection_des_paris_du_set(driver,set):
    #driver.switch_to.window(driver.window_handles[0])
    print('recherche du champ déroulant...')
    selection = False
    tentative = 0
    clic = False
    while selection == False and tentative <6:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'scoreboard-nav__select'))
            )
        except Exception as e:
            print(f"#E0012\nUne erreur est survenue : {e}")
            print("ERROR : champ déroulant non trouvé")
            tentative = tentative +1
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav__select')
            try:
                select_form[0].click()
                time.sleep(5)
            except Exception as e:
                print(f"#E0013\nUne erreur est survenue : {e}")
                tentative = tentative+1
            else:
                print("ouverture du champ déroulant...")
                try:
                    element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'multiselect__element'))
                    )
                except Exception as e:
                    print(f"#E0014\nUne erreur est survenue : {e}")
                    print("ERROR : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        print('Plusieurs liens trouvés....')
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_span = select_option.find_elements(By.CLASS_NAME,'multiselect__option')[0]
                                select_option_text = select_span.find_elements(By.TAG_NAME,'span')[0].get_attribute('title')
                            except Exception as e:
                                print(f"#E0015\nUne erreur est survenue : {e}")
                                print("no = select_option_text")
                                tentative = tentative+1
                            else:
                                if select_option_text.strip() == set:
                                    print('menu :' + set + ' trouvé in :' + select_option.text)
                                    try:
                                        select_option.click()
                                        time.sleep(1)
                                    except Exception as e:
                                        print(f"#E0015\nUne erreur est survenue : {e}")
                                        print("ERROR : clic impossible menu 1set")
                                        tentative = tentative + 1
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 10:
                                            try:
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].clear()
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].send_keys(
                                                    "Paris")
                                                l = driver.find_elements(By.CLASS_NAME,
                                                                         'scoreboard-nav-items-search__input')[
                                                    0].get_attribute("value")

                                                if l == "Paris":
                                                    paris = 1
                                                else:
                                                    tentative = tentative+1
                                                    time.sleep(1)
                                            except Exception as e:
                                                print(f"#E0016\nUne erreur est survenue : {e}")
                                                print("ERROR : impossible ecrire 'Paris'")
                                                if verification_page_de_match(driver) != True:
                                                    break
                                            else:
                                                selection = True
                                else:
                                    print('SET '+set+' non trouvé : error '+select_option_text)
                    time.sleep(2)
                time.sleep(2)
    return selection

def recherche_paris_40a(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 40 A....')
    if_get_jeu = False
    clic = 0

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                jeu) + ' : 40-40 - Oui")]'))
        )
    except Exception as e:
        #print(f"#E0017\nUne erreur est survenue : {e}")
        print("Paris Jeu " + str(jeu) + " : 40-40 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 40-40 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]')
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(" : 40-40 - Oui")
                jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(" : 40-40 - Oui")
                game1 = int(newbet_type1[0].split("Jeu ")[1])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(" : 40-40 - Oui")
                game2 = int(newbet_type2[0].split("Jeu ")[1])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                if game1 < game2:
                    jeu = game1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                        jeu) + ' : 40-40 - Oui")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 40A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' : 40-40 - Oui")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 40A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' : 40-40 - Oui")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 40 recuperé")
                clic = 0
    return [clic, jeu]

def recherche_paris_30a(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 30 A....')
    if_get_jeu = False
    clic = 0
    try:
        element = WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                jeu) + ' 30-30 - Oui")]'))
        )
    except Exception as e:
        print("Paris Jeu " + str(jeu) + " 30-30 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 30-30 - Oui")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 30-30 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 30-30 - Oui")]')
            score_actuel = get_score_actuel(driver,"")
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(" 30-30 - Oui")
                jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                if_get_jeu = True
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(" 30-30 - Oui")
                game1 = int(newbet_type1[0].split("Jeu ")[1])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(" 30-30 - Oui")
                game2 = int(newbet_type2[0].split("Jeu ")[1])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                score_actuel = get_score_actuel(driver,"")
                if game1 < game2 and (score_actuel =="40:15" or score_actuel =="15:40" or score_actuel =="40:0" or score_actuel =="0:40" or score_actuel =="40:40" or score_actuel =="40:A" or score_actuel =="A:40" ):
                    jeu = game1-1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2-1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                        jeu) + ' 30-30 - Oui")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 30A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 30-30 - Oui")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 30A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            #driver.find_element(By.XPATH,'//*[@id="sports_right"]/div/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div[contains(text(), "Jeu ' + str(jeu) + ' 30-30 - Oui")]').click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 30-30 - Oui")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print(f"#E00124\nUne erreur est survenue : {e}")
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 30 recuperé")
                clic = 0
    return [clic, jeu]

def recherche_paris_15a(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 15 A....')
    if_get_jeu = False
    clic = 0
    try:
        element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                jeu) + ' 15-15 - Oui")]'))
        )
    except Exception as e:
        print("Paris Jeu " + str(jeu) + " 15-15 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 15-15 - Oui")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 15-15 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 15-15 - Oui")]')
            score_actuel = get_score_actuel(driver,"")
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(" 15-15 - Oui")
                jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                if_get_jeu = True
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(" 15-15 - Oui")
                game1 = int(newbet_type1[0].split("Jeu ")[1])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(" 15-15 - Oui")
                game2 = int(newbet_type2[0].split("Jeu ")[1])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                score_actuel = get_score_actuel(driver,"")
                if game1 < game2 and (score_actuel =="0:30" or score_actuel =="30:0" or score_actuel =="40:15" or score_actuel =="15:40" or score_actuel =="40:0" or score_actuel =="0:40" or score_actuel =="40:40" or score_actuel =="40:A" or score_actuel =="A:40" ):
                    jeu = game1-1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2-1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                        jeu) + ' 15-15 - Oui")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 30A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 15-15 - Oui")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 30A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            #driver.find_element(By.XPATH,'//*[@id="sports_right"]/div/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/div[2]/div[contains(text(), "Jeu ' + str(jeu) + ' 30-30 - Oui")]').click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 15-15 - Oui")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print(f"#E00124\nUne erreur est survenue : {e}")
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 15 recuperé")
                clic = 0
    return [clic, jeu]

def recherche_prochain_paris_30a(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    jeu = jeu +1
    print('RECHERCHE DES PARIS 30 A....')
    if_get_jeu = False
    clic = 0
    try:
        element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                jeu) + ' 30-30 - Oui")]'))
        )
    except Exception as e:
        print("Paris Jeu " + str(jeu) + " 30-30 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 30-30 - Oui")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 30-30 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 30-30 - Oui")]')
            score_actuel = get_score_actuel(driver,"")
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(" 30-30 - Oui")
                jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                if_get_jeu = True
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(" 30-30 - Oui")
                game1 = int(newbet_type1[0].split("Jeu ")[1])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(" 30-30 - Oui")
                game2 = int(newbet_type2[0].split("Jeu ")[1])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                score_actuel = get_score_actuel(driver,"")
                if game1 < game2 and (score_actuel =="40:15" or score_actuel =="15:40" or score_actuel =="40:0" or score_actuel =="0:40" or score_actuel =="40:40" or score_actuel =="40:A" or score_actuel =="A:40" ):
                    jeu = game1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                        jeu) + ' 30-30 - Oui")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 30A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 30-30 - Oui")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 30A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 30-30 - Oui")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print(f"#E00124\nUne erreur est survenue : {e}")
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 30 recuperé")
                clic = 0
    return [clic, jeu]

def recherche_prochain_paris_15a(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    jeu = jeu +1
    print('RECHERCHE DES PARIS 15 A....')
    if_get_jeu = False
    clic = 0
    try:
        element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                jeu) + ' 15-15 - Oui")]'))
        )
    except Exception as e:
        print("Paris Jeu " + str(jeu) + " 15-15 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 15-15 - Oui")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 15-15 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " 15-15 - Oui")]')
            score_actuel = get_score_actuel(driver,"")
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(" 15-15 - Oui")
                jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                if_get_jeu = True
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(" 15-15 - Oui")
                game1 = int(newbet_type1[0].split("Jeu ")[1])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(" 15-15 - Oui")
                game2 = int(newbet_type2[0].split("Jeu ")[1])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                score_actuel = get_score_actuel(driver,"")
                if game1 < game2 and (score_actuel =="0:30" or score_actuel =="30:0" or score_actuel =="40:15" or score_actuel =="15:40" or score_actuel =="40:0" or score_actuel =="0:40" or score_actuel =="40:40" or score_actuel =="40:A" or score_actuel =="A:40" ):
                    jeu = game1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                        jeu) + ' 15-15 - Oui")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 15A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 15-15 - Oui")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 15A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' 15-15 - Oui")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print(f"#E00124\nUne erreur est survenue : {e}")
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 15 recuperé")
                clic = 0
    return [clic, jeu]

def get_mise(driver,rattrape_perte,wantwin,perte):
    #driver.switch_to.window(driver.window_handles[0])
    #rattrape_perte = 0
    if rattrape_perte == 0:
        print('Pas de rattrapage, cote : 3')
        cote= 3
    elif rattrape_perte == 3 :
        print('Bonne proba, cote : 3')
        cote = 3
    else:
        print("Rattrapage, recuperation de la cote")
        try:
            cote = driver.find_elements(By.CLASS_NAME,
                'cpn-bet__coef')[
                0].text
        except:
            print('erreur recup cote : 3')
            cote = 3
        else:
            print('cote recupéré ' + cote)
            if cote != '':
                try:
                    cote = float(cote)
                except:
                    print('error float cote : cote = 3')
                    cote = 3
            else:
                cote = 3
    mise = (wantwin + perte) / (cote - 1)
    mise = round(mise, 2)
    if mise < 0.2:
        mise = 0.2
    print("cote : " + str(cote))
    print("wantwin : " + str(wantwin))
    print("perte : " + str(perte))
    print("mise : " + str(mise))

    return [mise,cote]
def get_mise30a(driver,rattrape_perte,wantwin,perte):
    #driver.switch_to.window(driver.window_handles[0])
    rattrape_perte = 0
    if rattrape_perte == 3:
        print('Pas de rattrapage, cote : 2.4')
        cote= 2.4
    else:
        print("Rattrapage, recuperation de la cote")
        try:
            cote = driver.find_elements(By.CLASS_NAME,
                                        'cpn-bet__coef')[
                0].text
        except:
            print('erreur recup cote : 2.4')
            cote = 2.4
        else:
            print('cote recupéré ' + cote)
            if cote != '':
                try:
                    cote = float(cote)
                except:
                    print('error float cote : cote = 2.4')
                    cote = 2.4

            else:
                cote = 2.4
    mise = (wantwin + perte) / (cote - 1)
    mise = round(mise, 2)
    if mise < 0.5:
        mise = 0.5
    print("cote : " + str(cote))
    print("wantwin : " + str(wantwin))
    print("perte : " + str(perte))
    print("mise : " + str(mise))

    return [mise,cote]
def get_mise15a(driver,rattrape_perte,wantwin,perte):
    #driver.switch_to.window(driver.window_handles[0])
    rattrape_perte = 0
    if rattrape_perte == 0:
        print('Pas de rattrapage, cote : 1.85')
        cote= 1.85
    else:
        print("Rattrapage, recuperation de la cote")
        try:
            cote = driver.find_elements(By.CLASS_NAME,
                'cpn-total__coef')[
                0].text
        except:
            print('erreur recup cote : 2.4')
            cote = 1.85
        else:
            print('cote recupéré ' + cote)
            if cote != '':
                try:
                    cote = float(cote)
                except:
                    print('error float cote : cote = 2.4')
                    cote = 1.85

            else:
                cote = 1.85
    mise = (wantwin + perte) / (cote - 1)
    mise = round(mise, 2)
    if mise < 0.2:
        mise = 0.2
    print("cote : " + str(cote))
    print("wantwin : " + str(wantwin))
    print("perte : " + str(perte))
    print("mise : " + str(mise))

    return [mise,cote]


def accepter_changement_de_cote(driver):
    #driver.switch_to.window(driver.window_handles[0])
    accept_change = 0
    error = 0
    tentative = 0
    while accept_change == 0 and error == 0 and tentative < 2:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'cpn-coef-change')))
        except:
            error = 1
            print("error 1767")
            tentative = tentative +1
        else:

            select_form = driver.find_elements(By.CLASS_NAME,'cpn-coef-change')[0]
            select_form = select_form.find_elements(By.CLASS_NAME, 'multiselect__tags')
            select_form[0].click()
            time.sleep(2)
        if error == 0:
            select_form_accept_change = driver.find_elements(By.CLASS_NAME,'multiselect__element')
            if len(select_form_accept_change) > 0:
                for select_option in select_form_accept_change:
                    if len(re.findall("Accepter tous les changements", select_option.text)) > 0:
                        # print(select_option.text)
                        select_option.click()
                        time.sleep(2)
                        # print("click select_form_tps_regl")
                        accept_change = 1
                        break
            else:
                error = 1

def placer_mise(driver,mise):
    #driver.switch_to.window(driver.window_handles[0])
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,'cpn-info__division')))
    except Exception as e:
        print(f"#E001912\nUne erreur est survenue : {e}")
        print("CHAMP DE MISE NON TROUVÉ")
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, 'cpn-info__division')
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, 'cpn-value-controls__input')
        sending_mise = 0
        tentative = 0
        while sending_mise == 0 and tentative<10:
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            l = cpn_setting.get_attribute("value")
            print("mise insérrer : "+str(l))
            if str(l) == str(mise):
                sending_mise = 1
                return True

            else:
                tentative = tentative + 1
                print('mauvaise mise insérée!')
                time.sleep(1)

def retour_section_tps_reglementaire(driver):
    #driver.switch_to.window(driver.window_handles[0])
    temps_reg = 0
    error = 0
    tentative = 0
    while temps_reg == 0 and error == 0:
        try:
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scoreboard-nav-items-search__input')))
        except:
            error = 1
            print("error 75")
        else:

            try:
                txt_input = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav-items-search__input')[0].text
                print('text input = '+str(txt_input))
                driver.find_elements(By.CLASS_NAME,'scoreboard-nav-items-search__input')[0].clear()
            except Exception as e:
                print('erreur effacer champ recherche')
                print(f"#Eret001\nUne erreur est survenue : {e}")
            else:
                temps_reg = 1
                #print("champ effacé")
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'scoreboard-nav__select')))
            except:
                error = 1
                print("error 77")
            else:

                select_form = driver.find_elements(By.CLASS_NAME,'scoreboard-nav__select')
                try:
                    select_form[0].click()
                    print('ouverture liste deroulante')
                except:
                    fenetre_validation = 0

                    while fenetre_validation == 0 and tentative < 2:
                        tentative = tentative + 1
                        try:
                            print('Vérification de validation')
                            element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located(
                                    (By.CLASS_NAME,
                                     'c-coupon-modal__wrapper'))
                            )  ###vérifaction d'affichage pop up validation
                        except:
                            print('pas de fentre validation, vérification erreur')
                            try:
                                element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                    (By.XPATH, '//*[@id="swal2-title"]')))
                            except:
                                print('pas de fenetre alerte 2')
                            else:
                                alerttexte = driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text
                                print('alert : ' + alerttexte)
                                if len(re.findall("Maximum",
                                                  driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text)) > 0:
                                    error = 1
                                    driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                elif len(re.findall("modifiées",
                                                    driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text)) > 0:
                                    error = 1
                                    driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                elif len(re.findall("déjà",
                                                    driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text)) > 0:
                                    driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                    print("Paris déjà placé")
                                    delete_bet(driver, error)
                                    return True
                                else:
                                    driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                        else:
                            validation = driver.find_elements(By.CLASS_NAME,
                                                              'c-coupon-modal__title')[
                                0].text
                            if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                print('PARI VALIDÉ!')

                                try:
                                    element = WebDriverWait(driver, 3).until(
                                        EC.presence_of_element_located(
                                            (By.CLASS_NAME,
                                             'o-btn-group__item'))
                                    )
                                except:
                                    print('impossible de cliqué sur ok')
                                else:
                                    modal_wrapper = driver.find_elements(By.CLASS_NAME, 'c-coupon-modal__wrapper')[0]
                                    modal_wrapper.find_elements(By.TAG_NAME,
                                                                'button')[0].click()
                                    fenetre_validation = 1
                                    validation = 1
                                    return True
                time.sleep(2)

        if error == 0:
            select_form_tps_regl = driver.find_elements(By.CLASS_NAME,'multiselect__element')
            if len(select_form_tps_regl) > 0:
                for select_option in select_form_tps_regl:
                    if len(re.findall("Temps réglementaire", select_option.text)) > 0:
                        # print(select_option.text)
                        try:
                            select_option.click()
                        except:
                            print('error tps regl 5555')
                        else:
                            time.sleep(2)
                            # print("click select_form_tps_regl")
                            temps_reg = 1
                            break
            else:
                error = 1

def get_if_game_start(driver,saved_score):
    #driver.switch_to.window(driver.window_handles[0])
    gamestart = 0
    error = 0
    printext = 0
    while (gamestart <= 0 and error == 0):
        driver.switch_to.window(driver.window_handles[0])
        score_actuel = get_score_actuel(driver,saved_score)
        saved_score = saved_score
        if score_actuel == '0:0':
            if score_actuel == False:
                error = 1
            if printext == 0:
                print('GAME NOT START')
                printext = 1
                if verification_page_de_match(driver)!=True:
                    error = 1
            time.sleep(1)#attente 20 sec que le jeu commence
            # END GET SCORE
        elif score_actuel == '15:0' or score_actuel == '0:15' or score_actuel == '15:15' or score_actuel == '30:15' or score_actuel == '15:30' or score_actuel == '40:15' or score_actuel == '15:40' or score_actuel == '0:30' or score_actuel == '30:0' or score_actuel == '30:30' or score_actuel == '30:40' or score_actuel == '40:30' or score_actuel == '0:40' or score_actuel == '40:0' or score_actuel == '40:40' or score_actuel == 'A:40' or score_actuel == '40:A':
            print('GAME START')
            gamestart = 1
        else:
            gamestart = 0
            if verification_page_de_match(driver) != True:
                error = 1

def get_if_game_start_scnd(driver,saved_score):
    #driver.switch_to.window(driver.window_handles[0])
    gamestart = 0
    error = 0
    printext = 0
    while (gamestart <= 0 and error == 0):
        #driver.switch_to.window(driver.window_handles[0])
        score_actuel = get_score_actuel(driver,saved_score)
        saved_score = score_actuel
        if score_actuel == '0:0' or score_actuel == '15:0' or score_actuel == '0:15' or score_actuel == '15:15' or score_actuel == '30:15' or score_actuel == '15:30' or  score_actuel == '30:30':
            print('GAME START')
            gamestart = 1
        else:
            gamestart = 0
            if verification_page_de_match(driver) != True:
                error = 1
            if printext ==0:
                print('wait FOR GAME START')
                printext = 1

def get_players_name(driver):
    print('c-scoreboard-team')

    players = driver.find_elements(By.CLASS_NAME,'c-scoreboard-team')
    print(str(len(players)))
    players_name=[]
    for player in players:
        name = player.find_element(By.CLASS_NAME, 'c-tablo-container__text').text
        print('getname : '+name)
        name = name.split('(')[0]
        name = name.strip()
        print(name)
        players_name.append(name)
    return players_name



def selection_des_paris_30_40_du_set(driver,set):
    #driver.switch_to.window(driver.window_handles[0])
    print('recherche du champ déroulant...')
    selection = False
    tentative = 0
    clic = False
    while selection == False and tentative <6:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'scoreboard-nav__select'))
            )
        except Exception as e:
            print(f"#E0012\nUne erreur est survenue : {e}")
            print("ERROR : champ déroulant non trouvé")
            tentative = tentative +1
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav__select')
            try:
                select_form[0].click()
                time.sleep(3)
            except Exception as e:
                print(f"#E0013\nUne erreur est survenue : {e}")
                tentative = tentative+1
            else:
                print("ouverture du champ déroulant...")
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'multiselect__element'))
                    )
                except Exception as e:
                    print(f"#E0014\nUne erreur est survenue : {e}")
                    print("ERROR : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        print('Plusieurs liens trouvés....')
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_span = select_option.find_elements(By.CLASS_NAME,'multiselect__option')[0]
                                select_option_text = select_span.find_elements(By.TAG_NAME,'span')[0].get_attribute('title')
                            except Exception as e:
                                print(f"#E0015\nUne erreur est survenue : {e}")
                                print("no = select_option_text")
                                tentative = tentative+1
                            else:
                                if select_option_text.strip() == set:
                                    print('menu :' + set + ' trouvé in :' + select_option.text)
                                    try:
                                        select_option.click()
                                        time.sleep(1)
                                    except Exception as e:
                                        print(f"#E0015\nUne erreur est survenue : {e}")
                                        print("ERROR : clic impossible menu 1set")
                                        tentative = tentative + 1
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 10:
                                            try:
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].clear()
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].send_keys(
                                                    "Score du Jeu.")
                                                l = driver.find_elements(By.CLASS_NAME,
                                                                         'scoreboard-nav-items-search__input')[
                                                    0].get_attribute("value")

                                                if l == "Score du Jeu.":
                                                    paris = 1
                                                else:
                                                    tentative = tentative+1
                                                    time.sleep(1)
                                            except Exception as e:
                                                print(f"#E0016\nUne erreur est survenue : {e}")
                                                print("ERROR : impossible ecrire 'Paris'")
                                                if verification_page_de_match(driver) != True:
                                                    break
                                            else:
                                                selection = True
                                else:
                                    print('SET '+set+' non trouvé : error '+select_option_text)
                    time.sleep(2)
                time.sleep(2)
    return selection
def recherche_paris_40_30(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 40 30....')
    scoreboard_player = driver.find_elements(By.CLASS_NAME,'c-scoreboard-player-score__row')
    scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME,'c-scoreboard-player-score__heading')[0]
    first_player = scoreboard_player1.find_elements(By.CLASS_NAME,'c-scoreboard-player-score__ball')
    if len(first_player)>0:
        first_player = 2

        win_type = '15:40'
    else:
        first_player = 1
        win_type = '40:15'
    print('next player to win : ' + str(first_player) + ' ' + win_type)
    win_texte = '40-15'
    if_get_jeu = False
    clic = 0

    try:
        print('Recherche : Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte))
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]'))
        )

    except Exception as e:
        #print(f"#E0017\nUne erreur est survenue : {e}")
        print("Paris Jeu " + str(jeu) + " : 40-40 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 40-40 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]')
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(win_texte)
                jeu = int(list_of_newbet_type[0].split("jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(win_type)
                game1 = int(newbet_type1[0].split("Jeu ")[1].split(" ")[0])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(win_type)
                game2 = int(newbet_type2[0].split("Jeu ")[1].split(" ")[0])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                if game1 < game2:
                    jeu = game1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 40A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 40A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 40 recuperé")
                clic = 0
    return [clic, jeu,win_type]
def recherche_first_paris_40_30(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 40 30....')
    scoreboard_player = driver.find_elements(By.CLASS_NAME,'c-scoreboard-player-score__row')
    scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME,'c-scoreboard-player-score__heading')[0]
    first_player = scoreboard_player1.find_elements(By.CLASS_NAME,'c-scoreboard-player-score__ball')
    if len(first_player)>0:
        first_player = 1
        win_type = '40:15'

    else:
        first_player = 2
        win_type = '15:40'
    print('next player to win : '+str(first_player)+' '+win_type)
    win_texte = '40-15'
    if_get_jeu = False
    clic = 0

    try:
        print('Recherche : Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte))
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]'))
        )

    except Exception as e:
        #print(f"#E0017\nUne erreur est survenue : {e}")
        print("Paris Jeu " + str(jeu) + " : 40-40 - Oui NON TROUVÉ!")
        print("Vérificattion si autre jeu en cours...")
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]'))
            )
        except Exception as e:
            print('Aucun bouton paris 40-40 - Oui TROUVÉ!')
        else:
            list_of_newbet_type = driver.find_elements(By.XPATH,
                                                       '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]')
            if len(list_of_newbet_type) == 1:
                list_of_newbet_type = list_of_newbet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(win_texte)
                jeu = int(list_of_newbet_type[0].split("jeu ")[1])
                print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
            elif len(list_of_newbet_type) >= 2:
                print('PLUSIEURS JEUX TROUVÉS!')
                newbet_type1 = list_of_newbet_type[0].text
                newbet_type1 = newbet_type1.split(win_type)
                game1 = int(newbet_type1[0].split("Jeu ")[1].split(" ")[0])
                print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                newbet_type2 = list_of_newbet_type[1].text
                print(newbet_type2)
                newbet_type2 = newbet_type2.split(win_type)
                game2 = int(newbet_type2[0].split("Jeu ")[1].split(" ")[0])
                print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                print("vérification ordre de jeu")
                if game1 < game2:
                    jeu = game1
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
                else:
                    jeu = game2
                    print("Jeu actuel : " + str(jeu))
                    if_get_jeu = True
            else:
                print('ERROR: try get num game running')
    else:
        if_get_jeu = True

    if if_get_jeu == True:
        try:
            list_of_bet_type = driver.find_elements(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]')
        except Exception as e:
            print(f"#E0018\nUne erreur est survenue : {e}")
            print("btn 40A not reachable")
        else:
            if len(list_of_bet_type) > 0:
                print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                tentative = 0
                while clic == 0 and tentative < 5:
                    print('VERIFICATTION SI CLIQUABLE...')
                    try:
                        element = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]')))
                    except:
                        tentative = tentative + 1
                        print("btn 40A not clicable retry")
                        the_jeu = get_jeu_actuel(driver)
                        if jeu != the_jeu:
                            tentative = 99
                            print('jeu diff')


                    else:
                        try:
                            #list_of_bet_type[0].click()
                            driver.find_element(By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                first_player) + ' va gagner le Jeu ' + str(
                                                jeu) + ' ' + str(
                                                win_texte) + '")]').click()
                        except Exception as e:
                            print(f"#E0019\nUne erreur est survenue : {e}")
                            print('CLICK IMPOSSIBLE!')
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                            tentative = tentative + 1
                            time.sleep(1)
                        else:
                            try :
                                element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                )
                            except Exception as e:
                                print('Pas de paris affiché!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                clic = True

            else:
                print("pas de btn 40 recuperé")
                clic = 0
    return [clic, jeu,win_type]
