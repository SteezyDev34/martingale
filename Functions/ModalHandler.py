from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

from Functions.DeleteBet import DeleteBet
from Functions.PlacerMise import PlacerMise
import config

def ModalHandler(driver):
    validation = False
    tentative = 0
    print('Gestion de Modal')
    fenetre_validation = 0
    while fenetre_validation == 0 and tentative < 2:
        tentative = tentative + 1
        # NOTIF QUESTION
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'notification-question')))
        except:
            config.saveLog('pas de fenetre de question',1, config.newmatch)
        else:
            alerttexte = driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text
            config.saveLog('alert : ' + alerttexte, 1,config.newmatch)
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.saveLog("Paris déjà placé", 1, config.newmatch)
                DeleteBet(driver)
                # Store bet information in validated_bet variable
                from datetime import datetime
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                config.validated_bet = {
                    'montant': config.mise,
                    'jeu': config.jeu_actuel if hasattr(config, 'jeu_actuel') else None,
                    'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                    'timestamp': current_timestamp
                }
                print(config.validated_bet)
                return False
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.saveLog("Paris déjà placé", 1, config.newmatch)
                DeleteBet(driver)
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()

        # NOTIF ALERT
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'notification-alert')))
        except:
            config.saveLog('pas de fenetre de notif',1, config.newmatch)
        else:
            alerttexte = driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text
            config.saveLog('alert : ' + alerttexte, 1,config.newmatch)
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.saveLog("Paris déjà placé",1, config.newmatch)
                DeleteBet(driver)
                # Store bet information in validated_bet variable
                from datetime import datetime
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                config.validated_bet = {
                    'montant': config.mise,
                    'jeu': config.jeu_actuel if hasattr(config, 'jeu_actuel') else None,
                    'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                    'timestamp': current_timestamp
                }
                print(config.validated_bet)
                config.saveLog(f'Bet validé: Montant={config.mise}, Jeu={getattr(config, "jeu_actuel", "N/A")}, Set={getattr(config, "set_actuel", "N/A")}', 1, config.newmatch)
                
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.saveLog("Paris déjà placé",1,config.newmatch)
                DeleteBet(driver)
                # Store bet information in validated_bet variable
                from datetime import datetime
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                config.validated_bet = {
                    'montant': config.mise,
                    'jeu': config.jeu_actuel if hasattr(config, 'jeu_actuel') else None,
                    'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                    'timestamp': current_timestamp
                }
                print(config.validated_bet)
                config.saveLog(f'Bet validé: Montant={config.mise}, Jeu={getattr(config, "jeu_actuel", "N/A")}, Set={getattr(config, "set_actuel", "N/A")}', 1, config.newmatch)
                
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
        # NOTIF VALIDATION
        try:
            config.saveLog('Vérification de validation',1, config.newmatch)
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     'ui-coupon-modal-header__title'))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.saveLog('pas de fentre validation, vérification erreur',1 , config.newmatch)

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              'ui-coupon-modal-header__title')[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE) is not None:
                config.saveLog('PARI VALIDÉ!',1, config.newmatch)
                # Store bet information in validated_bet variable
                from datetime import datetime
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                config.validated_bet = {
                    'montant': config.mise,
                    'jeu': config.jeu_actuel if hasattr(config, 'jeu_actuel') else None,
                    'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                    'timestamp': current_timestamp
                }
                print(config.validated_bet)
                config.saveLog(f'Bet validé: Montant={config.mise}, Jeu={getattr(config, "jeu_actuel", "N/A")}, Set={getattr(config, "set_actuel", "N/A")}', 1, config.newmatch)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             'coupon-success-modal-controls__item'))
                    )
                except:
                    config.saveLog('impossible de cliqué sur ok', 1, config.newmatch)
                else:
                    modal_wrapper = driver.find_elements(By.CLASS_NAME, 'coupon-success-modal-controls__item')[0]
                    modal_wrapper.click()
                    fenetre_validation = 1
                    validation = 1
                    return False
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    ModalHandler(driver)
