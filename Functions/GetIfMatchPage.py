# Function_GetIfMatchPage

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


# VÉRIFIERR SI PAGE DE MATCH
def GetIfMatchPage(driver):
    # driver.switch_to.window(driver.window_handles[0])
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'scoreboard-section__scroll'))
        )
    except:
        config.log('        Tableau des scores introuvable!', 'warning', False)
        config.log_clear_line()
        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'statistic-frame'))
            )
        except:
            config.log('        Tableau des stats introuvable!', 'warning', False)
            config.log_clear_line()
            try:
                ul_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'new-breadcrumbs'))
                )
            except Exception as e:
                config.log('     Ce n\'est pas une page de match', 'warning', False)
                config.log_clear_line()
                config.error = True
                return False
            else:
                config.log_clear_line(5)
                # Récupérer le texte du <ul>
                ul_text = ul_element.text
                print(ul_text)
                # Vérifier si le texte contient le mot "résume", indépendamment de la casse
                if 'résume' in ul_text.lower():
                    config.log('     MATCH TERMINÉ!', 'info', False)
                    driver.get(config.site_url)
                    config.error = True
                    return False
                else:
                    config.log('     Ce n\'est pas une page de résumé', 'info', False)
                    config.log_clear_line()
                    driver.get(config.site_url)
                    config.error = True
                    return False

        else:
            config.log('     MATCH TERMINÉ!', 'info', False)
            driver.get(config.site_url)
            config.error = True
            return False
    else:
        config.log('     PAGE MATCH OK!', 'info', False)
        config.log_clear_line()
        return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    print(GetIfMatchPage(driver))
