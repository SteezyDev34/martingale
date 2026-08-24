import os
import subprocess
import sys
import time

# Récupérer le chemin absolu du fichier actuel
current_file_path = os.path.abspath(__file__)

# Récupérer le dossier parent du fichier actuel
parent_directory = os.path.dirname(current_file_path)
# ajouter un autre niveau parent si nécessaire
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)
if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
    # Simple écriture de lignes vides pour PyCharm

    # Vérification de l'environnement
    import VenvDependencyManager

    VenvDependencyManager.main()
from art import *

# Chargement des variables globales
import config

# Récupérer le nom du script
# Nom du fichier
file_name = os.path.basename(__file__)  # ou directement '40-1.py' pour l'exemple
# Séparer le nom du fichier et l'extension
name_part = os.path.splitext(file_name)[0]
# Séparer les parties du nom
parts = name_part.split('-')
if len(parts) > 1:
    config.scriptType = parts[0]  # Suppose que le type est avant le tiret
    config.script_num = int(parts[1])  # Suppose que le numéro est avant le tiret
    localhost = str(config.scriptType) + str(config.script_num)
    config.localhost = ''.join(caractere for caractere in localhost if caractere.isdigit())
    if int(config.localhost) < 1024:
        config.localhost = 1024 + int(config.localhost)
    # Demander confirmation à l'utilisateur
    # Le lancement de Chrome est maintenant géré dans SetDriver.py
    config.log_clear_line(3)

    print(f"{config.PURPLE}{text2art(f'Start martingal {config.scriptType} {config.script_num}')}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions
# Chargement de Chrome driver
from websocket_server import start_bridge

start_bridge(wait_timeout=0)
driver = None
from Functions import Functions_431a
from Functions.GetJsonData import DispatchPerte
from Functions.ScriptRechercheDeMatch import classementeDeMatch, newclassementeDeMatch
config.in_stat = True
config.scriptTypeList = config.scriptTypeList
for i in config.scriptTypeList:
    config.ScriptConfig(i)
config.winmatch = {script_type: 0 for script_type in config.scriptTypeList}
config.global_match_win = {script_type: 0 for script_type in config.scriptTypeList}
while (config.win < 100):
    try:
        Functions_431a.all_script(driver)
    except Exception as e:
        # Récupérer les informations détaillées de l'erreur (fichier, ligne, fonction)
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            last_frame = tb[-1]
            fichier = last_frame.filename
            ligne = last_frame.lineno
            fonction = last_frame.name
            config.log(f"ERROR SCRIPT : {e} | Fichier: {fichier} | Ligne: {ligne} | Fonction: {fonction}", 'error', False)
            config.log(f"Traceback complet:\n{traceback.format_exc()}", 'error', False)
        else:
            config.log(f"ERROR SCRIPT : {e}", 'error', False)
    else:
        if config.perte > 0:
            DispatchPerte()
        for i in config.scriptTypeList:
            config.switchScript('4315A')
            config.ScriptConfig(i).reset()
            config.init_variable()
            config.switchScript(i)
            DispatchPerte()
            config.global_match_win[i] = 0  # Initialize win counter for script type
            config.winmatch[i] = 0  # Initialize match counter for script type
            sucess = False
        while not sucess:
            try:
                from websocket_server import bridge
                if bridge.connected:
                    bridge.navigate(config.site_url)
                elif driver:
                    driver.get(config.site_url)
            except:
                continue
            else:
                sucess = True

print('TOTAL WIN : ' + str(config.win))
