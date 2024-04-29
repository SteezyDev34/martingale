from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def main(driver,mise):
    #driver.switch_to.window(driver.window_handles[0])
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,'cpn-info__division')))
    except Exception as e:
        print(f"#E001912\nUne erreur est survenue : {e}")
        print("CHAMP DE MISE NON TROUVÉ")
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, 'cpn-info__division')
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, 'cpn-value-controls__input')
        sending_mise = 0
        tentative = 0
        while sending_mise == 0 and tentative<10:
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            l = cpn_setting.get_attribute("value")
            print("mise insérrer : "+str(l))
            if str(l) == str(mise):
                sending_mise = 1
                return True

            else:
                tentative = tentative + 1
                print('mauvaise mise insérée!')
                time.sleep(1)