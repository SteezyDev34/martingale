# SelectionDesParisDuSet.py
import time
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from config import matchlist_file_name
from Functions import VerificationMatchTrouve


def selection_des_paris_du_set(driver,set):
    #driver.switch_to.window(driver.window_handles[0])
    print('recherche du champ déroulant...')
    selection = False
    tentative = 0
    clic = False
    while selection == False and tentative <6:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'scoreboard-nav__select'))
            )
        except Exception as e:
            print(f"#E0012\nUne erreur est survenue : {e}")
            print("ERROR : champ déroulant non trouvé")
            tentative = tentative +1
        else:
            select_form = driver.find_elements(By.CLASS_NAME, 'scoreboard-nav__select')
            try:
                select_form[0].click()
                time.sleep(1)
            except Exception as e:
                print(f"#E0013\nUne erreur est survenue : {e}")
                tentative = tentative+1
            else:
                print("ouverture du champ déroulant...")
                try:
                    element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, 'multiselect__element'))
                    )
                except Exception as e:
                    print(f"#E0014\nUne erreur est survenue : {e}")
                    print("ERROR : aucun element dans le champ déroulant ")
                else:
                    select_form_set_1 = driver.find_elements(By.CLASS_NAME,
                                                             'multiselect__element')
                    if len(select_form_set_1) > 0:
                        print('Plusieurs liens trouvés....')
                        for select_option in select_form_set_1:
                            if selection == True:
                                break
                            try:
                                select_span = select_option.find_elements(By.CLASS_NAME,'multiselect__option')[0]
                                select_option_text = select_span.find_elements(By.TAG_NAME,'span')[0].get_attribute('title')
                            except Exception as e:
                                print(f"#E0015\nUne erreur est survenue : {e}")
                                print("no = select_option_text")
                                tentative = tentative+1
                            else:
                                if select_option_text.strip() == set:
                                    try:
                                        select_option.click()
                                        time.sleep(1)
                                    except Exception as e:
                                        print(f"#E0015\nUne erreur est survenue : {e}")
                                        print("ERROR : clic impossible menu 1set")
                                        tentative = tentative + 1
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
                                                print(f"#E0016\nUne erreur est survenue : {e}")
                                                print("ERROR : impossible ecrire 'Paris'")
                                                if not VerificationMatchTrouve.fromUrl(driver, matchlist_file_name):
                                                    break
                                            else:
                                                selection = True
                                else:
                                    print('SET '+set+' non trouvé : error '+select_option_text)
                    time.sleep(2)
                time.sleep(2)
    return selection
