from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfNewSite import GetIfNewSite


def DeleteBet(driver):
    from Functions.BridgeAdapter import bridge_active, bridge_delete_bet
    if bridge_active():
        return bridge_delete_bet()
    # driver.switch_to.window(driver.window_handles[0])
    if config.site_type == 'mobile_site':
        try:
            container = driver.find_element(By.CLASS_NAME, 'bottom-navigation-link-coupon-content__count')
            if not container.is_displayed()  and container.text == '0':
                return False
        except:
            pass
        else:
            try:
                container = driver.find_element(By.CLASS_NAME, 'quick-coupon-container__coupon')
                if not container.is_displayed():
                    bottom_navigation_item_coupon = driver.find_element(By.CLASS_NAME, 'bottom-navigation__item--coupon')
                    bottom_navigation_item_coupon.click()
            except:
                pass
    count = 0
    while True:
        try:
            element = WebDriverWait(driver, 0.5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['coupon_bet_remove'][config.site_type]))
            )
            element = driver.find_element(By.CLASS_NAME, config.classes['coupon_bet_remove'][config.site_type])
            element.click()

        except:
            try:
                element = WebDriverWait(driver, 0.5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, config.classes['coupon_bet_remove_lock'][config.site_type]))
                )
                element = driver.find_element(By.CLASS_NAME, config.classes['coupon_bet_remove_lock'][config.site_type])
                element.click()
            except:
                count +=1
                print('pas de bouton supprimé')
                if count >=2:
                    break
        else:
            count = 0
            print("coupon supprimé")


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '40A'

    DeleteBet(driver)
