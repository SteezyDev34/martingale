# Import des modules personnalisés
# Import des modules standards
import datetime
import json
import os
import re
import sys
import threading

import Functions.Functions_telegram
from Functions.Functions_telegram import send_telegram
from Functions.PlacerCode import PlacerCode

# Récupérer le chemin absolu du fichier actuel
current_file_path = os.path.abspath(__file__)

# Récupérer le dossier parent du fichier actuel
parent_directory = os.path.dirname(current_file_path)
# ajouter un autre niveau parent si nécessaire
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

# Sauvegarder le répertoire de travail actuel
original_cwd = os.getcwd()

if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
    # Simple écriture de lignes vides pour PyCharm

    # Vérification de l'environnement
    # Changer vers le répertoire racine du projet pour VenvDependencyManager
    os.chdir(project_directory)

    import VenvDependencyManager

    VenvDependencyManager.main()

    # Revenir au répertoire original
    os.chdir(original_cwd)

# Chargement des variables globales
from Functions.PlacerPari import placer_pari
import config

config.localhost = 7879
# Demander confirmation à l'utilisateur
# Define Chrome launch command based on operating system
chrome_profile = f"ChromeDebugProfile{config.localhost}"
command = 'start chrome' if config.systeme == 'Windows' else 'open -na "Google Chrome" --args'
command = f'{command} --remote-debugging-port={config.localhost} --user-data-dir="{os.path.join(project_directory if config.systeme == "Windows" else "$HOME", chrome_profile)}"'
confirmation = input(f"Avez-vous exécuté la commande \n{command}\n? (Y/N): ")

if confirmation.upper() not in ['Y', 'O']:
    print("Programme arrêté par l'utilisateur.")
    sys.exit(0)  # Arrêter le programme

# First install telethon using: pip install telethon
import ssl
import os
import urllib3
from telethon import TelegramClient, events
from ChromeDriver.SetDriver import driver

# Configuration SSL pour éviter les erreurs de certificat
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'
os.environ['AIOHTTP_NO_EXTENSIONS'] = '1'

# Configurer SSL pour ignorer les certificats
ssl._create_default_https_context = ssl._create_unverified_context

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration spécifique pour aiohttp (utilisé par Telethon)

# Configuration supplémentaire pour les requêtes

# Configuration globale pour requests
import requests.adapters

requests.adapters.DEFAULT_RETRIES = 3

from Functions import Functions_telegram
from Functions.getTextFromImageGPT import extraire_pari_depuis_image

# Déclaration d'une variable globale qui va stocker les codes de paris
global codeList, betList
codeList = []
betList = []

# Informations d'identification pour l'API de Telegram
api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

# Identifiants de l'auxo bot et du groupe de notifications
auxo_bot_id = "820171667"
alertGroup = "-1001848207367"

# Configuration SSL spécifique pour Telethon
import aiohttp


def filter_txt(txt):
    try:
        fichier = open(f"{config.projectPath}/conf/excluded_words.txt", "r")
        words = fichier.read()
        fichier.close()
        words = words.split('\n')
        for word in words:
            txt = txt.replace(word.strip().upper(), "")
        return txt
    except Exception as e:
        send_telegram(Functions.Functions_telegram.alertGroup, f"#E0007\nUne erreur est survenue : {e}")
        print(f"#E0007\nUne erreur est survenue : {e}")
        return txt


def bot_msg_handler(txt):
    # Gestion des commandes spécifiques via regex
    if len(re.findall("/addword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Quel mot?")
    elif len(re.findall("/delword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Mot à supprimer?")
    elif len(re.findall("/instapronos", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "team1 - team2\npick\nCOTE :\nMISE :")
        success = 1


def add_word_to_replace(word):
    try:
        words = word.split('\n')
        for word in words:
            word = word.strip().upper()
            codes = open(f"{config.projectPath}/conf/excluded_words.txt", "a")
            codes.write('\n' + word)
            codes.close()
            print("word ADDED  : " + word)
        return True
    except Exception as e:
        send_telegram(Functions.Functions_telegram.alertGroup, f"#E00017\nUne erreur est survenue : {e}")
        print(f"#E00017\nUne erreur est survenue : {e}")
        return False


def delete_word_to_replace(word):
    try:
        words = word.split('\n')
        used_codes = ""
        codes = open(f"{config.projectPath}/conf/excluded_words.txt", "r")
        used_codes = codes.read()
        codes.close()
        updates_used_codes = used_codes  # Initialiser la variable
        for word in words:
            word = word.strip().upper()
            updates_used_codes = updates_used_codes.replace('\n' + word, '')
        codes = open(f"{config.projectPath}/conf/excluded_words.txt", "w")
        codes.write(updates_used_codes)
        codes.close()
        # print("CODES UPDATED : "+updates_used_codes)
        return True
    except Exception as e:
        send_telegram(Functions_telegram.alertGroup, f"#E00018\nUne erreur est survenue : {e}")
        print(f"#E00018\nUne erreur est survenue : {e}")
        return False


def extract_code_1XBET(txt):
    """
    Extrait un code 1XBET de 5 caractères alphanumériques en majuscules depuis un texte.
    
    Args:
        txt (str): Le texte à analyser
        
    Returns:
        list: Liste contenant le code trouvé si exactement un code est détecté
        bool: False si aucun code ou plusieurs codes sont trouvés
    """
    txt = filter_txt(txt)

    # Recherche de codes de 5 caractères alphanumériques en majuscules uniquement
    # Le pattern \b[A-Z0-9]{5}\b recherche exactement 5 caractères consécutifs
    # composés uniquement de lettres majuscules (A-Z) et de chiffres (0-9)
    # entourés de délimiteurs de mots (\b)
    codes = re.findall(r"\b[A-Z0-9]{5}\b", txt)
    # Retourne le code uniquement si exactement un code est trouvé
    if len(codes) == 1:
        print(f"Codes trouvés : {codes}")
        return codes
    else:
        return False


# Patch pour aiohttp afin de désactiver la vérification SSL
original_create_connection = aiohttp.TCPConnector._create_connection


async def patched_create_connection(self, req, traces, timeout):
    return await original_create_connection(self, req, traces, timeout)


# Appliquer le patch
aiohttp.TCPConnector._create_connection = patched_create_connection

# Initialisation du client Telegram avec paramètres robustes
try:
    client = TelegramClient(
        '2',
        api_id,
        api_hash,
        connection_retries=5,
        retry_delay=1,
        timeout=30,
        request_retries=5,
        auto_reconnect=True,
        device_model="Desktop",
        system_version="Windows 10",
        app_version="1.0",
        lang_code="fr",
        system_lang_code="fr"
    )
    print("Client Telegram initialisé avec succès")
except Exception as e:
    print(f"Erreur lors de l'initialisation du client Telegram : {e}")
    # Fallback vers une configuration simple
    client = TelegramClient('2', api_id, api_hash)


# Gestionnaire d'événements pour détecter les nouveaux messages Telegram
@client.on(events.NewMessage())
async def my_event_handler(event):
    # Chaque fois qu'un nouveau message est reçu, cette fonction est déclenchée
    print('Nouvel événement détecté')
    print(event.raw_text)  # Affiche le texte brut du message
    print('chat id', event.chat_id)  # Affiche l'ID du chat d'où vient le message
    try:
        success = 0  # Indicateur pour contrôler le succès du traitement
        while success == 0:
            success = 1  # Passe à 1 une fois que le traitement est réussi
            # Récupération et affichage du pseudo de l'expéditeur
            sender = await event.get_sender()
            txt = event.raw_text  # Convertit le texte en majuscules pour faciliter le traitement

            if str(event.chat_id) == '1910869556':
                bot_msg_handler(txt)
                reply = await event.get_reply_message()  # Récupère le message auquel il est répondu
                if reply:
                    reply_raw_text = reply.raw_text  # Texte du message de réponse
                    # Cas où on ajoute un mot à la liste
                    if reply_raw_text == "Quel mot?":
                        word = add_word_to_replace(txt)
                        try:
                            if word == True:
                                Functions_telegram.send_telegram(auxo_bot_id, txt + ' Ajouté!')
                        except Exception as e:
                            print(f"Erreur : {e}")

                    # Cas où on supprime un mot de la liste
                    elif reply_raw_text == "Mot à supprimer?":
                        word = delete_word_to_replace(txt)
                        try:
                            if word == True:
                                Functions_telegram.send_telegram(auxo_bot_id, txt + ' Supprimé!')
                        except Exception as e:
                            print(f"Erreur : {e}")
            if sender:
                # Affiche le nom d'utilisateur s'il existe, sinon le nom complet
                if sender.username:
                    print('Pseudo de l\'expéditeur:', sender.username)
                    # Check if message contains media/image
                    has_media = event.message.media is not None
                    print('Message contains media:', has_media)
                    code = extract_code_1XBET(event.raw_text)
                    if code:
                        codeList.append(code)
                    # Download media if present
                    elif has_media:
                        try:
                            # Create unique filename using timestamp
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"media_{timestamp}.jpg"
                            # Create temp directory in the script directory
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            temp_dir = os.path.join(script_dir, 'media')
                            os.makedirs(temp_dir, exist_ok=True)
                            # Set full path for the image in temp directory
                            image_path = os.path.join(temp_dir, filename)
                            print(f"Répertoire temp créé: {temp_dir}")
                            print(f"Chemin de l'image: {image_path}")
                            # Download the media directly to temp directory
                            await event.message.download_media(file=image_path)
                            print(f"Media downloaded successfully as {image_path}")
                            # Process the image
                            result = extraire_pari_depuis_image(image_path, event.raw_text)
                            # Delete the downloaded image file
                            try:
                                # Vérifier que le fichier existe avant de le supprimer
                                if os.path.exists(image_path):
                                    # Vérifier les permissions de lecture/écriture
                                    if os.access(image_path, os.W_OK):
                                        os.remove(image_path)
                                        print(f"Fichier image supprimé avec succès: {filename}")
                                    else:
                                        print(f"Erreur: Pas de permission d'écriture pour {image_path}")
                                        # Essayer de changer les permissions
                                        try:
                                            os.chmod(image_path, 0o666)
                                            os.remove(image_path)
                                            print(f"Fichier image supprimé après changement de permissions: {filename}")
                                        except OSError as chmod_error:
                                            print(f"Impossible de changer les permissions: {chmod_error}")
                                else:
                                    print(f"Erreur: Le fichier {image_path} n'existe pas")
                            except OSError as e:
                                print(f"Erreur lors de la suppression du fichier image: {e}")
                                print(f"Chemin du fichier: {image_path}")
                                print(f"Répertoire courant: {os.getcwd()}")
                                print(f"Le fichier existe: {os.path.exists(image_path)}")
                            # Clean up empty temp directory
                            try:
                                # Vérifier que le répertoire existe et est vide
                                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                    os.rmdir(temp_dir)
                                    print(f"Répertoire temporaire supprimé: {temp_dir}")
                            except OSError as e:
                                print(f"Impossible de supprimer le répertoire temporaire: {e}")
                            # Revenir au répertoire original
                            os.chdir(original_cwd)
                            # Convertir le résultat JSON en dictionnaire et l'ajouter à codeList
                            try:
                                pari_dict = json.loads(result)
                                betList.append(pari_dict)
                                print(f"Pari ajouté à codeList: {pari_dict}")
                            except json.JSONDecodeError as e:
                                print(f"Erreur lors de la conversion JSON: {e}")
                                print(f"Résultat brut: {result}")
                        except Exception as e:
                            print(f"Error downloading media: {e}")

    except Exception as e:
        print('Erreur dans le traitement du message', e)


# Démarrage du client Telegram
client.start()

config.scriptType = 'LIVE'


# Fonction de vérification des nouveaux codes et envoi
def check():
    while True:
        if codeList != []:
            driver.get(config.site_line_url)
            try:
                PlacerCode(driver, codeList[0])
            except Exception as e:
                print(f"Erreur lors du placement du code: {e}")
            else:
                print(f"Code placé avec succès: {codeList[0]}")
                del codeList[0]
        if betList != []:
            try:
                print('gestion du pari')
                placer_pari(driver, betList)
            except Exception as e:
                print(f"Erreur lors du placement du pari: {e}")
            else:
                print(f"Pari placé avec succès: {betList[0]}")
                del betList[0]


# Lancement d'un thread pour vérifier les messages en continu
confirmThread = threading.Thread(target=check)
confirmThread.start()

# Indique que le bot est démarré
Functions_telegram.send_telegram(auxo_bot_id, "Bot 1XBET Démarré")

# Le bot continue à tourner tant qu'il n'est pas déconnecté
client.run_until_disconnected()
