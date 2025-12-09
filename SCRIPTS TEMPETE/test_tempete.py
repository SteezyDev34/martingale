#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour tempeteBetting.py
Teste toutes les fonctionnalités principales
"""

import os
import sys
import requests
import sqlite3
from datetime import datetime

# Ajouter le répertoire parent au chemin Python
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

# Configuration
BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
BASE_URL2 = "https://adrbetting.fr/wp-content/uploads/{year}/{month:02d}/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "images.db")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def test_database_creation():
    """Test de création de la base de données"""
    print("🧪 Test 1: Création de la base de données")
    try:
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
        
        # Test d'insertion
        cursor.execute("INSERT OR IGNORE INTO images (image_url) VALUES (?)", ("test_image.jpg",))
        conn.commit()
        
        # Vérifier l'insertion
        cursor.execute("SELECT COUNT(*) FROM images")
        count = cursor.fetchone()[0]
        
        conn.close()
        print(f"✅ Base de données créée, {count} images en base")
        return True
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def test_website_access():
    """Test d'accès aux sites web"""
    print("🧪 Test 2: Accès aux sites web")
    
    now = datetime.now()
    
    # Test TempeteBetting
    try:
        url1 = BASE_URL.format(year=now.year, month=now.month)
        response1 = requests.get(url1, headers=HEADERS, timeout=10)
        print(f"✅ TempeteBetting accessible (Status: {response1.status_code})")
        print(f"   URL: {url1}")
        tempete_ok = True
    except Exception as e:
        print(f"❌ TempeteBetting inaccessible: {e}")
        tempete_ok = False
    
    # Test ADRBetting
    try:
        url2 = BASE_URL2.format(year=now.year, month=now.month)
        response2 = requests.get(url2, headers=HEADERS, timeout=10)
        print(f"✅ ADRBetting accessible (Status: {response2.status_code})")
        print(f"   URL: {url2}")
        adr_ok = True
    except Exception as e:
        print(f"❌ ADRBetting inaccessible: {e}")
        adr_ok = False
    
    return tempete_ok and adr_ok

def test_telegram_bot():
    """Test du bot Telegram"""
    print("🧪 Test 3: Configuration Bot Telegram")
    
    try:
        # Test SSL bot
        try:
            from telegram_ssl import TelegramBotSSL
            bot = TelegramBotSSL('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
            print("✅ Bot Telegram SSL configuré")
            ssl_ok = True
        except ImportError:
            ssl_ok = False
        
        # Test bot standard
        if not ssl_ok:
            try:
                import telepot
                bot = telepot.Bot('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
                print("✅ Bot Telegram standard configuré")
                standard_ok = True
            except ImportError:
                print("❌ Aucun module Telegram disponible")
                standard_ok = False
        else:
            standard_ok = True
            
        return ssl_ok or standard_ok
        
    except Exception as e:
        print(f"❌ Erreur configuration Telegram: {e}")
        return False

def test_image_processing_import():
    """Test des imports pour le traitement d'images"""
    print("🧪 Test 4: Imports traitement d'images")
    
    try:
        from Functions.getTextFromImageGPT import extraire_pari_depuis_image
        print("✅ Module OpenAI importé")
        openai_ok = True
    except Exception as e:
        print(f"❌ Erreur import OpenAI: {e}")
        openai_ok = False
    
    try:
        from PIL import Image
        from io import BytesIO
        print("✅ Modules PIL importés")
        pil_ok = True
    except Exception as e:
        print(f"❌ Erreur import PIL: {e}")
        pil_ok = False
    
    return openai_ok and pil_ok

def test_image_scraping():
    """Test de récupération d'images"""
    print("🧪 Test 5: Récupération des liens d'images")
    
    try:
        from bs4 import BeautifulSoup
        import re
        
        now = datetime.now()
        url = BASE_URL.format(year=now.year, month=now.month)
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ Impossible d'accéder à {url}")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a') if link.get('href')]
        
        # Filtrer les images
        image_links = [link for link in links if re.match(r".*\.(jpg|jpeg|png)$", link, re.IGNORECASE)]
        
        print(f"✅ {len(image_links)} liens d'images trouvés")
        
        # Afficher quelques exemples
        for i, link in enumerate(image_links[:3]):
            print(f"   - {link}")
        if len(image_links) > 3:
            print(f"   ... et {len(image_links) - 3} autres")
            
        return len(image_links) > 0
        
    except Exception as e:
        print(f"❌ Erreur récupération images: {e}")
        return False

def run_all_tests():
    """Lance tous les tests"""
    print("🚀 Démarrage des tests TempeteBetting\n")
    
    tests_results = []
    
    # Test 1: Base de données
    tests_results.append(test_database_creation())
    print()
    
    # Test 2: Accès sites web
    tests_results.append(test_website_access())
    print()
    
    # Test 3: Bot Telegram
    tests_results.append(test_telegram_bot())
    print()
    
    # Test 4: Traitement d'images
    tests_results.append(test_image_processing_import())
    print()
    
    # Test 5: Récupération d'images
    tests_results.append(test_image_scraping())
    print()
    
    # Résumé
    print("="*50)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*50)
    
    passed = sum(tests_results)
    total = len(tests_results)
    
    test_names = [
        "Base de données",
        "Accès sites web", 
        "Bot Telegram",
        "Traitement d'images",
        "Récupération d'images"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, tests_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le script est prêt.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)