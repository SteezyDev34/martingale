import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

##DEFINITION DES FONCTIONS
##
##FIN DEFINITION DES FONCTIONS
from unidecode import unidecode

def get_proba_40A_other(playerName1, playerName2,driver,link):
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
    while ok ==0 and tentative <1:
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
                        prob_service_joueur1 =0
                    else:
                        prob_service_joueur1 =  float(prob_service_joueur1)/ 100
                        print('prob_service_joueur1 : '+str(prob_service_joueur1))
                    prob_service_joueur2 = trok[1].replace('%', '')
                    if prob_service_joueur2 == '':
                        prob_service_joueur2 = 0
                    else:
                        prob_service_joueur2 = float(prob_service_joueur2) / 100
                        print('prob_service_joueur2 : ' + str(prob_service_joueur2))
                if re.search('Return Points Won %'.lower(), tr.text.lower()):
                    trok = tr.text.split('Return Points Won %')
                    prob_retour_joueur1 = trok[0].replace('%','')
                    if prob_retour_joueur1 == '':
                        prob_retour_joueur1 = 0
                    else:
                        prob_retour_joueur1 =  float(prob_retour_joueur1)/ 100
                        print('prob_retour_joueur1 : '+str(prob_retour_joueur1))
                    prob_retour_joueur2 = trok[1].replace('%', '')
                    if prob_retour_joueur2 == '':
                        prob_retour_joueur2 = 0
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
        except:
            prob =0
            tentative = tentative +1
        else:
            ok = 1
    driver.get(link)
    return prob
#print(get_proba_40A('DENIS YEVSEYEV', 'MARK LAJAL', driver))
import time
from datetime import date
import requests
import json

global headers
headers= {
    'X-RapidAPI-Key': 'b052b9bd1cmsh0e38ccdfaf9d624p1dd988jsnde30c2e5a6dc',
    "X-RapidAPI-Host": "ultimate-tennis1.p.rapidapi.com"
}

def getPlayerApiId(playerName):
    file1 = open("atprankinjson.txt", "r")
    playerId = False
    # Lisez le contenu mis à jour du fichier
    playersList = file1.read()
    # Fermez le fichier après la lecture
    file1.close()
    playersList = playersList.split('\n')
    # on supprime la date
    del playersList[0]

    print(playerName)
    #playerNameElements = playerName.split(" ")
    LastName = playerName.lower()
    for player in playersList:
        nplayer = player.lower().split('|')[0]
        LastName = LastName
        #print(LastName)
        if nplayer in LastName:
            playerElements = player.split('|')
            playerLastName = playerElements[0].split(' ')[-1]
            playerId = playerElements[1]
            print('Player Name : ' + playerName)
            print('Player ID : ' + playerId)
            break
    return playerId
def getPlayerWtaApiId(playerName):
    file1 = open("wtarankinjson.txt", "r")
    playerId = False
    # Lisez le contenu mis à jour du fichier
    playersList = file1.read()
    # Fermez le fichier après la lecture
    file1.close()

    playersList = playersList.split('\n')
    # on supprime la date
    del playersList[0]
    playerNameElements = playerName.split(" ")
    LastName = playerNameElements[-1]

    for player in playersList:
        if LastName.lower() in player.lower():
            playerElements = player.split('|')
            playerLastName = playerElements[0].split(' ')[-1]
            if LastName.lower() == playerLastName.lower():
                playerId = playerElements[1]
                print('Player Name : '+playerName)
                print('Player ID : '+playerId)
                break
    return playerId
def get_proba_40A(playerName1, playerName2,cat='atp',surface='clay'):

    try:
        playerID1 = getPlayerApiId(playerName1)
        playerID2 = getPlayerApiId(playerName2)
        urlplayer1 = "https://ultimate-tennis1.p.rapidapi.com/player_stats/"+cat+"/"+playerID1+"/2023/"+surface
        urlplayer2 = "https://ultimate-tennis1.p.rapidapi.com/player_stats/" + cat + "/" + playerID2 + "/2023/" + surface

        response = requests.get(urlplayer1, headers=headers)
        time.sleep(1)
    except Exception as e:
        return 0
    else:

        try:
            data = str(response.json())
            data = data.replace("'", '"')
            data = json.loads(data)
            print(data)

            prob_service_joueur = float(data['ServiceRecordStats']['ServicePointsWonPercentage']) / 100
            prob_retour_joueur = float(data['ReturnRecordStats']['ReturnPointsWonPercentage']) / 100

            # Statistiques du joueur2
            response = requests.get(urlplayer2, headers=headers)
        except Exception as e:
            return 0
        else:
            try:

                data = str(response.json())
                data = data.replace("'", '"')
                data = json.loads(data)
                print(data)

                # Statistiques de l'adversaire
                prob_service_adversaire = float(data['ServiceRecordStats']['ServicePointsWonPercentage']) / 100
                prob_retour_adversaire = float(data['ReturnRecordStats']['ReturnPointsWonPercentage']) / 100

                # Calcul de la probabilité pour le joueur et l'adversaire
                prob_40_40_joueur = prob_service_joueur * prob_retour_joueur
                prob_40_40_adversaire = prob_service_adversaire * prob_retour_adversaire

                # Calcul de la probabilité totale
                prob_40_40_totale = prob_40_40_joueur + prob_40_40_adversaire
                prob = float("{:.2}".format(prob_40_40_totale))
                print('Proba 40 A = '+str(prob))
                if prob <=0.43:
                    print('PAS DE RATTRAPAGE')
                else:
                    print('RATTRAPAGE OK!')

            except:
                return 0
            else:
                return prob
def get_wta_proba_40A(playerName1, playerName2):
    print('proba wta')

    try:
        playerID1 = str(getPlayerWtaApiId(playerName1))
        playerID2 = str(getPlayerWtaApiId(playerName2))
        urlplayer1 = "https://ultimate-tennis1.p.rapidapi.com/player_stats/wta/" + playerID1 + "/2023"
        # print(urlplayer1)
        urlplayer2 = "https://ultimate-tennis1.p.rapidapi.com/player_stats/wta/" + playerID2 + "/2023"
        # print(urlplayer2)
        response = requests.get(urlplayer1, headers=headers)
        time.sleep(2)
    except:
        return 0
    else:
        try:
            #print(response.text)
            data = json.loads(response.text)

            print(data)

            prob_service_joueur = data['player_data'][0]['service_points_won_percent']/100
            prob_retour_joueur = data['player_data'][0]['return_points_won_percent']/100


            # Statistiques du joueur2
            response = requests.get(urlplayer2, headers=headers)
        except:
            return 0
        else:
            try:
                data = json.loads(response.text)
                print(data)

                # Statistiques de l'adversaire
                prob_service_adversaire = float(data['player_data'][0]['service_points_won_percent']) / 100
                prob_retour_adversaire = float(data['player_data'][0]['return_points_won_percent']) / 100

                # Calcul de la probabilité pour le joueur et l'adversaire
                prob_40_40_joueur = prob_service_joueur * prob_retour_joueur
                prob_40_40_adversaire = prob_service_adversaire * prob_retour_adversaire

                # Calcul de la probabilité totale
                prob_40_40_totale = prob_40_40_joueur + prob_40_40_adversaire
                prob = float("{:.2}".format(prob_40_40_totale))
                print(str(prob))
            except:
                return 0
            else:
                return prob
#get_wta_proba_40A('errani', 'wang')
#print(get_proba_40A('thiedm', 'MICHALSKI'))