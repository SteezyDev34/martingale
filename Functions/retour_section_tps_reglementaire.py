import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from Functions.Function_GetSetActuel import GetSetActuel, GetQTtActuel
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Functions.GetIfMatchPage import GetIfMatchPage
def RetourTpsReg(driver):
    config.saveLog('recherche du champ déroulant...', config.newmatch)
    selection = False
    tentative = 0
    temps_reg = False
    while not temps_reg and tentative < 10:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'game-toolbar__sub-games-dropdown'))
            )
        except Exception as e:
            config.saveLog(f"#E0012\nUne erreur est survenue : {e}")
            config.saveLog("ERROR : champ déroulant non trouvé")
            tentative = tentative +1
            if tentative == 10:
                config.error=True
                break
            config.saveLog(str(tentative),  config.newmatch)
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'game-toolbar__sub-games-dropdown')
            try:
                select_form[0].click()
            except Exception as e:
                config.saveLog(f"#E0013\nUne erreur est survenue : {e}", config.newmatch)
                config.saveLog("Erreur lors du clic sur le champ deroulant", config.newmatch)
                tentative = tentative+1
            else:
                config.saveLog("ouverture du champ déroulant...",0, config.newmatch)
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, 'multiselect__content-wrapper'))
                    )
                except Exception as e:
                    config.saveLog(f"#E0014\nUne erreur est survenue : {e}")
                    config.saveLog("ERROR : aucun element dans le champ déroulant ")
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
                                config.saveLog(f"#E0015\nUne erreur est survenue : {e}")
                                config.saveLog("Aucun élements multiselect__option")
                                tentative = tentative+1
                                config.saveLog(str(tentative))
                            else:
                                theset = "Temps réglementaire"
                                if select_option_text.strip().lower() == str(theset).lower():
                                    config.saveLog('Lien '+select_option_text.lower()+' = '+str(theset).lower(), config.newmatch)
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.saveLog(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                        config.saveLog("ERROR : clic impossible menu 1set", config.newmatch)
                                        tentative = tentative + 1
                                        config.saveLog(str(tentative), config.newmatch)
                                    else:
                                        return True
                                else:
                                    config.saveLog('Lien '+select_option_text.lower()+' > '+str(theset).lower()+' set Evénements rapides'.lower(), config.newmatch)
    return False
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])
    RetourTpsReg(driver)