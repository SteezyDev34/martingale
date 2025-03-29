# verification_liste_match_live
import time

from selenium.webdriver.common.by import By

import config


def VerificationListeMatchLive(driver):
    try:
        config.log('         Recherche tableau des scores', 'info', False)
        config.log('         CLASS="betting-content__main"', 'info', False)
        driver.find_element(By.CLASS_NAME, 'betting-content__main')
    except Exception as e:
        config.log_clear_line(2)
        config.log('        ⚠️Liste match live non visible!', 'warning', False)
        time.sleep(2)
        config.log_clear_line()
        return False
    else:
        config.log_clear_line(2)
        if not config.print_match_live_text:
            config.log('    Liste match live OK!', 'success', False)
            time.sleep(0.5)
            config.log_clear_line()
            config.print_match_live_text = True
        return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    VerificationListeMatchLive(driver)
