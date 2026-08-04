#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surveillance headless pour serveur : Telegram + Tempête Betting + AdrBetting + FrancePronos
Aucune dépendance Selenium/Chrome debug port.
Playwright tourne en mode headless.
"""
import datetime
import json
import os
import re
import sqlite3
import sys
import threading
import ssl
import time
import urllib3

# --- Chemins ---
current_file_path = os.path.abspath(__file__)
project_directory = os.path.dirname(current_file_path)
sys.path.insert(0, project_directory)

# --- Config minimale ---
import config
config.localhost = '43151'  # non utilisé mais évite les imports qui le lisent

# --- SSL désactivé (certificats auto-signés) ---
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'
os.environ['AIOHTTP_NO_EXTENSIONS'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
import requests.adapters
from bs4 import BeautifulSoup
requests.adapters.DEFAULT_RETRIES = 3

from dotenv import load_dotenv
load_dotenv(os.path.join(project_directory, '.env'))

from Functions.Logs.Logger import log
import Functions.Functions_telegram
from Functions.Functions_telegram import send_telegram
from Functions.getTextFromImageGPT import extraire_pari_depuis_image, extraire_pari_depuis_texte
from Functions.TelegramBetsAPI import send_bet_data_to_api, is_ignored_sender
from Functions.AdrBettingScraper import scrape_adrbetting_coupons
from Functions.FrancePronosScraper import scrape_francepronos

from telethon import TelegramClient, events
import aiohttp


# ─── Tempête Betting ─────────────────────────────────────────────────────────

TEMPETE_BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
TEMPETE_DB_PATH = os.path.join(project_directory, "SCRIPTS WATCH", "tempete_images.db")
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
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
        return [l for l in links if re.match(r'.*\.(jpg|jpeg|png)$', l, re.IGNORECASE)]
    except Exception as e:
        log(f"[Tempête] Erreur liens: {e}", "error", clear=False)
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
    _tempete_create_db()
    log("[Tempête] Thread démarré", "info", clear=False)
    while True:
        try:
            now = datetime.datetime.now()
            url = TEMPETE_BASE_URL.format(year=now.year, month=now.month)
            links = _tempete_get_image_links(url)
            originals = _tempete_filter_originals(links)
            new_images = _tempete_store_new(originals)
            if new_images:
                log(f"[Tempête] {len(new_images)} nouvelle(s) image(s)", "info", clear=False)
                for i, img_name in enumerate(new_images):
                    if i > 0:
                        time.sleep(3)
                    full_url = img_name if img_name.startswith('http') else url + img_name
                    try:
                        r = requests.get(full_url, headers=TEMPETE_HEADERS, timeout=15, verify=False)
                        if r.status_code != 200:
                            continue
                        temp_dir = os.path.join(project_directory, 'SCRIPTS WATCH', 'media')
                        os.makedirs(temp_dir, exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_path = os.path.join(temp_dir, f"tempete_{timestamp}.jpg")
                        with open(img_path, 'wb') as f:
                            f.write(r.content)
                        result = extraire_pari_depuis_image(img_path, "Tempête Betting")
                        try:
                            pari_dict = json.loads(result)
                            pari_dict["tipster"] = "TEMPÊTE BETTING ®️"
                            matches = pari_dict.get("matches", [])
                            if matches:
                                api_success = send_bet_data_to_api(pari_dict, message_original=full_url, sender_username="TEMPÊTE BETTING ®️")
                                status = "✅" if api_success else "❌"
                                log(f"[Tempête] {status} {len(matches)} match(s) envoyé(s)", "info", clear=False)
                        except json.JSONDecodeError as e:
                            log(f"[Tempête] Erreur JSON OCR: {e}", "error", clear=False)
                        finally:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                    except Exception as e:
                        log(f"[Tempête] Erreur image {img_name}: {e}", "error", clear=False)
        except Exception as e:
            log(f"[Tempête] Erreur boucle: {e}", "error", clear=False)
        time.sleep(600)  # toutes les 10 minutes


# ─── Telegram ────────────────────────────────────────────────────────────────

api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

IMAGE_CHANNELS = {
    "AdrBetting":          "TICKET SAFE PUBLIC",
    "Tennistiquer":        "CONFIANCE DU JOUR",
    "TEMPÊTE BETTING ®️":  None,
    "France Pronos Live":  None,
    "Auxo1XBOT":           None,
}


def filter_txt(txt):
    try:
        with open(os.path.join(project_directory, "conf/excluded_words.txt"), "r") as f:
            words = [w.strip().upper() for w in f.read().split('\n')]
        for word in words:
            txt = txt.replace(word, "")
    except Exception:
        pass
    return txt


def extract_code_1XBET(txt):
    txt = filter_txt(txt)
    codes = re.findall(r"\b[A-Z0-9]{5}\b", txt)
    return codes if len(codes) == 1 else False


try:
    client = TelegramClient(
        os.path.join(project_directory, '2'),
        api_id, api_hash,
        connection_retries=5, retry_delay=1, timeout=30,
        request_retries=5, auto_reconnect=True,
        device_model="Desktop", system_version="Windows 10",
        app_version="1.0", lang_code="fr", system_lang_code="fr",
    )
    log("Client Telegram initialisé", "success", clear=False)
except Exception as e:
    log(f"Erreur init Telegram: {e}", "error", clear=False)
    client = TelegramClient(os.path.join(project_directory, '2'), api_id, api_hash)


@client.on(events.NewMessage())
async def my_event_handler(event):
    sender = await event.get_sender()
    txt = event.raw_text

    # Filtre phrases ignorées
    try:
        with open(os.path.join(project_directory, "conf/ignored_messages.txt"), "r", encoding='utf-8') as f:
            ignored_phrases = [l.strip().lower() for l in f.read().split('\n') if l.strip() and not l.strip().startswith('#')]
        if any(p in txt.lower() for p in ignored_phrases):
            return
    except FileNotFoundError:
        pass

    if not (sender or event.chat_id):
        return

    if is_ignored_sender(sender.username if sender else None, event.chat_id):
        return

    chat_title = event.chat.title if event.chat and hasattr(event.chat, "title") else ""
    has_media = event.message.media is not None

    log(f"[Telegram] {chat_title or getattr(sender, 'username', event.chat_id)}: {txt[:80]}", "info", clear=False)

    # AdrBetting
    if chat_title == 'AdrBetting VIP':
        if "PRONOS EN LIGNE" not in txt.upper():
            return
        log("[AdrBetting] Lancement scraping...", "info", clear=False)
        def _run():
            try:
                coupons = scrape_adrbetting_coupons()
                if not coupons:
                    return
                for img_path, tipster in coupons:
                    try:
                        result = extraire_pari_depuis_image(img_path, txt)
                        pari_dict = json.loads(result)
                        pari_dict["tipster"] = tipster
                        matches = pari_dict.get("matches", [])
                        if matches:
                            send_bet_data_to_api(pari_dict, message_original=txt, sender_username=tipster)
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    except Exception as e:
                        log(f"[AdrBetting] Erreur OCR: {e}", "error", clear=False)
            except Exception as e:
                log(f"[AdrBetting] Erreur scraping: {e}", "error", clear=False)
        threading.Thread(target=_run, daemon=True).start()
        return

    # FrancePronos
    if chat_title == 'France Pronos':
        if "www.france-pronos.com/?source=telegram" not in txt.lower():
            return
        log("[FrancePronos] Lancement scraping...", "info", clear=False)
        def _run_fp():
            try:
                pronos = scrape_francepronos()
                for raw in (pronos or []):
                    try:
                        texte = (
                            f"Sport: {raw.get('sport','')}\nDate: {raw.get('date','')}\n"
                            f"Match: {raw.get('intitule', raw.get('equipe_1','') + ' vs ' + raw.get('equipe_2',''))}\n"
                            f"Équipe 1: {raw.get('equipe_1','')}\nÉquipe 2: {raw.get('equipe_2','')}\n"
                            f"Sélection: {raw.get('selection','')}\nCote: {raw.get('odds','')}\nTipster: FrancePronos"
                        )
                        result = extraire_pari_depuis_texte(texte, txt)
                        pari_dict = json.loads(result)
                        pari_dict["tipster"] = "FrancePronos"
                        matches = pari_dict.get("matches", [])
                        if matches:
                            send_bet_data_to_api(pari_dict, message_original=txt, sender_username="FrancePronos")
                    except Exception as e:
                        log(f"[FrancePronos] Erreur: {e}", "error", clear=False)
            except Exception as e:
                log(f"[FrancePronos] Erreur scraping: {e}", "error", clear=False)
        threading.Thread(target=_run_fp, daemon=True).start()
        return

    # Images (OCR → API)
    if has_media:
        required_text = IMAGE_CHANNELS.get(chat_title, "NOT_ALLOWED")
        if required_text == "NOT_ALLOWED":
            return
        if required_text is not None and required_text.upper() not in txt.upper():
            return
        from telethon.tl.types import MessageMediaDocument
        if isinstance(event.message.media, MessageMediaDocument):
            doc = event.message.media.document
            if any(str(type(attr).__name__) == 'DocumentAttributeAnimated' for attr in (doc.attributes or [])):
                return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(project_directory, 'SCRIPTS WATCH', 'media')
        os.makedirs(temp_dir, exist_ok=True)
        image_path = os.path.join(temp_dir, f"media_{timestamp}.jpg")
        await event.message.download_media(file=image_path)
        try:
            result = extraire_pari_depuis_image(image_path, txt)
            pari_dict = json.loads(result)
            pari_dict["tipster"] = chat_title
            matches = pari_dict.get("matches", [])
            if matches:
                send_bet_data_to_api(pari_dict, message_original=txt, sender_username=chat_title)
        except Exception as e:
            log(f"[Image] [{chat_title}] Erreur OCR: {e}", "error", clear=False)
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)


# ─── Démarrage ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    log("=== watch_server.py démarré ===", "success", clear=False)

    # Thread Tempête
    tempeteThread = threading.Thread(target=check_tempete_images, daemon=True)
    tempeteThread.start()

    # Client Telegram
    for attempt in range(5):
        try:
            client.start()
            break
        except Exception as e:
            if "database is locked" in str(e).lower() and attempt < 4:
                log(f"Session SQLite verrouillée, attente... ({attempt+1}/5)", "warning", clear=False)
                time.sleep(3)
            else:
                raise

    log("Client Telegram démarré, écoute des messages...", "success", clear=False)
    client.run_until_disconnected()
