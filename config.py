import datetime
import json
import os
import platform
from typing import Dict, Any, Optional

import requests

# System detection
systeme = platform.system()

SUPPORTED_SYSTEMS = ['Darwin', 'Windows']  # Extraction de constante

system_description = systeme if systeme in SUPPORTED_SYSTEMS else f"Système inconnu : {systeme}"  # Introduction de variable

# Project path initialization
projectPath = os.path.dirname(os.path.abspath(__file__))

# Script configuration
script_num = 0  # Numéro du Script
win = 0  # Nombre de victoire
cote = 3
scriptType = "40A"
localhost = ''
site_url = "https://ca.1xbet.com/fr/live/tennis"
# Score configurations
score_to_start = [
    "00(0)00(0)",
    "00(15)00(0)",
    "00(0)00(15)",
    "00(15)00(15)",
    "00(30)00(15)",
    "00(15)00(30)",
    "00(30)00(0)",
    "00(0)00(30)",
    "0000(0)(0)",
    "00(0)(0)",
    "0000(15)(0)",
    "0000(30)(0)",
    "0000(40)(0)",
    "0000(0)(15)",
    "0000(0)(30)",
    "0000(0)(40)",
    "0000(15)(15)",
    "0000(30)(30)",
    "0000(40)(40)",
    "0000(30)(15)",
    "0000(15)(30)",
    "0000(40)(15)",
    "0000(15)(40)",
    "0000(40)(30)",
    "0000(30)(40)"
]
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
saved_score = False
all_scores = {}
numset = ""
set = ""
gain = 0
global_match_win = 0
netprofit = 0
# File paths
matchlist_file_name = ""
matchlisttodo_file_name = ""
running_file_name = ""

# Game variables
match_list = []  # List des matchs
match_done_key = ""  # Nom du match dans Gsheets
match_found = False  # Match valide trouvé
mise = 0.2
probamini = 0.4
cotemini = 1
cotebase = 1
misemax = 0
perte = 0
win_type = ''
wantwin = 0.2
nb_tour = 1
increment = 0
recup40 = 0
recup30 = 0
rattrape_perte = 0
print_running_text = False
print_match_live_text = False
error = False
devMode = 1
restart_set2 = 0
log_message = ''
newset = 2


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


def init_variable():
    """Initialise les variables globales à partir des données de stratégie"""
    global mise, perte, wantwin, increment, probamini, cotemini, recup40, recup30
    global running_file_name, matchlist_file_name, matchlisttodo_file_name, print_running_text, rattrape_perte
    global print_match_live_text, devMode, match_list, match_done_key, match_found
    global error, cotebase, nb_tour, restart_set2, validated_bet, ligue_name, match_Url, newmatch, all_scores

    match_list = []  # List des matchs
    match_done_key = ""  # Nom du match dans Gsheets
    match_found = False  # Match valide trouvé

    url = f"http://p-com.studio/api/strategy{scriptType}/"
    strategy = getJsonData(url)

    # Initialisation des variables avec valeurs par défaut si strategy est None
    devMode = strategy.get("devmode") == "1" if strategy else False
    error = False

    validated_bet = {}  # Dictionnaire pour stocker les paris validés
    ligue_name = ""
    match_Url = ""
    newmatch = ""
    all_scores = {}

    mise = float(strategy.get("mise", 0)) if strategy else 0
    probamini = float(strategy.get("proba_mini", 0)) if strategy else 0
    cotemini = float(strategy.get("cote_recup", 0)) if strategy else 0
    cotebase = float(strategy.get("cote_base", 0)) if strategy else 0
    nb_tour = float(strategy.get("nb_tour", 0)) if strategy else 0
    restart_set2 = float(strategy.get("restart_set2", 0)) if strategy else 0
    perte = 0
    wantwin = float(strategy.get("wantwin", 0)) if strategy else 0
    increment = float(strategy.get("increment", 0)) if strategy else 0
    recup40 = float(strategy.get("mtt_recup", 0)) if strategy else 0
    recup30 = float(strategy.get("mtt_recup", 0)) if strategy else 0
    rattrape_perte = 0

    # Configuration des chemins de fichiers
    running_file_name = f"{projectPath}/SCRIPTS {scriptType}/running"
    matchlist_file_name = f"{projectPath}/SCRIPTS {scriptType}/matchlist"
    matchlisttodo_file_name = f"{projectPath}/matchlisttodo"


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
import time

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
print(YELLOW)


def log(message, type="", clear=True, indent=0):
    clear = False
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

    if clear:
        # Effacement de la ligne précédente
        log_clear_line()
        # Affichage du nouveau message sur la même ligne
        sys.stdout.write(f"{color}{indent}{message}{RESET}\n")
    else:
        # Affichage du message sur une nouvelle ligne
        sys.stdout.write(f"{color}{indent}{message}{RESET}\n")

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
            sys.stdout.write("clear\n")
    else:
        # Délai pour éviter les problèmes d'affichage
        time.sleep(0.5)
        for _ in range(line_number):
            # Remonte d'une ligne et l'efface
            try:
                sys.stdout.write("\033[F\033[K\r")
                sys.stdout.flush()
            except:
                clear_previous_line_windows()


import ctypes

# Obtenir un handle pour la console de sortie standard
std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)


# Fonction pour effacer la ligne précédente avec l'API Windows
def clear_previous_line_windows():
    # Obtenir la position actuelle du curseur
    csbi = ctypes.create_string_buffer(22)
    res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(std_out_handle, csbi)

    if res:
        from ctypes import Structure, c_short, c_long

        class COORD(Structure):
            _fields_ = [("X", c_short), ("Y", c_short)]

        class SMALL_RECT(Structure):
            _fields_ = [("Left", c_short), ("Top", c_short),
                        ("Right", c_short), ("Bottom", c_short)]

        class CONSOLE_SCREEN_BUFFER_INFO(Structure):
            _fields_ = [("dwSize", COORD),
                        ("dwCursorPosition", COORD),
                        ("wAttributes", c_long),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", COORD)]

        info = CONSOLE_SCREEN_BUFFER_INFO()
        ctypes.windll.kernel32.GetConsoleScreenBufferInfo(std_out_handle, ctypes.byref(info))

        # Déplacer le curseur à la ligne précédente
        new_pos = COORD(0, info.dwCursorPosition.Y - 1)
        ctypes.windll.kernel32.SetConsoleCursorPosition(std_out_handle, new_pos)

        # Effacer la ligne
        chars_written = ctypes.c_long()
        console_size = info.dwSize.X
        ctypes.windll.kernel32.FillConsoleOutputCharacterA(
            std_out_handle, ord(' '), console_size, new_pos, ctypes.byref(chars_written))
        ctypes.windll.kernel32.FillConsoleOutputAttribute(
            std_out_handle, info.wAttributes, console_size, new_pos, ctypes.byref(chars_written))


# Utilisation avec fallback
def clear_previous_line_cross_platform():
    try:
        sys.stdout.write("\033[F\033[K\r")
        sys.stdout.flush()
    except:
        clear_previous_line_windows()
