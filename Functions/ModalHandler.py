import os
import re
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetScoreActuel import GetScoreActuel


def ModalHandler(driver, close=True):
    validation = False
    tentative = 1
    config.log("GESTION DE MODAL", 'info', False, 2)
    print(config.site_type)
    logline = 1
    fenetre_validation = 0
    while fenetre_validation == 0 and tentative <= 2:
        if config.scriptType != 'LIVE':
            GetScoreActuel(driver)
        tentative = tentative + 1
        # NOTIF VALIDATION
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     config.classes['modal_header'][config.site_type]))
            )  ###vérifaction d'affichage pop up validation
        except:
            modal_class = config.classes['modal_header'][config.site_type]
            config.log(f'pas de fenetre de validation {modal_class}', 'warning',
                       False, indent=3)
            logline += 1

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              config.classes['modal_header'][config.site_type])[
                0].text
            print('test modal : ', validation)
            if config.site_type == 'mobile_site':
                search_result = re.search("effectué", validation, re.IGNORECASE)
            else:
                search_result = re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE)
            if search_result is not None:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             config.classes['close_modal_btn'][config.site_type]))
                    )
                    modal_wrapper = \
                        driver.find_elements(By.CLASS_NAME, config.classes['close_modal_btn'][config.site_type])[0]
                except:
                    config.log(f'            Impossible de cliquer sur Ok', 'warning', False)
                    logline += 1
                else:
                    time.sleep(2)
                    if close:
                        modal_wrapper.click()
                    config.log(f'PARIS VALIDÉ', 'success', False, indent=3)
                    return True
        if config.scriptType != 'LIVE':
            GetScoreActuel(driver)
        # NOTIF QUESTION
        try:
            element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(
                (By.CLASS_NAME, config.classes['notification_question'][config.site_type])))
        except:
            config.log('pas de fenetre de question', 'warning', False, indent=3)
            logline += 1
        else:
            if len(re.findall("Maximum",
                              driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                  0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                return False
            elif len(re.findall("déjà",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_cancel'][config.site_type]).click()
                config.log_clear_line(logline)
                config.log(f'Paris déjà placé', 'success', False, indent=3)
                DeleteBet(driver)
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_cancel'][config.site_type]).click()
                config.log_clear_line(logline)
                config.log(f'Paris déjà placé', 'success', False, indent=3)
                DeleteBet(driver)
                return True
            else:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()

        # NOTIF ALERT
        if config.scriptType != 'LIVE':
            GetScoreActuel(driver)
        try:
            element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(
                (By.CLASS_NAME, config.classes['notification_alert'][config.site_type])))
        except:
            config.log('pas de fenetre de notif', 'warning', False, indent=3)
            logline += 1
        else:
            if len(re.findall("Maximum",
                              driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                  0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                return False
            elif len(re.findall("plus possible",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                return False
            elif len(re.findall("déjà",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                config.log(f'Paris déjà placé', 'sucess', False, indent=3)
                DeleteBet(driver)
                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log_clear_line(logline)
                config.log(f'Paris déjà placé', 'success', False, indent=3)
                DeleteBet(driver)
                return True
            else:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
        # NOTIF VALIDATION
        if config.scriptType != 'LIVE':
            GetScoreActuel(driver)
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     config.classes['modal_header'][config.site_type]))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.log('pas de fenetre de validation', 'warning', False, indent=3)
            logline += 1

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              config.classes['modal_header'][config.site_type])[
                0].text
            if config.site_type == 'mobile_site':
                search_result = re.search("effectué", validation, re.IGNORECASE)
            else:
                search_result = re.search("VOTRE PARI A ÉTÉ ACCEPTÉ !", validation, re.IGNORECASE)
            if search_result is not None:

                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             config.classes['close_modal_btn'][config.site_type]))
                    )
                    modal_wrapper = \
                        driver.find_elements(By.CLASS_NAME, config.classes['close_modal_btn'][config.site_type])[0]
                except:
                    config.log(f'Impossible de cliquer sur Ok', 'warning', False, indent=3)
                    logline += 1
                else:

                    modal_wrapper.click()
                    config.log_clear_line(logline)
                    config.log(f'PARIS VALIDÉ', 'success', False, indent=3)
                    return True
        config.log(f'tentative {tentative}', 'warning', False, indent=3)
        logline += 1
    config.log_clear_line(logline)
    return False


if __name__ == "__main__":
    # driver.switch_to.window(driver.window_handles[0])
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'new_site'
    config.scriptType = 'LIVE'
    config.mise = 0.2
    ModalHandler(driver)
