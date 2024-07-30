import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Function_GetJeuActuel import GetJeuActuel
import config

def GetBet40A(driver):
    print('RECHERCHE DES PARIS 40 A....')
    GetJeuActuel(driver)
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    while not clic and tentative_clic<30:
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                    config.jeu_actuel) + ' : 40-40 - Oui")]'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic),config.newmatch)
            time.sleep(1)
            if tentative_clic ==5:
                config.saveLog("Paris Jeu " + str(config.jeu_actuel) + " : 40-40 - Oui NON TROUVÉ!", config.newmatch)
                config.saveLog("Vérificattion si autre jeu en cours...", config.newmatch)
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]'))
                    )
                except Exception as e:
                    config.saveLog('Aucun paris 40A TROUVÉ!', config.newmatch)
                    return
                else:
                    list_of_newbet_type = driver.find_elements(By.XPATH,
                                                               '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]')
                    if len(list_of_newbet_type) == 1:
                        config.saveLog('Un seul paris trouvé', config.newmatch)
                        list_of_newbet_type = list_of_newbet_type[0].text
                        print(list_of_newbet_type)
                        list_of_newbet_type = list_of_newbet_type.split(" : 40-40 - Oui")
                        config.jeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                        print("AUTRE JEU TROUVÉ : Jeu " + str(config.jeu_actuel))
                    elif len(list_of_newbet_type) >= 2:
                        config.saveLog('PLUSIEURS JEUX TROUVÉS!', config.newmatch)
                        newbet_type1 = list_of_newbet_type[0].text
                        newbet_type1 = newbet_type1.split(" : 40-40 - Oui")
                        game1 = int(newbet_type1[0].split("Jeu ")[1])
                        config.saveLog('PROCHAIN JEU TROUVÉ : ' + str(game1), config.newmatch)
                        newbet_type2 = list_of_newbet_type[1].text
                        config.saveLog(newbet_type2)
                        newbet_type2 = newbet_type2.split(" : 40-40 - Oui")
                        game2 = int(newbet_type2[0].split("Jeu ")[1])
                        config.saveLog('JEU D\'APRÈS TROUVÉ : ' + str(game2), config.newmatch)
                        config.saveLog("vérification ordre de jeu", config.newmatch)
                        if game1 < game2:
                            config.jeu_actuel = game1
                            config.saveLog("Jeu actuel : " + str(config.jeu_actuel), config.newmatch)
                        else:
                            config.jeu_actuel = game2
                            config.saveLog("Jeu actuel : " + str(config.jeu_actuel), config.newmatch)
                    else:
                        config.saveLog('ERROR: try get num game running', config.newmatch)
                        tentative_clic+=1
        else:
            try:
                list_of_bet_type = driver.find_elements(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            config.jeu_actuel) + ' : 40-40 - Oui")]')
            except Exception as e:
                config.saveLog(f"#E0015\ btn 40A not reachable : {e}", config.newmatch)
            else:
                if len(list_of_bet_type) > 0:
                    config.saveLog('JEU TROUVÉ! : '+list_of_bet_type[0].text, config.newmatch)
                    tentative = 0
                    while not clic and tentative < 5:
                        config.saveLog('VERIFICATTION SI CLIQUABLE...', config.newmatch)
                        try:
                            element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH,
                                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                config.jeu_actuel) + ' : 40-40 - Oui")]')))
                        except Exception as e:
                            tentative += 1
                            if tentative ==5:
                                config.saveLog(f"btn 40A not clicable retry : {e}", config.newmatch)
                                return
                            the_jeu = GetJeuActuel(driver)
                            if config.jeu_actuel != the_jeu:
                                config.saveLog('jeu diff', config.newmatch)


                        else:
                            show_bet_box = False
                            tentative_show_bet_box = 0
                            while not show_bet_box and tentative_show_bet_box<5:
                                try:
                                    driver.find_element(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                    config.jeu_actuel) + ' : 40-40 - Oui")]').click()
                                except Exception as e:
                                    config.saveLog(f"#E0019\nUne erreur est survenue : {e}")
                                    config.saveLog('CLICK IMPOSSIBLE!', config.newmatch)
                                    tentative_show_bet_box += 1
                                    time.sleep(1)
                                else:
                                    try :
                                        element = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                        )
                                    except Exception as e:
                                        config.saveLog('Pas de paris affiché!', config.newmatch)
                                        tentative_show_bet_box += 1
                                        time.sleep(1)
                                    else:

                                        clic = True
                                        return clic

                else:
                    config.saveLog("pas de btn 40 recuperé")
                    return clic
def GetNextBet40A(driver):
    print('RECHERCHE DES PROCHAINS PARIS 40 A....')
    GetJeuActuel(driver)
    config.jeu_actuel =config.jeu_actuel+1
    config.saveLog("PROCHAIN JEU : "+str(config.jeu_actuel), config.newmatch)
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    while not clic and tentative_clic<30:
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                    config.jeu_actuel) + ' : 40-40 - Oui")]'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic), config.newmatch)
            time.sleep(1)
            if tentative_clic ==5:
                config.saveLog("Paris Jeu " + str(config.jeu_actuel) + " : 40-40 - Oui NON TROUVÉ!", config.newmatch)
                config.saveLog("Vérificattion si autre jeu en cours...", config.newmatch)
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]'))
                    )
                except Exception as e:
                    config.saveLog('Aucun paris 40A TROUVÉ!', config.newmatch)
                    return
                else:
                    list_of_newbet_type = driver.find_elements(By.XPATH,
                                                               '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), " : 40-40 - Oui")]')
                    if len(list_of_newbet_type) == 1:
                        config.saveLog('Un seul paris trouvé', config.newmatch)
                        list_of_newbet_type = list_of_newbet_type[0].text
                        print(list_of_newbet_type)
                        list_of_newbet_type = list_of_newbet_type.split(" : 40-40 - Oui")
                        config.jeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                        print("AUTRE JEU TROUVÉ : Jeu " + str(config.jeu_actuel))
                    elif len(list_of_newbet_type) >= 2:
                        config.saveLog('PLUSIEURS JEUX TROUVÉS!', config.newmatch)
                        newbet_type1 = list_of_newbet_type[0].text
                        newbet_type1 = newbet_type1.split(" : 40-40 - Oui")
                        game1 = int(newbet_type1[0].split("Jeu ")[1])
                        config.saveLog('PROCHAIN JEU TROUVÉ : ' + str(game1), config.newmatch)
                        newbet_type2 = list_of_newbet_type[1].text
                        config.saveLog(newbet_type2, config.newmatch)
                        newbet_type2 = newbet_type2.split(" : 40-40 - Oui")
                        game2 = int(newbet_type2[0].split("Jeu ")[1])
                        config.saveLog('JEU D\'APRÈS TROUVÉ : ' + str(game2), config.newmatch)
                        config.saveLog("vérification ordre de jeu", config.newmatch)
                        if game1 < game2:
                            config.jeu_actuel = game1
                            config.saveLog("Jeu actuel : " + str(config.jeu_actuel), config.newmatch)
                        else:
                            config.jeu_actuel = game2
                            config.saveLog("Jeu actuel : " + str(config.jeu_actuel), config.newmatch)
                    else:
                        config.saveLog('ERROR: try get num game running', config.newmatch)
                        tentative_clic+=1
        else:
            try:
                list_of_bet_type = driver.find_elements(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                            config.jeu_actuel) + ' : 40-40 - Oui")]')
            except Exception as e:
                config.saveLog(f"#E0015\ btn 40A not reachable : {e}", config.newmatch)
            else:
                if len(list_of_bet_type) > 0:
                    config.saveLog('JEU TROUVÉ! : '+list_of_bet_type[0].text, config.newmatch)
                    tentative = 0
                    while not clic and tentative < 5:
                        config.saveLog('VERIFICATTION SI CLIQUABLE...', config.newmatch)
                        try:
                            element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH,
                                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                config.jeu_actuel) + ' : 40-40 - Oui")]')))
                        except Exception as e:
                            tentative += 1
                            if tentative ==5:
                                config.saveLog(f"btn 40A not clicable retry : {e}", config.newmatch)
                                return
                            the_jeu = GetJeuActuel(driver)
                            if config.jeu_actuel != the_jeu:
                                config.saveLog('jeu diff', config.newmatch)


                        else:
                            show_bet_box = False
                            tentative_show_bet_box = 0
                            while not show_bet_box and tentative_show_bet_box<5:
                                try:
                                    driver.find_element(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Jeu ' + str(
                                                                    config.jeu_actuel) + ' : 40-40 - Oui")]').click()
                                except Exception as e:
                                    config.saveLog(f"#E0019\nUne erreur est survenue : {e}", config.newmatch)
                                    config.saveLog('CLICK IMPOSSIBLE!')
                                    tentative_show_bet_box += 1
                                    time.sleep(1)
                                else:
                                    try :
                                        element = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME,'cpn-bets-list'))
                                        )
                                    except Exception as e:
                                        config.saveLog('Pas de paris affiché!', config.newmatch)
                                        tentative_show_bet_box += 1
                                        time.sleep(1)
                                    else:

                                        clic = True
                                        return clic

                else:
                    config.saveLog("pas de btn 40 recuperé", config.newmatch)
                    return clic
