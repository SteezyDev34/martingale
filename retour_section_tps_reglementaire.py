import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import DeleteBet


def main(driver):
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
                element = WebDriverWait(driver, 5).until(
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
                                    DeleteBet.main(driver, error)
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
