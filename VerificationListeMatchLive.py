# verification_liste_match_live
from selenium.webdriver.common.by import By
import config


def VerificationListeMatchLive(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'game_content_line')

    except:
        config.saveLog("Liste match live non visible!")
        return False
    else:
        if not config.print_match_live_text:
            config.saveLog("Liste match live OK!")
            config.print_match_live_text = True
        return True
