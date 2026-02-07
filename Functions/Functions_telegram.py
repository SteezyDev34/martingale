import json
import os
import ssl

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

import telepot
import config

# Configuration SSL pour requests
import requests.adapters

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


def load_ignored_senders():
    """Charge la liste des expéditeurs à ignorer depuis `conf/ignored_senders.txt`.

    Le fichier peut contenir des identifiants numériques ou des usernames (avec ou sans @),
    une entrée par ligne. Les lignes vides et les commentaires (#) sont ignorés.
    Retourne un set de valeurs en minuscules.
    """
    path = os.path.join(config.projectPath, 'conf', 'ignored_senders.txt')
    ignored = set()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    ignored.add(s.lstrip('@').lower())
    except Exception as e:
        print(f"Erreur lecture ignored_senders: {e}")
    return ignored


def is_ignored_sender(sender_username: str = None, chat_id: str = None) -> bool:
    """Vérifie si `sender_username` ou `chat_id` fait partie de la liste d'ignore.

    Args:
        sender_username: username Telegram (avec ou sans @)
        chat_id: identifiant de channel/groupe (string ou int)

    Retourne True si l'expéditeur doit être ignoré, False sinon.
    """
    ignored = load_ignored_senders()
    if sender_username:
        key = str(sender_username).lstrip('@').lower()
        if key in ignored:
            return True
    if chat_id is not None:
        if str(chat_id) in ignored:
            return True
    return False
