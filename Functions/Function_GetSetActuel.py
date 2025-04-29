# Function_GetSetActuel.py
# OBTENIR LE SET ACTUEL

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config


def GetSetActuel(driver):
    # config.log('Récupératon du set actuel', '', False, 3)
    # config.log_clear_line()
    try:
        # driver.switch_to.window(driver.window_handles[0])
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'ui-game-timer__label'))
        )
        config.set_actuel = driver.find_elements(By.CLASS_NAME, 'ui-game-timer__label')[0].text
    except Exception as e:
        config.log('        #E0009 ui-game-timer__label introuvable', 'warning', True)
        config.log_clear_line()
        return False
    else:
        try:
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log('#E0010 erreur : numset', 'warning', True, 3)
            config.log_clear_line()
            return False
        else:
            config.set_actuel = str(numset)
            if config.saved_set != config.set_actuel:
                # config.log('Nouveau Set actuel : ' + str(config.set_actuel), '', True, 3)
                # config.log_clear_line()
                return True
            else:
                # config.log('Set actuel : ' + str(config.set_actuel), '', True, 3)
                # config.log_clear_line()
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
            config.log("Vérification si numéro de QT bien récupéré", 0, config.newmatch)
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log(f"#E0010\nUne erreur est survenue : {e}", config.newmatch)
            config.log("erreur : numset", config.newmatch)
            return False
        else:
            config.set_actuel = str(numset)
            config.log(str(numset) + ' QT', 0, config.newmatch)
            if config.saved_set != config.set_actuel:
                print('QT actuel : ' + config.set_actuel)
                config.log('Récupération du QT actuel : ' + str(config.set_actuel), 0, config.newmatch)

    return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    print(GetSetActuel(driver))
