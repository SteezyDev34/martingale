# verification_liste_match_live
from selenium.webdriver.common.by import By
import config


def VerificationListeMatchLive(driver):

    try:
        driver.find_element(By.CLASS_NAME, 'game_content_line')

    except:
        txtlog = "Liste match live non visible!"
        config.saveLog(txtlog,1,config.newmatch)
        print(txtlog)
        return False
    else:
        if not config.print_match_live_text:
            txtlog = "Liste match live OK!"
            config.saveLog(txtlog,0, config.newmatch)
            config.print_match_live_text = True
        return True
