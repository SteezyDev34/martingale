from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

from Functions.DeleteBet import DeleteBet
from Functions.PlacerMise import PlacerMise
from Functions.ModalHandler import ModalHandler
import config

def ValidationDuParis(driver):
    validation = False
    tentative = 0
    print('validation paris')
    while not validation and tentative < 2:
        print('Vérification des paris validés')
        print('tentative', str(tentative))
        
        # Vérification que le jeu actuel et le set actuel n'ont pas déjà été pariés
        if hasattr(config, 'validated_bet') and config.validated_bet is not None:
            current_game = getattr(config, 'jeu_actuel', None)
            current_set = getattr(config, 'set_actuel', None)
            
            if (current_game is not None and current_set is not None and 
                config.validated_bet.get('jeu') == current_game and
                config.validated_bet.get('set') == current_set):
                
                config.saveLog(f"Ce jeu ({current_game}) et ce set ({current_set}) ont déjà été pariés. Annulation.", 1, config.newmatch)
                validation = True
                break  # Sortir de la boucle si le jeu et le set ont déjà été pariés
        print('boucle validation paris')
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
            l = cpn_setting.get_attribute("value")
            config.saveLog("mise insérée : " + str(l),1,config.newmatch)
        except Exception as e:
            print(e)
            tentative+=1
            config.saveLog('erreur verification mise',1,config.newmatch)
            break
        else:
            if str(l) == str(config.mise):
                sending_mise = 1
                config.saveLog('RECHERCHE DU BOUTON PLACER UN PARIS',1,config.newmatch)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'coupon-buttons'))
                    )
                except Exception as e:
                    config.saveLog(f"#E0021\nUne erreur est survenue : {e}", config.newmatch)
                    config.saveLog('zone de bouton non trouvé!',config.newmatch)
                    tentative = tentative + 1
                    validation = ModalHandler(driver)
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
                        l = cpn_setting.get_attribute(
                            "value")
                        config.saveLog("mise insérrer : " + str(l), config.newmatch)
                    except Exception as e:
                        config.saveLog(f"#E005689\nUne erreur est survenue : {e}", config.newmatch)
                        tentative = tentative + 1
                        validation = ModalHandler(driver)
                    else:
                        if str(l) == str(config.mise):
                            getbtn = driver.find_element(By.CLASS_NAME, 'coupon-buttons')
                            try:
                                getbtn.click()
                            except:
                                tentative = tentative + 1
                                validation = ModalHandler(driver)
                            else:
                                tentative = tentative + 1
                                preloader = 1
                                printtext = 0
                                while preloader == 1:
                                    try:
                                        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME,"coupon-main-tab__preloader")))
                                    except:
                                        config.saveLog('pas de loader',1,config.newmatch)
                                        preloader = 0
                                    else:
                                        if printtext ==0:
                                            config.saveLog('loading...',1,config.newmatch)
                                            printtext = 1

                                validation = ModalHandler(driver)
                        else:
                            PlacerMise(driver)
                            tentative = tentative + 1
            else:
                PlacerMise(driver)
                tentative = tentative + 1
    return validation

def ValidationDuParis4030(driver,mise):
    #driver.switch_to.window(driver.window_handles[0])
    validation = False
    tentative = 0
    while not validation and tentative < 4:
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
            l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute("value")
            config.saveLog("mise insérrer valid : " + str(l),config.newmatch)
        except:
            tentative+=1
            config.saveLog('erreur verification mise',config.newmatch)
            break
        else:
            if str(l) == str(mise):
                sending_mise = 1
                config.saveLog('RECHERCHE DU BOUTON PLACER UN PARIS',config.newmatch)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'cpn-settings'))
                    )
                except Exception as e:
                    config.saveLog(f"#E0021\nUne erreur est survenue : {e}",config.newmatch)
                    config.saveLog('zone de bouton non trouvé!',config.newmatch)
                    try:
                        # print('Vérification de validation déjà faite')
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]'))
                        )  ###vérifaction d'affichage pop up validation
                    except Exception as e:
                        config.saveLog(f"#E0023\nUne erreur est survenue : {e}",config.newmatch)
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            config.saveLog('pas de fenetre alerte 0',config.newmatch)
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        validation = driver.find_elements(By.XPATH,
                                                          '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]')[
                            0].text
                        if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                            txtlog = 'PARI VALIDÉ!'
                            print(txtlog)
                            config.saveLog(txtlog,config.newmatch)
                            try:
                                element = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button'))
                                )
                            except:
                                config.saveLog('impossible de cliqué sur ok',config.newmatch)
                            else:
                                driver.find_element(By.XPATH,
                                                    '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button').click()

                        else:
                            config.saveLog('impossible de récupérer les informations de validation',config.newmatch)
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
                        l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute(
                            "value")
                        config.saveLog("mise insérrer valid : " + str(l),config.newmatch)
                    except Exception as e:
                        config.saveLog(f"#E005689\nUne erreur est survenue : {e}",config.newmatch)
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            config.saveLog('pas de fenetre alertte 1',config.newmatch)
                            PlacerMise(driver)
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
                                    WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME,"cpn-preloader")))
                                except:
                                    txtlog = 'pas de loader'
                                    print(txtlog)
                                    config.saveLog(txtlog,config.newmatch)
                                    preloader = 0
                                else:
                                    if printtext ==0:
                                        txtlog = 'loading...'
                                        print(txtlog)
                                        config.saveLog(txtlog,config.newmatch)
                                        printtext = 1
                            fenetre_validation = 0
                            tentative = 1
                            while fenetre_validation == 0 and tentative <2:
                                tentative=tentative +1
                                try:
                                    config.saveLog('Vérification de validation',config.newmatch)
                                    element = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located(
                                            (By.CLASS_NAME,
                                             'c-coupon-modal__wrapper'))
                                    )  ###vérifaction d'affichage pop up validation
                                except:
                                    config.saveLog('pas de fentre validation, vérification erreur',config.newmatch)
                                    try:
                                        element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                            (By.XPATH, '//*[@id="swal2-title"]')))
                                    except:
                                        config.saveLog('pas de fenetre alerte 2',config.newmatch)
                                    else:
                                        alerttexte = driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text
                                        config.saveLog('alert : '+alerttexte,config.newmatch)
                                        if len(re.findall("Maximum",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            error=1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("modifiées",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            error=1
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                        elif len(re.findall("déjà",driver.find_elements(By.CLASS_NAME,'swal2-content')[0].text)) >0:
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                            config.saveLog("Paris déjà placé",config.newmatch)
                                            DeleteBet(driver)
                                            return True
                                        else:
                                            driver.find_element(By.CLASS_NAME,'swal2-confirm').click()
                                else:
                                    validation = driver.find_elements(By.CLASS_NAME,
                                        'c-coupon-modal__title')[
                                        0].text
                                    if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                        txtlog = 'PARI VALIDÉ!'
                                        print(txtlog)
                                        config.saveLog(txtlog,config.newmatch)

                                        try:
                                            element = WebDriverWait(driver, 3).until(
                                                EC.presence_of_element_located(
                                                    (By.CLASS_NAME,
                                                     'o-btn-group__item'))
                                            )
                                        except:
                                            config.saveLog('impossible de cliqué sur ok',config.newmatch)
                                        else:
                                            modal_wrapper = driver.find_elements(By.CLASS_NAME,'c-coupon-modal__wrapper')[0]
                                            modal_wrapper.find_elements(By.TAG_NAME,
                                                'button')[0].click()
                                            fenetre_validation = 1
                                            validation = 1
                                            return True
                        else:
                            PlacerMise(driver)
                            tentative = tentative + 1
            else:
                PlacerMise(driver)
                tentative = tentative + 1
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    ValidationDuParis(driver)
