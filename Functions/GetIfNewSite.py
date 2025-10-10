# Function_GetIfMatchPage

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


# VÉRIFIERR SI PAGE DE MATCH
def GetIfNewSite(driver):
    # driver.switch_to.window(driver.window_handles[0])
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, config.classes['go_to_new_platform_link']['old_site']))
        )
    except:
        config.log('NEW SITE', 'warning', True, show_script_type=False)
        config.site_type = 'new_site'
    else:
        config.log('OLD SITE', 'warning', True, show_script_type=False)
        config.site_type = 'old_site'


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetIfNewSite(driver)
    print(config.site_type)
