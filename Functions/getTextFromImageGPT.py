import base64
import os
import sys
import time
import requests
import json
from types import SimpleNamespace

# Ajouter le chemin du projet au PYTHONPATH pour permettre l'importation de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import config


def cleanJson(raw_response):
    print('cleand json ')
    # Assurer que l'on travaille sur une chaîne Unicode
    try:
        if isinstance(raw_response, bytes):
            raw = raw_response.decode('utf-8', errors='replace')
        else:
            raw = str(raw_response)
    except Exception:
        raw = repr(raw_response)

    raw = raw.strip()

    # Retirer les balises de code si presentes (```json ou ```)
    lower = raw.lower()
    if lower.startswith('```json'):
        raw = raw[len('```json'):].lstrip('\n')
    elif raw.startswith('```'):
        raw = raw[3:]

    if raw.endswith('```'):
        raw = raw[:-3]

    cleaned = raw.strip()

    # Forcer le format UTF-8 en remplacant les caracteres invalides
    cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
    return cleaned


# Initialisation du client OpenAI avec la cle API
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
                    # Supprimer les guillemets si presents
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value


# Charger le fichier .env s'il existe
load_env_file()

# Selection du provider et du modele via .env
TEXT_PROVIDER = os.getenv('TEXT_PROVIDER', 'openai').lower()

# Charger la cle OpenAI (toujours requise ici)
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raise ValueError(
        f"La cle API OpenAI n'est pas definie.\n"
        f"Solutions possibles :\n"
        f"1. Definir la variable d'environnement : export OPENAI_API_KEY='votre_cle'\n"
        f"2. Creer un fichier .env dans {project_root} avec : OPENAI_API_KEY=votre_cle\n"
        f"3. Voir le fichier .env.example pour un modele"
    )

# Initialiser le client OpenAI (utilise pour tous les providers ici)
client = OpenAI(api_key=api_key)

# Choisir le modele selon le provider (modifiable via .env)
if TEXT_PROVIDER == 'perplexity':
    MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')
else:
    MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')


# 🖼️ Charger l'image et la convertir en base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def stringify_xbet_type_list(xbet_type_list):
    """
    Convertit la liste des types de paris en chaîne de caracteres formatee.
    
    Args:
        xbet_type_list (dict): Dictionnaire ou chaque cle est une categorie 
                              et chaque valeur est une liste de types de paris
    
    Returns:
        str: Chaîne formatee avec les categories et types de paris
    """
    lines = []
    for categorie, types_list in xbet_type_list.items():
        # types_list est maintenant une liste de types de paris, pas un dictionnaire
        for type_pari in types_list:
            lines.append(
                f"Categorie: {categorie} | Type: {type_pari}"
            )
    return "\n".join(lines)


# 🧾 Envoyer l'image a ChatGPT avec des instructions specifiques
def extraire_pari_depuis_image(image_path, msg):
    print('extraire_pari_depuis_image called')
    image_b64 = image_to_base64(image_path)
    print('Image converted to base64')

    def _safe_str(v):
        try:
            return str(v).encode('ascii', errors='replace').decode('ascii')
        except Exception:
            return ''

    # Attempt to call the OpenAI client, sanitize headers first
    try:
        try:
            # sanitize possible internal header containers
            if hasattr(client, '_default_headers') and isinstance(client._default_headers, dict):
                client._default_headers = {k: _safe_str(v) for k, v in client._default_headers.items()}
            httpx_client = getattr(client, '_httpx_client', None)
            if httpx_client is not None and hasattr(httpx_client, 'headers'):
                try:
                    httpx_client.headers = {k: _safe_str(v) for k, v in dict(httpx_client.headers).items()}
                except Exception:
                    for k, v in dict(httpx_client.headers).items():
                        try:
                            httpx_client.headers[k] = _safe_str(v)
                        except Exception:
                            continue
        except Exception:
            pass

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un agent OCR intelligent. Ton role est de lire des captures d'ecran de tickets de paris sportifs "
                        "et d'en extraire les donnees principales sous forme de JSON structure."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Voici une capture d'ecran de ticket de pari, le fichier s'appelle {image_path} et le message qui l\'accompagen est : {msg}, merci d'extraire les donnees au format JSON. et de retourner uniquement le json"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=500,
        )
    except (UnicodeEncodeError, TypeError) as ue:
        # Fallback: call OpenAI via raw HTTP with ascii-safe headers
        try:
            print('Unicode/Type error with OpenAI client, using HTTP fallback:', ue)
            url = 'https://api.openai.com/v1/chat/completions'
            payload = {
                'model': MODEL,
                'messages': [
                    {'role': 'system', 'content': 'Tu es un agent OCR intelligent. Extrais les donnees et reponds uniquement en JSON.'},
                    {'role': 'user', 'content': f"Fichier: {image_path} ; message: {msg}"}
                ],
                'max_tokens': 500
            }
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'auxobetbot/1.0'
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            jr = r.json()
            # Try to extract content from OpenAI response
            content = None
            if isinstance(jr, dict):
                choices = jr.get('choices') or jr.get('results')
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict) and 'message' in first and isinstance(first['message'], dict):
                        content = first['message'].get('content')
                    elif isinstance(first, dict) and 'text' in first:
                        content = first.get('text')
            if content is None:
                content = json.dumps(jr, ensure_ascii=False)
            return cleanJson(content)
        except Exception as e:
            print('Fallback HTTP request failed:', e)
            raise

    return cleanJson(response.choices[0].message.content)


def extraire_pari_joueur_nba_depuis_image(image_path, msg):
    """
    Fonction specialisee pour extraire les paris sur les performances de joueurs NBA.
    Optimisee pour detecter les props joueurs (points, rebonds, passes, etc.)
    """
    image_b64 = image_to_base64(image_path)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content":
                    "Tu es un agent OCR specialise dans les paris sur les performances individuelles des joueurs NBA."
                    "Ton role est d'extraire les donnees de paris props joueurs depuis des captures d'ecran."
                    
                    "📊 Donnees a extraire :\n"
                    "- date : date du pari (format DD/MM/YYYY)\n"
                    "- match : les deux equipes qui s'affrontent (ex: 'Lakers vs Celtics')\n"
                    "- joueur : nom complet du joueur concerne\n"
                    "- equipe_joueur : equipe du joueur\n"
                    "- statistique : type de statistique (Points, Rebonds, Passes, Interceptions, etc.)\n"
                    "- ligne : la ligne du pari (ex: 25.5, 8.5, 10.5)\n"
                    "- sens : 'Plus de' ou 'Moins de'\n"
                    "- odds : la cote du pari (nombre flottant)\n"
                    "- bookmaker : nom du bookmaker si visible\n"
                    
                    "🏀 Types de statistiques NBA reconnues :\n"
                    "- Points (PTS)\n"
                    "- Rebonds (REB / Rebounds)\n"
                    "- Passes decisives (AST / Assists)\n"
                    "- Interceptions (STL / Steals)\n"
                    "- Contres (BLK / Blocks)\n"
                    "- Points + Rebonds (PTS+REB)\n"
                    "- Points + Passes (PTS+AST)\n"
                    "- Rebonds + Passes (REB+AST)\n"
                    "- Points + Rebonds + Passes (PTS+REB+AST)\n"
                    "- Tirs a 3 points reussis (3PM / 3-Points Made)\n"
                    "- Double-Double (Double Double)\n"
                    "- Triple-Double (Triple Double)\n"
                    
                    "⚠️ Regles strictes :\n"
                    "1. Normalise les noms de joueurs (ex: 'LeBron' → 'LeBron James')\n"
                    "2. Convertis les abreviations en texte complet (ex: 'PTS' → 'Points')\n"
                    "3. Detecte automatiquement si c'est 'Plus de' ou 'Moins de' (Over/Under, +/-)\n"
                    "4. Extrait la ligne exacte (nombre avec decimale)\n"
                    "5. Si plusieurs props du meme joueur, cree un objet JSON par prop\n"
                    "6. Si c'est un parlay/combine de plusieurs joueurs, retourne 'COMBINE_MULTIPLE_JOUEURS'\n"
                    
                    "📆 Gestion de la date :\n"
                    "- Extrait depuis le nom de fichier si disponible\n"
                    "- Sinon cherche dans l'image (date du match)\n"
                    "- Sinon utilise la date du jour\n"
                    
                    "🧾 Format de reponse JSON attendu (uniquement le JSON, sans explication) :\n"
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
                     "text": f"Voici une capture de pari NBA sur un joueur. Fichier: {image_path}. Message contexte: {msg}. Extrait uniquement le JSON des donnees du pari joueur."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=600
    )
    return cleanJson(response.choices[0].message.content)


def compare_match_name(match_name1, match_name2):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Tu es un agent qui compare deux noms de matchs sportifs. Reponds uniquement par true ou false en suivant ces regles : ignorer les accents, la casse, les separateurs et certains mots comme FC, Real, etc."

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
    # Convertir la reponse string "true"/"false" en booleen correspondant
    response_content = response.choices[0].message.content
    if response_content is None:
        return False
    response_text = response_content.strip().lower()
    return response_text == "true"


def compare_selection(match, selection, selection_list):
    print(f"pour le match {match} Compare ces deux selections :  {selection} et {selection_list}")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
                        Tu es un agent specialise dans la comparaison de selections de paris sportifs.
                        Ton objectif est de determiner si une selection donnee correspond exactement a une liste de selections possibles.
                        
                        Instructions :
                        1. Compare la selection demandee avec les options fournies.
                        2. Ignore :
                           - La casse (majuscule/minuscule)
                           - Les accents (ex. Gerone = Girona)
                           - Les espaces supplementaires
                        3. Repond strictement par :
                           - Le texte exact de la selection correspondante dans la liste si elle existe
                           - "false" si aucune selection ne correspond
                        4. Ne rajoute aucun autre texte ni explication.
                        
                        Exemples :
                        - Selection recherchee : "Total jeux Moins de 21.5"
                          Liste : ["Total Moins de 21", "Total Moins de 21.5", "Total Plus de 21.5"]
                          Reponse : "Total Moins de 21.5"
                        
                        - Selection recherchee : "Equipe 1 gagne et Total > 19.5"
                          Liste : ["Equipe 1 va gagner et Total > 19.5 - Oui", "Equipe 1 va gagner et Total < 19.5 - Oui"]
                          Reponse : "Equipe 1 va gagner et Total > 19.5 - Oui"
                        
                        - Selection recherchee : "Total jeux Moins de 25"
                          Liste : ["Total Moins de 21", "Total Moins de 21.5", "Total Plus de 21.5"]
                          Reponse : "false"
                          
                          Retourne le texte exacte dans la liste donnee.
                        """
            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Pour le match {match} compare {selection}  avec les selections suivantes: {selection_list} et retourne la selction de cette liste qui correspond sans texte superflu juste le texte de la liste qui correspond a la selectione envoyee."
                     },
                ]
            }
        ],
        max_tokens=500
    )
    # Convertir la reponse string "true"/"false" en booleen correspondant
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

    msg = "J'espere que tout le monde va bien. Apres une courte pause de quelques jours, place a un nouveau magnifique run qui nous attend sur cette tournee asiatique. Sur ce type de tournoi ATP 250, surtout apres de longs voyages et des conditions de jeu differentes, il convient de rester prudent dans ses mises. Alejandro Tabilo a poursuivi son parcours de qualification en ecartant Jordan Thompson. Le Chilien s’est montre plus rapide et incisif que son adversaire australien, s’imposant en deux sets secs, 6-4, 6-3. Il retrouvera desormais la deuxieme tete de serie, Luciano Darderi, qui quitte sa surface de predilection ( la terre battue ) apres avoir triomphe au Challenger de Genes. Ce sera leur troisieme affrontement sur le circuit, avec pour l’instant une victoire chacun. Darderi a deja souleve trois trophees ATP cette saison (dont Cordoba 2024), mais son jeu en dehors de l’ocre reste perfectible. Sa meilleure victoire sur dur a ce jour reste d’ailleurs son succes contre Tabilo a Cincinnati l’an dernier. L’Italien possede certains atouts pour s’adapter a des conditions plus rapides, mais son manque de constance se fait encore sentir. De son cote, Tabilo apparaît comme le favori : eleve au Canada, il a grandi sur surface dure et vient d’aligner trois victoires convaincantes ici, porte par un service tres efficace. Or, la relance de Darderi demeure un point faible : si Tabilo conserve la meme qualite au service qu’au cours de ses precedents tours, cela pourrait bien lui offrir un avantage decisif pour decrocher la victoire. LET'S GOOO !"

    if os.path.exists(image_path):
        result = extraire_pari_depuis_image(image_path, msg)
        # Initialize your webdriver here
        # driver = webdriver.Chrome()  # or whatever driver you're using
        # submit_bet_to_website(driver, result)
        print(result)
    else:
        print(f"Erreur: Le fichier image {image_path} n'existe pas.")
