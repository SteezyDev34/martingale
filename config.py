import datetime
import json
import os
import platform
import sys
from typing import Dict, Any, Optional

import requests

# Import des configurations depuis le module config
from conf import classes, score_to_start, total_want_win, total_want_winset1

__all__ = ['classes', 'score_to_start', 'total_want_win', 'total_want_winset1']
# System detection
systeme = platform.system()

SUPPORTED_SYSTEMS = ['Darwin', 'Windows']  # Extraction de constante

system_description = systeme if systeme in SUPPORTED_SYSTEMS else f"Système inconnu : {systeme}"  # Introduction de variable

# Project path initialization
projectPath = os.path.dirname(os.path.abspath(__file__))
scriptTypeList = ['300', '15A', '30A']
scriptTypeList1 = ['30A']
scriptTypeList2 = ['6P', '4015', '4030']
# scriptTypeList2 = ['4P', '5P', '6P', '40A']
scriptTypeList3 = ['5P', '6P', '40A', 'BREAK']
scriptTypeList4 = ['4015', '4030']
allScriptType = ['030', '300', '15A', '30A', '40A', '4P', '5P', '6P', '4030', '4015', '400', 'BREAK', '1SET']
# Script configuration
script_num = 0  # Numéro du Script
win = 0  # Nombre de victoire
cote = 3
tipster = '1xbet'
scriptType = ""
localhost = ''
api_url = "http://auxobetbot.sc2vagr6376.universe.wf"
site_url = 'https://1xbet.com/fr/live/tennis'
site_line_url = 'https://1xbet.com/fr/line/tennis'
site_type = 'new_site'
match_name = ''


def configure_site_type(use_ca_site=None):
    """
    Configure le type de site et les URLs en fonction du choix utilisateur.
    
    Args:
        use_ca_site (bool, optional): Si True, utilise le site CA. Si False, utilise le site standard.
                                     Si None, demande à l'utilisateur.
    
    Returns:
        str: Le type de site configuré ('new_site' ou 'old_site')
    """
    global site_url, site_line_url, site_type

    # Permettre une configuration non interactive (tests CI, pytest, etc.)
    env_val = os.environ.get("MARTINGALE_USE_CA_SITE")
    if env_val is not None:
        use_ca_site = str(env_val).strip().lower() in ("1", "true", "y", "o", "yes")

    if use_ca_site is None:
        # Si l'entrée standard n'est pas un TTY ou si pytest est détecté, éviter la saisie utilisateur
        if not sys.stdin.isatty() or os.environ.get("PYTEST_CURRENT_TEST"):
            use_ca_site = False
        else:
            wich_site = input("1XBET CA? (Y/N): ")
            use_ca_site = wich_site.upper() in ['Y', 'O']

    if use_ca_site:
        site_url = "https://ca.1xbet.com/fr/live/tennis"
        site_line_url = "https://ca.1xbet.com/fr/line/tennis"
        site_type = 'new_site'
    else:
        site_url = 'https://1xbet.com/fr/live/tennis'
        site_line_url = 'https://1xbet.com/fr/line/tennis'
        site_type = 'old_site'

    return site_type


configure_site_type()

# La configuration des scores est maintenant importée depuis le module config
passed_score = []
# Game state variables
validated_bet = {}  # Dictionnaire pour stocker les paris validés
ligue_name = ""
match_Url = ""
newmatch = ""
proba40A = 0
saved_set = ""
set_actuel = ""
jeu_actuel = ""
score_actuel = False
looking_game = False
placed_game = False
saved_score = False

numset = ""
game_end = False
game_start = False
gain = 0
netprofit = 0
result = False
# File paths
matchlist_file_name = f"{projectPath}/matchlist"
matchlisttodo_file_name = f"{projectPath}/matchlisttodo"
matchlist1set_name = ""
running_file_name = ""
in_stat = False
# Game variables
match_list = []  # List des matchs
match_done_key = ""  # Nom du match dans Gsheets
match_found = False  # Match valide trouvé
mise = 0.2
probamini = 0.1
cotebase = 1
cote_base = 1
misemax = 0
perte = 0
win_type = ''
wantwin = 0.2
nb_tour = 1
increment = 0
mtt_recup = 0

recup30 = 0
rattrape_perte = 0
print_running_text = False
print_match_live_text = False
error = False
devMode = True
restart_set2 = 0
log_message = ''
newset = 2
teams = False
all_scores = {}

# Le dictionnaire classes est maintenant importé depuis le module config
# Importation des types de paris 1xBet depuis le fichier JSON
xbet_types_file = os.path.join(projectPath, 'xbet_types.json')
with open(xbet_types_file, 'r', encoding='utf-8') as f:
    xbet_types_data = json.load(f)

# Préserver la structure originale des données JSON pour une meilleure utilisation
xbet_type_list = xbet_types_data

# Créer également une version avec des sets pour la compatibilité avec l'ancien code si nécessaire
xbet_type_list_sets = {}
for period, bet_types_list in xbet_types_data.items():
    # Créer un ensemble de toutes les sélections pour cette période
    # bet_types_list est une liste de types de paris, pas un dictionnaire
    all_selections = set(bet_types_list)
    xbet_type_list_sets[period] = all_selections
# Initialize dictionaries to track wins per script type
winmatch = {script_type: 0 for script_type in scriptTypeList}
global_match_win = {script_type: 0 for script_type in scriptTypeList}


# Configurations de paris importées depuis config.betting_config


def getJsonData(url: str) -> Optional[Dict[str, Any]]:
    """
    Récupère et parse les données JSON depuis une URL.
    
    Args:
        url: L'URL à partir de laquelle récupérer les données JSON
        
    Returns:
        Un dictionnaire contenant les données JSON ou None en cas d'erreur
    """
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
        except requests.exceptions.RequestException as e:
            print(f"Tentative {attempt + 1}/{max_attempts} - Erreur lors de la récupération des données : {e}")
        except json.JSONDecodeError as e:
            print(f"Tentative {attempt + 1}/{max_attempts} - Erreur lors du parsing du JSON : {e}")

        # Attendre un peu plus longtemps entre chaque tentative
        if attempt < max_attempts - 1:
            import time
            time.sleep(1 * (attempt + 1))

    return None


def saveLog(txt):
    """
    Enregistre un message dans un fichier de log et l'affiche éventuellement dans la console.
    
    Args:
        txt: Le texte à enregistrer
        prntxt: 1 pour afficher le texte, 0 pour ne pas l'afficher
        matchname: Le nom du match concerné par le log
    """
    # Obtenir la date et l'heure actuelles
    date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
    heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")

    # Créer le nom de fichier avec la date
    nom_de_base = f"{projectPath}/Logs/logScript{scriptType}-{script_num}-{newmatch}"
    nom_du_fichier = f"{nom_de_base}-{date_actuelle}.txt"

    # Créer le répertoire s'il n'existe pas
    nom_du_repertoire = os.path.dirname(nom_du_fichier)
    if nom_du_repertoire and not os.path.exists(nom_du_repertoire):
        os.makedirs(nom_du_repertoire)

    try:
        # Ouvrir le fichier en mode ajout
        with open(nom_du_fichier, 'a+') as fichier:
            # Vérifier si le fichier est non vide
            fichier.seek(0)
            contenu = fichier.read()

            # Ajouter un saut de ligne si le fichier n'est pas vide
            if contenu:
                fichier.write('\n')

            # Écrire le texte à la fin du fichier
            fichier.write(f"{heure_actuelle} : {txt}")
    except Exception as e:
        print(f'Erreur de log: {e}')


import colorama
import codecs
import sys
import os

# Forcer l'encodage en UTF-8 pour stdout
print(sys.platform)
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="backslashreplace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="backslashreplace")

# Initialisation de colorama pour le support des couleurs sur Windows
# Le terminal natif de Windows ne prend pas en charge les codes ANSI par défaut
# Colorama permet d'activer cette fonctionnalité sur Windows
colorama.init()

# Définition des couleurs ANSI avec colorama pour la compatibilité Windows
RESET = colorama.Style.RESET_ALL  # Réinitialisation des styles
BOLD = colorama.Style.BRIGHT  # Texte en gras
YELLOW = colorama.Fore.YELLOW  # Texte jaune
GREEN = colorama.Fore.GREEN  # Texte vert
BLUE = colorama.Fore.BLUE  # Texte bleu
CYAN = colorama.Fore.CYAN  # Texte cyan
RED = colorama.Fore.RED  # Texte rouge
PURPLE = colorama.Fore.MAGENTA  # Texte magenta
BGPURPLE = colorama.Back.MAGENTA  # Fond magenta
BGCYAN = colorama.Back.CYAN  # Fond cyan
BGBLUE = colorama.Back.BLUE  # Fond bleu
BGRESET = colorama.Back.BLACK  # Fond noir (réinitialisation)


def log(message, type="", clear=True, indent=0):
    """
    Affiche un message dans le terminal tout en effaçant dynamiquement la ligne précédente si demandé.

    :param message: Le texte du nouveau message.
    :param clear: Booléen indiquant si la ligne précédente doit être effacée.
    :return: La longueur du message actuel, pour l'utiliser dans l'appel suivant.
    """
    global log_message
    # Détermination de la couleur en fonction du type de message
    if type == "info":
        color = BOLD
    elif type == "title":
        color = CYAN
    elif type == "success":
        color = GREEN
    elif type == "warning":
        color = YELLOW
    elif type == "error":
        color = RED
    else:
        color = RESET  # Pas de couleur par défaut

    # Gestion de l'indentation
    indent = "    " * indent if indent > 0 else ""
    sys.stdout.write(f"{color}{scriptType}__{indent}{message}{RESET}\n")

    if clear:
        # Effacement de la ligne précédente
        # Affichage du nouveau message sur la même ligne
        log_clear_line()

    # Force l'écriture du buffer
    sys.stdout.flush()
    # Mise à jour du message global
    log_message = message
    saveLog(message)


def log_clear_line(line_number=1):
    """
    Efface un certain nombre de lignes dans le terminal.

    :param line_number: Nombre de lignes à effacer (par défaut 1)
    """
    if os.getenv('PYCHARM_HOSTED') == '1':  # Si exécuté dans PyCharm
        # Simple écriture de lignes vides pour PyCharm
        for _ in range(line_number):
            # sys.stdout.write("clear\n")
            continue
    else:
        # Délai pour éviter les problèmes d'affichage
        for _ in range(line_number):
            # Remonte d'une ligne et l'efface
            # sys.stdout.write("clear\n")
            pass
            # sys.stdout.write("\033[F\033[K\r")
            # sys.stdout.flush()


win_session = False
win = False
min_unit = float(0.00000001)
unit = min_unit
old_unit = False
perte = float(0.00000000)
side = 'over'
old_side = 'under'
old_result = False
xpath_over = '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[4]/div[2]/button'
xpath_under = '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[4]/div[1]/button'
