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
            config.saveLog('pas de fenetre de question', config.newmatch)
        else:
            alerttexte = driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text
            config.saveLog('alert : ' + alerttexte, config.newmatch)
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.saveLog("Paris déjà placé", config.newmatch)
                DeleteBet(driver)
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__cancel').click()
                config.saveLog("Paris déjà placé", config.newmatch)
                DeleteBet(driver)
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()

        # NOTIF ALERT
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'notification-alert')))
        except:
            config.saveLog('pas de fenetre de notif', config.newmatch)
        else:
            alerttexte = driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text
            config.saveLog('alert : ' + alerttexte, config.newmatch)
            if len(re.findall("Maximum", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                return False
            elif len(re.findall("déjà", driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.saveLog("Paris déjà placé", config.newmatch)
                DeleteBet(driver)
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, 'ui-popup__content')[0].text)) > 0:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
                config.saveLog("Paris déjà placé", config.newmatch)
                DeleteBet(driver)
                return True
            else:
                driver.find_element(By.CLASS_NAME, 'ui-popup__submit').click()
        # NOTIF VALIDATION
        try:
            config.saveLog('Vérification de validation', config.newmatch)
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     'ui-coupon-modal-header__title'))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.saveLog('pas de fentre validation, vérification erreur', config.newmatch)

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              'ui-coupon-modal-header__title')[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE) is not None:
                config.saveLog('PARI VALIDÉ!', config.newmatch)

                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             'coupon-success-modal-controls__item'))
                    )
                except:
                    config.saveLog('impossible de cliqué sur ok', config.newmatch)
                else:
                    modal_wrapper = driver.find_elements(By.CLASS_NAME, 'coupon-success-modal-controls__item')[0]
                    modal_wrapper.click()
                    fenetre_validation = 1
                    validation = 1
                    return True
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    ModalHandler(driver)
