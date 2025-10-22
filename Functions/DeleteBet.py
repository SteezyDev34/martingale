from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfNewSite import GetIfNewSite


def DeleteBet(driver):
    # driver.switch_to.window(driver.window_handles[0])
    try:
        element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, config.classes['coupon_bet_remove'][config.site_type]))
        )
        element = driver.find_element(By.CLASS_NAME, config.classes['coupon_bet_remove'][config.site_type])
        element.click()

    except:
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['coupon_bet_remove_lock'][config.site_type]))
            )
            element = driver.find_element(By.CLASS_NAME, config.classes['coupon_bet_remove_lock'][config.site_type])
            element.click()
        except:
            return False
        else:
            return True
    else:
        # print("coupon supprimé")
        return True


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '40A'

    DeleteBet(driver)
