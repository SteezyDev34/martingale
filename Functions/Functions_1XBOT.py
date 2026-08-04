from Features.LoadCoupon import LoadCoupon
from Features.SendMise import Sendmise
from Features.ValidateBet import ValidationDuParis, HandleValidationModal, GetModalData

error = 0

from datetime import datetime
import time

import Functions_telegram
from Features.Load1xbet import load_1xbet

import re
from datetime import date

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Features.GetCapital import get_total_capital
import pygsheets

global gc

##TELEGRAM GROUP IDS
auxo_bot_id = "820171667"
analytix_bot_id = '-1001773264381'
group_AuxoAnalytix = '-1001672474839'
channel_com2_bot = '-1001699523977'
groupID = "820171667"
# groupID = "-540044043"
alertGroup = "-1001848207367"
freeGroup = "-1001315247334"
"""auxoInvestGroup = "-540044043"""
auxoInvestGroup = "-1001441208953"
##END

try:
    gc = pygsheets.authorize(service_file='auxobetting-7a3cf182ba61.json')
except Exception as e:
    Functions_telegram.send_telegram(alertGroup, f"#E0008\nUne erreur est survenue : {e}")
    print(f"#E0008\nUne erreur est survenue : {e}")


# FNCTION RECUPERATION DU CAPITAL
def get_capital():
    try:
        file_capital = open("capital.txt", "r")
        capital = float(file_capital.read())
        print("Récupération du capital : ", capital)
        file_capital.close()
        return str(capital)
    except Exception as e:
        Functions_telegram.send_telegram(alertGroup, f"#E0009\nUne erreur est survenue : {e}")
        print(f"#E0009\nUne erreur est survenue : {e}")
        return False


# END

##FUNCTION GET CURRENT TIME
def get_current_time():
    try:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        return current_time
    except Exception as e:
        Functions_telegram.send_telegram(alertGroup, f"#E0010\nUne erreur est survenue : {e}")
        print(f"#E0010\nUne erreur est survenue : {e}")
        return False


##END

##FUNCTION SAVE LOG
def log_save(actions):
    try:
        the_current_time = get_current_time()
        logs = open("logs.txt", "a")
        logs.write('\n' + the_current_time + ' : ' + str(actions) + ',')
        logs.close()
        print('log saved')
    except Exception as e:
        Functions_telegram.send_telegram(alertGroup, f"#E0011\nUne erreur est survenue : {e}")
        print(f"#E0011\nUne erreur est survenue : {e}")
        return False


##END

##FUNCTION CONNECT TO 1XBET
def connect_to_1xbet(driver):
    try:
        login1xbet = 1  # 1 dea connecté
        while login1xbet == 0:
            # OUVERTURE DE 1XBET
            driver.switch_to.window(driver.window_handles[0])
            driver.get("https://1xbet.com/fr/")
            print("Ouverture de https://1xbet.com/fr/ ATTENTE DE CONNEXION")
            try:
                # ATTENTE DE L'AFFICHAGE DU BOUTON DE CONNEXION PAR QR CODE
                element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="loc_info"]/div[3]/button'))
                )
            except:
                try:
                    # SI LE BOUTON NE S'AFFICHE PAS ON VÉRIFIE SI L4ON EST PAS DÉJÀ CONNECTÉ
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//*[@id="user-money"]/div/div[1]/a/div'))
                    )
                except:
                    # EN CAS D'EREUR LA BOUCLE REDÉMARRE
                    print('Erreur de connexion à 1xbet')
                else:
                    login1xbet = 1
                    print("Vous êtes déjà connecté à 1xbet!")
            else:
                # ON AFFICHE LE QR CODE DE CONNEXION
                driver.find_elements(By.XPATH, '//*[@id="loc_info"]/div[3]/button')[0].click()
                input('TAPER ENTREE QUAND VOUS ETES CONNECTÉ!')
                login1xbet = 1
                log_save("CONNECTE A 1XBET!")
                print("CONNECTE A 1XBET!")
                driver.get("https://1xbet.com/fr/")
            # OUVERTURE DE 1XBET
    except Exception as e:
        Functions_telegram.send_telegram(alertGroup, f"#E0012\nUne erreur est survenue : {e}")
        print(f"#E0012\nUne erreur est survenue : {e}")
        driver.get("https://1xbet.com/fr/")
        print("nouvelle tentative")
        return False


##END
##FUNCTION RELOAD 1XBET
def load_lolly(driver):
    driver.get('https://lolly-bet99.com/fr/sportsbook')
    tentative = 0
    pageload = False
    while pageload == False:
        # GET IF LOGO IS VISIBLE
        try:
            driver.find_element(By.CLASS_NAME, 'sb-betslip-header')
            pageload = True
        except Exception as e:
            Functions_telegram.send_telegram(alertGroup, f"#E0013\nUne erreur est survenue : {e}")
            print(f"#E0013\nUne erreur est survenue : {e}")
            tentative = tentative + 1
            if tentative > 10:
                Functions_telegram.send_telegram(auxo_bot_id, "Erreur de chargement de 1Xbet")
                print('Erreur de chargement de 1Xbet')
                pageload = 0  # STOP LOOP
                return False
            else:
                driver.get("https://lolly-bet99.com/fr")
                print("nouvelle tentative")
        else:
            return True


##END

# FUNCTION SUPPRESSION  BET EN COURS


def del_bet_lolly(driver, error=0):
    driver.switch_to.window(driver.window_handles[-1])
    iframe = driver.find_element(By.ID, "bcsportsbookiframe")
    driver.switch_to.frame(iframe)
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "sb-betslip-item-v2__delete"))
        )
        time.sleep(2)
        elements = driver.find_elements(By.CLASS_NAME, 'sb-betslip-item-v2__delete')
    except Exception as e:
        print(f"lolly: cross no found : {e}")
        return False
    else:
        for element in elements:
            element.click()
        driver.switch_to.default_content()
        return 0


##FUNCTION LOAD COUPON CODE IN FIELD
def load_coupon_code_lolly(driver, code):
    error = 1
    errorMessage = "uy"
    driver.switch_to.window(driver.window_handles[-1])
    iframe = driver.find_element(By.ID, "bcsportsbookiframe")
    driver.switch_to.frame(iframe)
    try:
        # GET IF BUTTON LOAD CODE IS VISIBLE
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.TAG_NAME, 'sportsbook-dynamic-component'))
        )
        print('try')
    except Exception as e:
        Functions_telegram.send_telegram(alertGroup, "Impossible d\'afficher le champ le code  : ")
        Functions_telegram.send_telegram(alertGroup, str(code[0]))
        print("Impossible d\'afficher le champ le code: {e}")
        error = 1

    else:
        # OPEN TEXT FIELD
        try:
            driver.find_element(By.TAG_NAME, 'sportsbook-dynamic-component').click()
            print('click it')
        except Exception as e:
            Functions_telegram.send_telegram(alertGroup, f"#E0014\nUne erreur est survenue : {e}")
            print(f"#E0014\nUne erreur est survenue : {e}")
            error = 1
        else:
            try:
                # GET IF FIELD IS VISIBLE
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'sb-bet-slip-loader__input'))
                )
            except:
                Functions_telegram.send_telegram(alertGroup, "Impossible de charger le code : ")
                Functions_telegram.send_telegram(alertGroup, str(code[0]))
                error = 1
            else:
                # PUT CODE INDISE FIELD
                try:
                    driver.find_element(By.CLASS_NAME, "sb-bet-slip-loader__input").find_element(By.TAG_NAME,
                                                                                                 'input').clear()
                    driver.find_element(By.CLASS_NAME, "sb-bet-slip-loader__input").find_element(By.TAG_NAME,
                                                                                                 'input').send_keys(
                        code[0])
                    print("Coupon inséré avec succès!")
                    tentative = 0
                    couponload = 0
                    while couponload == 0 and tentative < 10:
                        tentative = tentative + 1
                        try:
                            # GET IF LOAD BUTTON IS VISIBLE
                            element = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located(
                                    (By.CLASS_NAME,
                                     "sb-bet-slip-loader__button_load"))
                            )
                        except:
                            Functions_telegram.send_telegram(alertGroup, "Impossible de charger le code (btn) : ")
                            print("le bouton n'est pas affiché")
                            error = 1
                        else:
                            # CLICK ON LOAD BUTTON
                            driver.execute_script("arguments[0].click();",
                                                  driver.find_elements(By.CLASS_NAME,
                                                                       "sb-bet-slip-loader__button_load")[0])
                            try:
                                # GET IF BET LIST IS VISIBLE
                                element = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.CLASS_NAME, 'cpn-bets-list'))
                                )
                            except:
                                print('Erreur de chargement du code')
                                try:
                                    element = WebDriverWait(driver, 3).until(
                                        EC.presence_of_element_located(
                                            (By.XPATH,
                                             '//*[@id="swal2-content"]'))
                                    )
                                    error = 1
                                except:
                                    print("Aucun message erreur")
                                else:
                                    errorMessage = driver.find_elements(By.XPATH, '//*[@id="swal2-content"]')[0].text
                                    print(errorMessage)
                                    if len(re.findall(
                                            "Une erreur s'est produite lors du téléchargement du coupon de pari",
                                            errorMessage)) > 0:
                                        print("Erreur: " + errorMessage)
                                        driver.execute_script("arguments[0].click();",
                                                              driver.find_elements(By.CLASS_NAME, 'swal2-confirm')[0])
                                        error = 1
                                    elif len(re.findall("Events in the downloaded bet slip have finished",
                                                        errorMessage)) > 0:
                                        print("Erreur dead: " + errorMessage)
                                        driver.execute_script("arguments[0].click();",
                                                              driver.find_elements(By.CLASS_NAME, 'swal2-confirm')[0])
                                        error = 1
                                        tentative = 10
                                        couponload = 1
                                        print("tet", tentative)
                                        break
                                    elif len(re.findall(
                                            "Un pari a déjà été placé sur cet événement. Voulez-vous placer un nouveau pari ?",
                                            errorMessage)) > 0:
                                        print("Erreur dead: " + errorMessage)
                                        driver.execute_script("arguments[0].click();",
                                                              driver.find_elements(By.CLASS_NAME, 'swal2-confirm')[0])
                                        error = 1
                                        tentative = 10
                                        couponload = 1
                                        print("tet", tentative)
                                        break
                                    elif len(re.findall("Code incorrect", errorMessage)) > 0:
                                        print("Erreur dead: " + errorMessage)
                                        driver.execute_script("arguments[0].click();",
                                                              driver.find_elements(By.CLASS_NAME, 'swal2-confirm')[0])
                                        error = 1
                                        tentative = 10
                                        couponload = 1
                                        print("tet", tentative)
                                    elif len(re.findall("Les évènements du coupon de pari téléchargé sont terminés",
                                                        errorMessage)) > 0:
                                        print("Erreur dead: " + errorMessage)
                                        driver.execute_script("arguments[0].click();",
                                                              driver.find_elements(By.CLASS_NAME, 'swal2-confirm')[0])
                                        error = 1
                                        tentative = 10
                                        couponload = 1
                                        print("tet", tentative)

                                    else:
                                        print("Erreur: " + errorMessage)
                                        Functions_telegram.send_telegram(alertGroup, errorMessage)
                                        Functions_telegram.send_telegram(alertGroup, str(code[0]))
                                        error = 1
                            else:
                                print("coupon chargé")
                                couponload = 1
                                error = 0
                except Exception as e:
                    Functions_telegram.send_telegram(alertGroup, f"#E0016\nUne erreur est survenue : {e}")
                    print(f"#E0016\nUne erreur est survenue : {e}")
                    driver.get("https://1xbet.com/fr/")
                    print("nouvelle tentative")
    if error == 1:
        return [False, errorMessage]
    else:
        return [True, errorMessage]


##END


##FUNCTION VALIDATE BET
def validate_bet_old(driver):
    result = 0
    error = 0
    tentative = 0
    btn_validation = 0
    while result == 0 and error == 0:
        try:
            print("vérification du bouton de validation")
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME,
                     'cpn-btns-group'))

            )
        except:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         '//*[@id="sports_right"]/div/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div/div/button'))

                )
            except:
                print("!!!Bouton de validation non trouvé!!!")
                tentative = tentative + 1
                if tentative > 10:
                    error = 1
                    Functions_telegram.send_telegram(auxo_bot_id,
                                                     "Impossible de valider le pari, tentative : " + str(tentative))
                    erreur = 1
                    break
            else:
                btn_validation = 2
        else:
            btn_validation = 1
        if btn_validation == 1:
            btn_place = driver.find_element(By.CLASS_NAME, "cpn-btns-group")
            driver.execute_script("arguments[0].click();",
                                  btn_place.find_element(By.CLASS_NAME, "cpn-btns-group__btn"))
        elif btn_validation == 2:
            driver.execute_script("arguments[0].click();",
                                  driver.find_elements(By.XPATH,
                                                       '//*[@id="sports_right"]/div/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div/div/button')[
                                      0])

        print("Bouton 2 de pari trouvé : VALIDATION DU PARI")
        try:
            print('Vérification de validation')
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]'))

            )
        except:
            try:
                element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'swal2-popup'))

                )
            except:

                print('impossible de récupérer les informations de validation 3')
                error = 1
                Functions_telegram.send_telegram(auxo_bot_id,
                                                 "Impossible de valider le pari 2 :  tentative : " + str(tentative))
                return False
                break
            else:
                swaltxt = driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text
                try:
                    driver.execute_script("arguments[0].click();",
                                          driver.find_elements(By.CLASS_NAME,
                                                               'swal2-confirm')[
                                              0])
                except:
                    print('impossible de récupérer les informations de validation 1')
                    error = 1
                    Functions_telegram.send_telegram(auxo_bot_id,
                                                     "Impossible de valider le pari 2 :  tentative : " + str(tentative))
                    return False
                    break
                else:
                    if swaltxt == "Events in the downloaded bet slip have finished":
                        break
                    elif swaltxt == "Vous n'avez pas suffisamment de fonds dans votre compte pour placer ce pari":
                        break

        else:
            validation = driver.find_elements(By.XPATH, '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]')[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                print('PARI VALIDÉ! : ' + validation)
                result = 1
                return True
            else:
                error = 1
                print('impossible de récupérer les informations de validation 2')
                print('INFOS PARI VALIDÉ! : ' + validation)
                Functions_telegram.send_telegram(auxo_bot_id, "Impossible de valider le pari : ")
                return False
    if error == 1:
        return False


def validate_bet(driver, mise):
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
                        put_mise(driver, mise)
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
                            put_mise(driver, mise)
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
                                    WebDriverWait(driver, 30).until(
                                        EC.visibility_of_element_located((By.CLASS_NAME, "cpn-preloader")))
                                except:
                                    print('pas de loader')
                                    preloader = 0
                                else:
                                    if printtext == 0:
                                        print('loading...')
                                        printtext = 1
                                        while preloader == 1:
                                            try:
                                                WebDriverWait(driver, 1).until(
                                                    EC.visibility_of_element_located((By.CLASS_NAME, "cpn-preloader")))
                                            except:
                                                print('pas de loader')
                                                preloader = 0
                                            else:
                                                printtext = 1
                            fenetre_validation = 0
                            tentative = 1
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
                                                          driver.find_elements(By.CLASS_NAME, 'swal2-content')[
                                                              0].text)) > 0:
                                            error = 1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("modifiées",
                                                            driver.find_elements(By.CLASS_NAME, 'swal2-content')[
                                                                0].text)) > 0:
                                            error = 1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("déjà",
                                                            driver.find_elements(By.CLASS_NAME, 'swal2-content')[
                                                                0].text)) > 0:
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                            print("Paris déjà placé")
                                            del_bet(driver, error)
                                            return True
                                        else:
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                else:
                                    validation = driver.find_elements(By.CLASS_NAME,
                                                                      'c-coupon-modal__title')[
                                        0].text
                                    if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                        print('PARI VALIDÉ!')

                                        '''try:
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
                                                'button')[0].click()'''
                                        fenetre_validation = 1
                                        validation = 1
                                        return True
                        else:
                            put_mise(driver, mise)
                            tentative = tentative + 1
            else:
                put_mise(driver, mise)
                tentative = tentative + 1


##END

##SAVE DATA FOR ANALYTIX
def save_data_to_gc(data):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('DATA FOR ANALYTIX')
    # select the sheet
    wk1 = sh[0]
    row = wk1.get_all_values()
    if len(row) == 1 and row[0] == ['', '', '', '', '', '', '', '']:
        wk1.update_row(1, data, col_offset=0)
    else:
        wk1.insert_rows(0, number=1, values=data, inherit=False)


##END

##FUNCTION ADD CODE TO LIST
def add_codes(code):
    codes = open("codes.txt", "a")
    codes.write('\n' + code + ',')
    codes.close()
    print("CODES ADDED  : " + code)


def delete_codes(code):
    used_codes = ""
    codes = open("codes.txt", "r")
    used_codes = codes.read()
    updates_used_codes = used_codes.replace('\n' + code + ',', '')
    codes.close()
    codes = open("codes.txt", "w")
    codes.write(updates_used_codes)
    codes.close()
    print("CODES UPDATED : " + updates_used_codes)


def check_codes(code):
    find = False
    fichier = open("codes.txt", "r")
    codes = fichier.read()
    fichier.close()
    if len(re.findall(code + ',', codes)) > 0:
        find = True
    return find
    print("CODES FOUND  : " + codes)


##END

# FUNCTION DE VERIFIFCATION
def get_bet_data(driver, code, mise):
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME,
                 'o-bet-box-list'))
        )
        data_sport = []
        data_league = []
        data_teams = []
        data_bet = []
        data_cote = []
    except:

        print("impossible de trouver les infos de paris")
        data_sport = "Autre sport"
        data_league = ""
    else:
        print("MODAL TROUVÉ...")

        bets_box_list = driver.find_element(By.CLASS_NAME, 'o-bet-box-list')  # BLOC DE LA LISTE DES PARIS
        bets_box_items = bets_box_list.find_elements(By.CLASS_NAME, 'o-bet-box-list__item')  # BLOC DE CHAQUE PARIS

        for bet_box_item in bets_box_items:
            # RECHERCHE DES INFOS DE LIGUES
            bet_box_header = bet_box_item.find_element(By.CLASS_NAME, 'c-bet-box__header')
            bet_ligue_text = bet_box_item.find_element(By.CLASS_NAME,
                                                       'c-bet-box__text').text  # BLOC DES INFOS DE LIGUE DE CHAQUE PARIS
            data_sport.append(verif_sport(bet_ligue_text))
            data_league.append(verif_league(bet_ligue_text))
            # END RECHERCHE DES INFOS DE LIGUES

            bet_box_content = bet_box_item.find_element(By.CLASS_NAME, 'c-bet-box__content')

            # RECHERCHE DES INFOS D'ÉQUIPES
            bet_box_teams = bet_box_content.find_element(By.CLASS_NAME, 'cpn-bet-teams')
            bet_teams_items = bet_box_teams.find_elements(By.CLASS_NAME, 'cpn-bet-teams__item')
            bet_teams = []
            for bet_teams_item in bet_teams_items:
                team_item_text = bet_teams_item.find_element(By.CLASS_NAME, 'cpn-bet-team__title').text
                bet_teams.append(team_item_text.strip())
            bet_teams = ' - '.join(bet_teams)
            data_teams.append(bet_teams)
            # END RECHERCHE DES INFOS D'ÉQUIPES

            # RECHERCHE DES INFOS DE BET
            bet_box_market = bet_box_content.find_element(By.CLASS_NAME, 'c-bet-box__market').text.strip()
            data_bet.append(bet_box_market)
            # END RECHERCHE DES INFOS DE BET

            # RECHERCHE DES INFOS DE COTE
            bet_box_odd = bet_box_content.find_element(By.CLASS_NAME, 'c-bet-box__bet').text.strip()
            data_cote.append(bet_box_odd)
            # END RECHERCHE DES INFOS DE COTE
        data_league = ' | '.join(data_league)
        print(data_league)
        data_sport = ' | '.join(data_sport)
        print(data_sport)
        data_teams = ' | '.join(data_teams)
        print(data_teams)
        data_bet = ' | '.join(data_bet)
        print(data_bet)
        data_cote_global = 1
        for cote in data_cote:
            data_cote_global = data_cote_global * float(cote)
        data_cote_global = round(data_cote_global, 3)
        data_cote = ' | '.join(data_cote)
        print(data_cote)
        print(data_cote_global)

    ###CONVERTION INTITULE
    root_data_bet = data_bet
    data_bet = convert_intitule1xbet(data_sport, data_teams, data_bet)
    today = date.today()
    # dd/mm/YY
    d1 = today.strftime("%d/%m/%Y")
    data = [data_sport, data_league, data_teams, root_data_bet, data_bet, data_cote, data_cote_global, code, mise, d1]
    print(data)
    return data


def get_bet_data_old(driver, code, mise):
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[1]'))
        )
        data_sport = []
        data_league = []
    except:

        print("impossible de trouver les infos de paris")
        data_sport = "Autre sport"
        data_league = ""
    else:
        ligues = driver.find_elements(By.XPATH,
                                      '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[1]')
        print('len of ligues : ' + str(len(ligues)))
        for ligue in ligues:
            data_header = ligue.text
            data_sport.append(verif_sport(data_header))
            data_league.append(verif_league(data_header))
        data_league = ' | '.join(data_league)
        data_sport = ' | '.join(data_sport)
    ## RECHERCHE DES EQUIPES ET BET
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div[2]'))
        )
    except:
        print("impossible de trouver les infos de paris")
        data_team = "X"
    else:
        print('test1')
        data_team = driver.find_element(By.CLASS_NAME, 'c-coupon-modal__content')
        bet_list = data_team.find_elements(By.CLASS_NAME, 'o-bet-box-list__item')
        get_data_team = []
        data_bet = []
        print('llen bet list : ' + str(len(bet_list)))
        if len(bet_list) > 1:
            for bet_info in bet_list:
                bet_info = bet_info.find_element(By.CLASS_NAME, 'c-bet-box__content')
                print('test3')
                if len(bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')) < 2:
                    print('len box contt : ' + str(len(bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name'))))
                    data_team1 = bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[0].text
                    data_bet.append(bet_info.find_element(By.CLASS_NAME, 'c-bet-box__market').text)
                    get_data_team.append(data_team1)
                else:
                    print('len box contt : ' + str(len(bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name'))))
                    data_team1 = bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[0].text
                    data_team2 = bet_info.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[1].text
                    print(data_team2)
                    intitule = bet_info.find_element(By.CLASS_NAME, 'c-bet-box__market').text
                    print(intitule)
                    data_bet.append(intitule)
                    get_data_team.append(data_team1 + ' - ' + data_team2)
            get_data_team = ' | '.join(get_data_team)
            data_bet = ' | '.join(data_bet)
            print(data_bet)
        else:
            data_team = driver.find_element(By.CLASS_NAME, 'c-coupon-modal__content')
            data_team = data_team.find_element(By.CLASS_NAME, 'c-bet-box__content')
            if len(data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')) < 2:
                print('len box contt : ' + str(len(data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name'))))
                data_team1 = data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[0].text
                data_bet = data_team.find_element(By.CLASS_NAME, 'c-bet-box__market').text
                get_data_team = data_team1
            else:
                print('len box contt : ' + str(len(data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name'))))
                data_team1 = data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[0].text
                data_team2 = data_team.find_elements(By.CLASS_NAME, 'cpn-bet-team__name')[1].text
                data_bet = data_team.find_element(By.CLASS_NAME, 'c-bet-box__market').text
                get_data_team = data_team1 + ' - ' + data_team2
    ##RECHERCHE DE LA COTE
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[3]'))
        )
    except:
        print("impossible de trouver les infos de paris")
        data_cote = "1"
    else:
        data_cote = driver.find_element(By.CLASS_NAME, 'c-coupon-modal')
        data_cote = data_cote.find_element(By.CLASS_NAME, 'coupon-grid__cell')
        print("coupon-grid__cell")
        data_cote = data_cote.find_elements(By.CLASS_NAME, 'coupon__text')[1].text
        print("coupon-grid__cell after")
    ##RECHERCHE TYPE DE PARIS
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[3]'))
        )
    except:
        print("impossible de trouver les infos de paris")
        data_type = "1"
    else:
        data_type = driver.find_element(By.CLASS_NAME, 'c-coupon-modal')
        data_type = data_type.find_elements(By.CLASS_NAME, 'coupon-grid__cell')[1]
        data_type = data_type.find_elements(By.CLASS_NAME, 'coupon__text')[1].text
        ##data_league = verif_league(data_header)
    ###CONVERTION INTITULE
    data_bet = convert_intitule1xbet(data_sport, get_data_team, data_bet)
    data = [data_sport, data_league, get_data_team, data_bet, data_cote, data_type, code, mise]
    print(data)
    return data


def verif_sport(data):
    betSport = "Autre sport"
    sportlist = ["Football Américain", "Football", "Hockey sur glace", "Basket-ball", "Baseball", "Tennis",
                 "Athlétisme", "Billard", "Boxe", "Course Automobile", "Courses hippiques", "Cyclisme",
                 "Formule 1", "Handball", "Hippisme", "Jeux Virtuels", "Judo", "Rugby", "Sports de Combat",
                 "Tennis de table", "Triathlon", "UFC", "Volleyball"]
    for sportitem in sportlist:
        if re.findall(sportitem, data):
            if sportitem == "Basket-ball":
                betSport = "Basketball"
            elif sportitem == "Football Américain":
                betSport = "Football US"
            elif sportitem == "Course Automobile":
                betSport = "Auto-Moto"
            elif sportitem == "Billard":
                betSport = "Snooker"
            elif sportitem == "Jeux Virtuels":
                betSport = "eSport"
            elif sportitem == "Baseball":
                betSport = False
            else:
                betSport = sportitem
    return betSport


def verif_league(data):
    data_league = "Autre LIGUE"
    sportlist1xbet = ["Football Américain", "Football", "Hockey sur glace", "Basket-ball", "Baseball", "Tennis",
                      "Athlétisme", "Billard", "Boxe", "Course Automobile", "Courses hippiques", "Cyclisme",
                      "Formule 1", "Handball", "Hippisme", "Jeux Virtuels", "Judo", "Rugby", "Sports de Combat",
                      "Tennis de table", "Triathlon", "UFC", "Volleyball"]
    for sportitem in sportlist1xbet:
        if re.findall(sportitem, data):
            data_league = data.split(sportitem)[1]  ##on supprime le sport de la chaine de caractere
            data_league = data_league.replace(".", " ")  ##on supprime les points de la chaine de caractere
            data_league = data_league.replace(" +", " ")  ##on rreemplace les doubles espaces
            data_league = data_league.strip()  ##on supprime les espaces à la fin et au début de la chaine de caractere
    return data_league


def convert_intitule1xbet(betSport, get_data_team, prono):
    x = get_data_team.split(' | ')
    y = prono.split(' | ')
    saved_prono = []
    i = 0
    for get_data_team in x:
        data_team = get_data_team.split(' - ')
        equipe1 = data_team[0]
        equipe2 = data_team[1]
        prono = y[i]
        i += 1
        if re.search("1x2", prono, re.IGNORECASE):
            pronotype = "RÉSULTATS"
            winset = ""
            if re.search("1 set", prono, re.IGNORECASE):
                winset = " le set 1"
            elif re.search(" 2 set", prono, re.IGNORECASE):
                winset = " le set 2"
            elif re.search("3 set", prono, re.IGNORECASE):
                winset = " le set 3"

            if re.search("v1", prono, re.IGNORECASE):
                if winset == '':
                    prono = 'Victoire ' + equipe1
                else:
                    prono = equipe1 + " gagne" + winset
            elif re.search("v2", prono, re.IGNORECASE):
                if winset == '':
                    prono = 'Victoire ' + equipe2
                else:
                    prono = equipe2 + " gagne" + winset
            elif re.search(rf"\b(?=\w){equipe1}\b(?!\w)", prono, re.IGNORECASE):
                if winset == '':
                    prono = 'Victoire ' + equipe1
                else:
                    prono = equipe1 + " gagne" + winset
            elif re.search(rf"\b(?=\w){equipe2}\b(?!\w)", prono, re.IGNORECASE):
                if winset == '':
                    prono = 'Victoire ' + equipe2
                else:
                    prono = equipe2 + " gagne" + winset
            else:
                print(prono)
                insensitive_hippo = re.compile(re.escape('1x2'), re.IGNORECASE)
                prono = insensitive_hippo.sub('', prono)
                insensitive_hippo = re.compile(re.escape('dans le temps réglementaire W'), re.IGNORECASE)
                prono = insensitive_hippo.sub('', prono)
                insensitive_hippo = re.compile(re.escape('dans le temps réglementaire W'), re.IGNORECASE)
                prono = insensitive_hippo.sub('(RT)', prono)
                prono = "Victoire " + prono
        elif len(re.findall("résultat \+ total", prono.lower())) >= 1:
            pronotype = "combo"
            point = ""
            if re.search("tennis", betSport, re.IGNORECASE):
                point = " jeux"
            elif re.search("football", betSport, re.IGNORECASE):
                point = " buts"
            elif re.search("basket", betSport, re.IGNORECASE):
                point = " paniers"
            if len(re.findall("equipe 1", prono.lower())) >= 1:
                if len(re.findall("va gagner et total", prono.lower())) >= 1:
                    prono = prono.lower().split("va gagner et total")[1]
                    verite = ''
                    if len(re.findall("non", prono.lower())) >= 1:
                        verite = ' : non'
                    prono = prono.lower().split(" - ")[0]
                    if len(re.findall(">", prono.lower())) >= 1:
                        prono = prono.lower().split("> ")[1]
                        prono = equipe1 + " et + de " + prono + point + verite
                    elif len(re.findall("<", prono.lower())) >= 1:
                        prono = prono.lower().split("< ")[1]
                        prono = equipe1 + " et - de " + prono + point + verite
            elif len(re.findall("equipe 2", prono.lower())) >= 1:
                if len(re.findall("va gagner et total", prono.lower())) >= 1:
                    prono = prono.lower().split("va gagner et total")[1]
                    verite = ''
                    if len(re.findall("non", prono.lower())) >= 1:
                        verite = ' : non'
                    prono = prono.lower().split(" - ")[0]
                    if len(re.findall(">", prono.lower())) >= 1:
                        prono = prono.lower().split("> ")[1]
                        prono = equipe2 + " et + de " + prono + point + verite
                    elif len(re.findall("<", prono.lower())) >= 1:
                        prono = prono.lower().split("< ")[1]
                        prono = equipe2 + " et - de " + prono + point + verite
            else:
                print(prono)
        elif len(re.findall("résultat et les deux equipes vont marquer", prono.lower())) >= 1 or len(
                re.findall("resultat et les deux equipes vont marquer", prono.lower())) >= 1:
            pronotype = "combo"

            if re.search("v1", prono, re.IGNORECASE) and len(re.findall("oui", prono.lower())) >= 1:
                prono = equipe1 + " gagne et les deux équipes marquent"
            elif re.search("v1", prono, re.IGNORECASE) and len(re.findall("non", prono.lower())) >= 1:
                prono = equipe1 + " gagne et les deux équipes ne marquent pas"
            elif re.search("v2", prono, re.IGNORECASE) and len(re.findall("oui", prono.lower())) >= 1:
                prono = equipe2 + " gagne et les deux équipes marquent"
            elif re.search("v2", prono, re.IGNORECASE) and len(re.findall("non", prono.lower())) >= 1:
                prono = equipe2 + "gagne et les deux équipes ne marquent pas"
            else:
                prono = prono.lower()
        elif len(re.findall("total", prono.lower())) >= 1:
            pronotype = "over/under"
            point = ""
            if re.search("tennis", betSport, re.IGNORECASE):
                point = " jeux"
            elif re.search("football", betSport, re.IGNORECASE):
                point = " buts"
            elif re.search("basket", betSport, re.IGNORECASE):
                point = " paniers"
            if re.search("total total", prono, re.IGNORECASE) or re.search("total asiatique total", prono,
                                                                           re.IGNORECASE):
                if re.search("plus de", prono, re.IGNORECASE):
                    prono = prono.lower().split("plus de ")[1]
                    if point == " buts" and prono == "0.5":
                        prono = "Au moins 1 but dans le match "
                    else:
                        prono = " + de " + prono + point
                elif re.search("moins de", prono, re.IGNORECASE):
                    prono = prono.lower().split("moins de ")[1]
                    if point == " buts" and prono == "0.5":
                        prono = "Score exact 0-0"
                    else:
                        prono = " - de " + prono + point
            elif re.search("total 1 total individuel 1", prono, re.IGNORECASE) or re.search(
                    "total asiatique d'équipe 1 total equipe 1", prono, re.IGNORECASE):
                if re.search("plus de", prono, re.IGNORECASE):
                    prono = prono.lower().split("plus de ")[1]
                    if point == " buts" and prono == "0.5":
                        prono = equipe1 + " marque dans le match "
                    else:
                        prono = equipe1 + " + de " + prono + point
                elif re.search("moins de", prono, re.IGNORECASE):
                    prono = prono.lower().split("moins de ")[1]
                    if point == " buts" and prono == "0.5":
                        prono = equipe1 + " ne marque pas dans le match "
                    else:
                        prono = equipe1 + " - de " + prono + point
            elif re.search("total 2 total individuel 2", prono, re.IGNORECASE) or re.search(
                    "total asiatique d'équipe 2 equipe 2 total", prono, re.IGNORECASE):
                if re.search("plus de", prono, re.IGNORECASE):
                    prono = prono.lower().split("plus de ")[1]
                    print(prono + ' ' + point)
                    if point == " buts" and prono == "0.5":
                        prono = equipe2 + " marque dans le match "
                    else:
                        prono = equipe2 + " + de " + prono + point
                elif re.search("moins de", prono, re.IGNORECASE):
                    prono = prono.lower().split("moins de ")[1]
                    if point == " buts" and prono == "0.5":
                        prono = equipe2 + " ne marque pas dans le match "
                    else:
                        prono = equipe2 + "- de " + prono + point
            else:
                print(prono)
                prono = prono.lower()
                prono = prono.split("total ")[1].strip()
        elif len(re.findall("score exact score exact", prono.lower())) >= 1:
            pronotype = "score exact"
            prono = prono.replace("score exact score exact", '').strip()
            prono = "Score exact " + prono
        elif len(re.findall("handicap", prono.lower())) >= 1:
            pronotype = "handicap"
            if len(re.findall("handicap 1", prono.lower())) >= 1:
                prono = prono.lower().replace("handicap 1", '').strip()
                prono = prono.lower().replace("handicap", '').strip()
                if prono == "(0)":
                    prono = equipe1 + " gagne (Remboursé si nul)"
                else:
                    prono = equipe1 + " H" + prono
            elif len(re.findall("handicap 2", prono.lower())) >= 1:
                prono = prono.lower().replace("handicap 2", '').strip()
                prono = prono.lower().replace("handicap", '').strip()
                if prono == "(0)":
                    prono = equipe2 + " gagne (Remboursé si nul)"
                else:
                    prono = equipe2 + " H" + prono
            elif len(re.findall("handicap des sets", prono.lower())) >= 1:
                pronotype = "handicap"
                if len(re.findall("1 handicap", prono.lower())) >= 1:
                    prono = equipe1 + " Gagne un set"
                elif len(re.findall("2 handicap", prono.lower())) >= 1:
                    prono = equipe2 + " Gagne un set"
                elif len(re.findall(equipe1, prono)) >= 1:
                    prono = equipe1 + " Gagne un set"
                elif len(re.findall(equipe2, prono)) >= 1:
                    prono = equipe2 + " Gagne un set"
                else:
                    print("test show " + prono)
                    prono = prono.lower().replace('handicap', '')
                    prono = prono.lower().replace('handicap', '')
            else:
                print(prono)
                prono = prono.lower()
                prono = prono.split("handicap")[1].strip()
        elif len(re.findall("les deux équipes vont marquer", prono.lower())) >= 1 or len(
                re.findall("les deux equipes vont marquer", prono.lower())) >= 1:
            pronotype = "BTTS"
            if len(re.findall("oui", prono.lower())) >= 1:
                prono = "Les deux équipes marquent"
            elif len(re.findall("non", prono.lower())) >= 1:
                prono = "Les deux équipes ne marquent pas"
            else:
                prono = prono.lower()
                prono = prono.split("Les deux équipes vont marquer")[1].strip()
        elif len(re.findall("qualifi", prono.lower())) >= 1:
            pronotype = "QUALIFICATION"
            if len(re.findall("equipe 1", prono.lower())) >= 1:
                prono = equipe1 + " se qualifie"
            elif len(re.findall("equipe 2", prono.lower())) >= 1:
                prono = equipe2 + " se qualifie"
            else:
                prono = prono.lower()
        elif len(re.findall("double chance", prono.lower())) >= 1:
            pronotype = "double chance"
            if len(re.findall("1x", prono.lower())) >= 1:
                prono = equipe1 + " ou nul"
            elif len(re.findall("2x", prono.lower())) >= 1:
                prono = equipe2 + " ou nul"
            else:
                prono = "Pas de match nul"
        elif len(re.findall("equipe gagne equipe", prono.lower())) >= 1:
            pronotype = "1x2"
            if len(re.findall("1", prono.lower())) >= 1:
                prono = equipe1
            elif len(re.findall("2", prono.lower())) >= 1:
                prono = equipe2
            else:
                prono = "Nul"
        elif len(re.findall("quel joueur va marquer le but", prono.lower())) >= 1:
            prono = prono.lower().split("joueur va marquer le but ")[1]
            prono = prono.lower().split(" va marquer")[0]
            pronotype = "BUTEUR"
            prono = prono.lower().title() + " buteur"
        else:
            print('inconnu')
        print(prono)
        saved_prono.append(prono)
    prono = ' | '.join(saved_prono)
    return prono


# END
def get_france_pronos_code(browser):
    print('Nouveau code sur le site')
    codeList = []
    success = 0
    tentative = 0
    while success == 0 and tentative < 3:
        tentative = tentative + 1
        print('tentattive : ' + str(tentative))
        browser.switch_to.window(browser.window_handles[0])
        browser.get("https://www.france-pronos.com/pronostics")
        time.sleep(5)
        try:
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "app-prono-preview"))
            )
        except:
            print('erreur de chargement de la page')
        else:
            print('find block')
            element = browser.find_element(By.CLASS_NAME, "section-4-container")

            sections = element.find_elements(By.CLASS_NAME, "app-prono-preview")
            for section in sections:
                success = 1
                print(section)
                try:
                    section.find_element(By.CLASS_NAME, "second-block")
                except:
                    print("code non trouvé")
                else:
                    secondblock = section.find_element(By.CLASS_NAME, "second-block")
                    try:
                        secondblock.find_element(By.CLASS_NAME, "code-container")
                    except:
                        print("code non trouvé")
                    else:
                        code_container = secondblock.find_element(By.CLASS_NAME, "code-container")
                        code = code_container.find_element(By.CLASS_NAME, "value").text
                        code = code.split('content_copy')[0]
                        code = ''.join(code.split('\n'))
                        if len(re.findall("[A-Z0-9]{5}", code)) == 1:
                            bankroll_results = secondblock.find_element(By.CLASS_NAME, "bankroll-results")
                            card_component = bankroll_results.find_element(By.CLASS_NAME, "card-component")
                            card_title = card_component.find_element(By.CLASS_NAME, "card-title").text
                            mise = card_title.split(' : ')[1]
                            txt = code + ' ' + mise
                            infos = Functions_telegram.extract_bet_infos_1xbet(txt)
                            if infos != False:
                                print('1xbet')
                                # ON RECUPERE LE CODE
                                codeList.append(infos)
                                success = 1
                            infos = Functions_telegram.extract_bet_infos_lolly(txt)
                            if infos != False:
                                print('lolly')
                                # ON RECUPERE LE CODE
                                codeList.append(infos)
                                success = 1
                            infos = Functions_telegram.extract_bet_infos_CZ(txt)
                            if infos != False:
                                print('cz')
                                # ON RECUPERE LE CODE
                                codeList.append(infos)
                                success = 1
                        else:
                            print("code non trouvé")
                    print("tet")
        print("end")
    return codeList
