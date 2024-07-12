#GetBetListSet
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from GetIfMatchPage import GetIfMatchPage


def GetBetListSet(driver,set):
    #driver.switch_to.window(driver.window_handles[0])
    #print('recherche du champ déroulant...')
    selection = False
    tentative_menu = 0
    clic = False
    while not selection and tentative_menu < 10:
        try:
            #on cherche le champ déroulant du menu tps règlementaire
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'scoreboard-nav__select'))
            )
        except Exception as e:
            tentative_menu += 1
            time.sleep(1)#on attend 1 seconde
            if tentative_menu>10:
                print(f"#E005\ Champ déroulant non trouvé : {e}")
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav__select')
            try:
                #on clic dessus pour l'ouvrir
                select_form[0].click()
            except Exception as e:
                print(f"#E006\ impossible de cliquer sur le champ déroulant : {e}")
                tentative_menu += 1
            else:
                tentative_menu_set = 0
                while not clic and tentative_menu_set <10:
                    try:
                        #on attend que les element du menu s'affiche
                        element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, 'multiselect__element'))
                        )
                    except Exception as e:
                        tentative_menu_set +=1
                        time.sleep(1)
                        if tentative_menu_set ==10:
                            print(f"#E007\ aucun element dans le champ déroulant : {e}")
                    else:
                        # on recupère la liste des éléments du menu
                        select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                                 'multiselect__element')
                        if len(select_form_set_1) > 0:#Si des liens sont trouvés
                            for select_option in select_form_set_1:
                                get_select_option =False
                                tentative_get_select_option = 0
                                while not get_select_option and tentative_get_select_option<5:
                                    try:
                                        #on récupère le texte du menu
                                        select_span = select_option.find_elements(By.CLASS_NAME, 'multiselect__option')[0]
                                        select_option_text = select_span.find_elements(By.TAG_NAME, 'span')[
                                            0].get_attribute('title')
                                    except Exception as e:
                                        tentative_get_select_option += 1
                                        time.sleep(1)
                                        if tentative_get_select_option == 5:
                                            print(f"#E008\ impossible de récuprer le texte du menu : {e}")
                                    else:
                                        get_select_option=True
                                        #on a reussi a avoir le nom de l'eleeznt
                                        if select_option_text.strip() == set:
                                            print('menu :' + set)
                                            select_option_click = False
                                            tentative_select_option_click = 0
                                            while not select_option_click and tentative_select_option_click<5:
                                                try:
                                                    select_option.click()
                                                    time.sleep(1)
                                                except Exception as e:

                                                    tentative_select_option_click += 1
                                                    if tentative_select_option_click==5:
                                                        print(f"#E009\ clic impossible menu {set} : {e}")

                                                else:
                                                    select_option_click = True
                                                    paris = False
                                                    tentative_paris = 0
                                                    while not paris and tentative_paris < 5:
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
                                                                paris = True
                                                            else:
                                                                tentative_paris += 1
                                                                if tentative_paris == 5:
                                                                    print(f"#E0010\ Impossible d'écrire paris : {e}")
                                                                time.sleep(1)
                                                        except Exception as e:
                                                            tentative_paris += 1
                                                            print(f"#E0011\ Impossible d'écrire paris : {e}")
                                                            if GetIfMatchPage(driver) != True:
                                                                return
                                                        else:
                                                            return True
