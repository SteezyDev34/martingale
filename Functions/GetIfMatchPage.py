# Function_GetIfMatchPage

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


# VÉRIFIERR SI PAGE DE MATCH
def GetIfMatchPage(driver):
    from Functions.BridgeAdapter import bridge_active
    if bridge_active():
        try:
            from websocket_server import bridge
            state = bridge.get_state()
            if state and (state.get('score') or state.get('isMatchPage')):
                return True
        except Exception:
            pass
        config.log('Tableau des scores introuvable!', 'warning', False, show_script_type=False)
        config.log_clear_line()
        return False
    # driver.switch_to.window(driver.window_handles[0])
    '''Recherche du container de match live'''
    try:

        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, config.classes['scoreboard'][config.site_type]))
        )
    except:
        config.log('Tableau des scores introuvable!', 'warning', False, show_script_type=False)
        config.log_clear_line()
        return False
    else:
        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['end_match_stats'][config.site_type]))
            )
        except:
            # config.log('Tableau des stats introuvable!', 'info', False, show_script_type=False)
            # config.log_clear_line()
            # config.log('PAGE DE MATCH!', 'info', False, show_script_type=False)
            # config.log_clear_line()
            return True
        else:
            try:
                ul_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, config.classes['resume_text_content'][config.site_type]))
                )
            except Exception as e:
                config.log('MATCH TERMINÉ!', 'info', show_script_type=False)
                driver.get(config.site_url)
                return False
            else:
                ul_text = ul_element.text
                # Vérifier si le texte contient le mot "résume", indépendamment de la casse
                if 'résume' in ul_text.lower() or 'terminé' in ul_text.lower():
                    config.log('MATCH TERMINÉ!', 'info', show_script_type=False)
                    driver.get(config.site_url)
                    return False
                else:
                    config.log("Ce n'est pas une page de résumé", 'info', False, show_script_type=False)
                    config.log_clear_line()
                    driver.get(config.site_url)
                    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.site_type = 'new_site'
    print(GetIfMatchPage(driver))
