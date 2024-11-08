import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def DeleteBet(driver):
    #driver.switch_to.window(driver.window_handles[0])
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "cpn-bet__remove"))
        )
        time.sleep(2)
        element = driver.find_element(By.CLASS_NAME,'cpn-bet__remove')
    except:
        print("cross no found")
        return False
    else:
        element.click()
        return True