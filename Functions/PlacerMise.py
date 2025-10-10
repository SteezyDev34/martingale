import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetMise import GetMise


# from ChromeDriver.SetDriver1 import driver


def PlacerMise(driver):
    sending_mise = False
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, config.classes['cpn_amount'][config.site_type])))
    except Exception as e:

        config.log("CHAMP DE MISE NON TROUVÉ", 'error', False)
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
    return sending_mise


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetIfNewSite(driver)
    config.mise = 21.34
    PlacerMise(driver)
