import base64
import os
import sys
import time

# Ajouter le chemin du projet au PYTHONPATH pour permettre l'importation de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import config


def cleanJson(raw_response):
    cleaned_response = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
    return cleaned_response


# Initialisation du client OpenAI avec la clé API
from openai import OpenAI

# Charger la clé API depuis les variables d'environnement
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("La clé API OpenAI n'est pas définie. Veuillez définir la variable d'environnement OPENAI_API_KEY.")

# Initialiser le client OpenAI
client = OpenAI(api_key=api_key)


# 🖼️ Charger l'image et la convertir en base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def stringify_xbet_type_list(xbet_type_list):
    """
    Convertit la liste des types de paris en chaîne de caractères formatée.
    
    Args:
        xbet_type_list (dict): Dictionnaire où chaque clé est une catégorie 
                              et chaque valeur est une liste de types de paris
    
    Returns:
        str: Chaîne formatée avec les catégories et types de paris
    """
    lines = []
    for categorie, types_list in xbet_type_list.items():
        # types_list est maintenant une liste de types de paris, pas un dictionnaire
        for type_pari in types_list:
            lines.append(
                f"Catégorie: {categorie} | Type: {type_pari}"
            )
    return "\n".join(lines)

# 🧾 Envoyer l'image à ChatGPT avec des instructions spécifiques
def extraire_pari_depuis_image(image_path, msg):
    print("Tu es un agent OCR intelligent. Ton rôle est de lire des captures d'écran de tickets de paris sportifs"
                                "et d'en extraire les données principales sous forme de JSON structuré."
                                "Les données à extraire sont les suivantes :\n"
                                "- equipe_1 : première équipe (ou joueur)\n"
                                "- equipe_2 : deuxième équipe (ou joueur)\n"
                                "- categorie : catégorie du pari\n"
                                "- type_de_pari : type de pari (doit être EXACTEMENT présent dans la liste ci-dessous)\n"
                                "- selection : la sélection faite (peut être générée dynamiquement si elle suit un format connu)\n"
                                "- odds : la cote du pari (nombre flottant)\n"
                                "- date : date du pari (extrait du nom de l'image, ou sinon date du jour)\n"
                                "- tipster : toujours \"marco\"\n\n"

                                "⚠️ Règles strictes à suivre :\n"
                                "1. Tu dois OBLIGATOIREMENT choisir la catégorie et le type de pari parmi ceux du dictionnaire ci-dessous.\n"
                                "2. Tu peux générer dynamiquement la sélection si elle respecte le même format qu'une sélection d'exemple.\n"
                                "3. Tu ne dois jamais inventer un type de pari ou une catégorie.\n"
                                "4. Si le texte 'générateur de paris' apparaît dans l’image, retourne une erreur avec le texte brut de l’image.\n"
                                "5. Tu dois ignorer les textes superflus et te concentrer uniquement sur les données mentionnées ci-dessus.\n\n"

                                "🧠 Exemples de correspondance dynamique :\n"
                                "- Texte image : 'Total 1: (0.5) Plus de' → type_de_pari : 'Total 1', selection : 'Total Individuel 1 Plus de 0.5'\n"
                                "- Texte image : 'Total 2: (1.5) Moins de' → type_de_pari : 'Total 2', selection : 'Total Individuel 2 Moins de 1.5'\n"
                                "- Texte image : 'Handicap 1 (-2)' → type_de_pari : 'Handicap', selection : 'Handicap 1 (-2)'\n\n"

                                "📆 Gestion de la date :\n"
                                "- Si le nom du fichier contient une date comme 'media_20250413_204440.jpg', la date du pari est 13/04/2025.\n"
                                "- Si le nom du fichier est 'Capture-decran_1-4-2025_205148.jpeg', la date est 01/04/2025.\n"
                                "- Si aucun format de date n'est détecté dans le nom de fichier, utilise la date du jour.\n\n"

                                "📖 Voici la liste de référence des catégories, types et formats de sélections :\n"
                                f"{stringify_xbet_type_list(config.xbet_type_list)}\n\n"

                                "🧾 Format de réponse attendu (aucune explication, juste le JSON brut) :\n"
                                "{\n"
                                "  \"date\": \"25/09/2025\",\n"
                                "  \"equipe_1\": \"Al Shabab Riyadh\",\n"
                                "  \"equipe_2\": \"Al Kholood\",\n"
                                "  \"categorie\": \"Temps réglementaire\",\n"
                                "  \"type_de_pari\": \"Total 1\",\n"
                                "  \"selection\": \"Total Individuel 1 Plus de 0.5\",\n"
                                "  \"odds\": \"1.432\",\n"
                                "  \"tipster\": \"marco\"\n"
                                "}")
    image_b64 = image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": 
                                "Tu es un agent OCR intelligent. Ton rôle est de lire des captures d'écran de tickets de paris sportifs"
                                "et d'en extraire les données principales sous forme de JSON structuré."
                                "Les données à extraire sont les suivantes :\n"
                                "- equipe_1 : première équipe (ou joueur)\n"
                                "- equipe_2 : deuxième équipe (ou joueur)\n"
                                "- categorie : catégorie du pari\n"
                                "- type_de_pari : type de pari (doit être EXACTEMENT présent dans la liste ci-dessous)\n"
                                "- selection : la sélection faite (peut être générée dynamiquement si elle suit un format connu)\n"
                                "- odds : la cote du pari (nombre flottant)\n"
                                "- date : date du pari (extrait du nom de l'image, ou sinon date du jour)\n"
                                "- tipster : toujours \"marco\"\n\n"

                                "⚠️ Règles strictes à suivre :\n"
                                "1. Tu dois OBLIGATOIREMENT choisir la catégorie et le type de pari parmi ceux du dictionnaire ci-dessous.\n"
                                "2. Tu peux générer dynamiquement la sélection si elle respecte le même format qu'une sélection d'exemple.\n"
                                "3. Tu ne dois jamais inventer un type de pari ou une catégorie.\n"
                                "4. Si le texte 'générateur de paris' apparaît dans l’image, retourne une erreur avec le texte brut de l’image.\n"
                                "5. Tu dois ignorer les textes superflus et te concentrer uniquement sur les données mentionnées ci-dessus.\n\n"

                                "🧠 Exemples de correspondance dynamique :\n"
                                "- Texte image : 'Total 1: (0.5) Plus de' → type_de_pari : 'Total 1', selection : 'Total Individuel 1 Plus de 0.5'\n"
                                "- Texte image : 'Total 2: (1.5) Moins de' → type_de_pari : 'Total 2', selection : 'Total Individuel 2 Moins de 1.5'\n"
                                "- Texte image : 'Handicap 1 (-2)' → type_de_pari : 'Handicap', selection : 'Handicap 1 (-2)'\n\n"

                                "📆 Gestion de la date :\n"
                                "- Si le nom du fichier contient une date comme 'media_20250413_204440.jpg', la date du pari est 13/04/2025.\n"
                                "- Si le nom du fichier est 'Capture-decran_1-4-2025_205148.jpeg', la date est 01/04/2025.\n"
                                "- Si aucun format de date n'est détecté dans le nom de fichier, utilise la date du jour.\n\n"

                                "📖 Voici la liste de référence des catégories, types et formats de sélections :\n"
                                f"{stringify_xbet_type_list(config.xbet_type_list)}\n\n"

                                "🧾 Format de réponse attendu (aucune explication, juste le JSON brut) :\n"
                                "{\n"
                                "  \"date\": \"25/09/2025\",\n"
                                "  \"equipe_1\": \"Al Shabab Riyadh\",\n"
                                "  \"equipe_2\": \"Al Kholood\",\n"
                                "  \"categorie\": \"Temps réglementaire\",\n"
                                "  \"type_de_pari\": \"Total 1\",\n"
                                "  \"selection\": \"Total Individuel 1 Plus de 0.5\",\n"
                                "  \"odds\": \"1.432\",\n"
                                "  \"tipster\": \"marco\"\n"
                                "}"


            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Voici une capture d'écran de ticket de pari, le fichier s'appelle {image_path} et le message qui l\'accompagen est : {msg},  merci d'extraire les données au format JSON. et de retourner uniquement le json"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=500
    )
    return cleanJson(response.choices[0].message.content)


def fordate(date_str):
    # Convert date format if needed
    return date_str


def submit_bet_to_website(driver, betslist):
    for bets in betslist:
        driver.get("https://auxobeg.cluster030.hosting.ovh.net/bilan/add-bet.php")
        bets[0] = fordate(bets[0])
        driver.find_element(By.CLASS_NAME, 'champ_date_du_paris').send_keys(bets[0])
        driver.find_element(By.CLASS_NAME, 'champ_sport').send_keys('Autre')
        driver.find_element(By.CLASS_NAME, 'champ_intitule').send_keys(bets[1])
        driver.find_element(By.CLASS_NAME, 'champ_cote').send_keys(str(bets[2].replace(',', '.')))
        driver.find_element(By.CLASS_NAME, 'champ_mise').send_keys(str(bets[3]))
        driver.find_element(By.CLASS_NAME, 'champ_code').send_keys('code' + str(time.time()))
        select_element = driver.find_element(By.CLASS_NAME, 'champ_etat')
        select = Select(select_element)
        select.select_by_value(bets[4])

        driver.find_element(By.CLASS_NAME, 'send_bet').click()

        time.sleep(2)


if __name__ == "__main__":
    # Example usage
    # Utiliser un chemin absolu pour l'image
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(project_path, "photo_5936041997808815360_y.jpg")

    msg = "J'espere que tout le monde va bien. Après une courte pause de quelques jours, place à un nouveau magnifique run qui nous attend sur cette tournée asiatique. Sur ce type de tournoi ATP 250, surtout après de longs voyages et des conditions de jeu différentes, il convient de rester prudent dans ses mises. Alejandro Tabilo a poursuivi son parcours de qualification en écartant Jordan Thompson. Le Chilien s’est montré plus rapide et incisif que son adversaire australien, s’imposant en deux sets secs, 6-4, 6-3. Il retrouvera désormais la deuxième tête de série, Luciano Darderi, qui quitte sa surface de prédilection ( la terre battue ) après avoir triomphé au Challenger de Gênes. Ce sera leur troisième affrontement sur le circuit, avec pour l’instant une victoire chacun. Darderi a déjà soulevé trois trophées ATP cette saison (dont Cordoba 2024), mais son jeu en dehors de l’ocre reste perfectible. Sa meilleure victoire sur dur à ce jour reste d’ailleurs son succès contre Tabilo à Cincinnati l’an dernier. L’Italien possède certains atouts pour s’adapter à des conditions plus rapides, mais son manque de constance se fait encore sentir. De son côté, Tabilo apparaît comme le favori : élevé au Canada, il a grandi sur surface dure et vient d’aligner trois victoires convaincantes ici, porté par un service très efficace. Or, la relance de Darderi demeure un point faible : si Tabilo conserve la même qualité au service qu’au cours de ses précédents tours, cela pourrait bien lui offrir un avantage décisif pour décrocher la victoire. LET'S GOOO !"

    if os.path.exists(image_path):
        result = extraire_pari_depuis_image(image_path, msg)
        # Initialize your webdriver here
        # driver = webdriver.Chrome()  # or whatever driver you're using
        # submit_bet_to_website(driver, result)
        print(result)
    else:
        print(f"Erreur: Le fichier image {image_path} n'existe pas.")
