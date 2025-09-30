# GetMise
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from Functions.GetIfNewSite import GetIfNewSite


def GetMise(driver):
    if config.rattrape_perte == 3:
        txtlog = 'Bonne proba, cote : 3'
        config.log(txtlog, 'info')
        config.log_clear_line()
        config.cote = config.cotebase
    else:
        txtlog = "Rattrapage, recuperation de la cote"
        config.log(txtlog, 'info')
        config.log_clear_line()
        try:
            config.cote = driver.find_elements(By.CLASS_NAME,
                                               config.classes['coef_value'][config.site_type])[
                0].text
        except:
            txtlog = 'erreur recup cote : 3'
            config.log(txtlog, 'info')
            config.log_clear_line()
            config.cote = config.cotebase
        else:

            txtlog = 'cote recupéré ' + str(config.cote)
            config.log(txtlog, 'info')
            config.log_clear_line()
            if config.cote == '' or str(config.cote) == '0' or str(config.cote) == '1' or config.cote == 0:
                config.cote = config.cotebase
    if config.scriptType == 'LIVE':
        api_url = f'https://bettracker.sc2vagr6376.universe.wf/backend/api.php?action=recommended_stake&tipster={config.tipster}&odds={config.cote}&target_percentage=1&recover_losses=1'
        req = requests.get(api_url, verify=False)
        config.mise = round(float(req.json()['recommended_stake']), 2)
        return True
    else:
        config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
    txtlog = "cote : " + str(config.cote) + " | perte : " + str(
        config.perte) + " | wantwin : " + str(
        config.wantwin) + " | mise : " + str(config.mise)
    config.log(txtlog, 'info')
    getmisemax = True
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
                tentative += 1
                if tentative > 5:
                    getmisemax = True
                    config.misemax = 0
            else:
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                                    'cpn-dropdown__content')[
                    0]
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
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
    return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetIfNewSite(driver)
    print(config.perte)
    GetMise(driver)
