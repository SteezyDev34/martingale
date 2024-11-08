#Function_GetIfMatchPage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import config
#VÉRIFIERR SI PAGE DE MATCH
def GetIfMatchPage(driver):
    #driver.switch_to.window(driver.window_handles[0])
    logTxt = "Vérfication si page match..."
    config.saveLog( logTxt)
    try:
        logTxt = "On cherche le tableau des scores"
        config.saveLog( logTxt)
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'c-scoreboard-score__heading'))
        )
    except:
        logTxt = "Tableau des scores introuvable!"
        config.saveLog( logTxt)
        try:
            logTxt ="On vérifie que le match ne soit pas terminé"
            config.saveLog( logTxt)
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'after-game-info__text'))
            )
        except:
            logTxt = "Ce n'est pas une page de match"
            config.saveLog(logTxt)
            return False
        else:
            logTxt = "MATCH TERMINÉ! Retour sur https://1xbet.com/fr/live/tennis"
            config.saveLog( logTxt)
            driver.get('https://1xbet.com/fr/live/tennis')
            return False
    else:
        logTxt = "PAGE MATCH OK!"
        config.saveLog( logTxt)
        return True
