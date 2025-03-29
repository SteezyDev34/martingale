import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet


def ModalHandler(driver):
    validation = False
    tentative = 1
    config.log("        GESTION DE MODAL", 'info', False)
    config.log_clear_line()
    fenetre_validation = 0
    while fenetre_validation == 0 and tentative <= 2:
        tentative = tentative + 1
        # NOTIF QUESTION
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'notification-question')))
        except:
            config.log('            pas de fenetre de question', 'warning', False)
            config.log_clear_line()
        else:
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.log(f'            Paris déjà placé', 'info', False)
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
                config.log(f'           {config.validated_bet}', 'info', True)
                config.log_clear_line()
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.log(f'            Paris déjà placé', 'info', False)
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
                config.log(f'           {config.validated_bet}', 'info', True)
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()

        # NOTIF ALERT
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'notification-alert')))
        except:
            config.log('            pas de fenetre de notif', 'warning', False)
            config.log_clear_line()

        else:
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("plus possible",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.log(f'            Paris déjà placé', 'info', False)
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
                config.log(f'           {config.validated_bet}', 'info', True)
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.log(f'            Paris déjà placé', 'info', False)
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
                config.log(f'           {config.validated_bet}', 'info', True)
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
        # NOTIF VALIDATION
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     'ui-coupon-modal-header__title'))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.log('            pas de fenetre de validation', 'warning', True)

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              'ui-coupon-modal-header__title')[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE) is not None:
                config.log(f'            PARIS VALIDÉ', 'success', False)
                # Store bet information in validated_bet variable
                from datetime import datetime
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                config.validated_bet = {
                    'montant': config.mise,
                    'jeu': config.jeu_actuel if hasattr(config, 'jeu_actuel') else None,
                    'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                    'timestamp': current_timestamp
                }
                config.log(f'           {config.validated_bet}', 'info', True)
                config.log_clear_line()
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             'coupon-success-modal-controls__item'))
                    )
                except:
                    config.log(f'            Impossible de lciquer sur Ok', 'warning', False)
                else:
                    modal_wrapper = driver.find_elements(By.CLASS_NAME, 'coupon-success-modal-controls__item')[0]
                    modal_wrapper.click()
                    return True
        config.log(f'            tentative {tentative}', 'warning', True)
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    ModalHandler(driver)
