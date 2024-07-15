from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import config

def PlacerMise(driver):
    sending_mise = False
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,'cpn-info__division')))
    except Exception as e:
        config.saveLog(f"#E001912\nUne erreur est survenue : {e}",config.newmatch)
        config.saveLog("CHAMP DE MISE NON TROUVÉ",config.newmatch)
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, 'cpn-info__division')
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, 'cpn-value-controls__input')
        tentative = 0
        while not sending_mise and tentative<10:
            cpn_setting.clear()
            cpn_setting.send_keys(str(config.mise))
            cpn_setting.clear()
            cpn_setting.send_keys(str(config.mise))
            l = cpn_setting.get_attribute("value")
            config.saveLog("pl mise insérrer : "+str(l), config.newmatch)
            if str(l) == str(config.mise):
                sending_mise = True

            else:
                tentative = tentative + 1
                config.saveLog('mauvaise mise insérée!', config.newmatch)
                time.sleep(1)
    return sending_mise
def PlacerMise30(driver,mise):
    sending_mise = False
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,'cpn-info__division')))
    except Exception as e:
        config.saveLog(f"#E001912\nUne erreur est survenue : {e}",config.newmatch)
        config.saveLog("CHAMP DE MISE NON TROUVÉ",config.newmatch)
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, 'cpn-info__division')
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, 'cpn-value-controls__input')
        tentative = 0
        while not sending_mise and tentative<10:
            cpn_setting.clear()
            cpn_setting.send_keys(str(config.mise))
            cpn_setting.clear()
            cpn_setting.send_keys(str(config.mise))
            l = cpn_setting.get_attribute("value")
            config.saveLog("mise insérrer : "+str(l),config.newmatch)
            if str(l) == str(config.mise):
                sending_mise = True

            else:
                tentative = tentative + 1
                config.saveLog('mauvaise mise insérée!',config.newmatch)
                time.sleep(1)
    return sending_mise
def PlacerMise4030(driver,mise):
    sending_mise = False
    try:

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,'cpn-info__division')))
    except Exception as e:
        config.saveLog(f"#E001912\nUne erreur est survenue : {e}",config.newmatch)
        config.saveLog("CHAMP DE MISE NON TROUVÉ",config.newmatch)
        return False
    else:
        cpn_setting = driver.find_element(By.CLASS_NAME, 'cpn-info__division')
        cpn_setting = cpn_setting.find_element(By.CLASS_NAME, 'cpn-value-controls__input')
        tentative = 0
        while not sending_mise and tentative<10:
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            cpn_setting.clear()
            cpn_setting.send_keys(str(mise))
            l = cpn_setting.get_attribute("value")
            config.saveLog("mise insérrer : "+str(l),config.newmatch)
            if str(l) == str(mise):
                sending_mise = True

            else:
                tentative = tentative + 1
                config.saveLog('mauvaise mise insérée!',config.newmatch)
                time.sleep(1)
    return sending_mise