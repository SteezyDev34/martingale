import time

from selenium.webdriver.support.wait import WebDriverWait

from Functions.Function_GetSetActuel import GetSetActuel, GetQTtActuel
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.ModalHandler import ModalHandler
def AfficherParis(driver):
    config.saveLog('recherche du champ déroulant...', config.newmatch)
    GetSetActuel(driver)
    selection = False
    tentative = 0
    clic = False
    while not selection and tentative <6:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'game-toolbar__sub-games-dropdown'))
            )
        except Exception as e:
            config.saveLog(f"#E0012\nUne erreur est survenue : {e}")
            config.saveLog("ERROR : champ déroulant non trouvé")
            tentative = tentative +1
            config.saveLog(str(tentative),  config.newmatch)
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'game-toolbar__sub-games-dropdown')
            try:
                select_form[0].click()
            except Exception as e:
                config.saveLog(f"#E0013\nUne erreur est survenue : {e}", config.newmatch)
                config.saveLog("Erreur lors du clic sur le champ deroulant", config.newmatch)
                ModalHandler(driver)
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
                                if  str(config.set_actuel) == "1":
                                    theset = "1er"
                                else:
                                    theset = str(config.set_actuel)+"ème"
                                if select_option_text.strip().lower() == str(theset).lower()+' set Evénements rapides'.lower():
                                    config.saveLog('Lien '+select_option_text.lower()+' = '+str(theset).lower()+' set Evénements rapides'.lower(), config.newmatch)
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.saveLog(f"#E0015\nUne erreur est survenue : {e}", config.newmatch)
                                        config.saveLog("ERROR : clic impossible menu 1set", config.newmatch)
                                        tentative = tentative + 1
                                        config.saveLog(str(tentative), config.newmatch)
                                        ModalHandler(driver)
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 10:
                                            try:
                                                toolbar = driver.find_elements(By.CLASS_NAME,
                                                                     'game-toolbar')[
                                                    0]
                                                searchbutton = toolbar.find_elements(By.CLASS_NAME,'ui-search')[0]
                                                searchbutton.click()
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                     'ui-search__input')[
                                                    0].clear()
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                     'ui-search__input')[
                                                    0].send_keys(
                                                    "Paris")
                                                l = toolbar.find_elements(By.CLASS_NAME,
                                                                         'ui-search__input')[
                                                    0].get_attribute("value")

                                                if l == "Paris":
                                                    paris = 1
                                                else:
                                                    tentative = tentative+1
                                            except Exception as e:
                                                config.saveLog(f"#E0016\nUne erreur est survenue : {e}")
                                                config.saveLog("ERROR : impossible ecrire 'Paris'")
                                                if GetIfMatchPage(driver) != True:
                                                    break
                                            else:
                                                selection = True
                                else:
                                    config.saveLog('Lien '+select_option_text.lower()+' > '+str(theset).lower()+' set Evénements rapides'.lower(), config.newmatch)
    return selection
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    AfficherParis(driver)
