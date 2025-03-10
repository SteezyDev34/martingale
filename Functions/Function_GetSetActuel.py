# Function_GetSetActuel.py
# OBTENIR LE SET ACTUEL
from selenium.webdriver.common.by import By
import config


def GetSetActuel(driver):
    try:
        config.set_actuel = driver.find_elements(By.CLASS_NAME, 'ui-game-timer__label')[0].text
    except Exception as e:
        config.saveLog(f"#E0009\nUne erreur est survenue : {e}",config.newmatch)
        config.saveLog("erreur : c-scoreboard-score__heading",config.newmatch)
        return False
    else:
        try:
            #config.saveLog("Vérification si numéro de set bien récupéré",0,config.newmatch)
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.saveLog(f"#E0010\nUne erreur est survenue : {e}",config.newmatch)
            config.saveLog("erreur : numset",config.newmatch)
            return False
        else:
            config.set_actuel = str(numset)
            if config.saved_set != config.set_actuel:
                #config.saveLog('Nouveau Set actuel : ' + str(config.set_actuel),0,config.newmatch)
                return True
            else:
                #config.saveLog('Set actuel : ' + str(config.set_actuel), 0, config.newmatch)
                return True

    return True
def GetQTtActuel(driver):
    try:
        config.set_actuel = driver.find_elements(By.CLASS_NAME, 'c-tablo__text')[0].text
    except Exception as e:
        config.saveLog(f"#E0009\nUne erreur est survenue : {e}",config.newmatch)
        config.saveLog("erreur : c-tablo__text",config.newmatch)
        return False
    else:
        try:
            config.saveLog("Vérification si numéro de QT bien récupéré",0,config.newmatch)
            numset = config.set_actuel.split(' ')[0]
            numset = int(''.join(char for char in numset if char.isdigit()))
        except Exception as e:
            config.saveLog(f"#E0010\nUne erreur est survenue : {e}",config.newmatch)
            config.saveLog("erreur : numset",config.newmatch)
            return False
        else:
            config.set_actuel = str(numset)
            config.saveLog(str(numset)+' QT',0,config.newmatch)
            if config.saved_set != config.set_actuel:
                print('QT actuel : '+config.set_actuel)
                config.saveLog('Récupération du QT actuel : ' + str(config.set_actuel),0,config.newmatch)

    return True
if __name__ == "__main__":
    from ChromeDriver.SetDriver4 import driver
    print(GetSetActuel(driver))