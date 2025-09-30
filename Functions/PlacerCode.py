import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


# from ChromeDriver.SetDriver1 import driver


def PlacerCode(driver, code):
    sending_mise = False
    tentative = 0
    config.scriptType = 'LIVE'
    while not sending_mise:
        tentative += 1
        DeleteBet(driver)
        try:

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, config.classes['cpn_events_trigger'][config.site_type])))
            cpn_setting = driver.find_element(By.CLASS_NAME, config.classes['cpn_events_trigger'][config.site_type])
            cpn_setting.click()
        except Exception as e:
            config.log("        CHAMP DE COUPON NON TROUVÉ")
            if tentative > 10:
                return False
            if tentative > 2:
                ModalHandler(driver)
        else:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, config.classes['cpn_events_input'][config.site_type])))
            except Exception as e:
                config.log(f"Erreur de recherche {config.classes['cpn_events_input'][config.site_type]} ")
                if tentative > 10:
                    return False
                if tentative > 2:
                    ModalHandler(driver)
            else:
                cpn_setting = driver.find_element(By.CLASS_NAME, config.classes['cpn_events_input'][config.site_type])
                cpn_setting.clear()
                cpn_setting.send_keys(str(code))
                l = cpn_setting.get_attribute("value")
                config.log("code insérré : " + str(l))
                if str(l) == str(code):
                    try:
                        element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.CLASS_NAME, config.classes['cpn_btn_theme_brand'][config.site_type])))
                    except Exception as e:
                        config.log(f"Erreur de recherche {config.classes['cpn_btn_theme_brand'][config.site_type]} ")
                        if tentative > 10:
                            return False
                    else:
                        # Localiser le bouton avec la classe spécifiée qui contient le texte 'charger' dans un span (insensible à la casse)
                        # XPath : recherche un bouton avec la classe cpn-btn--theme-brand qui contient un span avec le texte 'charger'
                        # La fonction translate() convertit le texte en minuscules pour ignorer la casse
                        # Le '..' à la fin remonte au bouton parent depuis le span trouvé
                        cpn_setting = driver.find_element(By.XPATH,
                                                          f"//button[contains(@class, '{config.classes['cpn_btn_theme_brand'][config.site_type]}')]//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'charger')]/..")
                        try:
                            cpn_setting.click()
                            validate_bet = False
                            config.log('On place la mise', 'infos', True, 2)
                            config.log_clear_line()
                            while not PlacerMise(driver):
                                config.log('On vérifie le score pour valider le paris', 'info', False, 2)
                                config.log_clear_line()
                                ##VALIDATION DU PARIS SI SCORE OK
                            while not validate_bet:
                                # VÉRIFICATION DU SCORE ACTUEL
                                tentative = tentative + 1
                                if ValidationDuParis(driver):
                                    validate_bet = True
                                    return True
                        except Exception as e:
                            config.log(f'{e}')
                            if tentative > 2:
                                ModalHandler(driver)
                                if tentative > 10:
                                    return False



                else:
                    config.log('mauvaise code insérée!', 'warning')
                    time.sleep(1)


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetIfNewSite(driver)
    code = 'G7SJV'
    PlacerCode(driver, code)
