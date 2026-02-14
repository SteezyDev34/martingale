import datetime
import json
import os
import platform
import time
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
scriptTypeList = ['015', '30A']
scriptTypeList1 = ['6P', '5P', '40A' ]
scriptTypeList2 = ['BREAK']
scriptTypeList3 = ['BREAK']
scriptTypeList4 = ['BREAK', '4015', '4030']
allScriptType = ['150', '015', '030', '300', '15A', '30A', '40A', '4P', '5P', '6P', '4030', '4015', '400', 'BREAK',
                 '1SET']
# Script configuration
script_num = 0  # Numéro du Script
win = 0  # Nombre de victoire
cote = 3
tipster = '1xbet'
scriptType = ""
localhost = ''
api_url = "http://auxobetbot.sc2vagr6376.universe.wf"
site_url = "https://ca.1xbet.com/fr/live/tennis?platform_type=desktop"
site_line_url = "https://ca.1xbet.com/fr/line/tennis?platform_type=desktop"
site_type = 'mobile_site'  # new_site, mobile_site, old_site
match_name = ''
nb_log_lines = 0
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
mtt_recup = 0.2

recup30 = 0
rattrape_perte = 1  # ne pas changer
print_running_text = False
print_match_live_text = False
error = False
devMode = True
restart_set2 = 0
log_message = ''
newset = 2
teams = False
all_scores = {}
# Récupération du dernier classement depuis le fichier
try:
    with open(os.path.join(projectPath, 'DataFiles', 'last_classement.txt'), 'r') as f:
        last_classement = f.read().strip()
except FileNotFoundError:
    last_classement = 'test'  # Valeur par défaut si le fichier n'existe pas
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
# Net profit per script type is tracked as float values
global_match_win: Dict[str, float] = {script_type: 0.0 for script_type in scriptTypeList}


# Configurations de paris importées depuis config.betting_config


def getJsonData(url: str) -> Optional[Dict[str, Any]]:
    """
    Récupère et parse les données JSON depuis une URL.
    
    Args:
        url: L'URL à partir de laquelle récupérer les données JSON
        
    Returns:
        Un dictionnaire contenant les données JSON ou None en cas d'erreur
    """
    max_attempts = 1
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
        except requests.exceptions.RequestException as e:
            log(f" Erreur lors de la récupération des données", 'warning')
        except json.JSONDecodeError:
            log(f" Erreur lors du parsing du JSON", 'warning')
        # Attendre un peu plus longtemps entre chaque tentative
        if attempt < max_attempts - 1:
            import time
            time.sleep(1 * (attempt + 1))

    return None


def init_variable():
    """Initialize global variables from strategy data"""
    global mise, perte, wantwin, increment, probamini
    global running_file_name, matchlisttodo_file_name, print_running_text, rattrape_perte
    global print_match_live_text, gain, netprofit, perte, placed_game, looking_game, saved_score
    global error, cotebase, nb_tour, restart_set2, validated_bet, win_type, mtt_recup, result, matchlist1set_name
    config_global = ScriptConfig(scriptType)

    # Initialize variables from config
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
    matchlisttodo_file_name = f"{projectPath}/matchlisttodo"


def save_variables():
    """Initialize global variables from strategy data"""
    global mise, perte, wantwin, increment, probamini
    global running_file_name, matchlisttodo_file_name, print_running_text, rattrape_perte
    global print_match_live_text, gain, netprofit, perte, placed_game, looking_game, saved_score
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

        url = f"{api_url}/strategy{self.script_type}/"
        strategy = getJsonData(url)
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
            config['rattrape_perte'] = 1
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
        # Gestion robuste des interruptions clavier et des erreurs d'encodage
        try:
            # Vérifier d'abord si le fichier existe et s'il est lisible
            if os.path.exists(nom_du_fichier):
                try:
                    # Test de lecture pour détecter les problèmes d'encodage
                    with open(nom_du_fichier, 'r', encoding='utf-8') as test_file:
                        test_file.seek(0, 2)  # Aller à la fin pour tester
                except UnicodeDecodeError:
                    # Fichier corrompu, le sauvegarder et en créer un nouveau
                    backup_file = f"{nom_du_fichier}.corrupted.{int(time.time())}"
                    print(f"⚠️ Fichier de log corrompu, sauvegarde vers: {backup_file}")
                    try:
                        os.rename(nom_du_fichier, backup_file)
                    except:
                        # Si on ne peut pas renommer, supprimer le fichier corrompu
                        os.remove(nom_du_fichier)
                        print(f"❌ Fichier corrompu supprimé: {nom_du_fichier}")

            # Ouvrir le fichier en mode ajout avec gestion d'erreur renforcée
            with open(nom_du_fichier, 'a+', encoding='utf-8', buffering=1, errors='replace') as fichier:
                # Méthode plus efficace - éviter de lire tout le fichier
                fichier.seek(0, 2)  # Aller à la fin du fichier
                position = fichier.tell()

                # Ajouter un saut de ligne si le fichier n'est pas vide
                if position > 0:
                    try:
                        # Vérifier le dernier caractère pour éviter les doubles sauts de ligne
                        fichier.seek(position - 1)
                        dernier_char = fichier.read(1)
                        fichier.seek(0, 2)  # Retourner à la fin

                        if dernier_char and dernier_char != '\n':
                            fichier.write('\n')
                    except:
                        # En cas d'erreur de lecture, simplement ajouter une ligne
                        fichier.write('\n')

                # Nettoyer le texte pour éviter les caractères problématiques
                txt_clean = str(txt).encode('utf-8', errors='replace').decode('utf-8')

                # Écrire le texte à la fin du fichier
                fichier.write(f"{heure_actuelle} : {txt_clean}")
                fichier.flush()  # Forcer l'écriture immédiate

        except KeyboardInterrupt:
            # Gestion spécifique de Ctrl+C - essayer de sauvegarder quand même
            print(f"⚠️ Interruption détectée lors de l'écriture du log: {txt[:50]}...")
            try:
                # Tentative rapide de sauvegarde avec nettoyage du texte
                txt_clean = str(txt).encode('utf-8', errors='replace').decode('utf-8')
                with open(nom_du_fichier, 'a', encoding='utf-8', errors='replace') as fichier_urgence:
                    fichier_urgence.write(f"\n{heure_actuelle} : [INTERROMPU] {txt_clean}")
            except:
                # Si même ça échoue, au moins l'afficher
                print(f"❌ Impossible de sauvegarder: {txt}")
            raise  # Re-lancer l'interruption

    except Exception as e:
        error_msg = str(e)
        print(f'❌ Erreur de log: {error_msg}')

        # Essayer une sauvegarde d'urgence avec un nom de fichier alternatif
        try:
            emergency_file = f"{projectPath}/Logs/emergency_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            os.makedirs(os.path.dirname(emergency_file), exist_ok=True)

            txt_clean = str(txt).encode('ascii', errors='replace').decode('ascii')
            with open(emergency_file, 'w', encoding='ascii', errors='replace') as emergency:
                emergency.write(f"{heure_actuelle} : [ERREUR_LOG] {txt_clean}\n")
                emergency.write(f"Erreur originale: {error_msg}\n")

            print(f"💾 Log de secours créé: {emergency_file}")

        except Exception as emergency_error:
            print(f"❌ Impossible de créer un log de secours: {emergency_error}")
            # Dernière tentative: afficher dans la console seulement
            print(f"LOG PERDU: {heure_actuelle} - {txt}")


import colorama
import codecs
import sys
import os

# Forcer l'encodage en UTF-8 pour stdout
try:
    # Si l'encodage du stdout n'est pas UTF-8, remplacer l'écrivain
    current_enc = getattr(sys.stdout, 'encoding', None)
    if not current_enc or current_enc.lower() != 'utf-8':
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
except Exception:
    # Ne pas faire échouer le démarrage si on ne peut pas remplacer stdout/stderr
    pass

# Initialisation de colorama pour le support des couleurs sur Windows
# Le terminal natif de Windows ne prend pas en charge les codes ANSI par défaut
# Colorama permet d'activer cette fonctionnalité sur Windows
colorama.init()

# Définition des couleurs ANSI avec colorama pour la compatibilité Windows
RESET = colorama.Style.RESET_ALL  # Réinitialisation des styles
WHITE = colorama.Fore.WHITE
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


def log(message, type="", clear=True, indent=0, show_script_type=True):
    """
    Affiche un message dans le terminal tout en effaçant dynamiquement la ligne précédente si demandé.

    :param message: Le texte du nouveau message.
    :param clear: Booléen indiquant si la ligne précédente doit être effacée.
    :return: La longueur du message actuel, pour l'utiliser dans l'appel suivant.
    """
    global log_message
    # Détermination de la couleur en fonction du type de message
    if type == "info":
        color = WHITE
    elif type == "title":
        color = CYAN
    elif type == "success":
        color = GREEN
    elif type == "warning":
        color = YELLOW
    elif type == "error":
        color = RED
    elif type == "purple":
        color = PURPLE
    elif type == "bgpurple":
        color = BGPURPLE
    elif type == "bgcyan":
        color = BGCYAN
    elif type == "bgblue":
        color = BGBLUE
    elif type == "bgreset":
        color = BGRESET
    else:
        color = RESET  # Pas de couleur par défaut

    # Gestion de l'indentation
    indent = "    " * indent if indent > 0 else ""
    s = ''
    if show_script_type:
        s = scriptType
    sys.stdout.write(f"{color}{s} {indent}{message}{RESET}\n")

    if clear:
        # Effacement de la ligne précédente
        # Affichage du nouveau message sur la même ligne
        time.sleep(0.3)
        log_clear_line()

    # Force l'écriture du buffer
    sys.stdout.flush()
    # Mise à jour du message global
    log_message = message

    # Sauvegarde protégée contre les interruptions
    try:
        saveLog(message)
    except:
        pass  # Si même ça échoue, on abandonne silencieusement


def log_clear_line(line_number=1):
    """
    Efface un certain nombre de lignes dans le terminal.

    :param line_number: Nombre de lignes à effacer (par défaut 1)
    """
    if os.getenv('PYCHARM_HOSTED') == '1':  # Si exécuté dans PyCharm
        # Simple écriture de lignes vides pour PyCharm
        for _ in range(line_number):
            sys.stdout.write("clear\n")
            continue
    else:
        # Délai pour éviter les problèmes d'affichage
        for _ in range(line_number):
            if not devMode:
                sys.stdout.write("\x1b[1A\x1b[2K\r")
            # Monte d’une ligne et efface-la entièrement

        sys.stdout.flush()


win_session = False
win = False
# min unit of lucky games is 0.00000001 with 7x0
min_unit = float(0.00000002)
unit = min_unit
old_unit = False
perte = float(0.00000000)
side = 'over'
old_side = 'under'
old_result = False
xpath_over = '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[4]/div[2]/button'
xpath_under = '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[4]/div[1]/button'


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

    if use_ca_site is None:
        wich_site = input("1XBET CA? (Y/N): ")
        use_ca_site = wich_site.upper() in ['Y', 'O']
        log_clear_line(1)

    if use_ca_site:
        site_url = "https://ca.1xbet.com/fr/live/tennis"
        site_line_url = "https://ca.1xbet.com/fr/line/tennis"
        site_type = 'new_site'
    else:
        site_url = 'https://1xbet.com/fr/live/tennis'
        site_line_url = 'https://1xbet.com/fr/line/tennis'
        site_type = 'old_site'

    log("-" * 60, "info", False)
    log(f"SITE CONFIGURÉ: {site_type.upper()} - {site_url}", "info", False)
    log("-" * 60, "info", False)
    return site_type


if systeme == 'Windows':
    import psutil


    def is_chrome_running_with_port(port):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any(f'--remote-debugging-port={port}' in arg for arg in cmdline):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
