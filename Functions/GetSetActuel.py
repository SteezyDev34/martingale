# GetSetActuel.py
# OBTENIR LE SET ACTUEL

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config


def GetSetActuel(driver):
    from Functions.BridgeAdapter import bridge_active, bridge_get_set_actuel
    if bridge_active():
        return bridge_get_set_actuel()
    # config.log('Récupératon du set actuel', '', False, 3)
    # config.log_clear_line()
    try:
        # w
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, config.classes['set_container'][config.site_type]
                                              ))
        )
        config.set_actuel = driver.find_elements(By.CLASS_NAME, config.classes['set_container'][config.site_type])[
            0].text
    except Exception as e:
        print(config.site_type)
        set_container_selector = config.classes["set_container"][config.site_type]
        config.log(f'#E0009 {set_container_selector} introuvable', 'warning', False)
        config.log_clear_line()
        return False
    else:
        try:
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log('#E0010 erreur : numset', 'warning', False, 3)
            config.log_clear_line()
            return False
        else:
            config.set_actuel = str(numset)
            if config.saved_set != config.set_actuel:
                config.log('Nouveau Set actuel : ' + str(config.set_actuel), '', False, 3)
                config.log_clear_line()
                return True
            else:
                config.log('Set actuel : ' + str(config.set_actuel), '', False, 3)
                config.log_clear_line()
                return True

    return True


def GetQTtActuel(driver):
    try:
        config.set_actuel = driver.find_elements(By.CLASS_NAME, 'c-tablo__text')[0].text
    except Exception as e:
        config.log(f"#E0009\nUne erreur est survenue : {e}", config.newmatch)
        config.log("erreur : c-tablo__text", config.newmatch)
        return False
    else:
        try:
            config.log("Vérification si numéro de QT bien récupéré", 'info', True, 3)
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log(f"#E0010\nUne erreur est survenue : {e}", config.newmatch)
            config.log("erreur : numset", config.newmatch)
            return False
        else:
            config.set_actuel = str(numset)
            config.log(str(numset) + ' QT', 'info', True, 3)
            if config.saved_set != config.set_actuel:
                config.log('Nouveau QT actuel : ' + config.set_actuel, '', True, 3)
                # config.log_clear_line()
                return True
            else:
                config.log('QT actuel : ' + config.set_actuel, '', True, 3)
                # config.log_clear_line()
                return True

    return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.saved_set = 1
    config.site_type = 'old_site'
    print(GetSetActuel(driver))
