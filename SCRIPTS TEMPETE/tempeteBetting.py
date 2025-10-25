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
try:
    import requests
    from bs4 import BeautifulSoup
    import sqlite3
    import re
    from io import BytesIO
    import time
    from datetime import datetime
    from PIL import Image
    from Functions.getTextFromImageGPT import extraire_pari_depuis_image
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Installation automatique...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "pillow"])
        print("✅ Dépendances installées, veuillez relancer le script")
    except Exception as install_error:
        print(f"❌ Échec de l'installation: {install_error}")
    sys.exit(1)

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

freeGroup = "-1001315247334"

# En-têtes pour contourner le blocage 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def send_telegram(chat_id, message, retry_count=3):
    """Envoie un message Telegram avec gestion d'erreurs optimisée"""
    for attempt in range(retry_count):
        try:
            if use_ssl_bot:
                result = bot.send_message(chat_id, message)
                if result:
                    return True
            else:
                bot.sendMessage(chat_id, message)
                return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Tentative {attempt + 1}/{retry_count} - {error_msg}")

            # Gestion du rate limit
            if "429" in error_msg or "Too Many Requests" in error_msg:
                wait_time = 10 * (attempt + 1)
                print(f"⏳ Rate limit - Attente de {wait_time}s...")
                time.sleep(wait_time)
                continue

            # Pause avant retry
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)

    print(f"❌ Échec définitif après {retry_count} tentatives")
    return False


# Paramètres de configuration
BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
BASE_URL2 = "https://adrbetting.fr/wp-content/uploads/{year}/{month:02d}/"
DB_PATH = "images.db"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def create_database():
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
            with open('images.jpg', 'wb') as f:
                f.write(response.content)

            # Extraction du texte avec gestion du rate limit
            text = extract_text_with_retry('images.jpg', i, len(images))

            # Envoi combiné pour réduire le nombre de messages
            combined_message = f"🖼️ Nouvelle image:\n{url + image_url}\n\n📝 Texte:\n{text}"

            if len(combined_message) > 4000:
                send_telegram(freeGroup, f"🖼️ Nouvelle image:\n{url + image_url}")
                time.sleep(2)
                send_telegram(freeGroup, f"📝 Texte:\n{text}")
            else:
                send_telegram(freeGroup, combined_message)

            print(f"✅ Image {i + 1}/{len(images)} envoyée")
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
            print(f"🔍 Extraction texte {label} [{index + 1}/{total}]...")
            text = extraire_pari_depuis_image(image_source, '')
            print("✅ Texte extrait")
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
        print(f"Found {len(new_images)} new images.")
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
            time.sleep(60)  # Attendre 10 minutes avant la prochaine vérification
        except Exception as e:
            print(e)
