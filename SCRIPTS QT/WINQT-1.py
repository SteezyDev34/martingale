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
# Vérification de l'environnement
if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
    import VenvDependencyManager

    VenvDependencyManager.main()

# Chargement des variables globales
import config

file_name = os.path.basename(__file__)  # ou directement '40-1.py' pour l'exemple
# Séparer le nom du fichier et l'extension
name_part = os.path.splitext(file_name)[0]
# Séparer les parties du nom

config.localhost = 43151
command = f'open -na "Google Chrome" --args --remote-debugging-port={config.localhost} --user-data-dir="$HOME/ChromeDebugProfile{config.localhost}"'

print(command)

from ChromeDriver.SetDriver import get_script_driver

num_fenetre = 1
time.sleep((num_fenetre - 1) * 3)  # Attendre un peu pour s'assurer que la fenêtre est prête

driver = get_script_driver(num_fenetre)
from Functions import Functions_QT
from Functions.GetJsonData import DispatchPerte

config.init_variable()

for i in config.scriptTypeList:
    config.ScriptConfig(i)
while (config.win < 100):
    tour = 0
    try:
        Functions_QT.all_script(driver)
    except Exception as e:
        # Récupérer les informations détaillées de l'erreur (fichier, ligne, fonction)
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            last_frame = tb[-1]
            fichier = last_frame.filename
            ligne = last_frame.lineno
            fonction = last_frame.name
            config.log(f"ERROR SCRIPT : {e} | Fichier: {fichier} | Ligne: {ligne} | Fonction: {fonction}", 'error',
                       False)
            config.log(f"Traceback complet:\n{traceback.format_exc()}", 'error', False)
        else:
            config.log(f"ERROR SCRIPT : {e}", 'error', False)

    else:
        if config.perte > 0:
            DispatchPerte()
        for i in config.scriptTypeList:
            config.switchScript('QT')
            config.ScriptConfig(i).reset()
        sucess = False
        while not sucess:
            try:
                print(config.site_url)
                driver.get(config.site_url)
            except:
                continue
            else:
                print("success", sucess)
                sucess = True

print('TOTAL WIN : ' + str(config.win))
