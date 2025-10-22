import time
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.ModalHandler import ModalHandler
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def AfficherParis(driver, categorie='', type_de_pari=''):
    if config.site_type == 'mobile_site':
        return AfficherParisMobile(driver, categorie, type_de_pari) 
    config.log('recherche du champ déroulant...', '', indent=2)
    logline = 1
    if config.scriptType in config.allScriptType:
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
            key = 'Score de la partie. ' + theset + args
    else:
        theset = ''
        args = categorie
        key = type_de_pari
    selection = False
    tentative = 1

    while not selection and tentative < 3:
        RetourTpsReg(driver)
        GetSetActuel(driver)
        if GetIfMatchPage(driver) != True:
            config.error = True
            break
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['period_select'][config.site_type]))
            )
        except Exception as e:
            period_select_selector = config.classes['period_select'][config.site_type]
            config.log(f"Champ déroulant {period_select_selector} introuvable !", "warning",
                       False, 2)
            logline += 1
            config.log(f'tentative {tentative}', 'warning', False, 2)
            logline += 1
            tentative = tentative + 1
        else:
            select_form = driver.find_elements(By.CLASS_NAME, config.classes['period_select'][config.site_type])
            config.log('Champ déroulant trouvé !', 'success', False, 2)
            logline += 1
            try:
                driver.execute_script("window.scrollTo(0, 0);")
                select_form[0].click()
                time.sleep(1)
            except Exception as e:
                config.log("#E0013 Erreur lors du clic sur le champ deroulant", 'warning', False, 2)
                logline += 1
                ModalHandler(driver)
                tentative = tentative + 1
            else:
                driver.execute_script("window.scrollTo(0, 0);")
                config.log('ouverture du champ déroulant...', 'info', True, 2)
                time.sleep(1)
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
                                        theset).lower() + f'{args}'.lower():
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
                                        ModalHandler(driver)
                                    else:
                                        paris = 0
                                        tentative = 0
                                        driver.execute_script("window.scrollTo(0, 0);")
                                        while paris == 0 and tentative < 1:
                                            try:
                                                try:
                                                    driver.execute_script("window.scrollTo(0, 0);")
                                                    toolbar.find_elements(By.CLASS_NAME,
                                                                          config.classes[
                                                                              'search_input'][
                                                                              config.site_type])[
                                                        0].clear()
                                                    print('clear')
                                                except:
                                                    driver.execute_script("window.scrollTo(0, 0);")
                                                    toolbar = driver.find_elements(By.CLASS_NAME,
                                                                                   config.classes['search_toolbar'][
                                                                                       config.site_type]
                                                                                   )[
                                                        0]
                                                    searchbutton = toolbar.find_elements(By.CLASS_NAME, config.classes[
                                                        'ui_search_to_click'][
                                                        config.site_type])[0]
                                                    searchbutton.click()

                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      config.classes[
                                                                          'search_input'][
                                                                          config.site_type])[
                                                    0].clear()
                                                toolbar.find_elements(By.CLASS_NAME,
                                                                      config.classes[
                                                                          'search_input'][
                                                                          config.site_type])[
                                                    0].send_keys(
                                                    key)
                                                l = toolbar.find_elements(By.CLASS_NAME,
                                                                          config.classes[
                                                                              'search_input'][
                                                                              config.site_type])[
                                                    0].get_attribute("value")
                                                if l == key:
                                                    try:
                                                        element = WebDriverWait(driver, 2).until(
                                                            EC.presence_of_element_located(
                                                                (By.CLASS_NAME, config.classes[
                                                                    'bet_list_container'][
                                                                    config.site_type]))
                                                        )
                                                    except:
                                                        if key == 'Paris':
                                                            key = 'Game Score. ' + theset + args
                                                        elif key == 'Game Score. ' + theset + args:
                                                            key = 'Score de la partie'
                                                        else:
                                                            key = 'Paris'
                                                    else:
                                                        paris = 1
                                                else:
                                                    tentative = tentative + 1


                                            except Exception as e:
                                                tentative += 1
                                                config.log(
                                                    f'#ERROR16 : impossible ecrire {key}',
                                                    'warning',
                                                    False)
                                                logline += 1
                                                if GetIfMatchPage(driver) != True:
                                                    config.error = True
                                                    break
                                            else:
                                                selection = True
                                else:
                                    config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                        theset).lower() + f'{args}'.lower(), 'warning', False, 3)
                                    logline += 1
                                    continue
    config.log_clear_line(logline)
    return selection

def AfficherParisMobile(driver, categorie='', type_de_pari=''):
    config.log('recherche du champ déroulant mobile...', '', indent=2)
    logline = 1
    if config.scriptType in config.allScriptType:
        GetSetActuel(driver)
        GetScoreActuel(driver)
        if str(config.set_actuel) == "1":
            theset = "1er set"
        else:
            theset = str(config.set_actuel) + "ème set"
        if config.scriptType == '1SET' or config.scriptType == 'BREAK':
            args = ' set'
        else:
            args = 'Evénements rapides'
        if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
            key = 'Gagne le jeu avec le score.'
        elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            key = 'Nombre exact de points dans un jeu'
        elif config.scriptType == '1SET':
            key = '1X2'
        elif config.scriptType == 'BREAK':
            key = 'Gagne dans le jeu'
        else:
            key = 'Score de la partie. ' + theset + ' ' + args
    else:
        theset = ''
        args = categorie
        key = type_de_pari
    selection = False
    tentative = 1

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
                            if config.site_type == 'mobile_site':
                                matching_text = select_option_text.strip().lower() == f'{args}'.lower() + '. ' + str(theset).lower()
                            else:
                                matching_text = select_option_text.strip().lower() == str(
                                    theset).lower() + f'{args}'.lower()
                            if matching_text:
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
                                    ModalHandler(driver)
                                else:
                                    paris = 0
                                    tentative = 0
                                    driver.execute_script("window.scrollTo(0, 0);")
                                    while paris == 0 and tentative < 1:
                                        try:
                    
                                            driver.execute_script("window.scrollTo(0, 0);")
                                            toolbar = driver.find_element(By.CLASS_NAME,
                                                                            config.classes['search_toolbar'][
                                                                                config.site_type]
                                                                            )
                                            searchbutton = toolbar.find_elements(By.CLASS_NAME, config.classes[
                                                'search_input'][
                                                config.site_type])[0]
                                            #searchbutton.click()
                                            search_input = toolbar.find_element(By.CSS_SELECTOR, 
                                                        f"input.{config.classes['search_input'][config.site_type]}")
                                            search_input.click()  # Focus sur le champ
                                            time.sleep(0.5)
                                            
                                            # Méthode JavaScript pour vider le champ
                                            driver.execute_script("arguments[0].value = '';", search_input)
                                            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
                                            
                                            search_input.send_keys(key)
                                            l = search_input.get_attribute("value")
                                            if l == key:
                                                try:
                                                    element = WebDriverWait(driver, 2).until(
                                                        EC.presence_of_element_located(
                                                            (By.CLASS_NAME, config.classes[
                                                                'bet_list_container'][
                                                                config.site_type]))
                                                    )
                                                except:
                                                    if key == 'Paris':
                                                        key = 'Game Score. ' + theset + args
                                                    elif key == 'Game Score. ' + theset + args:
                                                        key = 'Score de la partie'
                                                    else:
                                                        key = 'Paris'
                                                else:
                                                    paris = 1
                                            else:
                                                tentative = tentative + 1


                                        except Exception as e:
                                            tentative += 1
                                            config.log(
                                                f'#ERROR16 : impossible ecrire {key}',
                                                'warning',
                                                False)
                                            if config.devMode:
                                                config.log(str(e), 'warning', False)
                                            logline += 1
                                            if GetIfMatchPage(driver) != True:
                                                config.error = True
                                                break
                                        else:
                                            selection = True
                            else:
                                config.log('Lien ' + select_option_text.lower() + ' > ' + str(
                                    theset).lower() + f'{args}'.lower(), 'warning', False, 3)
                                logline += 1
                                continue

    config.log_clear_line(logline)
    return selection


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '40A'
    config.site_type = 'mobile_site'
    #GetIfNewSite(driver)
    print(config.site_type)
    AfficherParis(driver)
