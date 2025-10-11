# Function_getIfScriptsRunning
import sys
import os
import time
from datetime import datetime

# Ajouter le chemin du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

import config
from Functions.Managers.ScriptManager import script_manager


# EST CE QUE LE SCRIPT EST EN COURS
def GetIfScriptsRunning():
    """
    Vérifie si les scripts précédents sont en cours d'exécution dans l'ordre.
    Exemple: pour script_num = 3, les scripts 1 et 2 doivent être en cours.

    Returns:
        bool: True si le script peut démarrer, False sinon
    """
    dot_count = 0

    while True:
        if config.script_num <= 1:
            return True

        # Récupérer tous les scripts en cours
        running_scripts = script_manager.get_running_scripts()

        # Convertir en dictionnaire pour un accès plus facile
        running_dict = {
            int(script_id.split("-")[1]): status
            for script_id, start, last_beat, status, pid in running_scripts
        }

        # Vérifier que tous les scripts précédents sont en cours
        all_previous_running = True
        for script_num in range(1, config.script_num):
            if script_num not in running_dict:
                all_previous_running = False
                break

        if all_previous_running:
            return True

        # Affichage du message d'attente
        message = f"Script {config.script_num} en attente des scripts précédents"
        sys.stdout.write(f"\r{message}{'.' * dot_count}")
        sys.stdout.flush()

        dot_count = (dot_count + 1) % 4
        time.sleep(1)

        # Nettoyer la ligne pour le prochain affichage
        sys.stdout.write("\r" + " " * (len(message) + 4))
        sys.stdout.flush()


if __name__ == "__main__":
    config.script_num = 2
    config.running_file_name = "../SCRIPTS 40A/running"
    config.newmatch = "test"

    GetIfScriptsRunning()
