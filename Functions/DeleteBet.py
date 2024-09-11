import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ChromeDriver.SetDriver1 import driver
def DeleteBet(driver):
    #driver.switch_to.window(driver.window_handles[0])
    try:
        element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "coupon-bet-remove"))
        )
        element = driver.find_element(By.CLASS_NAME,'coupon-bet-remove')
        element.click()

    except:
        try:
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "coupon-bet-lock-remove"))
            )
            element = driver.find_element(By.CLASS_NAME, 'coupon-bet-lock-remove')
            element.click()
        except:
            print("cross no found")
            return False
        else:
            print("coupon supprimé")
            return True
    else:
        print("coupon supprimé")
        return True

DeleteBet(driver)