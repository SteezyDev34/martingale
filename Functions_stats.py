import time
from datetime import date
import requests
import json
import re
import threading
import time


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from unidecode import unidecode

##DEFINITION DES FONCTIONS
##
##FIN DEFINITION DES FONCTIONS

global headers
headers= {
    'X-RapidAPI-Key': 'b052b9bd1cmsh0e38ccdfaf9d624p1dd988jsnde30c2e5a6dc',
    "X-RapidAPI-Host": "ultimate-tennis1.p.rapidapi.com"
}
# Obtenez l'heure actuelle
today = date.today()
####
#ATP
####
# Ouvrez le fichier "atprankinjson.txt" en mode ajout et
# créez le fichier s'il n'existe pas
file1 = open("atprankinjson.txt", "a+")
# Fermez le fichier
file1.close()
# Ouvrez à nouveau le fichier en mode lecture
file1 = open("atprankinjson.txt", "r")

# Lisez le contenu mis à jour du fichier
txt_after_write = file1.read()
# Fermez le fichier après la lecture
file1.close()
txt_after_write = txt_after_write.split('\n')
try:
    if txt_after_write[0]!= str(today):
        print('nouvelle date')
        url = "https://ultimate-tennis1.p.rapidapi.com/live_leaderboard/450"



        response = requests.get(url, headers=headers)

        print(response.text)
        # Convertir la chaîne JSON en une structure de données Python
        data = json.loads(response.text)

        # Afficher la structure de données Python
        players_id_list = []
        for player in data['data']:
            thename = player['Name'].split('.')
            players_id_list.append(thename[1].strip()+'|'+player['id'])
        players_id_list = '\n'.join(players_id_list)
        # Ouvrez à nouveau le fichier en mode écriture
        file1 = open("atprankinjson.txt", "w+")
        # Écrivez l'heure actuelle dans le fichier
        file1.write(str(today)+'\n'+players_id_list)
        print(today)
        # Fermez le fichier après l'écriture
        file1.close()
except:
    pass


###
#WTA
###
# Ouvrez le fichier "atprankinjson.txt" en mode ajout et
# créez le fichier s'il n'existe pas
file1 = open("wtarankinjson.txt", "a+")
# Fermez le fichier
file1.close()
# Ouvrez à nouveau le fichier en mode lecture
file1 = open("wtarankinjson.txt", "r")

# Lisez le contenu mis à jour du fichier
txt_after_write = file1.read()
# Fermez le fichier après la lecture
file1.close()
txt_after_write = txt_after_write.split('\n')
try:
    if txt_after_write[0]!= str(today):
        print('nouvelle date')
        url = "https://ultimate-tennis1.p.rapidapi.com/rankings/wta/singles/1000/current"



        response = requests.get(url, headers=headers)
        # Convertir la chaîne JSON en une structure de données Python
        data = json.loads(response.text)
        print(data)
        # Afficher la structure de données Python
        players_id_list = []
        for player in data['data']:
            players_id_list.append(player['name'].strip()+'|'+str(player['ID']))
        players_id_list = '\n'.join(players_id_list)
        # Ouvrez à nouveau le fichier en mode écriture
        file1 = open("wtarankinjson.txt", "w+")
        # Écrivez l'heure actuelle dans le fichier
        file1.write(str(today)+'\n'+players_id_list)
        print(today)
        # Fermez le fichier après l'écriture
        file1.close()
except:
    pass


def getPlayerApiId(playerName):
    playerName = unidecode(playerName)
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

    playerName = unidecode(playerName)
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
#print(get_proba_40A('DENIS YEVSEYEV', 'MARK LAJAL'))