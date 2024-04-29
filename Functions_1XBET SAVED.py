from selenium.webdriver.common.by import By
import re
import time
from datetime import datetime

import GetSetActuel
import VerificationMatchTrouve
from config import matchlist_file_name

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


#MISE A JOUR DES MATCHS EFFECTUÉS
def update_mise_en_cours(action, values,mise_en_cours_file_name):
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
    driver.switch_to.window(driver.window_handles[0])
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










def get_jeu_actuel(driver):
    driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = GetSetActuel.main(driver, error, '')
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
    driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = GetSetActuel.main(driver, error, '')
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
    driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = GetSetActuel.main(driver, error, '')
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
    score_actuel = False
    get_score = 0
    error = 0
    saved = ''
    while get_score == 0 and error == 0:
        try:
            score_actuel = driver.find_element(By.CLASS_NAME,'c-scoreboard-score__content').text
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            error = 1
        else:
            get_score = 1
            score_actuel = score_actuel.replace("\n", "")
            if saved_score != score_actuel:
                print("Score actuel = "+score_actuel)
                print("saved actuel = " + saved_score)
            saved_score = score_actuel
    return score_actuel


def recherche_paris_40a(driver,jeu):
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 30 A....')
    if_get_jeu = False
    clic = 0
    try:
        element = WebDriverWait(driver, 10).until(
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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


def get_mise30a(driver,rattrape_perte,wantwin,perte):
    driver.switch_to.window(driver.window_handles[0])
    rattrape_perte = 0
    if rattrape_perte == 0:
        print('Pas de rattrapage, cote : 2.4')
        cote= 2.4
    else:
        print("Rattrapage, recuperation de la cote")
        try:
            cote = driver.find_elements(By.CLASS_NAME,
                'cpn-total__coef')[
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
    if mise < 0.2:
        mise = 0.2
    print("cote : " + str(cote))
    print("wantwin : " + str(wantwin))
    print("perte : " + str(perte))
    print("mise : " + str(mise))

    return [mise,cote]
def get_mise15a(driver,rattrape_perte,wantwin,perte):
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
    driver.switch_to.window(driver.window_handles[0])
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
                if VerificationMatchTrouve.fromUrl(driver,matchlist_file_name)!=True:
                    error = 1
            time.sleep(1)#attente 20 sec que le jeu commence
            # END GET SCORE
        elif score_actuel == '15:0' or score_actuel == '0:15' or score_actuel == '15:15' or score_actuel == '30:15' or score_actuel == '15:30' or score_actuel == '40:15' or score_actuel == '15:40' or score_actuel == '0:30' or score_actuel == '30:0' or score_actuel == '30:30' or score_actuel == '30:40' or score_actuel == '40:30' or score_actuel == '0:40' or score_actuel == '40:0' or score_actuel == '40:40' or score_actuel == 'A:40' or score_actuel == '40:A':
            print('GAME START')
            gamestart = 1
        else:
            gamestart = 0
            if VerificationMatchTrouve.fromUrl(driver,matchlist_file_name) != True:
                error = 1

def get_if_game_start_scnd(driver,saved_score):
    driver.switch_to.window(driver.window_handles[0])
    gamestart = 0
    error = 0
    printext = 0
    while (gamestart <= 0 and error == 0):
        driver.switch_to.window(driver.window_handles[0])
        score_actuel = get_score_actuel(driver,saved_score)
        saved_score = score_actuel
        if score_actuel == '0:0':
            print('GAME START')
            gamestart = 1
        else:
            gamestart = 0
            if VerificationMatchTrouve.fromUrl(driver,matchlist_file_name) != True:
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

