# Function_GetSetActuel.py
# OBTENIR LE SET ACTUEL

from selenium.webdriver.common.by import By

import config


def GetQTActuel(driver):
    try:
        config.qt_actuel = driver.find_elements(By.CLASS_NAME, 'scoreboard-status')[0].text
    except Exception as e:
        config.log(f"#E0009\nUne erreur est survenue : {e}", config.newmatch)
        config.log("erreur : scoreboard-status", config.newmatch)
        return False
    else:
        try:
            numset = config.qt_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log(f"#E0010\nUne erreur est survenue : {e}", config.newmatch)
            config.log("erreur : numset", config.newmatch)
            return False
        else:
            config.qt_actuel = int(numset)

    return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetQTActuel(driver)
