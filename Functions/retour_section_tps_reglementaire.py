import inspect
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfNewSite import GetIfNewSite


def RetourTpsReg(driver, theset="Temps réglementaire"):
    if config.site_type == 'mobile_site':
        return RetourTpsRegMobile(driver, theset)
    config.log('recherche du champ déroulant...', config.newmatch)
    # driver.switch_to.window(driver.window_handles[0])
    selection = False
    tentative = 0
    temps_reg = False
    while not temps_reg and tentative < 10:
        # driver.switch_to.window(driver.window_handles[0])
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['period_select'][config.site_type]))
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
        else:
            select_form = driver.find_elements(By.CLASS_NAME, config.classes['period_select'][config.site_type])
            try:
                select_form[0].click()
            except Exception as e:
                config.log(f"#E0013\nUne erreur est survenue : {e}", config.newmatch)
                config.log("Erreur lors du clic sur le champ deroulant", config.newmatch)
                tentative = tentative + 1
            else:
                config.log("souverture du champ déroulant...", 0, config.newmatch)
                time.sleep(1)
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, config.classes['multiselect_container_wrapper'][config.site_type]))
                    )
                except Exception as e:
                    config.log("#E0014 : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             config.classes['multiselect_element'][config.site_type])
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

                                if select_option_text.strip().lower() == str(theset).lower():
                                    # config.log('Lien ' + select_option_text.lower() + ' = ' + str(theset).lower(),config.newmatch)
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.log(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                        config.log("ERROR : clic impossible menu 1set", config.newmatch)
                                        tentative = tentative + 1
                                        config.log(str(tentative), config.newmatch)
                                    else:
                                        return True
                                # else:
                                # config.log('Lien ' + select_option_text.lower() + ' > ' + str(theset).lower() + ' set Evénements rapides'.lower(), config.newmatch)
    return False

def RetourTpsRegMobile(driver, theset="Temps réglementaire"):
    config.log('retour tps regl recherche du champ déroulant mobile...', '', indent=2)
    logline = 1
    selection = False
    tentative = 0
    while not selection and tentative < 3:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, config.classes['multiselect_container_wrapper'][config.site_type]))
                )
            except Exception as e:
                config.log('#E0014 aucun element dans le champ déroulant', 'error', False, 2)
                tentative = tentative + 1
                config.log(f'tentative {tentative}', 'warning', True, 2)
            else:

                select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                            config.classes['multiselect_element'][config.site_type])
                if len(select_form_set_1) > 0:
                    for select_option in select_form_set_1:
                        if selection == True:
                            break
                        try:
                            select_option_text = select_option.text
                        except Exception as e:
                            config.log('#E0015 Aucun élements multiselect__option', 'error', False, 3)
                            logline += 1
                            tentative = tentative + 1
                            config.log(f'tentative {tentative}', 'warning', False, 3)
                            logline += 1

                        else:
                            if select_option_text.strip().lower() == str(
                                    theset).lower():
                                config.log('Lien ' + select_option_text.lower() + ' = ' + str(
                                    theset).lower() + 'set Evénements rapides'.lower(), 'warning', False, 3)
                                logline += 1
                                try:
                                    select_option.click()
                                except Exception as e:
                                    config.log(f'#E0016 clic impossible menu 1set', 'warning', False, 3)
                                    logline += 1
                                    tentative = tentative + 1
                                    config.log(f'tentative {tentative}', 'warning', False, 3)
                                    logline += 1
                                else:
                                    paris = 0
                                    tentative = 0
                                    driver.execute_script("window.scrollTo(0, 0);")
                                    selection = True
                            else:
                                config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                    theset).lower(), 'warning', False, 3)
                                logline += 1
                                continue

    config.log_clear_line(logline)
    return selection



if __name__ == "__main__":

    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '40A'
    config.mise = 0.2
    # driver.switch_to.window(driver.window_handles[0])
    RetourTpsRegMobile(driver)
