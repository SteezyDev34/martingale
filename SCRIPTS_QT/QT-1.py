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
config.localhost = 43151
from ChromeDriver.SetDriver import get_script_driver

num_fenetre = 6
time.sleep((num_fenetre - 1) * 3)  # Attendre un peu pour s'assurer que la fenêtre est prête

driver = get_script_driver(num_fenetre)
# Chargement des fonctions
from Functions import Functions_QT
from Functions.GetJsonData import DispatchPerte

while (config.win < 100):
    config.init_variable()

    tour = 0
    try:
        while tour < config.nb_tour:
            tour += 1
            Functions_QT.all_script(driver)
    except Exception as e:
        print(f"ERROR SCRIPT : {e}")
    if config.perte > 0:
        DispatchPerte()
    try:
        driver.get('https://1xbet.com/fr/live/basketball/')
    except:
        continue
print('TOTAL WIN : ' + str(config.win))
