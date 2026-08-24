# verification_liste_match_live
import time

from selenium.webdriver.common.by import By

import config


def VerificationListeMatchLive(driver):
    from Functions.BridgeAdapter import bridge_active
    if bridge_active():
        return True
    try:
        config.log('         Recherche tableau des scores', 'info')
        driver.find_element(By.CLASS_NAME, config.classes['live_content'][config.site_type])
    except Exception as e:
        config.log('        Liste match live non visible!', 'warning')
        time.sleep(2)
        return False
    else:
        if not config.print_match_live_text:
            config.log('    Liste match live OK!', 'success')
            time.sleep(0.5)
            config.print_match_live_text = True
        return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    VerificationListeMatchLive(driver)
