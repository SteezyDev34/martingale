import os
import sys
import asyncio

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
    if config.systeme == 'Windows':
        command = f'start chrome --remote-debugging-port={config.localhost} --user-data-dir="{project_directory}\\ChromeDebugProfile{config.localhost}"'
    else:
        command = f'open -na "Google Chrome" --args --remote-debugging-port={config.localhost} --user-data-dir="$HOME/ChromeDebugProfile{config.localhost}"'

    confirmation = input(f"Avez-vous exécuté la commande \n{command}\n? (Y/N): ")

    if confirmation.upper() != 'Y' and confirmation.upper() != 'y' and confirmation.upper() != 'O' and confirmation.upper() != 'o':
        print("Programme arrêté par l'utilisateur.")
        sys.exit(0)  # Arrêter le programme
    else:
        config.log_clear_line(3)

    print(f"{config.PURPLE}{text2art(f'Start martingal {config.scriptType} {config.script_num}')}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions
# Chargement de Chrome driver
from ChromeDriver.SetDriver import driver

from Functions import Functions_431a
from Functions.GetJsonData import DispatchPerte
from Functions.ScriptRechercheDeMatch import classementeDeMatch, newclassementeDeMatch
from Functions.GetScoreActuelAsync import start_score_monitoring, stop_score_monitoring


# Fonction: Exécution asynchrone du script principal
# Commentaire: Lance le script principal avec surveillance des scores en parallèle
async def main_async():
    """
    Fonction principale asynchrone qui lance le script et la surveillance des scores
    """
    # Démarrer la surveillance des scores en arrière-plan
    print(f"{config.PURPLE}Démarrage de la surveillance des scores en arrière-plan...")
    score_task, stop_event = await start_score_monitoring(driver)
    
    try:
        # Exécution du script principal de manière synchrone dans un thread
        await run_main_script()
    finally:
        # Arrêter la surveillance des scores
        print(f"{config.PURPLE}Arrêt de la surveillance des scores...")
        await stop_score_monitoring(score_task, stop_event)


# Fonction: Exécution du script principal
# Commentaire: Contient la logique principale du script original
async def run_main_script():
    """
    Exécute la logique principale du script de manière asynchrone
    """
    confirmation = input(f"Classement ? (Y/N): ")
    config.log_clear_line()

    if confirmation.upper() == 'Y' or confirmation.upper() == 'y' or confirmation.upper() == 'O' or confirmation.upper() == 'o':
        confirmation = input(f"Type de Classement ? (1/2): ")
        config.log_clear_line()
        if confirmation == '1':
            config.log("-" * 60, "info", False, False, False)
            print("Classement simple en cours")
            config.log("-" * 60, "info", False, False, False)
            # Exécuter de manière asynchrone
            await asyncio.get_event_loop().run_in_executor(None, classementeDeMatch, driver)
        else:
            config.log("-" * 60, "info", False, False, False)
            print("Classement complet en cours")
            config.log("-" * 60, "info", False, False, False)
            # Exécuter de manière asynchrone
            await asyncio.get_event_loop().run_in_executor(None, newclassementeDeMatch, driver)
            await asyncio.get_event_loop().run_in_executor(None, classementeDeMatch, driver)

    is_in = input("Voulez-vous trier les matchs ? (Y/N): ")
    config.log_clear_line()
    if is_in.upper() == 'Y' or is_in.upper() == 'y' or is_in.upper() == 'O' or is_in.upper() == 'o':
        config.in_stat = True
        config.log("-" * 60, "purple", False, False, False)
        print(f"{config.PURPLE}CLASSEMENT : OUI")
        config.log("-" * 60, "purple", False, False, False)
    
    config.scriptTypeList = config.scriptTypeList
    for i in config.scriptTypeList:
        config.ScriptConfig(i)
    config.winmatch = {script_type: 0 for script_type in config.scriptTypeList}
    config.global_match_win = {script_type: 0 for script_type in config.scriptTypeList}
    
    while (config.win < 100):
        # Exécuter Functions_431a.all_script de manière asynchrone
        await asyncio.get_event_loop().run_in_executor(None, Functions_431a.all_script, driver)
        
        try:
            pass
        except Exception as e:
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
                    driver.get(config.site_url)
                except:
                    await asyncio.sleep(0.1)  # Petite pause asynchrone
                    continue
                else:
                    sucess = True
        
        # Petite pause pour permettre à la surveillance des scores de fonctionner
        await asyncio.sleep(0.1)

    print('TOTAL WIN : ' + str(config.win))


if __name__ == "__main__":
    # Lancer l'exécution asynchrone
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{config.PURPLE}Script interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\n{config.RED}Erreur lors de l'exécution : {e}")