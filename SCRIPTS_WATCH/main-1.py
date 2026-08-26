# Import des modules personnalises
# Import des modules standards
import datetime
import json
import os
import re
import sys
import threading

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
    # Simple ecriture de lignes vides pour PyChar
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
from Functions.Logs.Logger import log, log_clear_line

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
    log_clear_line(3)
else:
    log("Le format du nom du fichier est incorrect.", "error")
    exit()

# Chargement des functions
config.localhost = 43151
config.site_type = 'new_site'

from websocket_server import start_bridge, bridge
start_bridge()

# Vérification instance unique — tuer toute instance précédente du même script
import psutil as _psutil
_current_pid = os.getpid()
_script_name = os.path.basename(__file__)
for _proc in _psutil.process_iter(['pid', 'cmdline']):
    try:
        if _proc.pid == _current_pid:
            continue
        cmdline = ' '.join(_proc.info['cmdline'] or [])
        if _script_name in cmdline and 'python' in cmdline.lower():
            log(f"Instance précédente détectée (PID {_proc.pid}), arrêt...", "warning", clear=False)
            _proc.terminate()
            try:
                _proc.wait(timeout=5)
            except Exception:
                _proc.kill()
    except Exception:
        pass

# First install telethon using: pip install telethon
import ssl
import urllib3
from telethon import TelegramClient, events

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
import sqlite3
from bs4 import BeautifulSoup

requests.adapters.DEFAULT_RETRIES = 3

from Functions import Functions_telegram
from Functions.getTextFromImageGPT import extraire_pari_depuis_image, extraire_pari_depuis_texte
from Functions.TelegramBetsAPI import send_bet_data_to_api, is_ignored_sender
from Functions.AdrBettingScraper import scrape_adrbetting_coupons
from Functions.FrancePronosScraper import scrape_francepronos
from Functions.Bookmakers.session_init import init_bookmaker_sessions

# Connexion manuelle aux bookmakers au démarrage
init_bookmaker_sessions()

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
        log(f"#E0007\nUne erreur est survenue : {e}", "error", clear=False)
        return txt


def bot_msg_handler(txt):
    # Gestion des commandes specifiques via regex
    if len(re.findall("/addword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Quel mot?")
    elif len(re.findall("/delword", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "Mot a supprimer?")
    elif len(re.findall("/instapronos", txt)) == 1:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "team1 - team2\npick\nCOTE :\nMISE :")


def add_word_to_replace(word):
    try:
        words = word.split('\n')
        for word in words:
            word = word.strip().upper()
            codes = open(f"{config.projectPath}/conf/excluded_words.txt", "a")
            codes.write('\n' + word)
            codes.close()
            log("word ADDED  : " + word, "info", clear=False)
        return True
    except Exception as e:
        send_telegram(Functions.Functions_telegram.alertGroup, f"#E00017\nUne erreur est survenue : {e}")
        log(f"#E00017\nUne erreur est survenue : {e}", "error", clear=False)
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
        log("CODES UPDATED : " + updates_used_codes, "info", clear=False)
        return True
    except Exception as e:
        send_telegram(Functions_telegram.alertGroup, f"#E00018\nUne erreur est survenue : {e}")
        log(f"#E00018\nUne erreur est survenue : {e}", "error", clear=False)
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
        log(f"Codes trouves : {codes}", "info")
        return codes
    else:
        return False


# --- Vérification périodique des images publiées sur tempetebetting.com ---
TEMPETE_BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
TEMPETE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tempete_images.db")
TEMPETE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _tempete_create_db():
    conn = sqlite3.connect(TEMPETE_DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_url TEXT UNIQUE,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def _tempete_get_image_links(url):
    try:
        r = requests.get(url, headers=TEMPETE_HEADERS, timeout=15, verify=False)
        if r.status_code != 200:
            log(f"[Tempête] Accès échoué {url} ({r.status_code})", "warning", clear=False)
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
        return [l for l in links if re.match(r'.*\.(jpg|jpeg|png)$', l, re.IGNORECASE)]
    except Exception as e:
        log(f"[Tempête] Erreur récupération liens: {e}", "error", clear=False)
        return []


def _tempete_filter_originals(image_links):
    pattern = re.compile(r'(-\d+x\d+)?\.(jpg|jpeg|png)$', re.IGNORECASE)
    originals = set()
    for link in image_links:
        originals.add(pattern.sub(r'.\2', link))
    return list(originals)


def _tempete_store_new(image_urls):
    conn = sqlite3.connect(TEMPETE_DB_PATH)
    cursor = conn.cursor()
    new = []
    for url in image_urls:
        try:
            cursor.execute("INSERT INTO images (image_url) VALUES (?)", (url,))
            new.append(url)
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return new


def check_tempete_images():
    import time
    _tempete_create_db()
    log("[Tempête] Thread de vérification des images démarré", "info", clear=False)
    while True:
        try:
            now = datetime.datetime.now()
            url = TEMPETE_BASE_URL.format(year=now.year, month=now.month)
            links = _tempete_get_image_links(url)
            originals = _tempete_filter_originals(links)
            new_images = _tempete_store_new(originals)
            if new_images:
                log(f"[Tempête] {len(new_images)} nouvelle(s) image(s) détectée(s)", "info", clear=False)
                for i, img_name in enumerate(new_images):
                    if i > 0:
                        time.sleep(3)
                    full_url = img_name if img_name.startswith('http') else url + img_name
                    try:
                        r = requests.get(full_url, headers=TEMPETE_HEADERS, timeout=15, verify=False)
                        if r.status_code != 200:
                            log(f"[Tempête] Téléchargement échoué: {img_name} ({r.status_code})", "warning", clear=False)
                            continue
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        temp_dir = os.path.join(script_dir, 'media')
                        os.makedirs(temp_dir, exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_path = os.path.join(temp_dir, f"tempete_{timestamp}.jpg")
                        with open(img_path, 'wb') as f:
                            f.write(r.content)
                        log(f"[Tempête] Image téléchargée: {img_name}", "info", clear=False)
                        result = extraire_pari_depuis_image(img_path, "Tempête Betting")
                        try:
                            pari_dict = json.loads(result)
                            pari_dict["tipster"] = "TEMPÊTE BETTING ®️"
                            matches = pari_dict.get("matches", [])
                            if matches:
                                api_success = send_bet_data_to_api(pari_dict, message_original=full_url, sender_username="TEMPÊTE BETTING ®️", image_path=img_path)
                                if api_success:
                                    for match in matches:
                                        log(f"[Tempête] ✅ Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                                        msg = f"🌪️ TEMPÊTE BETTING\n{match.get('equipe_1')} vs {match.get('equipe_2')}\n🎯 {match.get('selection')} @ {match.get('cote')}"
                                        send_telegram(Functions_telegram.alertGroup, msg)
                                else:
                                    log(f"[Tempête] ❌ Échec envoi ({len(matches)} match(s))", "error", clear=False)
                            else:
                                log(f"[Tempête] Aucun match extrait de {img_name}", "warning", clear=False)
                        except json.JSONDecodeError as e:
                            log(f"[Tempête] Erreur JSON OCR: {e}", "error", clear=False)
                        finally:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                    except Exception as e:
                        log(f"[Tempête] Erreur traitement image {img_name}: {e}", "error", clear=False)
            else:
                log("[Tempête] Aucune nouvelle image", "info", clear=False)
        except Exception as e:
            log(f"[Tempête] Erreur boucle principale: {e}", "error", clear=False)
        time.sleep(600)  # Vérification toutes les 10 minutes


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
    log("Client Telegram initialise avec succès", "success", clear=False)
except Exception as e:
    log(f"Erreur lors de l'initialisation du client Telegram : {e}", "error", clear=False)
    # Fallback vers une configuration simple
    client = TelegramClient('2', api_id, api_hash)


# Gestionnaire d'evenements pour detecter les nouveaux messages Telegram
@client.on(events.NewMessage())
async def my_event_handler(event):
    try:
        e = event
    except Exception as e:
        pass

    success = 0  # Indicateur pour contrôler le succès du traitement
    if success == 0:
        while success == 0:
            print('test')
            success = 1  # Passe a 1 une fois que le traitement est reussi
            # Recuperation et affichage du pseudo de l'expediteur
            sender = await event.get_sender()
            txt = event.raw_text  # Convertit le texte en majuscules pour faciliter le traitement
            
            # Filtre pour ignorer les messages contenant certains mots/phrases
            try:
                with open(f"{config.projectPath}/conf/ignored_messages.txt", "r", encoding='utf-8') as fichier:
                    ignored_phrases = [line.strip().lower() for line in fichier.read().split('\n') if line.strip() and not line.strip().startswith('#')]
                    
                # Vérifier si le message contient une phrase à ignorer
                txt_lower = txt.lower()
                for phrase in ignored_phrases:
                    if phrase in txt_lower:
                        log(f"Message ignoré car contient '{phrase}': {txt[:50]}...", "info", clear=False)
                        return  # Ignorer ce message
                        
            except FileNotFoundError:
                # Si le fichier n'existe pas, continuer normalement
                log(f"Fichier ignored_messages.txt non trouvé, aucun filtrage appliqué", "warning", clear=False)

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
                            log(f"Erreur : {e}", "error", clear=False)

                    # Cas où on supprime un mot de la liste
                    elif reply_raw_text == "Mot a supprimer?":
                        word = delete_word_to_replace(txt)
                        try:
                            if word == True:
                                Functions_telegram.send_telegram(auxo_bot_id, txt + ' Supprime!')
                        except Exception as e:
                            log(f"Erreur : {e}", "error", clear=False)
            if event.chat and hasattr(event.chat, 'title') and event.chat.title == 'AdrBetting VIP':
                if "PRONOS EN LIGNE" not in txt.upper():
                    log(f"[AdrBetting] Message ignoré (pas de 'PRONOS EN LIGNE')", "info", clear=False)
                    return
                log(f"[AdrBetting] Message reçu du canal VIP — lancement du scraping", "info", clear=False)
                # Lancer le scraping dans un thread séparé pour ne pas bloquer l'event loop Telegram
                def _run_adrbetting_scrape():
                    try:
                        coupons = scrape_adrbetting_coupons()  # List[tuple(filepath, tipster)]
                        if not coupons:
                            log("[AdrBetting] Aucun coupon récupéré", "warning", clear=False)
                            return
                        log(f"[AdrBetting] {len(coupons)} coupon(s) récupéré(s), lancement OCR...", "info", clear=False)
                        for img_path, tipster in coupons:
                            try:
                                log(f"[AdrBetting] OCR [{tipster}]: {os.path.basename(img_path)}", "info", clear=False)
                                result = extraire_pari_depuis_image(img_path, txt)
                                pari_dict = json.loads(result)
                                pari_dict["tipster"] = tipster
                                matches = pari_dict.get("matches", [])
                                if matches:
                                    api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username=tipster, image_path=img_path)
                                    if api_success:
                                        for match in matches:
                                            log(f"[AdrBetting] ✅ [{tipster}] Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                                            msg = f"🎰 {tipster}\n{match.get('equipe_1')} vs {match.get('equipe_2')}\n🎯 {match.get('selection')} @ {match.get('cote')}"
                                            send_telegram(Functions_telegram.alertGroup, msg)
                                    else:
                                        log(f"[AdrBetting] ❌ [{tipster}] Échec envoi pari ({len(matches)} match(s))", "error", clear=False)
                                if os.path.exists(img_path):
                                    os.remove(img_path)
                            except json.JSONDecodeError as e:
                                log(f"[AdrBetting] Erreur JSON OCR [{tipster}]: {e}", "error", clear=False)
                            except Exception as e:
                                log(f"[AdrBetting] Erreur traitement coupon {img_path}: {e}", "error", clear=False)
                    except Exception as e:
                        log(f"[AdrBetting] Erreur scraping: {e}", "error", clear=False)

                scrape_thread = threading.Thread(target=_run_adrbetting_scrape, daemon=True)
                scrape_thread.start()
                return  # Ne pas traiter le message Telegram normalement

            if event.chat and hasattr(event.chat, 'title') and event.chat.title == 'France Pronos':
                if "www.france-pronos.com/?source=telegram" not in txt.lower():
                    log("[FrancePronos] Message ignoré (pas de lien france-pronos.com)", "info", clear=False)
                    return
                log("[FrancePronos] Message reçu — lancement du scraping", "info", clear=False)
                def _run_francepronos_scrape():
                    try:
                        pronos = scrape_francepronos()
                        if not pronos:
                            log("[FrancePronos] Aucun pronostic récupéré", "warning", clear=False)
                            return
                        log(f"[FrancePronos] {len(pronos)} pronostic(s) récupéré(s), passage à l'IA...", "info", clear=False)
                        for raw in pronos:
                            try:
                                # Formatter le texte brut pour l'IA
                                texte = (
                                    f"Sport: {raw.get('sport', '')}\n"
                                    f"Date: {raw.get('date', '')}\n"
                                    f"Match: {raw.get('intitule', raw.get('equipe_1','') + ' vs ' + raw.get('equipe_2',''))}\n"
                                    f"Équipe 1: {raw.get('equipe_1', '')}\n"
                                    f"Équipe 2: {raw.get('equipe_2', '')}\n"
                                    f"Sélection: {raw.get('selection', '')}\n"
                                    f"Cote: {raw.get('odds', '')}\n"
                                    f"Tipster: FrancePronos"
                                )
                                result = extraire_pari_depuis_texte(texte, txt)
                                pari_dict = json.loads(result)
                                pari_dict["tipster"] = "FrancePronos"
                                matches = pari_dict.get("matches", [])
                                if matches:
                                    api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username="FrancePronos")
                                    if api_success:
                                        for match in matches:
                                            log(f"[FrancePronos] ✅ Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                                            msg = f"🇫🇷 France Pronos\n{match.get('equipe_1')} vs {match.get('equipe_2')}\n🎯 {match.get('selection')} @ {match.get('cote')}"
                                            send_telegram(Functions_telegram.alertGroup, msg)
                                    else:
                                        log(f"[FrancePronos] ❌ Échec envoi ({len(matches)} match(s))", "error", clear=False)
                            except json.JSONDecodeError as e:
                                log(f"[FrancePronos] Erreur JSON IA: {e}", "error", clear=False)
                            except Exception as e:
                                log(f"[FrancePronos] Erreur traitement prono: {e}", "error", clear=False)
                    except Exception as e:
                        log(f"[FrancePronos] Erreur scraping: {e}", "error", clear=False)
                scrape_thread = threading.Thread(target=_run_francepronos_scrape, daemon=True)
                scrape_thread.start()
                return  # Ne pas traiter le message Telegram normalement
            if sender or event.chat_id:
                if is_ignored_sender(sender.username if sender else None, event.chat_id):
                    log("Expediteur ignore, message ignore", "warning", clear=True)
                    return  # Ignorer le message si l'expediteur est dans la liste d'ignorés
                # Affiche le nom d'utilisateur s'il existe, sinon le nom complet
                if sender.username:
                    log(f'Pseudo de l\'expediteur: {sender.username}', "info", clear=False)
                else:
                    log(f'Channel ID: {event.chat_id} - {event.chat.title if event.chat and hasattr(event.chat, "title") else "N/A"}',
                        "info", clear=False)
                # Chaque fois qu'un nouveau message est reçu, cette fonction est declenchee
                log('Nouvel evenement detecte')
                log(event.raw_text, "info", clear=False)  # Affiche le texte brut du message
                log(f'chat id {event.chat_id}', "info", clear=False)  # Affiche l'ID du chat d'où vient le message
                # Check if message contains media/image
                has_media = event.message.media is not None
                log(f'Message contains media: {has_media}', "info", clear=False)

                # Canaux autorisés à envoyer des images de pronos + condition textuelle éventuelle
                # None = pas de condition (toute image est traitée sauf GIF)
                IMAGE_CHANNELS = {
                    "AdrBetting":        "TICKET SAFE PUBLIC",
                    "Tennistiquer":      "CONFIANCE DU JOUR",
                    "TEMPÊTE BETTING ®️":   None,
                    "France Pronos Live": None,
                    "Auxo1XBOT": None
                }

                chat_title = event.chat.title if event.chat and hasattr(event.chat, "title") else ""

                codes = extract_code_1XBET(event.raw_text)
                if codes and isinstance(codes, list):
                    for code in codes:
                        codeList.append(code)
                # Download media if present and canal autorisé
                elif has_media:
                    # Vérifier si le canal est dans la whitelist
                    required_text = IMAGE_CHANNELS.get(chat_title, "NOT_ALLOWED")
                    if required_text == "NOT_ALLOWED":
                        log(f"[Image] Canal '{chat_title}' non autorisé, image ignorée", "info", clear=False)
                        return
                    # Vérifier la condition textuelle si elle existe
                    if required_text is not None and required_text.upper() not in txt.upper():
                        log(f"[Image] [{chat_title}] Image ignorée (condition '{required_text}' absente du message)", "info", clear=False)
                        return
                    # Ignorer les GIFs
                    from telethon.tl.types import MessageMediaDocument
                    if isinstance(event.message.media, MessageMediaDocument):
                        doc = event.message.media.document
                        if any(getattr(attr, 'mime_type', '') == 'image/gif' or str(type(attr).__name__) == 'DocumentAttributeAnimated' for attr in (doc.attributes or [])):
                            log(f"[Image] [{chat_title}] GIF ignoré", "info", clear=False)
                            return
                    log(f"[Image] [{chat_title}] Traitement image autorisé", "info", clear=False)
                    if has_media:
                        # Create unique filename using timestamp
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"media_{timestamp}.jpg"
                        # Create temp directory in the script directory
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        temp_dir = os.path.join(script_dir, 'media')
                        os.makedirs(temp_dir, exist_ok=True)
                        # Set full path for the image in temp directory
                        image_path = os.path.join(temp_dir, filename)
                        log(f"Repertoire temp cree: {temp_dir}", "info", clear=False)
                        log(f"Chemin de l'image: {image_path}", "info", clear=False)
                        # Download the media directly to temp directory
                        await event.message.download_media(file=image_path)
                        log(f"Media downloaded successfully as {image_path}", "info", clear=False)
                        # Process the image
                        result = extraire_pari_depuis_image(image_path, txt)
                        try:
                            pari_dict = json.loads(result)
                            pari_dict["tipster"] = chat_title
                            matches = pari_dict.get("matches", [])
                            if matches:
                                api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username=chat_title, image_path=image_path)
                                if api_success:
                                    for match in matches:
                                        msg = f"📩 {chat_title}\n{match.get('equipe_1')} vs {match.get('equipe_2')}\n🎯 {match.get('selection')} @ {match.get('cote')}"
                                        send_telegram(Functions_telegram.alertGroup, msg)
                        except Exception as _e:
                            log(f"[Image] [{chat_title}] Erreur traitement OCR: {_e}", "error", clear=False)
                        # Delete the downloaded image file
                        print("Attempting to delete the image file...")
                        # try:
                        if image_path:
                            # Verifier que le fichier existe avant de le supprimer
                            if os.path.exists(image_path):
                                # Verifier les permissions de lecture/ecriture
                                if os.access(image_path, os.W_OK):
                                    os.remove(image_path)
                                    log(f"Fichier image supprime avec succès: {filename}", "info", clear=False)
                                else:
                                    log(f"Erreur: Pas de permission d'ecriture pour {image_path}", "error", clear=False)
                                    # Essayer de changer les permissions
                                    try:
                                        os.chmod(image_path, 0o666)
                                        os.remove(image_path)
                                        log(f"Fichier image supprime après changement de permissions: {filename}",
                                            "info", clear=False)
                                    except OSError as chmod_error:
                                        log(f"Impossible de changer les permissions: {chmod_error}", "error",
                                            clear=False)
                            else:
                                log(f"Erreur: Le fichier {image_path} n'existe pas", "error", clear=False)
                        # except OSError as e:
                        # log(f"Erreur lors de la suppression du fichier image: {e}", "error", clear=False)
                        # log(f"Chemin du fichier: {image_path}", "info", clear=False)
                        # log(f"Repertoire courant: {os.getcwd()}", "info", clear=False)
                        # log(f"Le fichier existe: {os.path.exists(image_path)}", "info", clear=False)
                        # Clean up empty temp directory
                        try:
                            # Verifier que le repertoire existe et est vide
                            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                os.rmdir(temp_dir)
                                log(f"Repertoire temporaire supprime: {temp_dir}", "info", clear=False)
                        except OSError as e:
                            log(f"Impossible de supprimer le repertoire temporaire: {e}", "error", clear=False)
                        # Revenir au repertoire original
                        os.chdir(original_cwd)
                    # except Exception as e:
                    # log(f"Error downloading media: {e}", "error", clear=False)

            else:
                log("Expediteur introuvable", "warning", clear=False)
    # except Exception as e:
    # log('Erreur dans le traitement du message', e, "error", clear=False)


# Demarrage du client Telegram
import time as _time
for _attempt in range(5):
    try:
        client.start()
        break
    except Exception as _e:
        if "database is locked" in str(_e).lower() and _attempt < 4:
            log(f"Session SQLite verrouillée, attente... ({_attempt+1}/5)", "warning", clear=False)
            _time.sleep(3)
        else:
            raise

config.scriptType = 'LIVE'


# Fonction de verification des nouveaux codes et envoi
def check():
    import time

    last_api_check = 0
    api_check_interval = 1  # Verifier l'API toutes les 5 minutes

    while True:
        # Traitement des codes directs
        if codeList != []:
            bridge.navigate(config.site_line_url)
            try:
                PlacerCode(codeList[0])
            except Exception as e:
                log(f"Erreur lors du placement du code: {e}", "error", clear=False)
            else:
                log(f"Code place avec succès: {codeList[0]}", "info", clear=False)
                del codeList[0]

        # Traitement des paris en temps reel
        if betList != []:
            try:
                log('Gestion du pari en temps reel', "info", clear=False)
                placer_pari(betList)
            except Exception as e:
                log(f"Erreur lors du placement du pari: {e}", "error", clear=False)
            else:
                log(f"Pari place avec succès: {betList[0]}", "info", clear=False)
                del betList[0]

        # Verification periodique de l'API pour les paris non traites
        current_time = time.time()
        if current_time - last_api_check > api_check_interval:
            #try:
            if current_time:
                #log("Verification des paris non traites dans l'API...", "info", clear=False)
                #processed_count = process_api_bets(limit=5)
                #if processed_count > 0:
                    #log(f"Traite {processed_count} paris depuis l'API", "info", clear=False)
                #else:
                    #log_clear_line()
                last_api_check = current_time
            #except Exception as e:
            #    log(f"Erreur lors du traitement des paris API: {e}", "error", clear=False)

        # Petite pause pour eviter une boucle trop intensive
        time.sleep(10)


# Lancement d'un thread pour verifier les messages en continu
confirmThread = threading.Thread(target=check)
confirmThread.start()

# Thread de vérification des images publiées sur tempetebetting.com
tempeteThread = threading.Thread(target=check_tempete_images, daemon=True)
tempeteThread.start()

# Indique que le bot est demarre
Functions_telegram.send_telegram(auxo_bot_id, "Bot 1XBET Demarre")

# Le bot continue a tourner tant qu'il n'est pas deconnecte
client.run_until_disconnected()
