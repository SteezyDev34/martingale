from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
            print("cross no found")
            return False
        else:
            print("coupon supprimé")
            return True
    else:
        # print("coupon supprimé")
        return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '40A'
    GetIfNewSite(driver)
    print(config.site_type)
    DeleteBet(driver)
