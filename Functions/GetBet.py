import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.DeleteBet import DeleteBet
import config
#from ChromeDriver.SetDriver1 import driver

def GetBet(driver):
    print("RECHERCHE DES PARIS "+config.scriptType+"....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    if_get_jeu = False
    clic = False
    sType = ": 40-40"
    if config.scriptType == "40A":
        sType = ": 40-40"
    elif config.scriptType == "30A":
        sType = " 30-30"
    elif config.scriptType == "15A":
        sType = " 15-15"

    tentative_clic = 0
    tentative = 0
    canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    sautDeLigne = 50
    ligne = 1
    while not clic and tentative<10:
        print('Ligne suivante')
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = size['height'] / -2 + sautDeLigne
        x = -5
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
                                                'ui-coupon-bet-market__name'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic))
            time.sleep(1)
            if tentative_clic ==3:
                config.saveLog('Pas d\'infos, suivant...')
                sautDeLigne = sautDeLigne + 40
                ligne = ligne+1
        else:
            print('Infos de paris affiché')
            try:
                time.sleep(1)
                print('Lecture des infos')
                list_of_bet_type = driver.find_elements(By.CLASS_NAME,
                                                        'ui-coupon-bet-market__name')
            except Exception as e:
                config.saveLog(f"#E0015\ Infos de paris non lisible : {e}")
            else:
                list_of_newbet_type = list_of_bet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(sType+" - Oui")
                if len(list_of_newbet_type) >1:
                    getjeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                        return clic
                    else:
                        print('mauvais jeu')
                        sautDeLigne = sautDeLigne + 40
                else:
                    print('Mauvais paris')
                    sautDeLigne = sautDeLigne + 40
                    ligne = ligne + 1
        if ligne == 10:
            print('Aucun paris trouvé, nouvelle tentative : '+str(tentative))
            tentative = tentative+1
            return False
def GetNextBet(driver):
    print("RECHERCHE DES PARIS "+config.scriptType+"....")
    DeleteBet(driver)
    GetJeuActuel(driver)
    config.jeu_actuel = config.jeu_actuel+1
    if_get_jeu = False
    clic = False
    sType = ": 40-40"
    if config.scriptType == "40A":
        sType = ": 40-40"
    elif config.scriptType == "30A":
        sType = " 30-30"
    elif config.scriptType == "15A":
        sType = " 15-15"

    tentative_clic = 0
    tentative = 0
    canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    sautDeLigne = 50
    ligne = 1
    while not clic and tentative<10:
        print('Ligne suivante')
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        y = size['height'] / -2 + sautDeLigne
        x = -5
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
                                                'ui-coupon-bet-market__name'))
            )
        except Exception as e:
            tentative_clic+=1
            config.saveLog('tentative_clic : '+str(tentative_clic))
            time.sleep(1)
            if tentative_clic ==3:
                config.saveLog('Pas d\'infos, suivant...')
                sautDeLigne = sautDeLigne + 40
                ligne = ligne+1
        else:
            print('Infos de paris affiché')
            try:
                time.sleep(1)
                print('Lecture des infos')
                list_of_bet_type = driver.find_elements(By.CLASS_NAME,
                                                        'ui-coupon-bet-market__name')
            except Exception as e:
                config.saveLog(f"#E0015\ Infos de paris non lisible : {e}")
            else:
                list_of_newbet_type = list_of_bet_type[0].text
                print(list_of_newbet_type)
                list_of_newbet_type = list_of_newbet_type.split(sType+" - Oui")
                if len(list_of_newbet_type) >1:
                    getjeu_actuel = int(list_of_newbet_type[0].split("Jeu ")[1])
                    if str(config.jeu_actuel) == str(getjeu_actuel):
                        print('paris trouvé')
                        clic = True
                        return clic
                    else:
                        print('mauvais jeu')
                        sautDeLigne = sautDeLigne + 40
                else:
                    print('Mauvais paris')
                    sautDeLigne = sautDeLigne + 40
                    ligne = ligne + 1
        if ligne == 10:
            print('Aucun paris trouvé, nouvelle tentative : '+str(tentative))
            tentative = tentative+1
            return False

#GetBet(driver)