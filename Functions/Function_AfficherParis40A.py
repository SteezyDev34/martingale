import time

from selenium.webdriver.support.wait import WebDriverWait

from Function_GetSetActuel import GetSetActuel
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from GetIfMatchPage import GetIfMatchPage
def AfficherParis40A(driver):
    config.saveLog('recherche du champ déroulant...', config.newmatch)
    GetSetActuel(driver)
    selection = False
    tentative = 0
    clic = False
    while not selection and tentative <6:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'scoreboard-nav__select'))
            )
        except Exception as e:
            config.saveLog(f"#E0012\nUne erreur est survenue : {e}", config.newmatch)
            config.saveLog("ERROR : champ déroulant non trouvé", config.newmatch)
            tentative = tentative +1
            config.saveLog(str(tentative),  config.newmatch)
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav__select')
            try:
                select_form[0].click()
                time.sleep(5)
            except Exception as e:
                config.saveLog(f"#E0013\nUne erreur est survenue : {e}", config.newmatch)
                config.saveLog("Erreur lors du clic sur le champ deroulant", config.newmatch)
                tentative = tentative+1
            else:
                config.saveLog("ouverture du champ déroulant...", config.newmatch)
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'multiselect__element'))
                    )
                except Exception as e:
                    config.saveLog(f"#E0014\nUne erreur est survenue : {e}", config.newmatch)
                    config.saveLog("ERROR : aucun element dans le champ déroulant ", config.newmatch)
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        config.saveLog('Plusieurs liens trouvés....', config.newmatch)
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_span = select_option.find_elements(By.CLASS_NAME,'multiselect__option')[0]
                                select_option_text = select_span.find_elements(By.TAG_NAME,'span')[0].get_attribute('title')
                            except Exception as e:
                                config.saveLog(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                config.saveLog("Aucun élements multiselect__option", config.newmatch)
                                tentative = tentative+1
                                config.saveLog(str(tentative), config.newmatch)
                            else:
                                if select_option_text.strip() == str(config.set_actuel)+' Set':
                                    config.saveLog('menu :' + str(config.set_actuel) + ' trouvé in :' + select_option.text, config.newmatch)
                                    try:
                                        select_option.click()
                                        time.sleep(1)
                                    except Exception as e:
                                        config.saveLog(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                        config.saveLog("ERROR : clic impossible menu 1set", config.newmatch)
                                        tentative = tentative + 1
                                        config.saveLog(str(tentative), config.newmatch)
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 10:
                                            try:
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].clear()
                                                driver.find_elements(By.CLASS_NAME,
                                                                     'scoreboard-nav-items-search__input')[
                                                    0].send_keys(
                                                    "Paris")
                                                l = driver.find_elements(By.CLASS_NAME,
                                                                         'scoreboard-nav-items-search__input')[
                                                    0].get_attribute("value")

                                                if l == "Paris":
                                                    paris = 1
                                                else:
                                                    tentative = tentative+1
                                                    time.sleep(1)
                                            except Exception as e:
                                                config.saveLog(f"#E0016\nUne erreur est survenue : {e}", config.newmatch)
                                                config.saveLog("ERROR : impossible ecrire 'Paris'", config.newmatch)
                                                if GetIfMatchPage(driver) != True:
                                                    break
                                            else:
                                                selection = True
                                else:
                                    config.saveLog('SET '+str(config.set_actuel)+' non trouvé : error '+select_option_text, config.newmatch)
                    time.sleep(2)
                time.sleep(2)
    return selection

