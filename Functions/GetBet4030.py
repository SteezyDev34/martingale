import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Functions.DeleteBet import DeleteBet
from Functions.Function_GetJeuActuel import GetJeuActuel
import config
from selenium.webdriver.common.action_chains import ActionChains
#from ChromeDriver.SetDriver1 import driver

def GetBet4030(driver):
    print("RECHERCHE DES PARIS " + config.scriptType + "....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    print('RECHERCHE DES PARIS 40 30....FIRST')
    scoreboard_player = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__heading')[0]
    first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__ball')
    if len(first_player) > 0:
        first_player = 1
        win_type = '40:30'
        sType = "ueur "+str(first_player)+" va gagner le Jeu "+str(config.jeu_actuel)+" 40-3"

    else:
        first_player = 2
        win_type = '30:40'
        sType = "ueur "+str(first_player)+" va gagner le Jeu "+str(config.jeu_actuel)+" 40-3"

    print('next player to win : ' + str(first_player) + ' ' + win_type)
    win_texte = '40-30'
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    tentative = 0
    canvas = driver.find_element(By.ID, 'allBetsTable')
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    sautDeLigne = 40
    decalageX = 5
    ligne = 1
    i = 0
    while not clic and tentative<3:
        GetJeuActuel(driver)
        print('Ligne suivante')
        canvas = driver.find_element(By.ID, 'allBetsTable')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = sautDeLigne
        x = decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        print('Y offset : '+str(y))
        # Créer une instance ActionChains
        actions = ActionChains(driver)
        # Cliquer aux coordonnées calculées
        actions.move_to_element_with_offset(canvas, x, y).click().perform()
        print('Click sur la ligne')
        time.sleep(1)
        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME,
                                                'cpn-bet-market__label'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic))
            time.sleep(1)
            if tentative_clic ==3:
                config.saveLog('Pas d\'infos, suivant...')
                if i % 2 ==0:
                    sautDeLigne = sautDeLigne + 30
                    decalageX = 5
                else:
                    sautDeLigne = sautDeLigne
                    decalageX = size['width']/2 -5
                    print('cliic en face')
                ligne = ligne+1
                print('ligne '+str(ligne))
                tentative_clic = 0
        else:
            print('Infos de paris affiché')
            try:
                time.sleep(1)
                print('Lecture des infos')
                list_of_bet_type = driver.find_elements(By.CLASS_NAME,
                                                        'cpn-bet-market__label')
            except Exception as e:
                config.saveLog(f"#E0015\ Infos de paris non lisible : {e}")
            else:
                print('jeu actu '+str(config.jeu_actuel))
                list_of_newbet_type_text = list_of_bet_type[0].text
                print(list_of_newbet_type_text)
                list_of_newbet_type = list_of_newbet_type_text.split(sType)
                print('len list_of_newbet_type')
                print(len(list_of_newbet_type))
                print(list_of_newbet_type)
                if len(list_of_newbet_type) >1:
                    list_of_newbet_type_text = list_of_newbet_type_text.split(" 40")[0]
                    getjeu_actuel = int(list_of_newbet_type_text.split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                        return [clic, win_type]
                    else:
                        print('mauvais jeu')
                        if i % 2 == 0:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = 5
                        else:
                            sautDeLigne = sautDeLigne
                            decalageX = size['width'] / 2 - 5
                            print('cliic en face')
                else:
                    print('Mauvais paris')
                    if i % 2 == 0:
                        sautDeLigne = sautDeLigne + 30
                        decalageX = 5
                    else:
                        sautDeLigne = sautDeLigne
                        decalageX = size['width'] / 2 - 5
                        print('cliic en face')
                    ligne = ligne + 1
                    print('ligne ' + str(ligne))
        if y > size['height'] or ligne > 16:
            print('size height :'+str(size['height'] ))
            print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
            sautDeLigne = 40
            y = size['height'] + sautDeLigne
            ligne = 1
            tentative = tentative + 1
            i=0
        i = i + 1
def GetNextBet4030(driver):
    print("RECHERCHE DES PARIS " + config.scriptType + "....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    config.jeu_actuel = config.jeu_actuel+1
    print('RECHERCHE DES PARIS 40 30....FIRST')
    scoreboard_player = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__heading')[0]
    first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__ball')
    if len(first_player) > 0:
        first_player = 2
        win_type = '40:30'
        sType = "ueur " + str(first_player) + " va gagner le Jeu " + str(config.jeu_actuel) + " 40-3"

    else:
        first_player = 1
        win_type = '30:40'
        sType = "ueur " + str(first_player) + " va gagner le Jeu " + str(config.jeu_actuel) + " 40-3"

    print('next player to win : ' + str(first_player) + ' ' + win_type)
    win_texte = '40-30'
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    tentative = 0
    canvas = driver.find_element(By.ID, 'allBetsTable')
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    sautDeLigne = 40
    decalageX = 5
    ligne = 1
    i = 0
    while not clic and tentative<3:
        GetJeuActuel(driver)
        config.jeu_actuel = config.jeu_actuel + 1
        print('Ligne suivante')
        #canvas = driver.find_element(By.ID, 'allBetsTable')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = sautDeLigne
        x = decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        print('Y offset : '+str(y))
        # Créer une instance ActionChains
        actions = ActionChains(driver)
        # Cliquer aux coordonnées calculées
        actions.move_to_element_with_offset(canvas, x, y).click().perform()
        print('Click sur la ligne')
        time.sleep(1)
        try:
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME,
                                                'cpn-bet-market__label'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic))
            time.sleep(1)
            if tentative_clic ==3:
                config.saveLog('Pas d\'infos, suivant...')
                if i % 2 == 0:
                    sautDeLigne = sautDeLigne + 30
                    decalageX = 5
                else:
                    sautDeLigne = sautDeLigne
                    decalageX = size['width'] / 2 - 5
                    print('cliic en face')
                ligne = ligne+1
                print('ligne '+str(ligne))
                tentative_clic = 0
        else:
            print('Infos de paris affiché')
            try:
                time.sleep(1)
                print('Lecture des infos')
                list_of_bet_type = driver.find_elements(By.CLASS_NAME,
                                                        'cpn-bet-market__label')
                list_of_newbet_type_text = list_of_bet_type[0].text

            except Exception as e:
                config.saveLog(f"#E0015\ Infos de paris non lisible : {e}")
            else:
                print('jeu actu '+str(config.jeu_actuel))

                print(list_of_newbet_type_text)
                print(sType)
                list_of_newbet_type = list_of_newbet_type_text.split(sType)
                if len(list_of_newbet_type) >1:
                    list_of_newbet_type_text = list_of_newbet_type_text.split(" 40")[0]
                    getjeu_actuel = int(list_of_newbet_type_text.split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                        return [clic, win_type]
                    else:
                        print('mauvais jeu')
                        if i % 2 == 0:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = 5
                        else:
                            sautDeLigne = sautDeLigne
                            decalageX = size['width'] / 2 - 5
                            print('cliic en face')
                else:
                    print('Mauvais paris')
                    if i % 2 == 0:
                        sautDeLigne = sautDeLigne + 30
                        decalageX = 5
                    else:
                        sautDeLigne = sautDeLigne
                        decalageX = size['width'] / 2 - 5
                        print('cliic en face')
                    ligne = ligne + 1
                    print('ligne ' + str(ligne))
        if y > size['height'] or ligne>16:
            print('size height :' + str(size['height']))
            print('Aucun paris trouvé, nouvelle tentative : '+str(tentative))
            sautDeLigne = 40
            y = size['height'] + sautDeLigne
            ligne = 1
            tentative = tentative+1
            i=0
        i = i + 1