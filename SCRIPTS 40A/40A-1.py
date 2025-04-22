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
    localhost = '7' + str(config.scriptType) + str(config.script_num)
    config.localhost = ''.join(caractere for caractere in localhost if caractere.isdigit())
    print(config.localhost)
    # Demander confirmation à l'utilisateur
    if config.systeme == 'Windows':
        command = f'start chrome --remote-debugging-port={config.localhost} --user-data-dir="{project_directory}\\ChromeDebugProfile{config.localhost}"'
    else:
        command = f'open -na "Google Chrome" --args --remote-debugging-port={config.localhost} --user-data-dir="$HOME/ChromeDebugProfile{config.localhost}"'

    confirmation = input(f"Avez-vous exécuté la commande \n{command}\n? (Y/N): ")

    if confirmation.upper() != 'Y' and confirmation.upper() != 'y' and confirmation.upper() != 'O' and confirmation.upper() != 'o':
        print("Programme arrêté par l'utilisateur.")
        sys.exit(0)  # Arrêter le programme

    print(f'{config.PURPLE}' + text2art(
        f"Start martingal {config.scriptType} {config.script_num}"))  # Crée un texte en art ASCII
    # sys.stdout.write(f"\rSCRIPT TYPE : {config.scriptType}")
    # sys.stdout.write(f"\rSCRIPT NUM : {config.script_num}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions
# Chargement de Chrome driver
from ChromeDriver.SetDriver import driver

from Functions import Functions_40a_proba
from Functions.GetJsonData import DispatchPerte
from Functions.ScriptRechercheDeMatch import classementeDeMatch
from Functions.Authenticator import is_logged_in, loginProcess

confirmation = input(f"Classement ? (Y/N): ")

if confirmation.upper() == 'Y' or confirmation.upper() == 'y' or confirmation.upper() == 'O' or confirmation.upper() == 'o':
    classementeDeMatch(driver)

# Call the function to get the code
if not is_logged_in(driver):
    loginProcess(driver)
else:
    print("You are already logged in.")

is_in = input("Voulez-vous trier les matchs ? (Y/N): ")
if is_in.upper() == 'Y' or is_in.upper() == 'y' or is_in.upper() == 'O' or is_in.upper() == 'o':
    config.in_stat = True
config.init_variable()

while (config.win < 100):

    try:
        Functions_40a_proba.all_script(driver)
    except Exception as e:
        config.log(f"ERROR SCRIPT : {e}", 'error', False)
    else:
        if config.perte > 0:
            DispatchPerte()
        config.init_variable()
        sucess = False
        while not sucess:
            try:
                driver.get(config.site_url)
            except:
                continue
            else:
                sucess = True

print('TOTAL WIN : ' + str(config.win))
