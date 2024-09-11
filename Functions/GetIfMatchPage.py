#Function_GetIfMatchPage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import config
from ChromeDriver.SetDriver1 import driver

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
                (By.CLASS_NAME, 'scoreboard-section__scroll'))
        )
    except:
        logTxt = "Tableau des scores introuvable!"
        config.saveLog( logTxt)
        try:
            logTxt ="On vérifie que le match ne soit pas terminé"
            config.saveLog( logTxt)
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'old-layout__content'))
            )
        except:
            try:
                logTxt = "On vérifie que le match ne soit pas en résumé"
                config.saveLog(logTxt)
                ul_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'new-breadcrumbs'))
                )
            except Exception as e:
                logTxt = "Ce n'est pas une page de match"
                print(f'{e}')
                config.saveLog(logTxt)
                return False
            else:

                # Récupérer le texte du <ul>
                ul_text = ul_element.text
                print(ul_text)
                # Vérifier si le texte contient le mot "résume", indépendamment de la casse
                if 'résume' in ul_text.lower():
                    logTxt = "MATCH TERMINÉ! Retour sur https://ca.1x001.com/fr/live/tennis"
                    config.saveLog(logTxt)
                    driver.get('https://ca.1x001.com/fr/live/tennis')
                    return False
                else:
                    logTxt = "Ce n'est pas une page de match"
                    config.saveLog(logTxt)
                    driver.get('https://ca.1x001.com/fr/live/tennis')
                    return False

        else:
            logTxt = "MATCH TERMINÉ! Retour sur https://ca.1x001.com/fr/live/tennis"
            config.saveLog( logTxt)
            driver.get('https://ca.1x001.com/fr/live/tennis')
            return False
    else:
        logTxt = "PAGE MATCH OK!"
        config.saveLog( logTxt)
        return True
GetIfMatchPage(driver)