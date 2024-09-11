# GetMise
import time

from selenium.webdriver.common.by import By
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
def GetMise(driver):
    if config.rattrape_perte == 3:
        txtlog = 'Bonne proba, cote : 3'
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        config.cote = config.cotebase
    else:
        txtlog = "Rattrapage, recuperation de la cote"
        config.saveLog(txtlog, config.newmatch)
        time.sleep(2)
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               'coupon-result-coef-value')[
                0].text
        except:
            txtlog = 'erreur recup cote : 3'
            config.saveLog(txtlog, config.newmatch)
            config.cote = config.cotebase
        else:
            txtlog = 'cote recupéré ' + str(config.cote)
            config.saveLog(txtlog, config.newmatch)
            if config.cote != '':
                try:
                    config.cote = float(config.cote)
                except:
                    txtlog = 'error float cote : cote = '+str(config.cote)
                    config.saveLog(txtlog,config.newmatch)
                    config.cote = config.cotebase
            else:
                config.cote = config.cotebase
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
