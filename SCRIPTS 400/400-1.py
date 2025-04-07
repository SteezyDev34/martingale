import os
import sys

# Récupérer le chemin absolu du fichier actuel
current_file_path = os.path.abspath(__file__)

# Récupérer le dossier parent du fichier actuel
parent_directory = os.path.dirname(current_file_path)
# ajouter un autre niveau parent si nécessaire
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)
# Vérification de l'environnement
import VenvDependencyManager

VenvDependencyManager.main()
from art import *

# Chargement des variables globales
import config
# Chargement de Chrome driver
from ChromeDriver.SetDriver6 import driver

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
    print(f'{config.PURPLE}' + text2art(
        f"Start martingal {config.scriptType} {config.script_num}"))  # Crée un texte en art ASCII
    # sys.stdout.write(f"\rSCRIPT TYPE : {config.scriptType}")
    # sys.stdout.write(f"\rSCRIPT NUM : {config.script_num}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions

from Functions import Functions_400
from Functions.GetJsonData import DispatchPerte

while (config.win < 100):
    config.init_variable()
    try:
        Functions_400.all_script(driver)
    except Exception as e:
        config.log(f"ERROR SCRIPT : {e}", 'error', False)
    else:
        if config.perte > 0:
            DispatchPerte()
print('TOTAL WIN : ' + str(config.win))
