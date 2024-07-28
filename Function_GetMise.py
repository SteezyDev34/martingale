# GetMise
import time

from selenium.webdriver.common.by import By
import config
import config
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
def GetMise(driver):
    if config.rattrape_perte == 3:
        txtlog = 'Bonne proba, cote : 3'
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        config.cote = 3
    else:
        txtlog = "Rattrapage, recuperation de la cote"
        config.saveLog(txtlog, config.newmatch)
        time.sleep(2)
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'cpn-total__coef')[
                0].text
        except:
            txtlog = 'erreur recup cote : 3'
            config.saveLog(txtlog, config.newmatch)
            config.cote = 3
        else:
            txtlog = 'cote recupéré ' + str(config.cote)
            config.saveLog(txtlog, config.newmatch)
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    txtlog = 'error float cote : cote = 3'
                    config.saveLog(txtlog,config.newmatch)
                    config.cote = 3
            else:
                config.cote = 3
    config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
        txtlog  = "cote : " + str(config.cote) + " | perte : " + str(
            config.perte) + " | wantwin : " + str(
            config.wantwin) + " | mise : " + str(config.mise)
        print(txtlog)
        config.saveLog(txtlog,config.newmatch)
    getmisemax = False
    tentative = 0
    while not getmisemax:
        try:
            btn_extra = driver.find_elements(By.CLASS_NAME,
                                               'cpn-extra__btn')[
                0]
        except:
            tentative += 1
            if tentative > 5:
                getmisemax = True
                config.misemax = 0
        else:
            btn_extra.click()
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'cpn-dropdown--is-active'))
                )
                btn_extra = driver.find_elements(By.CLASS_NAME,
                                             'cpn-dropdown--is-active')[
                0]
            except:
                tentative +=1
                if tentative > 5:
                    getmisemax = True
                    config.misemax = 0
            else:
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                             'cpn-dropdown__content')[
                0]
                btn_extra =btn_extra.find_elements(By.CLASS_NAME,
                                             'cpn-extra-settings__item')[
                0]
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                             'cpn-extra-settings__btn')[
                0].text
                try:
                    config.misemax = float(btn_extra.split(' EUR')[0].replace(' ', ''))
                except:
                    getmisemax = True
                    config.misemax = 0
                else:
                    getmisemax = True



    print('miise max : '+str(config.misemax))
    return True
def GetMise30A(driver):
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
def GetMise4030(driver):
    config.rattrape_perte = 1
    if config.rattrape_perte == 0:
        config.saveLog('Pas de rattrapage, cote : 4')
        config.cote = 3
    elif config.rattrape_perte == 2:
        config.saveLog('Bonne proba, cote : 4')
        config.cote = 3
    else:
        config.saveLog("Rattrapage, recuperation de la cote")
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'cpn-total__coef')[
                0].text
        except:
            config.saveLog('erreur recup cote : 3')
            config.cote = 4
        else:
            config.saveLog('cote recupéré ' + str(config.cote))
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    config.saveLog('error float cote : cote = 2.4')
                    config.cote = 4
            else:
                config.cote = 4
    config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
        config.saveLog("cote : " + str(config.cote) + " | perte : " + str(
            config.perte) + " | wantwin : " + str(
            config.wantwin) + " | mise : " + str(config.mise))

    return True