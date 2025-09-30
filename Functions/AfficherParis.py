import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.ModalHandler import ModalHandler


def AfficherParis(driver, categorie='', type_de_pari='', ):
    config.log('recherche du champ déroulant...', '', True, 2)
    if config.scriptType in config.allScriptType:
        print(config.scriptType)
        GetSetActuel(driver)
        GetScoreActuel(driver)

        if str(config.set_actuel) == "1":
            theset = "1er"
        else:
            theset = str(config.set_actuel) + "ème"
        if config.scriptType == '1SET' or config.scriptType == 'BREAK':
            args = ' set'
        else:
            args = ' set Evénements rapides'

        if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
            key = 'Gagne le jeu avec le score.'
        elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            key = 'Nombre exact de points dans un jeu'
        elif config.scriptType == '1SET':
            key = '1X2'
        elif config.scriptType == 'BREAK':
            key = 'Gagne dans le jeu'
        else:
            if config.site_type == 'old_site':
                key = 'Score de la partie. ' + theset + args
            else:
                key = 'Score du jeu. ' + theset + args
    else:
        theset = ''
        args = categorie
        key = type_de_pari
    selection = False
    tentative = 1
    clic = False

    while not selection and tentative < 6:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['period_select'][config.site_type]))
            )
        except Exception as e:
            config.log(f"Champ déroulant {config.classes['period_select'][config.site_type]} introuvable !", "warning",
                       False, 2)
            config.log(f'tentative {tentative}', 'warning', True, 2)
            tentative = tentative + 1
        else:
            select_form = driver.find_elements(By.CLASS_NAME, config.classes['period_select'][config.site_type])
            # config.log('Champ déroulant trouvé !', 'success', True, 2)
            try:
                select_form[0].click()
            except Exception as e:
                config.log("#E0013 Erreur lors du clic sur le champ deroulant", 'warning', False, 2)
                ModalHandler(driver)
                tentative = tentative + 1
            else:
                config.log('ouverture du champ déroulant...', 'info', True, 2)
                time.sleep(1)
                try:
                    print('decttion')
                    element = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, config.classes['multiselect_container_wrapper'][config.site_type]))
                    )
                except Exception as e:
                    config.log('#E0014 aucun element dans le champ déroulant', 'error', False, 2)
                    tentative = tentative + 1
                    config.log(f'tentative {tentative}', 'warning', False, 2)
                else:

                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             config.classes['multiselect_element'][config.site_type])
                    print('detect multiselect_element', len(select_form_set_1))
                    if len(select_form_set_1) > 0:
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_option_text = select_option.text
                            except Exception as e:
                                config.log('#E0015 ucun élements multiselect__option', 'error', False, 2)
                                tentative = tentative + 1
                                config.log(f'tentative {tentative}', 'warning', False, 2)

                            else:

                                if select_option_text.strip().lower() == str(
                                        theset).lower() + f'{args}'.lower():
                                    config.log('            Lien ' + select_option_text.lower() + ' = ' + str(
                                        theset).lower() + ' set Evénements rapides'.lower(), 'warning', True, 2)
                                    try:
                                        select_option.click()
                                    except Exception as e:
                                        config.log(f'        #E0016 clic impossible menu 1set', 'warning', False, 2)
                                        tentative = tentative + 1
                                        config.log(f'        tentative {tentative}', 'warning', False, 2)
                                        ModalHandler(driver)
                                    else:
                                        paris = 0
                                        tentative = 0
                                        while paris == 0 and tentative < 5:
                                            try:
                                                toolbar = driver.find_elements(By.CLASS_NAME,
                                                                               config.classes['search_toolbar'][
                                                                                   config.site_type]
                                                                               )[
                                                    0]
                                                searchbutton = toolbar.find_elements(By.CLASS_NAME, config.classes[
                                                    'ui_search_to_click'][
                                                    config.site_type])[0]
                                                searchbutton.click()
                                                print('click')
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      config.classes[
                                                                          'search_input'][
                                                                          config.site_type])[
                                                    0].clear()
                                                print('clear')

                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      config.classes[
                                                                          'search_input'][
                                                                          config.site_type])[
                                                    0].send_keys(
                                                    key)
                                                print(f'send {key}')
                                                l = toolbar.find_elements(By.CLASS_NAME,
                                                                          config.classes[
                                                                              'search_input'][
                                                                              config.site_type])[
                                                    0].get_attribute("value")
                                                print(f'l : {l}')
                                                if l == key:
                                                    try:
                                                        print('wait for market grid container')
                                                        element = WebDriverWait(driver, 2).until(
                                                            EC.presence_of_element_located(
                                                                (By.CLASS_NAME, config.classes[
                                                                    'bet_list_container'][
                                                                    config.site_type]))
                                                        )
                                                    except:
                                                        print(
                                                            f"no market grid {config.classes['bet_list_container'][config.site_type]}")
                                                        if key == 'Paris':
                                                            key = 'Game Score. ' + theset + args
                                                        elif key == 'Game Score. ' + theset + args:
                                                            key = 'Score de la partie'
                                                        else:
                                                            key = 'Paris'
                                                    else:
                                                        print('find market grid')
                                                        paris = 1
                                                else:
                                                    tentative = tentative + 1


                                            except Exception as e:
                                                config.log(
                                                    f'        #ERROR16 : impossible ecrire {key}, {e}',
                                                    'warning',
                                                    False)
                                                config.log_clear_line()
                                                if GetIfMatchPage(driver) != True:
                                                    config.error = True
                                                    break
                                            else:
                                                selection = True
                                else:
                                    config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                        theset).lower() + f'{args}'.lower(), 'warning', True, 2)
                                    continue
                        return selection
    return selection


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = 'LIVE'
    GetIfNewSite(driver)
    print(config.site_type)
    AfficherParis(driver, 'Corners')
