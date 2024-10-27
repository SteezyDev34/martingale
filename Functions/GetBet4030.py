import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Functions.DeleteBet import DeleteBet
from Functions.Function_GetJeuActuel import GetJeuActuel
import config
from selenium.webdriver.common.action_chains import ActionChains


def GetBet4030(driver):
    print("RECHERCHE DES PARIS "+config.scriptType+"....")
    DeleteBet(driver)
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
        print('Ligne suivante')
        canvas = driver.find_element(By.ID, 'allBetsTable')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = size['height'] / -2 + sautDeLigne
        x = size['width'] / -2 + decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        print('X offset : '+str(x))
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
                ligne = ligne + 1
                print('ligne ' + str(ligne))
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
                list_of_newbet_type = list_of_bet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split("40-3")
                list_of_newbet_player = list_of_newbet_type[0].split("oueur "+str(first_player)+" va gagner")
                if len(list_of_newbet_type) >1 and len(list_of_newbet_player)>1:
                    getjeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                    else:
                        print('mauvais jeu')
                        if i % 2 == 0:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = 5
                        else:
                            sautDeLigne = sautDeLigne
                            decalageX = size['width']/2 -5
                            print('cliic en face')
                else:
                    print('Mauvais paris')
                    if i % 2 == 0:
                        sautDeLigne = sautDeLigne + 30
                        decalageX = 5
                    else:
                        sautDeLigne = sautDeLigne
                        decalageX = size['width']/2 -5
                        print('cliic en face')
                    ligne = ligne + 1
                    print('ligne ' + str(ligne))
        if y > size['height'] / 2 or ligne > 8:
            print('size height :'+str(size['height'] ))
            print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
            sautDeLigne = 40
            y = size['height'] / -2 + sautDeLigne
            ligne = 1
            tentative = tentative + 1
            i = 0
        i=i+1
    return [clic, win_type]
def GetNextBet4030(driver):
    print("RECHERCHE DES PARIS "+config.scriptType+"....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    config.jeu_actuel = config.jeu_actuel + 1
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
    tentative = 0
    canvas = driver.find_element(By.ID, 'allBetsTable')
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    sautDeLigne = 40
    decalageX = 5
    ligne = 1
    i=0
    while not clic and tentative<10:
        print('Ligne suivante')
        canvas = driver.find_element(By.ID, 'allBetsTable')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = size['height'] / -2 + sautDeLigne
        x = size['width'] / -2 + decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        print('X offset : '+str(x))
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
                    decalageX = size['width']/2 -5
                    print('cliic en face')
                ligne = ligne + 1
                print('ligne ' + str(ligne))
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
                list_of_newbet_type = list_of_bet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split("40-3")
                list_of_newbet_player = list_of_newbet_type[0].split("oueur "+str(first_player)+" va gagner")
                if len(list_of_newbet_type) >1 and len(list_of_newbet_player)>1:
                    getjeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                    else:
                        print('mauvais jeu')
                        if i % 2 == 0:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = 5
                        else:
                            sautDeLigne = sautDeLigne
                            decalageX = size['width']/2 -5
                            print('cliic en face')
                else:
                    print('Mauvais paris')
                    if i % 2 == 0:
                        sautDeLigne = sautDeLigne + 30
                        decalageX = 5
                    else:
                        sautDeLigne = sautDeLigne
                        decalageX = size['width']/2 -5
                        print('cliic en face')
                    ligne = ligne + 1
                    print('ligne ' + str(ligne))
        if y > size['height'] / 2 or ligne > 8:
            print('size height :'+str(size['height'] ))
            print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
            sautDeLigne = 40
            y = size['height'] / -2 + sautDeLigne
            ligne = 1
            tentative = tentative + 1
        i = i+1
    return [clic, win_type]