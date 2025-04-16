from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.ModalHandler import ModalHandler


def AfficherParis(driver):
    config.log('recherche du champ déroulant...', '', False, 2)
    driver.switch_to.window(driver.window_handles[0])
    GetSetActuel(driver)
    selection = False
    tentative = 1
    clic = False
    key = 'Paris'
    if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
        key = 'Score du Jeu.'
    elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
        key = 'Nombre exact de points dans un jeu'
    while not selection and tentative < 6:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'game-toolbar__sub-games-dropdown'))
            )
        except Exception as e:
            config.log('Champ déroulant introuvable !', 'warning', False, 2)
            config.log(f'tentative {tentative}', 'warning', False, 2)
            tentative = tentative + 1
            config.log_clear_line()
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'game-toolbar__sub-games-dropdown')
            config.log('Champ déroulant trouvé !', 'success', False, 2)
            config.log_clear_line()
            try:
                select_form[0].click()
            except Exception as e:
                config.log("#E0013 Erreur lors du clic sur le champ deroulant", 'warning', False, 2)
                config.log_clear_line()
                ModalHandler(driver)
                tentative = tentative + 1
            else:
                config.log('ouverture du champ déroulant...', 'info', False, 2)
                config.log_clear_line()
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, 'multiselect__content-wrapper'))
                    )
                except Exception as e:
                    config.log('#E0014 aucun element dans le champ déroulant', 'error', False, 2)
                    config.log_clear_line()
                    tentative = tentative + 1
                    config.log(f'tentative {tentative}', 'warning', False, 2)
                    config.log_clear_line()
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
                                config.log('#E0015 ucun élements multiselect__option', 'error', False, 2)
                                config.log_clear_line()
                                tentative = tentative + 1
                                config.log(f'tentative {tentative}', 'warning', False, 2)
                                config.log_clear_line()

                            else:
                                if str(config.set_actuel) == "1":
                                    theset = "1er"
                                else:
                                    theset = str(config.set_actuel) + "ème"
                                if select_option_text.strip().lower() == str(
                                        theset).lower() + ' set Evénements rapides'.lower():
                                    config.log('            Lien ' + select_option_text.lower() + ' = ' + str(
                                        theset).lower() + ' set Evénements rapides'.lower(), 'warning', False, 2)
                                    config.log_clear_line()
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.log(f'        #E0016 clic impossible menu 1set', 'warning', False, 2)
                                        tentative = tentative + 1
                                        config.log(f'        tentative {tentative}', 'warning', False, 2)
                                        config.log_clear_line()
                                        ModalHandler(driver)
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 10:
                                            try:
                                                toolbar = driver.find_elements(By.CLASS_NAME,
                                                                               'game-toolbar')[
                                                    0]
                                                searchbutton = toolbar.find_elements(By.CLASS_NAME, 'ui-search')[0]
                                                searchbutton.click()
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      'ui-search__input')[
                                                    0].clear()
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      'ui-search__input')[
                                                    0].send_keys(
                                                    key)
                                                l = toolbar.find_elements(By.CLASS_NAME,
                                                                          'ui-search__input')[
                                                    0].get_attribute("value")

                                                if l == key:
                                                    paris = 1
                                                else:
                                                    tentative = tentative + 1
                                            except Exception as e:
                                                config.log(f'        #ERROR16 : impossible ecrire {key}', 'warning',
                                                           True)
                                                config.log_clear_line()
                                                if GetIfMatchPage(driver) != True:
                                                    break
                                            else:
                                                config.log_clear_line()
                                                selection = True
                                else:
                                    config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                        theset).lower() + ' set Evénements rapides'.lower(), 'warning', False, 2)
                                    config.log_clear_line()
                        return selection
    print('error #3GHHE ', config.error)
    return selection


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    AfficherParis(driver)
