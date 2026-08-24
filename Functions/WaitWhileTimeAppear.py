from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


def WaitWhileTimeAppear(driver):
    from Functions.BridgeAdapter import bridge_active
    if bridge_active():
        return True
    tentative = 0
    time_show = False

    while not time_show and tentative < 10:
        tentative += 1
        try:
            bet_items = driver.find_elements(By.CLASS_NAME,
                                             config.classes['dashboard-game__block'][
                                                 config.site_type])
        except:
            # s'il y une erreur on passe au suivant
            return False
        else:
            if len(bet_items) <= 0:
                config.log('AUCUN MATCHS RÉCUPÉ', 'warning', True)
                return False  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
            i = 0
            for bet_item in bet_items:
                try:
                    # Attendre jusqu'à 10 secondes que l'élément s'affiche dans bet_item
                    wait = WebDriverWait(bet_item, 1)
                    time_element = wait.until(EC.presence_of_element_located(
                        (By.CLASS_NAME, config.classes['events_time'][config.site_type])))
                except Exception as e:
                    events_time_selector = config.classes['events_time'][config.site_type]
                    config.log(
                        f'heure de debut non trouvé {events_time_selector} ',
                        'warning', True)
                else:
                    return True


if '__main__' == __name__:
    print(WaitWhileTimeAppear(driver))
