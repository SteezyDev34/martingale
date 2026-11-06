import os
import sys
import time
import traceback

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
from websocket_server import start_bridge

# Port dédié (pas le 9999 par défaut) -- sans ça, 15V1 et 15V2 (et une
# session debug_classement_check.py en parallèle) entraient en collision de
# bind sur le même port 9999, empêchant l'extension de s'y connecter et
# faisant retomber tout le flux sur Selenium en silence (constaté le
# 2026-11-02, cf. WS_PORTS dans chrome_extension/service_worker.js).
WS_PORT = 10104  # port dedie a ce script - cf. WS_PORTS dans chrome_extension/service_worker.js

start_bridge(wait_timeout=0, port=WS_PORT)
# Plus de fenêtre Selenium ouverte systématiquement au démarrage (get_script_driver) --
# le reste du flux (ValidationDuParis, AfficherParis, GetBetOld, etc.) vérifie déjà
# bridge_active() partout et ne touche jamais à `driver` tant que le bridge répond,
# aligné sur le pattern déjà en place côté 1530A/4P6P (demandé le 2026-11-06, la
# fenêtre Selenium qui s'ouvrait sans jamais servir ne se justifiait plus).
driver = None
from Functions import Functions_15V1
from Functions.GetJsonData import DispatchPerte
from Functions.ScriptRechercheDeMatch import classementeDeMatch, newclassementeDeMatch

config.in_stat = True
# Détermine le filtre appliqué par _load_dynamic_scripttypes (ScriptRechercheDeMatch.py)
# quand rechercheDeMatch() charge les scriptTypes calculés au classement pour un
# match : seul '15V1' (favori du match, cf. compute_script_types_from_match_data)
# sera retenu pour ce process (2026-10-28).
config.bot_family = '15V1'
config.scriptTypeList = config.scriptTypeList
for i in config.scriptTypeList:
    config.ScriptConfig(i)
config.winmatch = {script_type: 0 for script_type in config.scriptTypeList}
config.global_match_win = {script_type: 0 for script_type in config.scriptTypeList}
while (config.win < 100):
    try:
        Functions_15V1.all_script(driver)
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
            config.switchScript(i)
            config.ScriptConfig(i).reset()
            DispatchPerte()
            # Filet de sécurité : si le match s'est terminé (ou le bot a été
            # interrompu) avant que ce scriptType atteigne son objectif de gain,
            # Functions_15V1.py n'a jamais appelé finalize_match -- sans ça, les
            # jeux déjà accumulés resteraient collés au prochain match pour ce
            # même scriptType (martingale_legs n'est pas scopé par match, cf.
            # MartingaleSequence.py, demandé le 2026-11-06). No-op si déjà vidé
            # (cas normal : objectif atteint, déjà envoyé plus haut).
            from Functions.MartingaleSequence import finalize_match
            finalize_match(i, config.global_match_win.get(i, 0))
            config.init_variable()
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
