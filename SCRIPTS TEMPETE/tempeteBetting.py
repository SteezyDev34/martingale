import subprocess


# Vérification et installation automatique des dépendances
def auto_install_requirements():
    try:
        import cv2
    except ImportError as e:
        print(f"⚠️ Dépendance manquante : {e}. Installation automatique...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("✅ Dépendances installées. Relance du script...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as err:
            print(f"❌ Échec de l'installation automatique des dépendances : {err}")
            sys.exit(1)


auto_install_requirements()
import os
import sys

# Ajouter le répertoire parent au chemin Python
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

from Functions.getTextFromImageGPT import extraire_pari_depuis_image

# Vérification et installation des dépendances au démarrage
try:
    from dependency_manager import check_and_install_dependencies

    print("🔧 Vérification des dépendances...")
    if not check_and_install_dependencies(auto_install=True):
        print("❌ Erreur lors de l'installation des dépendances. Arrêt du programme.")
        sys.exit(1)
    print("✅ Toutes les dépendances sont prêtes!\n")

except ImportError as e:
    print(f"⚠️  Module dependency_manager non trouvé: {e}")
    print("Le programme va continuer sans vérification automatique des dépendances.")

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
    import telepot
    import pytesseract
    from ImageTreatment import getTextFromImage
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Veuillez installer les dépendances manquantes avec:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Correction des problèmes SSL pour Telegram
try:
    from ssl_fix import create_telegram_bot_with_ssl_fix, diagnose_ssl_issues

    print("🔒 Vérification et correction SSL...")
    ssl_ok = diagnose_ssl_issues()

    if not ssl_ok:
        print("🛠️  Application des corrections SSL...")
        create_telegram_bot_with_ssl_fix()

except ImportError:
    print("⚠️  Module ssl_fix non trouvé, continuons sans correction SSL automatique...")

# Configuration du bot Telegram avec gestion SSL améliorée
try:
    from telegram_ssl import TelegramBotSSL

    bot = TelegramBotSSL('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
    print("✅ Bot Telegram SSL configuré")
    use_ssl_bot = True
except ImportError:
    print("⚠️  Module telegram_ssl non trouvé, utilisation de telepot standard")
    import telepot

    bot = telepot.Bot('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
    use_ssl_bot = False

freeGroup = "-1001315247334"
# En-têtes pour contourner le blocage 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}


def send_telegram(freeGroup, message, retry_count=3):
    """Envoie un message Telegram avec gestion d'erreurs SSL améliorée"""
    global bot, use_ssl_bot

    for attempt in range(retry_count):
        try:
            if use_ssl_bot:
                # Utilisation du bot SSL personnalisé
                result = bot.send_message(freeGroup, message)
                if result:
                    return True
            else:
                # Utilisation de telepot standard
                bot.sendMessage(freeGroup, message)
                return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Tentative {attempt + 1}/{retry_count} échouée: {error_msg}")

            # Gestion des erreurs spécifiques
            if ("SSL" in error_msg or "certificate" in error_msg) and not use_ssl_bot:
                print("🔒 Erreur SSL détectée, basculement vers bot SSL personnalisé...")
                try:
                    from telegram_ssl import TelegramBotSSL
                    bot = TelegramBotSSL('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
                    use_ssl_bot = True
                    print("✅ Basculement vers bot SSL réussi")
                    continue  # Retry avec le nouveau bot
                except ImportError as ie:
                    print(f"⚠️  Impossible d'importer le bot SSL: {ie}")

            elif "429" in error_msg or "Too Many Requests" in error_msg:
                # Gestion spéciale pour l'erreur 429
                wait_time = 10 * (attempt + 1)  # Attente progressive plus longue
                print(f"⏳ Rate limit atteint - Attente de {wait_time}s...")
                time.sleep(wait_time)
                continue  # Retry sans compter comme échec

            # Pause avant retry pour autres erreurs
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Backoff exponentiel

    print(f"❌ Échec définitif de l'envoi après {retry_count} tentatives")
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
    now = datetime.now()
    url = BASE_URL.format(year=now.year, month=now.month)
    for i, image_url in enumerate(images):
        # Délai entre les images pour éviter le rate limit
        if i > 0:
            print(f"⏳ Attente de 3 secondes avant traitement de l'image suivante...")
            time.sleep(3)

        response = requests.get(url + image_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Save image locally
            with open('images.jpg', 'wb') as f:
                f.write(response.content)

            # Import and use ImageTreatment function avec gestion d'erreur
            try:
                print(f"🔍 Extraction du texte pour l'image {i + 1}/{len(images)}...")
                text = extraire_pari_depuis_image('images.jpg', '')
                print("✅ Texte extrait avec succès")
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    print("⚠️  Rate limit OpenAI atteint, attente de 70 secondes...")
                    time.sleep(70)  # Attendre plus d'une minute pour réinitialiser la limite
                    try:
                        text = extraire_pari_depuis_image('images.jpg', '')
                        print("✅ Texte extrait après attente")
                    except Exception as retry_e:
                        print(f"❌ Erreur persistante: {retry_e}")
                        text = "Erreur d'extraction du texte (rate limit)"
                else:
                    print(f"❌ Erreur d'extraction: {e}")
                    text = "Erreur d'extraction du texte"

            # Extract text from image
            print("Texte extrait :")
            print(text)

            try:
                # Combiner URL et texte en un seul message pour réduire le taux d'envoi
                combined_message = f"🖼️ Nouvelle image:\n{url + image_url}\n\n📝 Texte extrait:\n{text}"

                # Découper le message si trop long (limite Telegram: 4096 caractères)
                if len(combined_message) > 4000:
                    send_telegram(freeGroup, f"🖼️ Nouvelle image:\n{url + image_url}")
                    time.sleep(2)  # Délai entre messages Telegram
                    send_telegram(freeGroup, f"📝 Texte extrait:\n{text}")
                else:
                    send_telegram(freeGroup, combined_message)

                print(f"✅ Message envoyé pour: {image_url}")
                time.sleep(2)  # Délai après envoi pour éviter spam Telegram
            except Exception as e:
                print(f"❌ Échec envoi pour {image_url} - {str(e)}")


def send_images_via_telegram2(images):
    now = datetime.now()
    url = BASE_URL2.format(year=now.year, month=now.month)
    for i, image_url in enumerate(images):
        # Délai entre les images pour éviter le rate limit
        if i > 0:
            print(f"⏳ Attente de 3 secondes avant traitement de l'image suivante...")
            time.sleep(3)

        response = requests.get(url + image_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:

            img = Image.open(BytesIO(response.content))
            custom_config = r'--psm 6 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

            # Extraction avec gestion d'erreur pour rate limit
            try:
                print(f"🔍 Extraction du texte pour l'image ADR {i + 1}/{len(images)}...")
                text = extraire_pari_depuis_image(img, '')
                print("✅ Texte extrait avec succès")
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    print("⚠️  Rate limit OpenAI atteint, attente de 70 secondes...")
                    time.sleep(70)  # Attendre plus d'une minute pour réinitialiser la limite
                    try:
                        text = extraire_pari_depuis_image(img, '')
                        print("✅ Texte extrait après attente")
                    except Exception as retry_e:
                        print(f"❌ Erreur persistante: {retry_e}")
                        text = "Erreur d'extraction du texte (rate limit)"
                else:
                    print(f"❌ Erreur d'extraction: {e}")
                    text = "Erreur d'extraction du texte"

            # Extraire le texte de l'image
            print("Texte extrait :")
            print(text)

        try:
            # Combiner URL et texte en un seul message pour réduire le taux d'envoi
            combined_message = f"🖼️ Nouvelle image (ADR):\n{url + image_url}\n\n📝 Texte extrait:\n{text}"

            # Découper le message si trop long (limite Telegram: 4096 caractères)
            if len(combined_message) > 4000:
                send_telegram(freeGroup, f"🖼️ Nouvelle image (ADR):\n{url + image_url}")
                time.sleep(2)  # Délai entre messages Telegram
                send_telegram(freeGroup, f"📝 Texte extrait:\n{text}")
            else:
                send_telegram(freeGroup, combined_message)

            print(f"✅ Message ADR envoyé pour: {image_url}")
            time.sleep(2)  # Délai après envoi pour éviter spam Telegram
        except Exception as e:
            print(f"❌ Échec envoi ADR pour {image_url} - {str(e)}")


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
            time.sleep(600)  # Attendre 10 minutes avant la prochaine vérification
        except Exception as e:
            print(e)
