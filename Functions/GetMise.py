# GetMise
import os
import sys

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions import RedisIPC
import config


def GetMise(driver):
    logline = 0
    if config.rattrape_perte == 3:
        config.log('Bonne proba, cote : 3', 'info', False)
        logline += 1
        config.cote = config.cotebase
    else:
        config.log("Rattrapage, recuperation de la cote", 'info', False)
        logline += 1
        try:
            config.log(f"tentative de recup cote avec class {config.classes['coef_value'][config.site_type]}", 'info', False)
            config.cote = ''.join(filter(lambda x: x.isdigit() or x in ',.',
                                        driver.find_elements(By.CLASS_NAME,
                                                            config.classes['coef_value'][config.site_type])[0].text))
        except Exception as e:
            try:
                if config.scriptType == 'LIVE' and config.site_type == 'mobile_site':
                    config.cote = ''.join(filter(lambda x: x.isdigit() or x in ',.',
                                                    driver.find_elements(By.CLASS_NAME,
                                                                        config.classes['coef_value'][config.site_type])[0].text))
                else:
                    config.log(f"tentative de recup cote avec class {config.classes['cpn_action_coef'][config.site_type]}", 'info', False)
                    
            except Exception as e:
                print(e)
                config.log('erreur recup cote', 'info', False)
                logline += 1
                config.cote = config.cotebase
        else:
            config.log(f'cote recupéré {str(config.cote)}', 'info', False)
            logline += 1
            if config.cote == '' or str(config.cote) == '0' or str(config.cote) == '1' or config.cote == 0:
                config.cote = config.cotebase
    if config.scriptType == 'LIVE':
        api_url = f'https://bettracker.sc2vagr6376.universe.wf/backend/api.php?action=recommended_stake&tipster={config.tipster}&odds={config.cote}&target_percentage=1&recover_losses=1'
        req = requests.get(api_url, verify=False)
        resp_json = req.json()
        try:
            config.mise = round(float(resp_json.get('recommended_stake', 0)), 2)
        except Exception:
            config.mise = round(float(getattr(config, 'mise', 0)), 2)
        # Si 'last_lost_bet_id' existe, le récupérer sinon mettre une chaîne vide
        config.bet_to_recover_id = resp_json.get('last_lost_bet_id') or ''
        config.log_clear_line(logline)
        if config.mise < 0.2:
            config.mise = 0.2
        return True
    else:
        if RedisIPC.get_loss(config.scriptType) is not None:
            config.perte = RedisIPC.get_loss(config.scriptType)
        config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
    txtlog = "cote : " + str(config.cote) + " | perte : " + str(
        config.perte) + " | wantwin : " + str(
        config.wantwin) + " | mise : " + str(config.mise)
    config.log(txtlog, 'info', False, indent=3)
    logline += 1
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
    config.log_clear_line(logline)
    return True


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 0
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.perte = 2
    print(config.perte)
    GetMise(driver)
