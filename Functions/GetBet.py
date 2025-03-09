import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Functions.DeleteBet import DeleteBet
from Functions.Function_GetJeuActuel import GetJeuActuel
import config
from selenium.webdriver.common.action_chains import ActionChains
#from ChromeDriver.SetDriver1 import driver

def GetBet(driver,nextBet=False):
    print("RECHERCHE DES PARIS "+config.scriptType+"....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    if nextBet:
        config.jeu_actuel = config.jeu_actuel + 1
    if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
        print('RECHERCHE DES PARIS 40 30....FIRST')
        scoreboard_player = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-body__container')
        scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-inning')[0]
        first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'scoreboard-periods-inning__ico')
        if len(first_player) > 0:
            first_player = 1
            config.win_type = '40:30'
            win_texte = '40-30'
            sType = "Jeu "+str(config.jeu_actuel)+" 40-30, Joueur "+str(first_player)

        else:
            first_player = 2
            config.win_type = '30:40'
            win_texte = '30-40'
            sType = "Jeu " + str(config.jeu_actuel) + " 30-40, Joueur " + str(first_player)
        print('next player to win : ' + str(first_player) + ' ' + config.win_type)
    if_get_jeu = False
    clic = False
    if config.scriptType == "40A":
        sType = ": 40-40"

    elif config.scriptType == "30A":
        sType = " 30-30"
    elif config.scriptType == "15A":
        sType = " 15-15"

    tentative_clic = 0
    tentative = 0
    try:
        canvas = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'market-grid-canvas__container'))
        )
    except:
        return False
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    if config.systeme == 'Darwin':
        print('darwini')
        sautDeLigne = 50
        decalageX = size['width'] / -2 + 50
    elif config.systeme == 'Windows':
        print('windows')
        y =0
        sautDeLigne = 70
        decalageX = 50
    ligne = 1
    i=0
    while not clic and tentative<10:
        GetJeuActuel(driver)
        if nextBet:
            config.jeu_actuel = config.jeu_actuel + 1
        #print('Ligne suivante')
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        if config.systeme == 'Darwin':
            y = size['height'] / -2 +10+ sautDeLigne
            x = decalageX
        elif config.systeme == 'Windows':
            y = sautDeLigne
            x = decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        #print('Y offset : '+str(y))
        #print('X offset : ' + str(x))
        # Créer une instance ActionChains
        actions = ActionChains(driver)
        # Cliquer aux coordonnées calculées
        try:
            actions.move_to_element_with_offset(canvas, x, y).click().perform()
        except:
            return False
        #print('Click sur la ligne')
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                'ui-coupon-bet-market__name'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic))

            if tentative_clic ==3:
                config.saveLog('Pas d\'infos, suivant...')
                if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                    if config.systeme == 'Darwin':
                        if i % 2 == 0:
                            sautDeLigne = sautDeLigne
                            decalageX = 50
                        else:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = size['width'] / -2 + 50
                else:
                    sautDeLigne = sautDeLigne + 30
                ligne = ligne+1
                print('ligne '+str(ligne))
                tentative_clic = 0
        else:
            #print('Infos de paris affiché')
            try:
                #print('Lecture des infos')
                time.sleep(1)
                list_of_bet_type = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.CLASS_NAME,
                                                      'ui-coupon-bet-market__name'))
                )
            except Exception as e:
                config.saveLog(f"#E0015\ Infos de paris non lisible : {e}")
            else:
                list_of_newbet_type = list_of_bet_type.text
                #print(list_of_newbet_type)
                if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                    print(sType)
                    list_of_newbet_type_text = list_of_newbet_type
                    print(list_of_newbet_type_text)
                    list_of_newbet_type = list_of_newbet_type_text.split(sType)
                    #print(len(list_of_newbet_type))
                    #print(list_of_newbet_type)
                    if len(list_of_newbet_type) > 1:
                        list_of_newbet_type_text = list_of_newbet_type_text.split(" "+win_texte)[0]
                        getjeu_actuel = int(list_of_newbet_type_text.split("Jeu ")[1])+10
                        if str(config.jeu_actuel) == str(getjeu_actuel):
                            print('paris trouvé')
                            clic = True
                            return clic
                        else:
                            print('mauvais jeu')
                            if config.systeme == 'Darwin':
                                if i % 2 == 0:
                                    sautDeLigne = sautDeLigne
                                    decalageX = 50
                                else:
                                    sautDeLigne = sautDeLigne + 30
                                    decalageX = size['width'] / -2 + 50
                    else:
                        print('Mauvais paris')
                        if config.systeme == 'Darwin':
                            if i % 2 == 0:
                                sautDeLigne = sautDeLigne
                                decalageX = 50
                            else:
                                sautDeLigne = sautDeLigne + 30
                                decalageX = size['width'] / -2 + 50
                        ligne = ligne + 1
                        print('ligne ' + str(ligne))
                else:
                    list_of_newbet_type = list_of_newbet_type.split(sType + " - Oui")
                    if len(list_of_newbet_type) >1:
                        getjeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                        if str(config.jeu_actuel) == str(getjeu_actuel):
                            #print('paris trouvé')
                            clic = True
                            return clic
                        else:
                            #print('mauvais jeu')
                            sautDeLigne = sautDeLigne + 30
                    else:
                        #print('Mauvais paris')
                        sautDeLigne = sautDeLigne + 30
                        ligne = ligne + 1
                        print('ligne ' + str(ligne))
        if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
            max_line = 16
        else:
            max_line = 8
        if config.systeme == 'Darwin':
            if y > size['height']/2 or ligne > max_line:
                #print('size height :'+str(size['height'] ))
                #print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
                sautDeLigne = 40
                y = size['height'] / -2 + 10 + sautDeLigne
                decalageX = size['width'] / -2 + 50
                ligne = 1
                tentative = tentative + 1
                i = 0
        elif config.systeme == 'Windows':
            if y > size['height'] or ligne > max_line:
                #print('size height :' + str(size['height']))
                #print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
                sautDeLigne = 70
                y = size['height'] + sautDeLigne
                ligne = 1
                tentative = tentative + 1
        i = i + 1
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    config.scriptType = '4030'
    driver.switch_to.window(driver.window_handles[0])
    GetBet(driver)
