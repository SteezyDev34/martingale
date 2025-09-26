import json
import ssl
import os
import urllib3

# Configuration SSL pour éviter les erreurs de certificat
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'

# Désactiver la vérification SSL par défaut
ssl._create_default_https_context = ssl._create_unverified_context

# Désactiver les avertissements SSL
try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

import requests
import telepot

# Configuration SSL pour requests
import requests.adapters
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration de session avec SSL désactivé
session = requests.Session()
session.verify = False

api_id = '5493357'
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'
CHANNEL = "Test channel code"
TEL = "+33626996498"

auxo_bot_id = "820171667"
channel_com2_bot = '-1001699523977'
group_AuxoAnalytix = '-1001672474839'
groupID = "-540044043"
alertGroup = "-1001848207367"
freeGroup = "-1001315247334"
"""auxoInvestGroup = "-540044043"""
auxoInvestGroup = "-1001441208953"

cmd = [{
    "command": "addword",
    "description": "Ajouter un mot à filter"
},
    {
        "command": "delword",
        "description": "Supprimer un mot à filtrer"
    },
    {
        "command": "instapronos",
        "description": "Ajouter un pronos sur insta"
    },
    {
        "command": "majcapital",
        "description": "Mettre à jour le capital"
    }]


def set_commands(cmd):
    url = "https://api.telegram.org/bot1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc/setMyCommands?commands="
    cmd = json.dumps(cmd)
    url = url + str(cmd)
    response = session.get(url, verify=False)
    if str(response) == "<Response [200]>":
        print('Commands set!')
    else:
        print('Une erreur s\'est produite : ' + str(response))


global bot
set_commands(cmd)

# Token du bot
BOT_TOKEN = '1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc'

# Initialiser telepot avec gestion d'erreur
try:
    bot = telepot.Bot(BOT_TOKEN)
except Exception as e:
    print(f"Erreur lors de l'initialisation de telepot : {e}")
    bot = None


def send_telegram(groupid, message):
    try:
        # Utiliser requests directement avec notre session SSL configurée
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': groupid,
            'text': message
        }
        response = session.post(url, data=data, verify=False)
        if response.status_code != 200:
            print(f"Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")


def send_telegram_group(groupid, message, code):
    try:
        # Utiliser requests directement avec notre session SSL configurée
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': groupid,
            'text': message
        }
        response = session.post(url, data=data, verify=False)
        if response.status_code == 200:
            result = response.json()
            message_id = result['result']['message_id']
            codesmessage = open("codesmessage.txt", "a")
            codesmessage.write("\n" + str(code) + ' | ' + str(message_id))
            codesmessage.close()
        else:
            print(f"Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")


# WORD TO AVOID ON MESSAGE RECEIVE
def filter_txt(txt):
    try:
        fichier = open("words.txt", "r")
        words = fichier.read()
        fichier.close()
        words = words.split('\n')
        for word in words:
            txt = txt.replace(word.strip().upper(), "")
        return txt
    except Exception as e:
        send_telegram(alertGroup, f"#E0007\nUne erreur est survenue : {e}")
        print(f"#E0007\nUne erreur est survenue : {e}")
        return txt


def add_word_to_replace(word):
    try:
        words = word.split('\n')
        for word in words:
            word = word.strip().upper()
            codes = open("words.txt", "a")
            codes.write('\n' + word)
            codes.close()
            print("word ADDED  : " + word)
        return True
    except Exception as e:
        send_telegram(alertGroup, f"#E00017\nUne erreur est survenue : {e}")
        print(f"#E00017\nUne erreur est survenue : {e}")
        return False


def delete_word_to_replace(word):
    try:
        words = word.split('\n')
        used_codes = ""
        codes = open("words.txt", "r")
        used_codes = codes.read()
        codes.close()
        updates_used_codes = used_codes  # Initialiser la variable
        for word in words:
            word = word.strip().upper()
            updates_used_codes = updates_used_codes.replace('\n' + word, '')
        codes = open("words.txt", "w")
        codes.write(updates_used_codes)
        codes.close()
        # print("CODES UPDATED : "+updates_used_codes)
        return True
    except Exception as e:
        send_telegram(alertGroup, f"#E00018\nUne erreur est survenue : {e}")
        print(f"#E00018\nUne erreur est survenue : {e}")
        return False
