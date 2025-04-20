import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise


def ValidationDuParis(driver, nexbet=False):
    validation = False
    tentative = 0
    config.log('validation paris', 'info', False, 2)
    config.log_clear_line()
    current_game = config.jeu_actuel
    while not validation and tentative < 2:
        config.log('Vérification des paris validés')
        config.log_clear_line()
        config.log('        tentative', str(tentative))
        config.log_clear_line()

        # Vérification que le jeu actuel et le set actuel n'ont pas déjà été pariés
        if hasattr(config, 'validated_bet') and config.validated_bet is not None:
            current_game = getattr(config, 'jeu_actuel', None)
            current_set = getattr(config, 'set_actuel', None)
            if nexbet:
                current_game = float(current_game) + 1

            if (current_game is not None and current_set is not None and
                    config.validated_bet.get('jeu') == current_game and
                    config.validated_bet.get('set') == current_set):
                config.log(f"Ce jeu ({current_game}) et ce set ({current_set}) ont déjà été pariés. Annulation.")
                validation = True
                break  # Sortir de la boucle si le jeu et le set ont déjà été pariés
        config.log('boucle validation paris')
        config.log_clear_line()
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
            l = cpn_setting.get_attribute("value")
            config.log("mise insérée : " + str(l), 'info', False, 2)
        except Exception as e:
            config.log(e)
            tentative += 1
            config.log('erreur verification mise')
            break
        else:
            if str(l) == str(config.mise):
                sending_mise = 1
                config.log('RECHERCHE DU BOUTON PLACER UN PARIS', 'info', False, 2)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'coupon-buttons'))
                    )
                except Exception as e:
                    config.log(f"#E0021\nUne erreur est survenue : {e}")
                    config.log('zone de bouton non trouvé!')
                    tentative = tentative + 1
                    validation = ModalHandler(driver)
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
                        l = cpn_setting.get_attribute(
                            "value")
                        config.log("mise insérrer : " + str(l))
                    except Exception as e:
                        config.log(f"#E005689\nUne erreur est survenue : {e}")
                        tentative = tentative + 1
                        if ModalHandler(driver):
                            validation = True
                    else:
                        if str(l) == str(config.mise):
                            getbtn = driver.find_element(By.CLASS_NAME, 'coupon-buttons')
                            try:
                                getbtn.click()
                            except:
                                tentative = tentative + 1
                                if ModalHandler(driver):
                                    validation = True
                            else:
                                tentative = tentative + 1
                                preloader = 1
                                printtext = 0
                                while preloader == 1:
                                    try:
                                        WebDriverWait(driver, 3).until(EC.visibility_of_element_located(
                                            (By.CLASS_NAME, "coupon-main-tab__preloader")))
                                    except:
                                        config.log('        pas de loader')
                                        preloader = 0
                                    else:
                                        if printtext == 0:
                                            config.log('        loading...')
                                            printtext = 1

                                if ModalHandler(driver):
                                    validation = True
                        else:
                            PlacerMise(driver)
                            tentative = tentative + 1
            else:
                PlacerMise(driver)
                tentative = tentative + 1
    if validation:
        # Store bet information in validated_bet variable
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config.validated_bet = {
            'montant': config.mise,
            'jeu': current_game,
            'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
            'timestamp': current_timestamp
        }
        config.log(f'           {config.validated_bet}', 'info', True)
        config.perte = float(config.perte) + float(config.mise)
        config.wantwin = float(config.wantwin) + float(config.increment)
        # Calculate net profit based on stake, odds and losses
        config.netprofit = round(
            (float(config.mise) * float(config.cote)) - float(config.perte), 2)
        config.log(f'Potential Net profit: {config.netprofit}')
    return validation


def ValidationDuParis4030(driver, mise):
    # driver.switch_to.window(driver.window_handles[0])
    validation = False
    tentative = 0
    while not validation and tentative < 4:
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
            l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute("value")
            config.log("        mise insérrer valid : " + str(l))
        except:
            tentative += 1
            config.log('        erreur verification mise')
            break
        else:
            if str(l) == str(mise):
                sending_mise = 1
                config.log('        RECHERCHE DU BOUTON PLACER UN PARIS')
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'cpn-settings'))
                    )
                except Exception as e:
                    config.log(f"#E0021\nUne erreur est survenue : {e}")
                    config.log('        zone de bouton non trouvé!')
                    try:
                        # config.log('      Vérification de validation déjà faite')
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                 '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]'))
                        )  ###vérifaction d'affichage pop up validation
                    except Exception as e:
                        config.log(f"#E0023\nUne erreur est survenue : {e}")
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            config.log('        pas de fenetre alerte 0')
                        else:
                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                    else:
                        validation = driver.find_elements(By.XPATH,
                                                          '//*[@id="modals-container"]/div/div/div[2]/div/div[1]/div[1]')[
                            0].text
                        if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                            txtlog = 'PARI VALIDÉ!'
                            config.log(txtlog)
                            config.log(txtlog)
                            try:
                                element = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button'))
                                )
                            except:
                                config.log('        impossible de cliqué sur ok')
                            else:
                                driver.find_element(By.XPATH,
                                                    '//*[@id="modals-container"]/div/div/div[2]/div/div[2]/div[1]/button').click()

                        else:
                            config.log('        impossible de récupérer les informations de validation')
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'cpn-info__division')[0]
                        l = cpn_setting.find_elements(By.CLASS_NAME, 'cpn-value-controls__input')[0].get_attribute(
                            "value")
                        config.log("        mise insérrer valid : " + str(l))
                    except Exception as e:
                        config.log(f"#E005689\nUne erreur est survenue : {e}")
                        try:
                            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                                (By.XPATH, '//*[@id="swal2-title"]')))
                        except:
                            config.log('        pas de fenetre alertte 1')
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
                                    WebDriverWait(driver, 3).until(
                                        EC.visibility_of_element_located((By.CLASS_NAME, "cpn-preloader")))
                                except:
                                    txtlog = 'pas de loader'
                                    config.log(txtlog)
                                    config.log(txtlog)
                                    preloader = 0
                                else:
                                    if printtext == 0:
                                        txtlog = 'loading...'
                                        config.log(txtlog)
                                        config.log(txtlog)
                                        printtext = 1
                            fenetre_validation = 0
                            tentative = 1
                            while fenetre_validation == 0 and tentative < 2:
                                tentative = tentative + 1
                                try:
                                    config.log('        Vérification de validation')
                                    element = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located(
                                            (By.CLASS_NAME,
                                             'c-coupon-modal__wrapper'))
                                    )  ###vérifaction d'affichage pop up validation
                                except:
                                    config.log('        pas de fentre validation, vérification erreur')
                                    try:
                                        element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                            (By.XPATH, '//*[@id="swal2-title"]')))
                                    except:
                                        config.log('        pas de fenetre alerte 2')
                                    else:
                                        alerttexte = driver.find_elements(By.CLASS_NAME, 'swal2-content')[0].text
                                        config.log('        alert : ' + alerttexte)
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
                                            config.log("        Paris déjà placé")
                                            DeleteBet(driver)
                                            return True
                                        else:
                                            driver.find_element(By.CLASS_NAME, 'swal2-confirm').click()
                                else:
                                    validation = driver.find_elements(By.CLASS_NAME,
                                                                      'c-coupon-modal__title')[
                                        0].text
                                    if re.search("VOTRE PARI EST ACCEPTÉ !", validation) != None:
                                        txtlog = 'PARI VALIDÉ!'
                                        config.log(txtlog)
                                        config.log(txtlog)

                                        try:
                                            element = WebDriverWait(driver, 3).until(
                                                EC.presence_of_element_located(
                                                    (By.CLASS_NAME,
                                                     'o-btn-group__item'))
                                            )
                                        except:
                                            config.log('        impossible de cliqué sur ok')
                                        else:
                                            modal_wrapper = \
                                                driver.find_elements(By.CLASS_NAME, 'c-coupon-modal__wrapper')[0]
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
