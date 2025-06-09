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
scriptTypeList = ['030', '300', '30A']
scriptTypeList2 = ['4P', '5P', '6P', '40A']
scriptTypeList3 = ['400', '4015', '4030']
# Script configuration
script_num = 0  # Numéro du Script
win = 0  # Nombre de victoire
cote = 3
scriptType = "40A"
localhost = ''
site_url = "https://ca.1xbet.com/fr/live/tennis"
# Score configurations
score_to_start = [
    "01(0)00(0)",
    "00(0)01(0)",
    "01(0)01(0)",
    "02(0)00(0)",
    "00(0)02(0)",
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
all_scores = {}
numset = ""
set = ""
game_end = False
game_start = False
gain = 0
netprofit = 0
result = False
# File paths
matchlist_file_name = ""
matchlisttodo_file_name = f"{projectPath}/matchlisttodo"
matchlist1set_name = ""
running_file_name = ""
in_stat = False
# Game variables
match_list = []  # List des matchs
match_done_key = ""  # Nom du match dans Gsheets
match_found = False  # Match valide trouvé
mise = 0.2
probamini = 0.4
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
devMode = 1
restart_set2 = 0
log_message = ''
newset = 2
teams = False

# Initialize dictionaries to track wins per script type
winmatch = {script_type: 0 for script_type in scriptTypeList}
global_match_win = {script_type: 0 for script_type in scriptTypeList}

total_want_win = 0.2


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
    """Initialize global variables from strategy data"""
    global mise, perte, wantwin, increment, probamini
    global running_file_name, matchlist_file_name, matchlisttodo_file_name, print_running_text, rattrape_perte
    global print_match_live_text, devMode, gain, netprofit, perte, placed_game, looking_game, saved_score
    global error, cotebase, nb_tour, restart_set2, validated_bet, win_type, mtt_recup, result, matchlist1set_name
    config_global = ScriptConfig(scriptType)

    # Initialize variables from config
    devMode = config_global.get("devmode")
    error = config_global.get("error")
    validated_bet = config_global.get("validated_bet")

    # On suppose que chacune de ces variables a déjà une valeur par défaut
    # définie avant ce bloc. On ne modifie la variable que si la clé existe
    # dans config_global et que sa valeur n’est pas None.

    # Game settings
    val = config_global.get("cote_base")
    if val is not None:
        cotebase = float(val)
    val = config_global.get("mise")
    if val is not None:
        mise = float(val)

    val = config_global.get("nb_tour")
    if val is not None:
        nb_tour = int(val)

    val = config_global.get("proba_mini")
    if val is not None:
        probamini = float(val)

    # Game state
    val = config_global.get("gain")
    if val is not None:
        gain = float(val)

    val = config_global.get("increment")
    if val is not None:
        increment = float(val)

    val = config_global.get("looking_game")
    if val is not None:
        looking_game = int(val)

    val = config_global.get("netprofit")
    if val is not None:
        netprofit = float(val)

    val = config_global.get("perte")
    if val is not None:
        perte = float(val)

    val = config_global.get("placed_game")
    if val is not None:
        placed_game = int(val)

    val = config_global.get("rattrape_perte")
    if val is not None:
        rattrape_perte = int(val)

    val = config_global.get("restart_set2")
    if val is not None:
        restart_set2 = int(val)

    val = config_global.get("saved_score")
    if val is not None:
        saved_score = val

    val = config_global.get("validated_bet")
    if val is not None:
        validated_bet = val

    val = config_global.get("wantwin")
    if val is not None:
        wantwin = float(val)

    val = config_global.get("win_type")
    if val is not None:
        win_type = val

    val = config_global.get("mtt_recup")
    if val is not None:
        mtt_recup = float(val)

    val = config_global.get("result")
    if val is not None:
        result = val

    # Display settings
    print_match_live_text = config_global.get("print_match_live_text")
    print_running_text = config_global.get("print_running_text")

    # File paths configuration
    running_file_name = f"{projectPath}/SCRIPTS {scriptType}/running"
    matchlist_file_name = f"{projectPath}/SCRIPTS {scriptType}/matchlist"
    matchlisttodo_file_name = f"{projectPath}/matchlisttodo"
    matchlist1set_name = f"{projectPath}/matchlist1set"


def save_variables():
    """Initialize global variables from strategy data"""
    global mise, perte, wantwin, increment, probamini
    global running_file_name, matchlist_file_name, matchlisttodo_file_name, print_running_text, rattrape_perte
    global print_match_live_text, devMode, gain, netprofit, perte, placed_game, looking_game, saved_score
    global error, cotebase, nb_tour, restart_set2, validated_bet, win_type, mtt_recup, result, matchlist1set_name

    """Save current variables state back to config"""
    config_global = ScriptConfig(scriptType)

    # Save game settings
    config_global.set("cote_base", cotebase)
    config_global.set("mise", mise)
    config_global.set("nb_tour", nb_tour)
    config_global.set("proba_mini", probamini)

    # Save game state
    config_global.set("gain", gain)
    config_global.set("increment", increment)
    config_global.set("looking_game", looking_game)
    config_global.set("netprofit", netprofit)
    config_global.set("perte", perte)
    config_global.set("placed_game", placed_game)
    config_global.set("rattrape_perte", rattrape_perte)
    config_global.set("restart_set2", restart_set2)
    config_global.set("saved_score", saved_score)
    config_global.set("validated_bet", validated_bet)
    config_global.set("wantwin", wantwin)
    config_global.set("win_type", win_type)
    config_global.set("mtt_recup", mtt_recup)
    config_global.set("result", result)

    # Save display settings
    config_global.set("print_match_live_text", print_match_live_text)
    config_global.set("print_running_text", print_running_text)
    matchlisttodo_file_name = f"{projectPath}/matchlisttodo"


def switchScript(newScriptType):
    global scriptType
    save_variables()
    scriptType = newScriptType
    init_variable()


class ScriptConfig:
    _instances = {}  # Dictionnaire pour stocker les instances par type de script

    def __init__(self, script_type):
        self.script_type = script_type
        # Récupérer l'instance existante si elle existe, sinon en créer une nouvelle
        if script_type in ScriptConfig._instances:
            self.variables = ScriptConfig._instances[script_type].variables
        else:
            self.variables = self._init_variables()
            ScriptConfig._instances[script_type] = self

    def _init_variables(self):

        url = f"http://p-com.studio/api/strategy{self.script_type}/"
        strategy = getJsonData(url)
        print('init scriptconfig')
        # Configuration par défaut selon le type de script
        default_configs = {
        }
        config = default_configs.get(self.script_type, {})
        if strategy:
            for key, strat in strategy.items():
                config[key] = strat
            config['error'] = False
            config['validated_bet'] = {}

            config['print_running_text'] = False
            config['print_match_live_text'] = False
            config['win_type'] = ''
            config['netprofit'] = 0
            config['gain'] = 0
            config['looking_game'] = False
            config['placed_game'] = False
            config['saved_score'] = False
            config['rattrape_perte'] = False
            config['result'] = False

        return config

    def get(self, var_name):
        """Récupère une variable par son nom"""
        return self.variables.get(var_name)

    def set(self, var_name, value):
        """Définit une variable"""
        self.variables[var_name] = value

    def reset(self):
        """Force la réinitialisation de la configuration"""
        self.variables = self._init_variables()
        ScriptConfig._instances[self.script_type] = self
        return self


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
