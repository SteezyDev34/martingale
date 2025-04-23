import inspect
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config


def RetourTpsReg(driver):
    config.log('recherche du champ déroulant...', config.newmatch)
    driver.switch_to.window(driver.window_handles[0])
    selection = False
    tentative = 0
    temps_reg = False
    while not temps_reg and tentative < 10:
        driver.switch_to.window(driver.window_handles[0])
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'game-toolbar__sub-games-dropdown'))
            )
        except Exception as e:
            config.log(f"#E0012\nUne erreur est survenue : {e}")
            config.log("ERROR : champ déroulant non trouvé")
            tentative = tentative + 1
            if tentative == 3:
                config.error = True
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', False)
                print('error champ deroul##12321')
                break
            config.log(str(tentative), config.newmatch)
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'game-toolbar__sub-games-dropdown')
            try:
                select_form[0].click()
            except Exception as e:
                config.log(f"#E0013\nUne erreur est survenue : {e}", config.newmatch)
                config.log("Erreur lors du clic sur le champ deroulant", config.newmatch)
                tentative = tentative + 1
            else:
                config.log("ouverture du champ déroulant...", 0, config.newmatch)
                time.sleep(1)
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, 'multiselect__content-wrapper'))
                    )
                except Exception as e:
                    config.log(f"#E0014\nUne erreur est survenue : {e}")
                    config.log("ERROR : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_option_text = select_option.text
                            except Exception as e:
                                config.log(f"#E0015\nUne erreur est survenue : {e}")
                                config.log("Aucun élements multiselect__option")
                                tentative = tentative + 1
                                config.log(str(tentative))
                            else:
                                theset = "Temps réglementaire"
                                if select_option_text.strip().lower() == str(theset).lower():
                                    config.log('Lien ' + select_option_text.lower() + ' = ' + str(theset).lower(),
                                               config.newmatch)
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.log(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                        config.log("ERROR : clic impossible menu 1set", config.newmatch)
                                        tentative = tentative + 1
                                        config.log(str(tentative), config.newmatch)
                                    else:
                                        return True
                                else:
                                    config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                        theset).lower() + ' set Evénements rapides'.lower(), config.newmatch)
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    RetourTpsReg(driver)
