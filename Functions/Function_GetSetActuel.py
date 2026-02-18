# Function_GetSetActuel.py
# OBTENIR LE SET ACTUEL

from selenium.webdriver.common.by import By

import config


def GetQTActuel(driver):
    try:
        period = driver.find_elements(By.CLASS_NAME, 'scoreboard-status')[0].text
    except Exception as e:
        config.log(f"#E0009\nUne erreur est survenue : {e}", config.newmatch)
        config.log("erreur : scoreboard-status", config.newmatch)
        return False
    else:
        try:
            # config.log("Vérification si numéro de QT bien récupéré", 0, config.newmatch)
            score_block = driver.find_element(By.CLASS_NAME, 'scoreboard-periods-table__content')
            score_col = score_block.find_elements(By.CLASS_NAME, 'scoreboard-periods-table__col')[-1]
            config.qt_actuel = score_col.find_element(By.CLASS_NAME, 'scoreboard-periods-table-cell--th').text
            numset = config.qt_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.log(f"#E0010AZ\nUne erreur est survenue : {e}", config.newmatch)
            config.log("erreur : numset", config.newmatch)
            return False
        else:
            if 'mi-temps' in period.lower():
                config.qt_actuel = numset + 1
            elif 'fin' in period.lower():
                config.qt_actuel = 9
            else:
                config.qt_actuel = numset
            config.log(str(config.qt_actuel) + ' QT', 0, config.newmatch)

            if config.saved_set != config.qt_actuel:
                print('QT actuel : ', config.qt_actuel)
                config.log('Récupération du QT actuel : ' + str(config.qt_actuel), 0, config.newmatch)

    return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetQTActuel(driver)
