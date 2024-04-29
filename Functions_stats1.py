import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

##DEFINITION DES FONCTIONS
##
##FIN DEFINITION DES FONCTIONS
from unidecode import unidecode

def get_proba_40A(playerName1, playerName2,driver,link):
    prob_service_joueur1 = 0
    prob_service_joueur2 = 0
    prob_retour_joueur1 = 0
    prob_retour_joueur2 = 0
    playerName1 = unidecode(playerName1)
    playerName2 = unidecode(playerName2)
    playerName1 = playerName1.replace('-',' ')
    playerName2 = playerName2.replace('-',' ')
    tentative = 0
    prob = 0
    ok =0
    while ok ==0 and tentative <3:
        try:
            driver.get('https://www.ultimatetennisstatistics.com/headToHead?tab=statistics')
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.ID, 'player1'))
            )



            fieldplayer1 = driver.find_element(By.ID,'player1')
            fieldplayer1.send_keys(playerName1)
            element = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.ID, 'ui-id-1'))
            )
            player_block = driver.find_element(By.ID,'ui-id-1')
            player_list = player_block.find_elements(By.CLASS_NAME,'ui-menu-item')
            for player in player_list:
                if re.search(playerName1.lower(), player.text.lower()):
                    player.click()
                    break
            fieldplayer2 = driver.find_element(By.ID, 'player2')
            fieldplayer2.send_keys(playerName2)
            element = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.ID, 'ui-id-2'))
            )
            player_block = driver.find_element(By.ID, 'ui-id-2')
            player_list = player_block.find_elements(By.CLASS_NAME, 'ui-menu-item')
            for player in player_list:
                if re.search(playerName2.lower(), player.text.lower()):
                    player.click()
                    break
            url = driver.current_url
            playerID1 = url.split('playerId1=')[1]
            playerID1 = playerID1.split('&')[0]

            playerID2 = url.split('playerId2=')[1]

            driver.get('https://www.ultimatetennisstatistics.com/headToHead?tab=statistics&playerId1='+playerID1+'&playerId2='+playerID2)
            element = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.ID, 'statisticsOverview'))
            )
            stats_list = driver.find_element(By.ID,'statisticsOverview')
            stats_tr = stats_list.find_elements(By.TAG_NAME,'tr')
            for tr in stats_tr:
                if re.search('Service Points Won %'.lower(), tr.text.lower()):
                    trok = tr.text.split('Service Points Won %')
                    prob_service_joueur1 = trok[0].replace('%','')
                    if prob_service_joueur1 == '':
                        prob_service_joueur1 =0.5
                    else:
                        prob_service_joueur1 =  float(prob_service_joueur1)/ 100
                        print('prob_service_joueur1 : '+str(prob_service_joueur1))
                    prob_service_joueur2 = trok[1].replace('%', '')
                    if prob_service_joueur2 == '':
                        prob_service_joueur2 = 0.5
                    else:
                        prob_service_joueur2 = float(prob_service_joueur2) / 100
                        print('prob_service_joueur2 : ' + str(prob_service_joueur2))
                if re.search('Return Points Won %'.lower(), tr.text.lower()):
                    trok = tr.text.split('Return Points Won %')
                    prob_retour_joueur1 = trok[0].replace('%','')
                    if prob_retour_joueur1 == '':
                        prob_retour_joueur1 = 0.5
                    else:
                        prob_retour_joueur1 =  float(prob_retour_joueur1)/ 100
                        print('prob_retour_joueur1 : '+str(prob_retour_joueur1))
                    prob_retour_joueur2 = trok[1].replace('%', '')
                    if prob_retour_joueur2 == '':
                        prob_retour_joueur2 = 0.5
                    else:
                        prob_retour_joueur2 = float(prob_retour_joueur2) / 100
                        print('prob_retour_joueur2 : ' + str(prob_retour_joueur2))
                    break
            # Calcul de la probabilité pour le joueur et l'adversaire
            prob_40_40_joueur1 = prob_service_joueur1 * prob_retour_joueur1
            prob_40_40_joueur2 = prob_service_joueur2 * prob_retour_joueur2

            # Calcul de la probabilité totale
            prob_40_40_totale = prob_40_40_joueur1 + prob_40_40_joueur2
            prob = float("{:.2}".format(prob_40_40_totale))
            print('Proba 40 A = ' + str(prob))
            driver.get(link)
        except:
            print('erreur lors du la proba40A')
            prob =0
            tentative = tentative +1
        else:
            ok = 1
    return prob
#print(get_proba_40A('DENIS YEVSEYEV', 'MARK LAJAL', driver))
