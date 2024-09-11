import time

from selenium.webdriver.support.wait import WebDriverWait

from Functions.Function_GetSetActuel import GetSetActuel
import config
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Functions.GetIfMatchPage import GetIfMatchPage
#from ChromeDriver.SetDriver1 import driver

def AfficherParis(driver):
    config.saveLog('recherche du champ déroulant...')
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
            config.saveLog(str(tentative))
        else:
            #récupération du bouton de menu deroulant
            select_form = driver.find_elements(By.CLASS_NAME, 'game-toolbar__sub-games-dropdown')
            try:
                select_form[0].click()
                time.sleep(1)
            except Exception as e:
                config.saveLog(f"#E0013\nUne erreur est survenue : {e}")
                config.saveLog("Erreur lors du clic sur le champ deroulant")
                tentative = tentative+1
                config.saveLog(str(tentative))
            else:
                config.saveLog("ouverture du champ déroulant...")
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'multiselect__element'))
                    )
                except Exception as e:
                    config.saveLog(f"#E0014\nUne erreur est survenue : {e}")
                    config.saveLog("ERROR : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        config.saveLog('Plusieurs liens trouvés....')
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
                                if select_option_text.strip() == str(config.set_actuel)+' Set':
                                    config.saveLog('menu :' + str(config.set_actuel) + ' trouvé in :' + select_option.text)
                                    try:
                                        select_option.click()
                                        time.sleep(1)
                                    except Exception as e:
                                        config.saveLog(f"#E0015\nUne erreur est survenue : {e}")
                                        config.saveLog("ERROR : clic impossible menu 1set")
                                        tentative = tentative + 1
                                        config.saveLog(str(tentative))
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
                                                time.sleep(1)
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
                                                    time.sleep(1)
                                            except Exception as e:
                                                config.saveLog(f"#E0016\nUne erreur est survenue : {e}")
                                                config.saveLog("ERROR : impossible ecrire 'Paris'")
                                                if GetIfMatchPage(driver) != True:
                                                    break
                                            else:
                                                selection = True
                                else:
                                    config.saveLog('SET '+str(config.set_actuel)+' non trouvé : error '+select_option_text)
                    time.sleep(2)
                time.sleep(2)
    return selection

#AfficherParis(driver)