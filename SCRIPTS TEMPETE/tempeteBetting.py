import os
import sys

# Ajouter le répertoire parent au chemin Python
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
    # Simple écriture de lignes vides pour PyCharm

    # Vérification de l'environnement
    import VenvDependencyManager

    VenvDependencyManager.main()
# Imports des modules requis

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from io import BytesIO
import time
from datetime import datetime
from PIL import Image
from Functions.getTextFromImageGPT import extraire_pari_depuis_image, extraire_pari_joueur_nba_depuis_image

# Configuration SSL pour éviter les erreurs de certificat
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Configuration du bot Telegram simplifié (comme Functions_telegram.py)
BOT_TOKEN = '1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc'
# Utiliser auxo_bot_id pour l'envoi direct au bot
freeGroup = "820171667"  # auxo_bot - Testé et fonctionne ✅

# Créer une session requests sans vérification SSL
session = requests.Session()
session.verify = False

print("✅ Bot Telegram configuré (requests direct)", flush=True)

# En-têtes pour contourner le blocage 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def send_telegram(chat_id, message, retry_count=3):
    """Envoie un message Telegram via requests (comme Functions_telegram.py)"""
    try:
        # Limiter la longueur du message
        if len(message) > 4096:
            message = message[:4090] + "\n..."
        
        # Utiliser requests directement avec notre session SSL configurée
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message
        }
        
        for attempt in range(retry_count):
            try:
                response = session.post(url, data=data, verify=False, timeout=10)
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:
                    # Rate limit
                    wait_time = 10 * (attempt + 1)
                    print(f"⏳ Rate limit - Attente de {wait_time}s...", flush=True)
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Erreur HTTP {response.status_code}: {response.text[:200]}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur réseau tentative {attempt + 1}/{retry_count}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        return False


# Paramètres de configuration
BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
BASE_URL2 = "https://adrbetting.fr/wp-content/uploads/{year}/{month:02d}/"

# Chemin absolu vers la base de données dans le dossier du script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "images.db")

print(f"📁 Chemin de la base de données : {DB_PATH}", flush=True)

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def create_database():
    """Crée la base de données SQLite pour stocker les URLs des images"""
    print(f"🔧 Création/vérification de la base : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS images
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       image_url
                       TEXT
                       UNIQUE,
                       added_at
                       DATETIME
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    conn.commit()
    conn.close()
    print(f"✅ Base de données prête", flush=True)


def get_image_links(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to access {url} {response}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a') if link.get('href')]

    # Filtrer les liens pour ne garder que les images
    image_links = [link for link in links if re.match(r".*\.(jpg|jpeg|png)$", link, re.IGNORECASE)]
    return image_links


def filter_original_images(image_links):
    # Identifie les images originales (sans taille à la fin)
    original_images = set()
    pattern = re.compile(r'(-\d+x\d+)?\.(jpg|jpeg|png)$', re.IGNORECASE)

    for link in image_links:
        # Enlève le suffixe de taille pour identifier l'image d'origine
        original_image = pattern.sub(r'.\2', link)
        original_images.add(original_image)

    return list(original_images)


def store_images_in_db(image_urls):
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
    return new_images


def send_images_via_telegram(images):
    """Traite et envoie les images de tempetebetting.com"""
    now = datetime.now()
    url = BASE_URL.format(year=now.year, month=now.month)

    for i, image_url in enumerate(images):
        if i > 0:
            time.sleep(3)  # Délai entre images

        try:
            response = requests.get(url + image_url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"❌ Impossible de télécharger: {image_url}")
                continue

            # Sauvegarder l'image localement
            with open(image_url, 'wb') as f:
                f.write(response.content)
            
            # Envoyer l'image locale à Telegram
            try:
                telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(image_url, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': freeGroup}
                    photo_response = session.post(telegram_url, data=data, files=files, verify=False, timeout=30)
                    
                    if photo_response.status_code == 200:
                        print(f"📸 Image envoyée à Telegram", flush=True)
                    else:
                        print(f"⚠️ Erreur envoi image: {photo_response.status_code}", flush=True)
                        # Envoi de l'URL en fallback si l'upload échoue
                        send_telegram(freeGroup, url + image_url)
                        
            except Exception as img_error:
                print(f"❌ Erreur upload image: {img_error}", flush=True)
                # Envoi de l'URL en fallback
                send_telegram(freeGroup, url + image_url)
            
            time.sleep(2)

            # Extraction du texte avec gestion du rate limit
            text = extract_text_with_retry('images.jpg', i, len(images))
            
            # Vérifier que le texte est valide
            if not text or text.strip() == "":
                text = "❌ Impossible d'extraire le texte de cette image"
            
            # Nettoyer le texte extrait
            text = text.strip()
            
            # Limiter la longueur du texte
            if len(text) > 3500:
                text = text[:3500] + "\n... (texte tronqué)"
            send_telegram(freeGroup, text)


            print(f"✅ Image {i + 1}/{len(images)} envoyée", flush=True)
            time.sleep(2)

        except Exception as e:
            print(f"❌ Erreur pour {image_url}: {e}")


def send_images_via_telegram2(images):
    """Traite et envoie les images de adrbetting.fr"""
    now = datetime.now()
    url = BASE_URL2.format(year=now.year, month=now.month)

    for i, image_url in enumerate(images):
        if i > 0:
            time.sleep(3)

        try:
            response = requests.get(url + image_url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"❌ Impossible de télécharger: {image_url}")
                continue

            img = Image.open(BytesIO(response.content))

            # Extraction du texte avec gestion du rate limit
            text = extract_text_with_retry(img, i, len(images), is_adr=True)

            # Envoi combiné
            combined_message = f"🖼️ Nouvelle image (ADR):\n{url + image_url}\n\n📝 Texte:\n{text}"

            if len(combined_message) > 4000:
                send_telegram(freeGroup, f"🖼️ Nouvelle image (ADR):\n{url + image_url}")
                time.sleep(2)
                send_telegram(freeGroup, f"📝 Texte:\n{text}")
            else:
                send_telegram(freeGroup, combined_message)

            print(f"✅ Image ADR {i + 1}/{len(images)} envoyée")
            time.sleep(2)

        except Exception as e:
            print(f"❌ Erreur pour {image_url}: {e}")


def extract_text_with_retry(image_source, index, total, is_adr=False, max_retries=2):
    """Extrait le texte d'une image avec gestion du rate limit OpenAI"""
    label = "ADR" if is_adr else "Tempete"

    for attempt in range(max_retries):
        try:
            print(f"🔍 Extraction texte {label} [{index + 1}/{total}]...", flush=True)
            
            # Utiliser la fonction spécialisée NBA pour Tempete
            if not is_adr:
                text = extraire_pari_joueur_nba_depuis_image(image_source, '')
            else:
                text = extraire_pari_depuis_image(image_source, '')
                
            print("✅ Texte extrait", flush=True)
            return text

        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                if attempt < max_retries - 1:
                    print("⚠️  Rate limit OpenAI - Attente de 70s...")
                    time.sleep(70)
                else:
                    print("❌ Rate limit persistant")
                    return "Erreur: Rate limit OpenAI dépassé"
            else:
                print(f"❌ Erreur extraction: {e}")
                return f"Erreur d'extraction: {str(e)[:100]}"

    return "Erreur: Échec extraction après plusieurs tentatives"


def main():
    create_database()
    now = datetime.now()
    url = BASE_URL.format(year=now.year, month=now.month)

    # Récupérer les liens des images
    image_links = get_image_links(url)

    # Filtrer les images d'origine
    original_images = filter_original_images(image_links)

    # Stocker les nouvelles images dans la base de données et récupérer celles qui sont nouvelles
    new_images = store_images_in_db(original_images)

    # Envoyer les nouvelles images via Telegram
    if new_images:
        print(f"Found {len(new_images)} new images.", flush=True)
        send_images_via_telegram(new_images)
    else:
        print("No new images found.")
        # Récupérer les liens des images


if __name__ == "__main__":
    # Exécution toutes les 10 minutes pour vérifier les nouvelles images
    while True:
        try:
            main()
            now = datetime.now()
            print(now)
            time.sleep(600)  # Attendre 10 minutes avant la prochaine vérification
        except Exception as e:
            print(e)
