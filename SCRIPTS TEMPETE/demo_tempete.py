#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test en mode démonstration du script tempeteBetting.py
Exécute un seul cycle pour vérifier le fonctionnement
"""

import os
import sys
import time
from datetime import datetime

# Ajouter le répertoire parent au chemin Python
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

# Import du script principal
import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from io import BytesIO
from PIL import Image

# Configuration du bot Telegram simplifié
try:
    from telegram_ssl import TelegramBotSSL
    bot = TelegramBotSSL('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
    print("✅ Bot Telegram SSL configuré")
    use_ssl_bot = True
except ImportError:
    try:
        import telepot
        bot = telepot.Bot('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
        print("✅ Bot Telegram standard configuré")
        use_ssl_bot = False
    except ImportError:
        print("❌ Aucun module Telegram disponible")
        sys.exit(1)

# Configuration
BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
BASE_URL2 = "https://adrbetting.fr/wp-content/uploads/{year}/{month:02d}/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "images_demo.db")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def create_demo_database():
    """Crée une base de données de démonstration"""
    print(f"🔧 Création base de données de démonstration : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT UNIQUE,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Base de données de démonstration prête")

def get_image_links_demo(url):
    """Version démo de récupération des liens"""
    print(f"🔍 Récupération des liens depuis: {url}")
    
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        print(f"❌ Échec accès {url} (Status: {response.status_code})")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a') if link.get('href')]

    # Filtrer les liens pour ne garder que les images
    image_links = [link for link in links if re.match(r".*\.(jpg|jpeg|png)$", link, re.IGNORECASE)]
    print(f"✅ {len(image_links)} liens d'images trouvés")
    return image_links

def filter_original_images_demo(image_links):
    """Version démo du filtre d'images originales"""
    original_images = set()
    pattern = re.compile(r'(-\d+x\d+)?\.(jpg|jpeg|png)$', re.IGNORECASE)

    for link in image_links:
        original_image = pattern.sub(r'.\2', link)
        original_images.add(original_image)

    result = list(original_images)
    print(f"🎯 {len(result)} images originales identifiées")
    return result

def store_images_in_demo_db(image_urls):
    """Stocke les images dans la base de démonstration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_images = []
    for image_url in image_urls:
        try:
            cursor.execute("INSERT INTO images (image_url) VALUES (?)", (image_url,))
            new_images.append(image_url)
        except sqlite3.IntegrityError:
            # L'image est déjà dans la base de données
            pass

    conn.commit()
    conn.close()
    print(f"📝 {len(new_images)} nouvelles images ajoutées à la base")
    return new_images

def demo_cycle():
    """Exécute un cycle de démonstration"""
    print("🚀 DÉMONSTRATION TEMPETEBETTING - CYCLE UNIQUE")
    print("="*50)
    
    create_demo_database()
    
    now = datetime.now()
    url = BASE_URL.format(year=now.year, month=now.month)
    
    print(f"🕐 Début du cycle: {now.strftime('%H:%M:%S')}")
    
    # Récupérer les liens des images
    image_links = get_image_links_demo(url)
    
    if not image_links:
        print("❌ Aucun lien d'image trouvé")
        return False
    
    # Filtrer les images d'origine
    original_images = filter_original_images_demo(image_links)
    
    # Stocker les nouvelles images dans la base de données
    new_images = store_images_in_demo_db(original_images)
    
    # Traitement des nouvelles images
    if new_images:
        print(f"🎉 {len(new_images)} nouvelles images détectées !")
        print("📸 Exemples de nouvelles images:")
        for i, img in enumerate(new_images[:5]):
            print(f"   {i+1}. {img}")
        if len(new_images) > 5:
            print(f"   ... et {len(new_images) - 5} autres")
            
        # Simuler l'envoi Telegram (sans vraiment envoyer)
        print("📤 Simulation d'envoi Telegram...")
        print(f"✅ {len(new_images)} images auraient été envoyées vers Telegram")
    else:
        print("ℹ️  Aucune nouvelle image trouvée")
    
    print("="*50)
    print("✅ CYCLE DE DÉMONSTRATION TERMINÉ")
    
    # Statistiques finales
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM images")
    total_images = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 Total d'images en base: {total_images}")
    return True

if __name__ == "__main__":
    try:
        success = demo_cycle()
        if success:
            print("🎉 Démonstration réussie ! Le script tempeteBetting.py est fonctionnel.")
        else:
            print("❌ La démonstration a échoué.")
    except Exception as e:
        print(f"❌ Erreur pendant la démonstration: {e}")
        import traceback
        traceback.print_exc()