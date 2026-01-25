# Import des modules personnalises
# Import des modules standards
import datetime
import json
import os
import re
import sys
import threading
import time
from art import *


# Recuperer le chemin absolu du fichier actuel
current_file_path = os.path.abspath(__file__)

# Recuperer le dossier parent du fichier actuel
parent_directory = os.path.dirname(current_file_path)

# ajouter un autre niveau parent si necessaire
project_directory = os.path.dirname(parent_directory)

sys.path.append(project_directory)

# Sauvegarder le repertoire de travail actuel
original_cwd = os.getcwd()

if os.getenv('PYCHARM_HOSTED') != '1':  # Si execute dans PyCharm
    # Simple ecriture de lignes vides pour PyCharm

    # Verification de l'environnement
    # Changer vers le repertoire racine du projet pour VenvDependencyManager
    os.chdir(project_directory)

    import VenvDependencyManager

    VenvDependencyManager.main()

    # Revenir au repertoire original
    os.chdir(original_cwd)

# Chargement des variables globales
import Functions.Functions_telegram
from Functions.Functions_telegram import send_telegram
from Functions.PlacerCode import PlacerCode
from Functions.PlacerPari import placer_pari
import config

# Recuperer le nom du script
# Nom du fichier
file_name = os.path.basename(__file__)  # ou directement '40-1.py' pour l'exemple
# Separer le nom du fichier et l'extension
name_part = os.path.splitext(file_name)[0]
# Separer les parties du nom
parts = name_part.split('-')
if len(parts) > 1:
    config.scriptType = parts[0]  # Suppose que le type est avant le tiret
    config.script_num = int(parts[1])  # Suppose que le numero est avant le tiret
    localhost = str(config.scriptType) + str(config.script_num)
    config.localhost = ''.join(caractere for caractere in localhost if caractere.isdigit())
    if int(config.localhost) < 1024:
        config.localhost = 1024 + int(config.localhost)
    # Demander confirmation a l'utilisateur
    # Le lancement de Chrome est maintenant gere dans SetDriver.py
    config.log_clear_line(3)

    print(f'{config.PURPLE}{text2art(f'Start martingal {config.scriptType} {config.script_num}')}')
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions
# Chargement de Chrome driver
config.localhost = 43151
from ChromeDriver.SetDriver import get_script_driver
num_fenetre = 1
driver = get_script_driver(num_fenetre)
# First install telethon using: pip install telethon
import ssl
import os
import urllib3
from telethon import TelegramClient, events
from ChromeDriver.SetDriver import driver

# Configuration SSL pour eviter les erreurs de certificat
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'
os.environ['AIOHTTP_NO_EXTENSIONS'] = '1'

# Configurer SSL pour ignorer les certificats
ssl._create_default_https_context = ssl._create_unverified_context

# Desactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration specifique pour aiohttp (utilise par Telethon)

# Configuration supplementaire pour les requêtes

# Configuration globale pour requests
import requests.adapters

requests.adapters.DEFAULT_RETRIES = 3

from Functions import Functions_telegram
from Functions.getTextFromImageGPT import extraire_pari_depuis_image
from Functions.TelegramBetsAPI import send_bet_data_to_api, telegram_bets_api

# Declaration d'une variable globale qui va stocker les codes de paris
global codeList, betList
codeList = []
betList = []

# Informations d'identification pour l'API de Telegram
api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

# Identifiants de l'auxo bot et du groupe de notifications
auxo_bot_id = "820171667"
alertGroup = "-1001848207367"

# Configuration SSL specifique pour Telethon
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
    # Gestion des commandes specifiques via regex
    if len(re.findall("/addword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Quel mot?")
    elif len(re.findall("/delword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Mot a supprimer?")
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
    Extrait un code 1XBET de 5 caractères alphanumeriques en majuscules depuis un texte.
    
    Args:
        txt (str): Le texte a analyser
        
    Returns:
        list: Liste contenant le code trouve si exactement un code est detecte
        bool: False si aucun code ou plusieurs codes sont trouves
    """
    txt = filter_txt(txt)

    # Recherche de codes de 5 caractères alphanumeriques en majuscules uniquement
    # Le pattern \b[A-Z0-9]{5}\b recherche exactement 5 caractères consecutifs
    # composes uniquement de lettres majuscules (A-Z) et de chiffres (0-9)
    # entoures de delimiteurs de mots (\b)
    codes = re.findall(r"\b[A-Z0-9]{5}\b", txt)
    # Retourne le code uniquement si exactement un code est trouve
    if len(codes) == 1:
        print(f"Codes trouves : {codes}")
        return codes
    else:
        return False


# Patch pour aiohttp afin de desactiver la verification SSL
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
    print("Client Telegram initialise avec succès")
except Exception as e:
    print(f"Erreur lors de l'initialisation du client Telegram : {e}")
    # Fallback vers une configuration simple
    client = TelegramClient('2', api_id, api_hash)


# Gestionnaire d'evenements pour detecter les nouveaux messages Telegram
@client.on(events.NewMessage())
async def my_event_handler(event):
    # Chaque fois qu'un nouveau message est reçu, cette fonction est declenchee
    print('Nouvel evenement detecte')
    print(event.raw_text)  # Affiche le texte brut du message
    print('chat id', event.chat_id)  # Affiche l'ID du chat d'où vient le message
    try:
        success = 0  # Indicateur pour contrôler le succès du traitement
        while success == 0:
            success = 1  # Passe a 1 une fois que le traitement est reussi
            # Recuperation et affichage du pseudo de l'expediteur
            sender = await event.get_sender()
            txt = event.raw_text  # Convertit le texte en majuscules pour faciliter le traitement

            if str(event.chat_id) == '1910869556':
                bot_msg_handler(txt)
                reply = await event.get_reply_message()  # Recupère le message auquel il est repondu
                if reply:
                    reply_raw_text = reply.raw_text  # Texte du message de reponse
                    # Cas où on ajoute un mot a la liste
                    if reply_raw_text == "Quel mot?":
                        word = add_word_to_replace(txt)
                        try:
                            if word == True:
                                Functions_telegram.send_telegram(auxo_bot_id, txt + ' Ajoute!')
                        except Exception as e:
                            print(f"Erreur : {e}")

                    # Cas où on supprime un mot de la liste
                    elif reply_raw_text == "Mot a supprimer?":
                        word = delete_word_to_replace(txt)
                        try:
                            if word == True:
                                Functions_telegram.send_telegram(auxo_bot_id, txt + ' Supprime!')
                        except Exception as e:
                            print(f"Erreur : {e}")
            if sender:
                # Affiche le nom d'utilisateur s'il existe, sinon le nom complet
                if sender.username:
                    print('Pseudo de l\'expediteur:', sender.username)
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
                            print(f"Repertoire temp cree: {temp_dir}")
                            print(f"Chemin de l'image: {image_path}")
                            # Download the media directly to temp directory
                            await event.message.download_media(file=image_path)
                            print(f"Media downloaded successfully as {image_path}")
                            # Process the image
                            result = extraire_pari_depuis_image(image_path, event.raw_text)
                            # Delete the downloaded image file
                            try:
                                # Verifier que le fichier existe avant de le supprimer
                                if os.path.exists(image_path):
                                    # Verifier les permissions de lecture/ecriture
                                    if os.access(image_path, os.W_OK):
                                        os.remove(image_path)
                                        print(f"Fichier image supprime avec succès: {filename}")
                                    else:
                                        print(f"Erreur: Pas de permission d'ecriture pour {image_path}")
                                        # Essayer de changer les permissions
                                        try:
                                            os.chmod(image_path, 0o666)
                                            os.remove(image_path)
                                            print(f"Fichier image supprime après changement de permissions: {filename}")
                                        except OSError as chmod_error:
                                            print(f"Impossible de changer les permissions: {chmod_error}")
                                else:
                                    print(f"Erreur: Le fichier {image_path} n'existe pas")
                            except OSError as e:
                                print(f"Erreur lors de la suppression du fichier image: {e}")
                                print(f"Chemin du fichier: {image_path}")
                                print(f"Repertoire courant: {os.getcwd()}")
                                print(f"Le fichier existe: {os.path.exists(image_path)}")
                            # Clean up empty temp directory
                            try:
                                # Verifier que le repertoire existe et est vide
                                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                    os.rmdir(temp_dir)
                                    print(f"Repertoire temporaire supprime: {temp_dir}")
                            except OSError as e:
                                print(f"Impossible de supprimer le repertoire temporaire: {e}")
                            # Revenir au repertoire original
                            os.chdir(original_cwd)
                            # Convertir le resultat JSON en dictionnaire et l'ajouter a codeList
                            try:
                                pari_dict = json.loads(result)
                                betList.append(pari_dict)
                                print(f"Pari ajoute a betList: {pari_dict}")
                                
                                # Envoyer le pari a l'API
                                try:
                                    sender_username = sender.username if sender and sender.username else None
                                    api_success = send_bet_data_to_api(
                                        pari_dict, 
                                        message_original=event.raw_text,
                                        sender_username=sender_username
                                    )
                                    if api_success:
                                        print(f"Pari envoye avec succès a l'API")
                                    else:
                                        print(f"echec de l'envoi du pari a l'API")
                                except Exception as api_error:
                                    print(f"Erreur lors de l'envoi a l'API: {api_error}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"Erreur lors de la conversion JSON: {e}")
                                print(f"Resultat brut: {result}")
                        except Exception as e:
                            print(f"Error downloading media: {e}")

    except Exception as e:
        print('Erreur dans le traitement du message', e)


# Demarrage du client Telegram
client.start()

config.scriptType = 'LIVE'


# Fonction de verification des nouveaux codes et envoi
def check():
    from Functions.ProcessTelegramBets import process_api_bets
    import time
    
    last_api_check = 0
    api_check_interval = 300  # Verifier l'API toutes les 5 minutes
    
    while True:
        # Traitement des codes directs
        if codeList != []:
            driver.get(config.site_line_url)
            try:
                PlacerCode(driver, codeList[0])
            except Exception as e:
                print(f"Erreur lors du placement du code: {e}")
            else:
                print(f"Code place avec succès: {codeList[0]}")
                del codeList[0]
        
        # Traitement des paris en temps reel
        if betList != []:
            try:
                print('Gestion du pari en temps reel')
                placer_pari(driver, betList)
            except Exception as e:
                print(f"Erreur lors du placement du pari: {e}")
            else:
                print(f"Pari place avec succès: {betList[0]}")
                del betList[0]
        
        # Verification periodique de l'API pour les paris non traites
        current_time = time.time()
        if current_time - last_api_check > api_check_interval:
            try:
                print("Verification des paris non traites dans l'API...")
                processed_count = process_api_bets(driver, limit=5)
                if processed_count > 0:
                    print(f"Traite {processed_count} paris depuis l'API")
                last_api_check = current_time
            except Exception as e:
                print(f"Erreur lors du traitement des paris API: {e}")
        
        # Petite pause pour eviter une boucle trop intensive
        time.sleep(1)


# Lancement d'un thread pour verifier les messages en continu
confirmThread = threading.Thread(target=check)
confirmThread.start()

# Indique que le bot est demarre
Functions_telegram.send_telegram(auxo_bot_id, "Bot 1XBET Demarre")

# Le bot continue a tourner tant qu'il n'est pas deconnecte
client.run_until_disconnected()
