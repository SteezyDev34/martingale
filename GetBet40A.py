import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from GetJeuActuel import GetJeuActuel


def GetBet40A(driver,jeu):
    #driver.switch_to.window(driver.window_handles[0])
    print('RECHERCHE DES PARIS 40 A....')
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    while not clic and tentative_clic<30:
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                    jeu) + ' : 40-40 - Oui")]'))
            )
        except Exception as e:
            tentative_clic+=1
            time.sleep(1)
            if tentative_clic ==5:
                print("Paris Jeu " + str(jeu) + " : 40-40 - Oui NON TROUVÉ!")
                print("Vérificattion si autre jeu en cours...")
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]'))
                    )
                except Exception as e:
                    print('Aucun paris 40A TROUVÉ!')
                    return
                else:
                    list_of_newbet_type = driver.find_elements(By.XPATH,
                                                               '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]')
                    if len(list_of_newbet_type) == 1:
                        list_of_newbet_type = list_of_newbet_type[0].text
                        print(list_of_newbet_type)
                        list_of_newbet_type = list_of_newbet_type.split(" : 40-40 - Oui")
                        jeu = int(list_of_newbet_type[0].split("Jeu ")[1])
                        print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                    elif len(list_of_newbet_type) >= 2:
                        print('PLUSIEURS JEUX TROUVÉS!')
                        newbet_type1 = list_of_newbet_type[0].text
                        newbet_type1 = newbet_type1.split(" : 40-40 - Oui")
                        game1 = int(newbet_type1[0].split("Jeu ")[1])
                        print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                        newbet_type2 = list_of_newbet_type[1].text
                        print(newbet_type2)
                        newbet_type2 = newbet_type2.split(" : 40-40 - Oui")
                        game2 = int(newbet_type2[0].split("Jeu ")[1])
                        print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                        print("vérification ordre de jeu")
                        if game1 < game2:
                            jeu = game1
                            print("Jeu actuel : " + str(jeu))
                        else:
                            jeu = game2
                            print("Jeu actuel : " + str(jeu))
                    else:
                        print('ERROR: try get num game running')
                        tentative_clic+=1
        else:
            try:
                list_of_bet_type = driver.find_elements(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            jeu) + ' : 40-40 - Oui")]')
            except Exception as e:
                print(f"#E0015\ btn 40A not reachable : {e}")
            else:
                if len(list_of_bet_type) > 0:
                    print('JEU TROUVÉ! : '+list_of_bet_type[0].text)
                    tentative = 0
                    while not clic and tentative < 5:
                        print('VERIFICATTION SI CLIQUABLE...')
                        try:
                            element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH,
                                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                jeu) + ' : 40-40 - Oui")]')))
                        except Exception as e:
                            tentative += 1
                            if tentative ==5:
                                print(f"btn 40A not clicable retry : {e}")
                                return
                            the_jeu = GetJeuActuel(driver)
                            if jeu != the_jeu:
                                print('jeu diff')


                        else:
                            show_bet_box = False
                            tentative_show_bet_box = 0
                            while not show_bet_box and tentative_show_bet_box<5:
                                try:
                                    #list_of_bet_type[0].click()
                                    driver.find_element(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                    jeu) + ' : 40-40 - Oui")]').click()
                                except Exception as e:
                                    print(f"#E0019\nUne erreur est survenue : {e}")
                                    print('CLICK IMPOSSIBLE!')
                                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
                                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.DOWN)
                                    tentative_show_bet_box += 1
                                    time.sleep(1)
                                else:
                                    try :
                                        element = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                        )
                                    except Exception as e:
                                        print('Pas de paris affiché!')
                                        tentative_show_bet_box += 1
                                        time.sleep(1)
                                    else:

                                        clic = True
                                        return [clic, jeu]

                else:
                    print("pas de btn 40 recuperé")
                    return
