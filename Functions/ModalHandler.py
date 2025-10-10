import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite


def ModalHandler(driver):
    validation = False
    tentative = 1
    config.log("GESTION DE MODAL", 'info', False, 2)
    fenetre_validation = 0
    while fenetre_validation == 0 and tentative <= 2:
        tentative = tentative + 1
        # NOTIF VALIDATION
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     config.classes['modal_header'][config.site_type]))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.log('pas de fenetre de validation', 'warning', True, indent=3)

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              config.classes['modal_header'][config.site_type])[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE) is not None:
                config.log(f'PARIS VALIDÉ', 'success', False, indent=3)

                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             config.classes['close_modal_btn'][config.site_type]))
                    )
                except:
                    config.log(f'            Impossible de cliquer sur Ok', 'warning', False)
                else:
                    modal_wrapper = \
                        driver.find_elements(By.CLASS_NAME, config.classes['close_modal_btn'][config.site_type])[0]
                    modal_wrapper.click()
                    return True
        # NOTIF QUESTION
        try:
            element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(
                (By.CLASS_NAME, config.classes['notification_question'][config.site_type])))
        except:
            config.log('pas de fenetre de question', 'warning', True, indent=3)
        else:
            if len(re.findall("Maximum",
                              driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                  0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
            elif len(re.findall("déjà",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_cancel'][config.site_type]).click()
                config.log(f'Paris déjà placé', 'info', False, indent=3)
                DeleteBet(driver)

                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_cancel'][config.site_type]).click()
                config.log(f'Paris déjà placé', 'info', False, indent=3)
                DeleteBet(driver)

                return True
            else:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()

        # NOTIF ALERT
        try:
            element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(
                (By.CLASS_NAME, config.classes['notification_alert'][config.site_type])))
        except:
            config.log('pas de fenetre de notif', 'warning', True, indent=3)

        else:
            if len(re.findall("Maximum",
                              driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                  0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
            elif len(re.findall("modifiées",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
            elif len(re.findall("plus possible",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
            elif len(re.findall("déjà",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log(f'Paris déjà placé', 'info', False, indent=3)
                DeleteBet(driver)

                return True
            elif len(re.findall("peut être accepté",
                                driver.find_elements(By.CLASS_NAME, config.classes['popup_content'][config.site_type])[
                                    0].text)) > 0:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                config.log(f'Paris déjà placé', 'info', False, indent=3)
                DeleteBet(driver)

                return True
            else:
                driver.find_element(By.CLASS_NAME, config.classes['popup_submit'][config.site_type]).click()
                return False
        # NOTIF VALIDATION
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME,
                     config.classes['modal_header'][config.site_type]))
            )  ###vérifaction d'affichage pop up validation
        except:
            config.log('pas de fenetre de validation', 'warning', True, indent=3)

        else:
            validation = driver.find_elements(By.CLASS_NAME,
                                              config.classes['modal_header'][config.site_type])[
                0].text
            if re.search("VOTRE PARI EST ACCEPTÉ !", validation, re.IGNORECASE) is not None:
                config.log(f'PARIS VALIDÉ', 'success', False, indent=3)

                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME,
                             config.classes['close_modal_btn'][config.site_type]))
                    )
                except:
                    config.log(f'Impossible de cliquer sur Ok', 'warning', False, indent=3)
                else:
                    modal_wrapper = \
                        driver.find_elements(By.CLASS_NAME, config.classes['close_modal_btn'][config.site_type])[0]
                    modal_wrapper.click()
                    return True
        config.log(f'tentative {tentative}', 'warning', True, indent=3)
    config.log_clear_line()
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    # driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    GetIfNewSite(driver)
    ModalHandler(driver)
