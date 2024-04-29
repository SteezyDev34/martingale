from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

import DeleteBet
import PlacerMise


def main(driver, jeu,mise):
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
                        PlacerMise.main(driver, mise)
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
                            PlacerMise.main(driver, mise)
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
                                            DeleteBet.main(driver, error)
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
                            PlacerMise.main(driver, mise)
                            tentative = tentative + 1
            else:
                PlacerMise.main(driver,mise)
                tentative = tentative + 1