import time
import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetMise import GetMise


# from ChromeDriver.SetDriver1 import driver


def PlacerMise(driver, constructor=False):
    sending_mise = False
    if config.scriptType == 'LIVE' and config.site_type == 'mobile_site' and constructor:
        saved_class_cpn_amount = config.classes['cpn_amount']
        config.classes['cpn_amount'] = config.classes['cpn_action_amount']
        
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, config.classes['cpn_amount'][config.site_type])))
    except Exception as e:

        config.log(f"CHAMP DE MISE NON TROUVÉ {config.classes['cpn_amount'][config.site_type]}", 'error', False)
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, config.classes['cpn_amount'][config.site_type])
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, config.classes['cpn_amount_input'][config.site_type])
        tentative = 0
        while not sending_mise and tentative < 10:
            GetMise(driver)
            cpn_setting.clear()
            cpn_setting.send_keys(str(config.mise))
            l = cpn_setting.get_attribute("value")
            config.log("mise insérrer : " + str(l))
            if str(l) == str(config.mise):
                sending_mise = True

            else:
                tentative = tentative + 1
                config.log('mauvaise mise insérée!', 'warning', False)
                time.sleep(1)
    if config.scriptType == 'LIVE' and config.site_type == 'mobile_site' and constructor:
        config.classes['cpn_amount'] = saved_class_cpn_amount
    return sending_mise


if __name__ == "__main__":

    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '40A'
    config.perte = 21.34
    PlacerMise(driver)
