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


# Fonction pour charger les variables d'environnement depuis un fichier .env
def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env s'il existe."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, '.env')

    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Supprimer les guillemets si présents
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value


# Charger le fichier .env s'il existe
load_env_file()

# Charger la clé API depuis les variables d'environnement
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raise ValueError(
        f"La clé API OpenAI n'est pas définie.\n"
        f"Solutions possibles :\n"
        f"1. Définir la variable d'environnement : export OPENAI_API_KEY='votre_clé'\n"
        f"2. Créer un fichier .env dans {project_root} avec : OPENAI_API_KEY=votre_clé\n"
        f"3. Voir le fichier .env.example pour un modèle"
    )

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

                    "⚠️ Règles strictes à suivre :\n"
                    "1. Tu dois OBLIGATOIREMENT choisir la catégorie et le type de pari parmi ceux du dictionnaire ci-dessous.\n"
                    "2. Tu peux générer dynamiquement la sélection si elle respecte le même format qu'une sélection d'exemple.\n"
                    "3. Tu ne dois jamais inventer un type de pari ou une catégorie.\n"
                    "4. Si le texte 'générateur de paris' apparaît dans l’image, retourne une erreur avec le texte brut de l’image.\n"
                    "5. Tu dois ignorer les textes superflus et te concentrer uniquement sur les données mentionnées ci-dessus.\n\n"
                    "6. Si tu vois le mot \"combiné\" tu renvoies \"Ce  paris est un combiné\"\n\n"

                    "🧠 Exemples de correspondance dynamique :\n"
                    "- Texte image : 'Total 1: (0.5) Plus de' → type_de_pari : 'Total 1', selection : 'Total Individuel 1 Plus de 0.5'\n"
                    "- Texte image : 'Total 2: (1.5) Moins de' → type_de_pari : 'Total 2', selection : 'Total Individuel 2 Moins de 1.5'\n"
                    "- Texte image : 'Handicap 1 (-2)' → type_de_pari : 'Handicap', selection : 'Handicap 1 (-2)'\n\n"

                    "📆 Gestion de la date :\n"
                    "- Si le nom du fichier contient une date comme 'media_20250413_204440.jpg', la date du pari est 13/04/2025.\n"
                    "- Si le nom du fichier est 'Capture-decran_1-4-2025_205148.jpeg', la date est 01/04/2025.\n"
                    "- Si aucun format de date n'est détecté dans le nom de fichier, utilise la date du jour.\n\n"
                    
                    "set handicap correspond à Handicap des sets\n"

                    "📖 Voici la liste de référence des catégories, types et formats de sélections :\n"
                    f"{stringify_xbet_type_list(config.xbet_type_list)}\n\n"
                    "Si tu ne vois aucune information sur la catégories utilise Temps réglementaire."
                    "Si c'est un pari remboursé si nul, ça correspond au type Handicap, et à la selection Handicap 1 (0) ou Handicap 2 (0), en fonction de si c'est équipe 1 ou équipe 2 si nul."
                    "Si c'est le vainqueur du match la selection est V1 ou V2 en fonction de l'équipe 1 ou 2 vainqueur"
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


def extraire_pari_joueur_nba_depuis_image(image_path, msg):
    """
    Fonction spécialisée pour extraire les paris sur les performances de joueurs NBA.
    Optimisée pour détecter les props joueurs (points, rebonds, passes, etc.)
    """
    image_b64 = image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content":
                    "Tu es un agent OCR spécialisé dans les paris sur les performances individuelles des joueurs NBA."
                    "Ton rôle est d'extraire les données de paris props joueurs depuis des captures d'écran."
                    
                    "📊 Données à extraire :\n"
                    "- date : date du pari (format DD/MM/YYYY)\n"
                    "- match : les deux équipes qui s'affrontent (ex: 'Lakers vs Celtics')\n"
                    "- joueur : nom complet du joueur concerné\n"
                    "- equipe_joueur : équipe du joueur\n"
                    "- statistique : type de statistique (Points, Rebonds, Passes, Interceptions, etc.)\n"
                    "- ligne : la ligne du pari (ex: 25.5, 8.5, 10.5)\n"
                    "- sens : 'Plus de' ou 'Moins de'\n"
                    "- odds : la cote du pari (nombre flottant)\n"
                    "- bookmaker : nom du bookmaker si visible\n"
                    
                    "🏀 Types de statistiques NBA reconnues :\n"
                    "- Points (PTS)\n"
                    "- Rebonds (REB / Rebounds)\n"
                    "- Passes décisives (AST / Assists)\n"
                    "- Interceptions (STL / Steals)\n"
                    "- Contres (BLK / Blocks)\n"
                    "- Points + Rebonds (PTS+REB)\n"
                    "- Points + Passes (PTS+AST)\n"
                    "- Rebonds + Passes (REB+AST)\n"
                    "- Points + Rebonds + Passes (PTS+REB+AST)\n"
                    "- Tirs à 3 points réussis (3PM / 3-Points Made)\n"
                    "- Double-Double (Double Double)\n"
                    "- Triple-Double (Triple Double)\n"
                    
                    "⚠️ Règles strictes :\n"
                    "1. Normalise les noms de joueurs (ex: 'LeBron' → 'LeBron James')\n"
                    "2. Convertis les abréviations en texte complet (ex: 'PTS' → 'Points')\n"
                    "3. Détecte automatiquement si c'est 'Plus de' ou 'Moins de' (Over/Under, +/-)\n"
                    "4. Extrait la ligne exacte (nombre avec décimale)\n"
                    "5. Si plusieurs props du même joueur, crée un objet JSON par prop\n"
                    "6. Si c'est un parlay/combiné de plusieurs joueurs, retourne 'COMBINE_MULTIPLE_JOUEURS'\n"
                    
                    "📆 Gestion de la date :\n"
                    "- Extrait depuis le nom de fichier si disponible\n"
                    "- Sinon cherche dans l'image (date du match)\n"
                    "- Sinon utilise la date du jour\n"
                    
                    "🧾 Format de réponse JSON attendu (uniquement le JSON, sans explication) :\n"
                    "{\n"
                    "  \"date\": \"10/12/2025\",\n"
                    "  \"match\": \"Lakers vs Celtics\",\n"
                    "  \"joueur\": \"LeBron James\",\n"
                    "  \"equipe_joueur\": \"Lakers\",\n"
                    "  \"statistique\": \"Points + Rebonds + Passes\",\n"
                    "  \"ligne\": \"45.5\",\n"
                    "  \"sens\": \"Plus de\",\n"
                    "  \"odds\": \"1.85\",\n"
                    "  \"bookmaker\": \"1xBet\"\n"
                    "}\n\n"
                    
                    "🎯 Exemples de reconnaissance :\n"
                    "- Image: 'Stephen Curry O 25.5 PTS @1.90' → statistique='Points', ligne='25.5', sens='Plus de'\n"
                    "- Image: 'Giannis Antetokounmpo Under 12.5 REB' → statistique='Rebonds', ligne='12.5', sens='Moins de'\n"
                    "- Image: 'Luka Doncic 35.5+ PTS+REB+AST' → statistique='Points + Rebonds + Passes', sens='Plus de'\n"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Voici une capture de pari NBA sur un joueur. Fichier: {image_path}. Message contexte: {msg}. Extrait uniquement le JSON des données du pari joueur."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=600
    )
    return cleanJson(response.choices[0].message.content)


def compare_match_name(match_name1, match_name2):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Tu es un agent qui compare deux noms de matchs sportifs. Réponds uniquement par true ou false en suivant ces règles : ignorer les accents, la casse, les séparateurs et certains mots comme FC, Real, etc."

            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Campare ces deux match :  {match_name1} et {match_name2}"
                     },
                ]
            }
        ],
        max_tokens=500
    )
    # Convertir la réponse string "true"/"false" en booléen correspondant
    response_content = response.choices[0].message.content
    if response_content is None:
        return False
    response_text = response_content.strip().lower()
    return response_text == "true"


def compare_selection(match, selection, selection_list):
    print(f"pour le match {match} Compare ces deux selections :  {selection} et {selection_list}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                        Tu es un agent spécialisé dans la comparaison de sélections de paris sportifs.
                        Ton objectif est de déterminer si une sélection donnée correspond exactement à une liste de sélections possibles.
                        
                        Instructions :
                        1. Compare la sélection demandée avec les options fournies.
                        2. Ignore :
                           - La casse (majuscule/minuscule)
                           - Les accents (ex. Gérone = Girona)
                           - Les espaces supplémentaires
                        3. Répond strictement par :
                           - Le texte exact de la sélection correspondante dans la liste si elle existe
                           - "false" si aucune sélection ne correspond
                        4. Ne rajoute aucun autre texte ni explication.
                        
                        Exemples :
                        - Sélection recherchée : "Total jeux Moins de 21.5"
                          Liste : ["Total Moins de 21", "Total Moins de 21.5", "Total Plus de 21.5"]
                          Réponse : "Total Moins de 21.5"
                        
                        - Sélection recherchée : "Equipe 1 gagne et Total > 19.5"
                          Liste : ["Equipe 1 va gagner et Total > 19.5 - Oui", "Equipe 1 va gagner et Total < 19.5 - Oui"]
                          Réponse : "Equipe 1 va gagner et Total > 19.5 - Oui"
                        
                        - Sélection recherchée : "Total jeux Moins de 25"
                          Liste : ["Total Moins de 21", "Total Moins de 21.5", "Total Plus de 21.5"]
                          Réponse : "false"
                          
                          Retourne le texte exacte dans la liste donnée.
                        """
            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Pour le match {match} compare {selection}  avec les selections suivantes: {selection_list} et retourne la selction de cette liste qui correspond sans texte superflu juste le texte de la liste qui correspond a la selectione envoyée."
                     },
                ]
            }
        ],
        max_tokens=500
    )
    # Convertir la réponse string "true"/"false" en booléen correspondant
    response_content = response.choices[0].message.content
    print(response_content)
    if response_content is None or response_content == 'false':
        return 'false'
    return response_content


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
    image_path = os.path.join(project_path, "images.jpg")

    msg = "J'espere que tout le monde va bien. Après une courte pause de quelques jours, place à un nouveau magnifique run qui nous attend sur cette tournée asiatique. Sur ce type de tournoi ATP 250, surtout après de longs voyages et des conditions de jeu différentes, il convient de rester prudent dans ses mises. Alejandro Tabilo a poursuivi son parcours de qualification en écartant Jordan Thompson. Le Chilien s’est montré plus rapide et incisif que son adversaire australien, s’imposant en deux sets secs, 6-4, 6-3. Il retrouvera désormais la deuxième tête de série, Luciano Darderi, qui quitte sa surface de prédilection ( la terre battue ) après avoir triomphé au Challenger de Gênes. Ce sera leur troisième affrontement sur le circuit, avec pour l’instant une victoire chacun. Darderi a déjà soulevé trois trophées ATP cette saison (dont Cordoba 2024), mais son jeu en dehors de l’ocre reste perfectible. Sa meilleure victoire sur dur à ce jour reste d’ailleurs son succès contre Tabilo à Cincinnati l’an dernier. L’Italien possède certains atouts pour s’adapter à des conditions plus rapides, mais son manque de constance se fait encore sentir. De son côté, Tabilo apparaît comme le favori : élevé au Canada, il a grandi sur surface dure et vient d’aligner trois victoires convaincantes ici, porté par un service très efficace. Or, la relance de Darderi demeure un point faible : si Tabilo conserve la même qualité au service qu’au cours de ses précédents tours, cela pourrait bien lui offrir un avantage décisif pour décrocher la victoire. LET'S GOOO !"

    if os.path.exists(image_path):
        result = extraire_pari_depuis_image(image_path, msg)
        # Initialize your webdriver here
        # driver = webdriver.Chrome()  # or whatever driver you're using
        # submit_bet_to_website(driver, result)
        print(result)
    else:
        print(f"Erreur: Le fichier image {image_path} n'existe pas.")
