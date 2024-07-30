import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Function_GetJeuActuel import GetJeuActuel
import config

def GetBet4030(driver):
    clic = False
    while not clic:
        GetJeuActuel(driver)
        print('RECHERCHE DES PARIS 40 30....FIRST')
        scoreboard_player = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
        scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__heading')[0]
        first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__ball')
        if len(first_player) > 0:
            first_player = 1
            win_type = '40:30'

        else:
            first_player = 2
            win_type = '30:40'
        print('next player to win : ' + str(first_player) + ' ' + win_type)
        win_texte = '40-30'
        if_get_jeu = False
        clic = False
        tentative_clic = 0
        try:
            print('Recherche : Joueur ' + str(
                first_player) + ' va gagner le Jeu ' + str(
                config.jeu_actuel) + ' ' + str(
                win_texte))
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                    first_player) + ' va gagner le Jeu ' + str(
                                                    config.jeu_actuel) + ' ' + str(
                                                    win_texte) + '")]'))
            )

        except Exception as e:
            # print(f"#E0017\nUne erreur est survenue : {e}")
            print("Paris Jeu " + str(config.jeu_actuel) + " : 40-40 - Oui NON TROUVÉ!")
            print("Vérificattion si autre jeu en cours...")
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]'))
                )
            except Exception as e:
                print('Aucun bouton paris 40-40 - Oui TROUVÉ!')
            else:
                list_of_newbet_type = driver.find_elements(By.XPATH,
                                                           '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]')
                if len(list_of_newbet_type) == 1:
                    list_of_newbet_type = list_of_newbet_type[0].text
                    print(list_of_newbet_type)
                    list_of_newbet_type = list_of_newbet_type.split(win_texte)
                    jeu = int(list_of_newbet_type[0].split("jeu ")[1])
                    print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                elif len(list_of_newbet_type) >= 2:
                    print('PLUSIEURS JEUX TROUVÉS!')
                    newbet_type1 = list_of_newbet_type[0].text
                    newbet_type1 = newbet_type1.split(win_type)
                    game1 = int(newbet_type1[0].split("Jeu ")[1].split(" ")[0])
                    print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                    newbet_type2 = list_of_newbet_type[1].text
                    print(newbet_type2)
                    newbet_type2 = newbet_type2.split(win_type)
                    game2 = int(newbet_type2[0].split("Jeu ")[1].split(" ")[0])
                    print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                    print("vérification ordre de jeu")
                    if game1 < game2:
                        jeu = game1
                        print("Jeu actuel : " + str(jeu))
                        if_get_jeu = True
                    else:
                        jeu = game2
                        print("Jeu actuel : " + str(jeu))
                        if_get_jeu = True
                else:
                    print('ERROR: try get num game running')
        else:
            if_get_jeu = True

        if if_get_jeu == True:
            try:
                list_of_bet_type = driver.find_elements(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                            first_player) + ' va gagner le Jeu ' + str(
                                                            config.jeu_actuel) + ' ' + str(
                                                            win_texte) + '")]')
            except Exception as e:
                print(f"#E0018\nUne erreur est survenue : {e}")
                print("btn 40A not reachable")
            else:
                if len(list_of_bet_type) > 0:
                    print('JEU TROUVÉ! : ' + list_of_bet_type[0].text)
                    tentative = 0
                    while clic == 0 and tentative < 5:
                        print('VERIFICATTION SI CLIQUABLE...')
                        try:
                            element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH,
                                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                                first_player) + ' va gagner le Jeu ' + str(
                                                                config.jeu_actuel) + ' ' + str(
                                                                win_texte) + '")]')))
                        except:
                            tentative = tentative + 1
                            print("btn 40A not clicable retry")
                            jeu = config.jeu_actuel
                            GetJeuActuel(driver)
                            the_jeu = config.jeu_actuel
                            if jeu != the_jeu:
                                tentative = 99
                                print('jeu diff')


                        else:
                            try:
                                # list_of_bet_type[0].click()
                                driver.find_element(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                        first_player) + ' va gagner le Jeu ' + str(
                                                        config.jeu_actuel) + ' ' + str(
                                                        win_texte) + '")]').click()
                            except Exception as e:
                                print(f"#E0019\nUne erreur est survenue : {e}")
                                print('CLICK IMPOSSIBLE!')
                                tentative = tentative + 1
                                time.sleep(1)
                                try:
                                    element = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, 'cpn-bets-list'))
                                    )
                                except Exception as e:
                                    print('Pas de paris affiché!')
                                    tentative = tentative + 1
                                    time.sleep(1)
                                else:
                                    clic = True
                            else:
                                clic = True
                else:
                    print("pas de btn 40 recuperé")
                    clic = False
    return [clic, win_type]
def GetNextBet4030(driver):
    clic = False
    while not clic:
        GetJeuActuel(driver)
        config.jeu_actuel = config.jeu_actuel + 1
        print('RECHERCHE DES PROCHAINS PARIS 40 30....')
        scoreboard_player = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
        print('lenrow')
        scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__heading')[0]
        print('lenrow2')
        first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__ball')
        print('lenrow3')
        print('len first pleyer : ' + str(len(first_player)))
        if len(first_player) > 0:
            first_player = 2
            win_type = '40:30'

        else:
            first_player = 1
            win_type = '30:40'
        print('next player to win : ' + str(first_player) + ' ' + win_type)
        win_texte = '40-30'
        if_get_jeu = False
        clic = 0
        tentative_clic = 0
        try:
            print('Recherche : Joueur ' + str(
                first_player) + ' va gagner le Jeu ' + str(
                config.jeu_actuel) + ' ' + str(
                win_texte))
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                    first_player) + ' va gagner le Jeu ' + str(
                                                    config.jeu_actuel) + ' ' + str(
                                                    win_texte) + '")]'))
            )

        except Exception as e:
            # print(f"#E0017\nUne erreur est survenue : {e}")
            print("Paris Jeu " + str(config.jeu_actuel) + " : 40-40 - Oui NON TROUVÉ!")
            print("Vérificattion si autre jeu en cours...")
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]'))
                )
            except Exception as e:
                print('Aucun bouton paris 40-40 - Oui TROUVÉ!')
            else:
                list_of_newbet_type = driver.find_elements(By.XPATH,
                                                           '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "va gagner le Jeu")]')
                if len(list_of_newbet_type) == 1:
                    list_of_newbet_type = list_of_newbet_type[0].text
                    print(list_of_newbet_type)
                    list_of_newbet_type = list_of_newbet_type.split(win_texte)
                    jeu = int(list_of_newbet_type[0].split("jeu ")[1])
                    print("AUTRE JEU TROUVÉ : Jeu " + str(jeu))
                elif len(list_of_newbet_type) >= 2:
                    print('PLUSIEURS JEUX TROUVÉS!')
                    newbet_type1 = list_of_newbet_type[0].text
                    newbet_type1 = newbet_type1.split(win_type)
                    game1 = int(newbet_type1[0].split("Jeu ")[1].split(" ")[0])
                    print('PROCHAIN JEU TROUVÉ : ' + str(game1))
                    newbet_type2 = list_of_newbet_type[1].text
                    print(newbet_type2)
                    newbet_type2 = newbet_type2.split(win_type)
                    game2 = int(newbet_type2[0].split("Jeu ")[1].split(" ")[0])
                    print('JEU D\'APRÈS TROUVÉ : ' + str(game2))
                    print("vérification ordre de jeu")
                    if game1 < game2:
                        jeu = game1
                        print("Jeu actuel : " + str(jeu))
                        if_get_jeu = True
                    else:
                        jeu = game2
                        print("Jeu actuel : " + str(jeu))
                        if_get_jeu = True
                else:
                    print('ERROR: try get num game running')
        else:
            if_get_jeu = True

        if if_get_jeu == True:
            try:
                list_of_bet_type = driver.find_elements(By.XPATH,
                                                        '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                            first_player) + ' va gagner le Jeu ' + str(
                                                            config.jeu_actuel) + ' ' + str(
                                                            win_texte) + '")]')
            except Exception as e:
                print(f"#E0018\nUne erreur est survenue : {e}")
                print("btn 40A not reachable")
            else:
                if len(list_of_bet_type) > 0:
                    print('JEU TROUVÉ! : ' + list_of_bet_type[0].text)
                    tentative = 0
                    while clic == 0 and tentative < 5:
                        print('VERIFICATTION SI CLIQUABLE...')
                        try:
                            element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH,
                                                            '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                                first_player) + ' va gagner le Jeu ' + str(
                                                                config.jeu_actuel) + ' ' + str(
                                                                win_texte) + '")]')))
                        except:
                            tentative = tentative + 1
                            print("btn 40A not clicable retry")
                            jeu = config.jeu_actuel
                            GetJeuActuel(driver)
                            the_jeu = config.jeu_actuel + 1
                            if jeu != the_jeu:
                                tentative = 99
                                print('jeu diff')


                        else:
                            try:
                                # list_of_bet_type[0].click()
                                driver.find_element(By.XPATH,
                                                    '//*[@id="allBetsTable"]/div/div[not(contains(@style,"display: none;"))]/div/div[2]/div/span[contains(text(), "Joueur ' + str(
                                                        first_player) + ' va gagner le Jeu ' + str(
                                                        config.jeu_actuel) + ' ' + str(
                                                        win_texte) + '")]').click()
                            except Exception as e:
                                print(f"#E0019\nUne erreur est survenue : {e}")
                                print('CLICK IMPOSSIBLE!')
                                tentative = tentative + 1
                                time.sleep(1)
                            else:
                                try:
                                    element = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, 'cpn-bets-list'))
                                    )
                                except Exception as e:
                                    print('Pas de paris affiché!')
                                    tentative = tentative + 1
                                    time.sleep(1)
                                else:
                                    clic = True

                else:
                    print("pas de btn 40 recuperé")
                    clic = True
    return [clic, win_type]