# GetMise
import time

from selenium.webdriver.common.by import By
import config


def GetMise(driver):
    print('rattrapeg : ',config.rattrape_perte)
    if config.rattrape_perte == 3:
        config.saveLog('Bonne proba, cote : 3')
        config.cote = 3
    else:
        config.saveLog("Rattrapage, recuperation de la cote")
        time.sleep(2)
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'cpn-total__coef')[
                0].text
        except:
            config.saveLog('erreur recup cote : 3')
            config.cote = 3
        else:
            config.saveLog('cote recupéré ' + str(config.cote))
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    config.saveLog('error float cote : cote = 3')
                    config.cote = 3
            else:
                config.cote = 3
    config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
        config.saveLog("cote : " + str(config.cote) + " | perte : " + str(
            config.perte) + " | wantwin : " + str(
            config.wantwin) + " | mise : " + str(config.mise))

    return True
def GetMise30A(driver):
    config.rattrape_perte = 1
    if config.rattrape_perte == 0:
        config.saveLog('Pas de rattrapage, cote : 2.4')
        config.cote = 2.4
    elif config.rattrape_perte == 2:
        config.saveLog('Bonne proba, cote : 2.4')
        config.cote = 2.4
    else:
        config.saveLog("Rattrapage, recuperation de la cote")
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'cpn-total__coef')[
                0].text
        except:
            config.saveLog('erreur recup cote : 3')
            config.cote = 2.4
        else:
            config.saveLog('cote recupéré ' + str(config.cote))
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    config.saveLog('error float cote : cote = 2.4')
                    config.cote = 2.4
            else:
                config.cote = 2.4
    config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
        config.saveLog("cote : " + str(config.cote) + " | perte : " + str(
            config.perte) + " | wantwin : " + str(
            config.wantwin) + " | mise : " + str(config.mise))

    return True

def GetMise15A(driver):
    # rattrape_perte = 0
    if config.rattrape_perte == 0:
        config.saveLog('Pas de rattrapage, cote : 3')
        config.cote = 1.85
    elif config.rattrape_perte == 2:
        config.saveLog('Bonne proba, cote : 3')
        config.cote = 1.85
    else:
        config.saveLog("Rattrapage, recuperation de la cote")
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'cpn-total__coef')[
                0].text
        except:
            config.saveLog('erreur recup cote : 3')
            config.cote = 1.85
        else:
            config.saveLog('cote recupéré ' + str(config.cote))
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    config.saveLog('error float cote : cote = 2.4')
                    config.cote = 1.85
            else:
                config.cote = 1.85
    config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
        config.saveLog("cote : " + str(config.cote) + " | perte : " + str(
            config.perte) + " | wantwin : " + str(
            config.wantwin) + " | mise : " + str(config.mise))

    return True
