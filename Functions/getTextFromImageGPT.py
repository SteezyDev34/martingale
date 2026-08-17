import base64
import os
import sys
import time

from PIL import Image

# Ajouter le chemin du projet au PYTHONPATH pour permettre l'importation de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import requests
from unidecode import unidecode
from urllib.parse import quote_plus


def cleanJson(raw_response):
    if raw_response is None:
        return ""

    text = str(raw_response).strip()

    # Try to extract JSON inside ```json ... ``` or ``` ... ``` code fences
    # Fallback to returning the stripped text
    import re

    # regex to capture between ```json ... ``` or ``` ... ```
    m = re.search(r"```\s*json\s*(.*?)```", text, re.S | re.I)
    if not m:
        m = re.search(r"```(.*?)```", text, re.S)

    if m:
        cleaned = m.group(1).strip()
    else:
        # remove possible leading/trailing backticks and whitespace
        cleaned = re.sub(r"^`+|`+$", "", text).strip()

    print(cleaned)
    return cleaned





import anthropic as _anthropic
from openai import OpenAI


def load_env_file():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value


load_env_file()

# Sélection du provider IA via .env : USE_CLAUDE=1, USE_PERPLEXITY=1, sinon OpenAI par défaut
USE_CLAUDE = os.getenv('USE_CLAUDE', '0').lower() in ('1', 'true', 'yes')
USE_PERPLEXITY = os.getenv('USE_PERPLEXITY', '0').lower() in ('1', 'true', 'yes')
PERPLEXITY_BASE_URL = os.getenv('PERPLEXITY_BASE_URL', 'https://api.perplexity.ai')
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')
DEFAULT_MODEL = os.getenv('MODEL_NAME', 'gpt-4o')
# CLAUDE_API_KEY (ancienne clé) ou ANTHROPIC_API_KEY (nouvelle) — les deux acceptés
CLAUDE_DEFAULT_MODEL = os.getenv('CLAUDE_MODEL') or os.getenv('CALUDE_MODEL') or 'claude-sonnet-4-6'

if USE_PERPLEXITY:
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY non définie dans le .env")
    client = OpenAI(api_key=api_key, base_url=PERPLEXITY_BASE_URL)
    MODEL_NAME = PERPLEXITY_MODEL
    PROVIDER = 'perplexity'
elif not USE_CLAUDE:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY non définie dans le .env")
    client = OpenAI(api_key=api_key)
    MODEL_NAME = DEFAULT_MODEL
    PROVIDER = 'openai'
else:
    # Claude par défaut (USE_CLAUDE=1 ou aucun provider explicite → Claude)
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if not api_key:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raise ValueError(
            f"La clé API Claude n'est pas définie.\n"
            f"Ajoute ANTHROPIC_API_KEY=sk-ant-... dans {project_root}/.env"
        )
    # timeout explicite : sans ça, un appel bloqué peut geler tout un thread
    # appelant (ex: le thread Tempête Betting de watch_server.py) pendant la
    # durée par défaut du SDK (plusieurs minutes), sans jamais lever d'erreur.
    client = _anthropic.Anthropic(api_key=api_key, timeout=60.0)
    MODEL_NAME = CLAUDE_DEFAULT_MODEL
    PROVIDER = 'claude'


# 🖼️ Charger l'image et la convertir en base64
def image_to_base64(image_path, max_width=1200, quality=80):
    """Read an image (path string or PIL.Image) and return a base64-encoded JPEG string.

    Everything is done in-memory via BytesIO — no temp files, no .load()/.copy()
    that can trigger the '_im' AttributeError on some Pillow builds.
    """
    from io import BytesIO
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # tolerate truncated files

    # --- 1. obtain raw file bytes ------------------------------------------------
    if isinstance(image_path, Image.Image):
        # Caller already gave us a PIL Image → dump it to PNG bytes in memory
        buf = BytesIO()
        image_path.save(buf, format="PNG")
        raw = buf.getvalue()
        print(f"[image_to_base64] received PIL Image, size={image_path.size}")
    elif isinstance(image_path, (str, bytes, os.PathLike)):
        print(f"[image_to_base64] reading file: {image_path}")
        with open(image_path, 'rb') as fh:
            raw = fh.read()
        if not raw:
            raise ValueError(f"Empty file: {image_path}")
    else:
        raise TypeError(f"Unsupported image_path type: {type(image_path)}")

    # --- 2. decode → resize → convert to RGB JPEG in one pass -------------------
    img = Image.open(BytesIO(raw))
    w, h = img.size
    if w > max_width:
        new_h = int(h * max_width / w)
        img = img.resize((max_width, new_h))

    rgb = img.convert("RGB")

    out = BytesIO()
    rgb.save(out, format="JPEG", quality=quality)
    encoded = base64.b64encode(out.getvalue()).decode('utf-8')
    print(f"[image_to_base64] OK  base64 length={len(encoded)}")
    return encoded


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


# 🧾 Envoyer l'image à l'IA avec des instructions spécifiques
def extraire_pari_depuis_image(image_path, msg):
    image_b64 = image_to_base64(image_path)
    system_prompt = (
        "Tu es un agent OCR intelligent. Ton rôle est de lire des captures d'écran de tickets de paris sportifs "
        "et d'en extraire les données principales sous forme de JSON structuré.\n"
        "⚠️ LECTURE DE L'IMAGE : lis l'intégralité de l'image, y compris les petits textes en bas. "
        "Les titres en gros sont des résumés marketing — ce sont les lignes de détail du ticket (noms des matchs, descriptions des paris, cotes individuelles) qui font foi. "
        "Si le ticket contient plusieurs lignes de paris, chacune correspond à un élément séparé dans 'matches', même si elles concernent des matchs différents.\n"
        "Les données à extraire sont les suivantes :\n"
        "- equipe_1 : première équipe (ou joueur Prénom en premier)\n"
        "- equipe_2 : deuxième équipe (ou joueur Prénom en premier)\n"
        "- categorie : catégorie du pari\n"
        "- type_de_pari : type de pari (doit être EXACTEMENT présent dans la liste ci-dessous)\n"
        "- selection : la sélection faite (peut être générée dynamiquement si elle suit un format connu)\n"
        "- odds : la cote du pari (nombre flottant)\n"
        "- date : date du pari (extrait du nom de l'image, ou sinon date du jour)\n"
        "⚠️ Règles strictes à suivre :\n"
        "Si le nom des équipe présente des virgules il faut les supprimer\n"
        "1. Tu dois OBLIGATOIREMENT choisir la catégorie et le type de pari parmi ceux du dictionnaire ci-dessous.\n"
        "2. Tu peux générer dynamiquement la sélection si elle respecte le même format qu'une sélection d'exemple.\n"
        "3. Tu ne dois jamais inventer un type de pari ou une catégorie.\n"
        "4. Tu dois ignorer les textes superflus et te concentrer uniquement sur les données mentionnées ci-dessus.\n\n"
        "Note importante : Un pari peut contenir plusieurs événements combinés (par ex. 'Vainqueur + Total de buts', 'Double chance + Total de buts').\n"
        "Dans ce cas, tu dois :\n"
        "Du dois d'abord chercher si une catégorie correspond à ce type de pari combiné (ex: '1, Résultat + Total' ou '2X Et chaque Equipe va marquer – Oui' ou '1, Résultat + Total de Sets'), et si oui, l'utiliser.\n"
        "Sinon, tu dois extraire les composantes individuelles du pari (ex: 'Vainqueur', 'Total de buts') et les traiter comme des événements séparés.\n"
        "  1) Extraire chaque composante du pari et les retourner dans un champ 'combined_events' (liste), chaque élément contenant: categorie, type_de_pari, selection, odds, etc.\n"
        "  2) Chercher dans la liste des sélections (ou sur le ticket) un libellé UNIQUE qui COMBINE tous les sous-paris (la formulation commerciale exacte) et le retourner dans un champ 'combined_label' si trouvé.\n"
        "     Exemples de libellés combinés à rechercher : '2X Et chaque Equipe va marquer – Oui', 'Equipe 2 va gagner et Total > 1.5 - Oui'.\n"
        "  3) Si le libellé combiné n'existe pas, mettre 'combined_label': null mais conserver 'combined_events' avec les composantes extraites.\n"
        "  4) Si une composante ne peut être extraite proprement, indique sa valeur comme null mais conserve les autres composantes extraites.\n\n"
        "Si un des evenements concerne un match différent de celui des autres événements, alors considère que c'est un pari combiné multi-matchs, et traite chaque match séparément dans un tableau.\n"
        "il peut y avoir des matchs différent avec des events différents dans ce cas chaque match doit avoir son combined_events et son combined_label si il existe, mais tous les matchs doivent être regroupés dans un tableau 'matches' qui contient pour chaque match : equipe_1, equipe_2, categorie, type_de_pari, selection, odds, date, sport, combined_events (liste), combined_label (string ou null)\n\n"
        "s'il n'ya qu'un match mets le quand meme dans un tableau 'matches' avec un seul élément, pour uniformiser le format de réponse.\n\n"
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
        "Liste des sports et leurs ids (utilisez l'id dans le champ 'sport' du JSON) :\n"
        "tennis: 2\nfootball: 3\nbasketball: 4\nrugby: 5\nhandball: 8\nice-hockey: 9\n"
        "baseball: 10\ntable-tennis: 11\namerican-football: 12\nvolleyball: 13\nesports: 14\n"
        "cricket: 15\ndarts: 16\nfutsal: 17\nbadminton: 18\nwaterpolo: 19\nsnooker: 20\n"
        "aussie-rules: 21\nufc: 22\nsurf: 23\nski-alpin: 24\nski: 25\n\n"
        "Si tu ne vois aucune information sur la catégories utilise Temps réglementaire."
        "Si c'est un pari remboursé si nul, ça correspond au type Handicap, et à la selection Handicap 1 (0) ou Handicap 2 (0), en fonction de si c'est équipe 1 ou équipe 2 si nul."
        "Si c'est le vainqueur du match la selection est V1 ou V2 en fonction de l'équipe 1 ou 2 vainqueur"
        "Si un des intitulé concerne un nombre de set strictement = 2, cela correspondt a total de set TM 2.5 \n"
        "Si c'est Match Nul rembousé si vainqueur il faut sélectionner victoire de l'équipe 1 ou 2 en fonction de l'équipe 1 ou 2 gagnante, et la catégorie est Vainqueur Match"
        "Si le sport est tennis et que le texte du pari indique qu'un des joueurs gagne le match, alors considère ce pari comme un pari de type '1x2' (catégorie Temps réglementaire) et génère la selection correspondante : 'V1' ou 'V2' selon s'il s'agit de l'équipe/joueur 1 ou 2.\n\n"
        "🎾 RÈGLE TENNIS — Handicap des sets :\n"
        "Si le texte d'un pari contient 'remporte un set' / 'gagne au moins 1 set' / 'remporte au moins un set' :\n"
        "  → categorie='Temps réglementaire', type_de_pari='Handicap des sets'\n"
        "  → selection='1 Handicap (+1.5) Sets' si le joueur qui gagne le set est equipe_1\n"
        "  → selection='2 Handicap (+1.5) Sets' si le joueur qui gagne le set est equipe_2\n"
        "  Tournoi standard (ATP 250/500, WTA) : +1.5 sets. Masters 1000 / Grand Slam : +2.5 sets.\n\n"
        "🎾 FORMAT TEMPÊTE BETTING — PRIORITÉ ABSOLUE :\n"
        "  Sur les tickets Tempête Betting il y a souvent un TITRE RÉSUMÉ en gros (ex: 'VICTOIRE A.RUBLEV + 1 SET DE BURRUCHAGA')\n"
        "  suivi de DÉTAILS du ticket en bas (petites lignes avec les vrais noms de matchs et les vrais paris).\n"
        "  ⚠️ IGNORE le titre résumé pour identifier les matchs. Lis les DÉTAILS DU TICKET pour extraire equipe_1, equipe_2 et le type de pari.\n"
        "  Chaque ligne de détail correspond à un pari séparé, potentiellement sur un match différent.\n"
        "  Exemple :\n"
        "    Titre : 'VICTOIRE A.RUBLEV (RUS) + 1 SET DE BURRUCHAGA (ARG)' — résumé, l'ignorer pour les noms.\n"
        "    Détail 1 : 'Burruchaga, Roman Andres vs Blockx, Alexander / Burruchaga remporte un set / 1.37'\n"
        "      → equipe_1='Burruchaga Roman Andres', equipe_2='Blockx Alexander', type='Handicap des sets', selection='1 Handicap (+1.5) Sets'\n"
        "    Détail 2 : 'Rublev, Andrey vs Van Assche, Luca / Vainqueur / 1.16'\n"
        "      → equipe_1='Rublev Andrey', equipe_2='Van Assche Luca', type='1x2', selection='V1'\n\n"
        "🧾 Format de réponse attendu (aucune explication, juste le JSON brut) :\n"
        "Tu dois également détecter le sport concerné (Football, Tennis, NBA) et l'indiquer dans le champ 'sport' du JSON extrait avec les id correspondants.\n"
        "Génère un intitulé simplifié compréhensible de tous, en combinant les éléments extraits (ex: 'Al Shabab Riyadh plus de 0.5 buts').\n\n"
        "{\n"
        "  \"matches\": [\n"
        "    {\n"
        "      \"date\": \"25/09/2025\",\n"
        "      \"equipe_1\": \"Al Shabab Riyadh\",\n"
        "      \"equipe_2\": \"Al Kholood\",\n"
        "      \"categorie\": \"Temps réglementaire\",\n"
        "      \"type_de_pari\": \"Total 1\",\n"
        "      \"selection\": \"Total Individuel 1 Plus de 0.5\",\n"
        "      \"sport\": \"3\",\n"
        "      \"intitule\": \"Al Shabab Riyadh plus de 0.5 buts\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Remarques :\n"
        "- Si un seul match, renvoyer `matches` avec un seul élément.\n"
        "- Si plusieurs matches, inclure chaque match comme élément de `matches`.\n"
        "- Ne renvoyer aucun texte hors du JSON.\n"
    )
    user_text = f"Le fichier s'appelle {image_path} et le message qui l'accompagne est : {msg}. Retourne uniquement le JSON."

    if PROVIDER == 'claude':
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                    {"type": "text", "text": user_text}
                ]}]
            )
        except Exception as e:
            print(f"❌ Erreur Claude extraire_pari_depuis_image: {e}")
            raise
        content = response.content[0].text if response.content else None
    else:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]}
                ]
            )
        except Exception as e:
            print(f"❌ Erreur {PROVIDER} extraire_pari_depuis_image: {e}")
            raise
        content = response.choices[0].message.content if response.choices else None

    if not content:
        raise ValueError(f"Empty or invalid model response: {response}")

    return cleanJson(content)


def extraire_pari_depuis_texte(texte_pari, msg=""):
    """
    Même logique qu'extraire_pari_depuis_image mais sans image.
    Utilisé pour les sources qui fournissent déjà les données en texte (ex: FrancePronos DOM).
    Retourne un JSON structuré identique avec le tableau 'matches'.
    """
    system_prompt = (
        "Tu es un agent intelligent spécialisé dans l'extraction de données de paris sportifs. "
        "Ton rôle est de lire un texte décrivant un ou plusieurs pronostics sportifs "
        "et d'en extraire les données principales sous forme de JSON structuré.\n"
        "Les données à extraire sont les suivantes :\n"
        "- equipe_1 : première équipe (ou joueur Prénom en premier)\n"
        "- equipe_2 : deuxième équipe (ou joueur Prénom en premier)\n"
        "- categorie : catégorie du pari\n"
        "- type_de_pari : type de pari (doit être EXACTEMENT présent dans la liste ci-dessous)\n"
        "- selection : la sélection faite\n"
        "- odds : la cote du pari (nombre flottant)\n"
        "- date : date du pari (au format JJ/MM/AAAA)\n\n"

        "⚠️ Règles strictes à suivre :\n"
        "1. Tu dois OBLIGATOIREMENT choisir la catégorie et le type de pari parmi ceux du dictionnaire ci-dessous.\n"
        "2. Tu ne dois jamais inventer un type de pari ou une catégorie.\n"
        "3. Tous les matchs doivent être dans un tableau 'matches', même s'il n'y en a qu'un.\n\n"

        "Note importante : Un pari peut contenir plusieurs événements combinés.\n"
        "Dans ce cas, traite chaque match séparément avec ses combined_events et combined_label.\n\n"

        "Si tu ne vois aucune information sur la catégorie utilise Temps réglementaire.\n"
        "Si c'est le vainqueur du match la selection est V1 ou V2 en fonction de l'équipe 1 ou 2 vainqueur.\n"
        "set handicap correspond à Handicap des sets.\n\n"

        f"📖 Liste de référence des catégories, types et formats de sélections :\n"
        f"{stringify_xbet_type_list(config.xbet_type_list)}\n\n"

        "Liste des sports et leurs ids :\n"
        "tennis: 2\nfootball: 3\nbasketball: 4\nrugby: 5\nhandball: 8\nice-hockey: 9\n"
        "baseball: 10\ntable-tennis: 11\namerican-football: 12\nvolleyball: 13\nesports: 14\n\n"

        "🧾 Format de réponse attendu (JSON brut uniquement) :\n"
        "{\n"
        "  \"matches\": [\n"
        "    {\n"
        "      \"date\": \"27/06/2026\",\n"
        "      \"equipe_1\": \"Nouvelle Zelande\",\n"
        "      \"equipe_2\": \"Belgique\",\n"
        "      \"categorie\": \"Temps réglementaire\",\n"
        "      \"type_de_pari\": \"Les deux équipes marquent\",\n"
        "      \"selection\": \"Les deux équipes marquent – Oui\",\n"
        "      \"odds\": 2.32,\n"
        "      \"sport\": \"3\",\n"
        "      \"intitule\": \"Nouvelle Zelande vs Belgique - Les deux équipes marquent\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "- Ne renvoyer aucun texte hors du JSON."
    )

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Voici les données du pronostic à formatter :\n\n{texte_pari}\n\nMessage d'accompagnement : {msg}\n\nRetourne uniquement le JSON."}
            ]
        )
    except Exception as e:
        print(f"❌ Erreur Claude extraire_pari_depuis_texte: {e}")
        raise

    content = response.content[0].text if response.content else None
    if not content:
        raise ValueError(f"Empty or invalid model response: {response}")

    return cleanJson(content)


def extraire_pari_nba_depuis_image(image_path, msg):
    """
    Variante étendue pour plusieurs types de paris (NBA et tennis).

    Les paris supportés :
    - Player Props (NBA)
    - Vainqueur de match (NBA)
    - Tennis Vainqueur (victoire d'un joueur)
    - Handicap de jeu
    - Handicap de set

    Comportement attendu :
    - Pour un "Player Props" : retourner {date, player_name, teams, prop_type, line, over_under, odds, tipster?}
    - Pour un "Vainqueur Match" ou "Tennis Vainqueur" : retourner {date, equipe_1 / player_1, equipe_2 / player_2, category: "Vainqueur Match"|"Tennis Vainqueur", selection: "V1"|"V2", odds, tipster?}
    - Pour un "Handicap Jeu" ou "Handicap Set" : retourner {date, teams/players, category: "Handicap Jeu"|"Handicap Set", handicap_value, selection, odds, tipster?}

    La réponse doit être STRICTEMENT le JSON brut correspondant au pari détecté, sans texte additionnel.
    """
    image_b64 = image_to_base64(image_path)
    nba_system_prompt = (
        "Tu es un agent OCR spécialisé sur les paris sportifs (NBA et Tennis). "
        "Tu dois détecter le type de pari parmi : 'Player Props', 'Vainqueur Match', 'Tennis Vainqueur', 'Handicap Jeu', 'Handicap Set'.\n\n"
        "Pour 'Player Props' : extraire les champs suivants : player_name, teams, prop_type (DOIT être EXACTEMENT l'un des types fournis ci-dessous), line (numérique), over_under ('Over' ou 'Under'), odds, date, tipster (si présent).\n"
        "Pour 'Vainqueur Match' ou 'Tennis Vainqueur' : extraire equipe_1 (ou player_1), equipe_2 (ou player_2), category (\"Vainqueur Match\" ou \"Tennis Vainqueur\"), selection ('V1' ou 'V2'), odds, date, tipster (si présent).\n"
        "Pour 'Handicap Jeu' ou 'Handicap Set' : extraire teams/players, category ('Handicap Jeu' ou 'Handicap Set'), handicap_value (ex: -2, 0), selection (ex: 'Handicap 1 (-2)'), odds, date, tipster (si présent).\n\n"
        "Règles strictes :\n"
        "1. Pour les player props, choisir obligatoirement `prop_type` parmi la liste fournie par config.nba_props_list.\n"
        "2. Ne pas inventer de prop_type ni de category. Si incertain, choisir la catégorie la plus proche et l'indiquer dans le champ 'category'.\n"
        "3. Si le pari correspond à une victoire d'équipe/joueur, utiliser 'Vainqueur Match' ou 'Tennis Vainqueur' et fournir 'selection' comme 'V1' ou 'V2'.\n"
        "4. Pour les handicaps, préciser si c'est 'Handicap Jeu' ou 'Handicap Set' dans 'category' et fournir 'handicap_value'.\n"
        "5. La réponse DOIT être UNIQUEMENT le JSON brut correspondant, rien d'autre.\n\n"
        "Liste de référence des player props :\n"
        f"{stringify_xbet_type_list(config.nba_props_list)}\n\n"
        "Liste des sports et leurs ids :\n"
        "tennis: 2\nfootball: 3\nbasketball: 4\nrugby: 5\nhandball: 8\nice-hockey: 9\n"
        "baseball: 10\ntable-tennis: 11\namerican-football: 12\nvolleyball: 13\nesports: 14\n"
        "cricket: 15\ndarts: 16\nfutsal: 17\nbadminton: 18\nwaterpolo: 19\nsnooker: 20\n"
        "aussie-rules: 21\nufc: 22\nsurf: 23\nski-alpin: 24\nski: 25\n\n"
        "Exemples de JSON attendus :\n"
        "Player Props -> {\"date\":\"25/09/2025\",\"player_name\":\"LeBron James\",\"teams\":\"Lakers - Clippers\",\"prop_type\":\"Points\",\"line\":27.5,\"over_under\":\"Over\",\"odds\":\"1.85\"}\n"
        "Vainqueur Match -> {\"date\":\"25/09/2025\",\"equipe_1\":\"Team A\",\"equipe_2\":\"Team B\",\"category\":\"Vainqueur Match\",\"selection\":\"V1\",\"odds\":\"1.60\"}\n"
        "Handicap -> {\"date\":\"25/09/2025\",\"teams\":\"Player A - Player B\",\"category\":\"Handicap Jeu\",\"handicap_value\":\"-2\",\"selection\":\"Handicap 1 (-2)\",\"odds\":\"1.95\"}\n"
    )
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            system=nba_system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Le fichier s'appelle {image_path} et le message qui l'accompagne est : {msg}. Retourne uniquement le JSON."
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"❌ Erreur Claude extraire_pari_nba_depuis_image: {e}")
        raise

    content = response.content[0].text if response.content else None
    if not content:
        raise ValueError(f"Empty or invalid model response: {response}")

    return cleanJson(content)


def _parse_match_into_teams(match_str):
    """Tente d'extraire deux équipes à partir d'un intitulé de match."""
    if not match_str or not isinstance(match_str, str):
        return None
    s = match_str.strip()
    # sépare sur ' vs ', ' v ', ' - ', '–', '—' en priorité
    parts = None
    for sep in [" vs ", " v ", " vs. ", " - ", " – ", " — ", " vs/ "]:
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if p.strip()]
            if len(parts) == 2:
                return parts[0], parts[1]
    # fallback: tenter séparation par 'contre' ou ' vs ' regex
    m = re.split(r"\bversus\b|\bcontre\b|\\/|:", s, flags=re.I)
    if len(m) >= 2:
        a = m[0].strip()
        b = m[1].strip()
        if a and b:
            return a, b
    return None


def _names_from_api(query, sport_id):
    """Interroge l'API search et renvoie un ensemble de noms possibles (name + nicknames).

    Retourne set() si rien trouvé ou en cas d'erreur.
    """
    try:
        url = f"https://api.auxotracker.p-com.studio/api/sports/{sport_id}/teams/search?search={quote_plus(query)}"
        print(f"🔍 API search URL: {url}")
        r = requests.get(url, timeout=5)
        j = r.json()
        results = j.get('data', []) if isinstance(j, dict) else []
        names = set()
        for item in results:
            name = item.get('name')
            nickname = item.get('nickname')
            if name:
                names.add(unidecode(name).strip().lower())
            if nickname:
                # nicknames peuvent être séparés par des virgules
                for nick in str(nickname).split(','):
                    nick = nick.strip()
                    if nick:
                        names.add(unidecode(nick).strip().lower())
        return names
    except Exception:
        return set()


def compare_match_name(match_name1, match_name2, sport_id):
    """Compare deux intitulés de match en utilisant l'API locale plutôt que l'IA.

    Logique :
    - Extraire deux équipes de chaque intitulé.
    - Pour chaque équipe, interroger l'API `teams/search` et collecter `name` + `nickname`.
    - Normaliser et vérifier si les paires correspondent (ordre ou ordre inverse).
    - Retourne True si correspondance claire, False sinon.
    """
    try:
        parsed1 = _parse_match_into_teams(match_name1)
        parsed2 = _parse_match_into_teams(match_name2)
        if not parsed1 or not parsed2:
            return False

        a1, a2 = parsed1
        b1, b2 = parsed2

        # obtenir ensembles de noms possibles via API
        set_a1 = _names_from_api(a1, sport_id)
        set_a2 = _names_from_api(a2, sport_id)
        set_b1 = _names_from_api(b1, sport_id)
        set_b2 = _names_from_api(b2, sport_id)

        # si aucune donnée API trouvée pour une des équipes, retourner False
        if not set_a1 or not set_a2 or not set_b1 or not set_b2:
            print(f"⚠️ API search: no data found for one of the teams in '{match_name1}' or '{match_name2}'")
            return False

        def norm(s):
            return unidecode(s).strip().lower()

        # ajouter aussi les versions normalisées des libellés extraits
        set_a1.add(norm(a1))
        set_a2.add(norm(a2))
        set_b1.add(norm(b1))
        set_b2.add(norm(b2))

        # vérification ordre identique
        if (set_a1 & set_b1) and (set_a2 & set_b2):
            print(f"✅ Match name comparison: '{match_name1}' vs '{match_name2}' => SAME MATCH (order match)")
            return True
        # vérification ordre inversé
        if (set_a1 & set_b2) and (set_a2 & set_b1):
            print(f"✅ Match name comparison: '{match_name1}' vs '{match_name2}' => SAME MATCH (reverse order match)")
            return True
        print(f"❌ Match name comparison: '{match_name1}' vs '{match_name2}' => DIFFERENT MATCHES")
        return False
    except Exception:
        print(f"❌ Error in compare_match_name API comparison for '{match_name1}' vs '{match_name2}'")
        return False


def compare_prop_name(prop_target, prop_found):
    """Compare deux libellés de prop (ex: 'Points+Assists' vs 'Points + Rebonds')
    Retourne True si l'IA considère qu'ils désignent la même prop, sinon False.
    Répond uniquement par true/false.
    """
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=120,
            system=(
                "Tu es un agent qui compare deux libellés de prop (ex: 'Points+Assists' et 'Points + Rebonds'). "
                "Réponds uniquement par true ou false. Ignore la casse, les accents, les séparateurs et les signes comme +, /, etc. "
                "Considère les équivalences sémantiques (ex: 'Rebounds' == 'Rebonds', 'Assists' == 'Passes').\n\n"
                "IMPORTANT — Correspondance STRICTE : la correspondance doit être exacte sur tous les composants du libellé. "
                "Ne retourne true que si les deux libellés représentent exactement la même prop structurelle et sémantique. "
                "Exemple : 'Points + Assists' n'est PAS égal à 'Points + Assists + Rebonds' (réponds false). "
                "Les correspondances partielles ou sous-ensembles doivent renvoyer false.\n\n"
                "Voici la liste des props possibles (texte brut) :\n"
                "Points\nRebounds\nTirs à trois points réussis\nInterceptions\nTurnovers\n"
                "Points + Rebonds\nPoints + Assists\nPoints + Assists + Rebonds\nAssists + Rebonds\n"
                "Interceptions + Blocages\nPasses décisives\nPoints du premier quart-temps\n"
                "Passes décisives du premier quart-temps\nRebonds du premier quart-temps\n"
                "FT réussis\nFT tentés\nFG réussis\nFG tentés\nTirs à trois points tentés\nFautes personnelles\n\n"
                "Utilise cette liste pour déterminer si les deux libellés correspondent semantiquement à une même prop."
            ),
            messages=[
                {"role": "user", "content": f"Compare ces deux props : '{prop_target}' et '{prop_found}'"}
            ]
        )
    except Exception as e:
        print(f"❌ Erreur Claude compare_prop_name: {e}")
        return False

    response_content = response.content[0].text if response.content else None
    if response_content is None:
        return False
    return response_content.strip().lower() == "true"


def compare_player_name(player_name1, player_name2):
    """Compare deux noms de joueurs et renvoie True si ce sont vraisemblablement la même personne.

    Règles appliquées par l'agent : ignorer la casse, les accents, les séparateurs, les suffixes
    courants (Jr, Sr, III) et les abréviations d'initiales. Répond uniquement par "true" ou "false".
    """
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=60,
            system=(
                "Tu es un agent qui compare deux intitulés de match sportif et dois répondre STRICTEMENT par 'true' ou 'false'.\n"
                "Retourne 'true' si les deux textes correspondent au même match (mêmes équipes), sinon 'false'.\n"
                "Ignore la casse et les accents, considère les abréviations et l'ordre des équipes. Ne fournis aucun autre texte."
            ),
            messages=[
                {"role": "user", "content": f"Compare ces deux joueurs : {player_name1} et {player_name2}"}
            ]
        )
    except Exception as e:
        print(f"❌ Erreur Claude compare_player_name: {e}")
        return False

    response_content = response.content[0].text if response.content else None
    if response_content is None:
        return False
    return response_content.strip().lower() == "true"


def compare_selection(match, selection, selection_list):
    return 'false'
    print(f"pour le match {match} Compare ces deux selections :  {selection} et {selection_list}")
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=500,
            system=(
                "Tu es un agent spécialisé dans la comparaison de sélections de paris sportifs.\n"
                "Ton objectif est de déterminer si une sélection donnée correspond exactement à une liste de sélections possibles.\n"
                "1. Compare la sélection demandée avec les options fournies.\n"
                "2. Ignore la casse, les accents et les espaces supplémentaires.\n"
                "3. Répond strictement par le texte exact de la sélection correspondante, ou \"false\" si aucune ne correspond.\n"
                "4. Ne rajoute aucun autre texte ni explication.\n"
                "5. Règle spéciale — Handicap de sets : choisis la valeur la plus élevée pour le même côté.\n"
                "Retourne le texte exact dans la liste donnée."
            ),
            messages=[
                {"role": "user", "content": f"Pour le match {match} compare {selection} avec les selections suivantes: {selection_list} et retourne la selection de cette liste qui correspond sans texte superflu."}
            ]
        )
    except Exception as e:
        print(f"❌ Erreur Claude compare_selection: {e}")
        return 'false'

    response_content = response.content[0].text if response.content else None
    print(response_content)
    if response_content is None or response_content.strip() == 'false':
        return 'false'
    return response_content.strip()


def fordate(date_str):
    # Convert date format if needed
    return date_str


def submit_bet_to_website(driver, betslist):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select
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
    image_path = os.path.join(project_path, "images.png")

    msg = ""
    if os.path.exists(image_path):
        result = extraire_pari_nba_depuis_image(image_path, msg)
        # Initialize your webdriver here
        # driver = webdriver.Chrome()  # or whatever driver you're using
        # submit_bet_to_website(driver, result)
        print(result)
    else:
        print(f"Erreur: Le fichier image {image_path} n'existe pas.")
