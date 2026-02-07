# -*- coding: utf-8 -*-
import os
import sys

current_file_path = os.path.abspath(__file__)

parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)
if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
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
    print(config.localhost)
    command = f'open -na "Google Chrome" --args --remote-debugging-port={config.localhost} --user-data-dir="$HOME/ChromeDebugProfile{config.localhost}"'
    print(command)
    print(f'{config.PURPLE}' + text2art(
        f"Start martingal {config.scriptType} {config.script_num}"))  # Crée un texte en art ASCII
    # sys.stdout.write(f"\rSCRIPT TYPE : {config.scriptType}")
    # sys.stdout.write(f"\rSCRIPT NUM : {config.script_num}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()

# Chargement des functions
# Chargement de Chrome driver
config.localhost = 43151
from ChromeDriver.SetDriver import get_script_driver

num_fenetre = 1
# time.sleep((num_fenetre - 1) * 3)  # Attendre un peu pour s'assurer que la fenêtre est prête

driver = get_script_driver(num_fenetre)

from Functions import Functions_1SET

config.scriptTypeList = ['1SET']
config.winmatch = {script_type: 0 for script_type in config.scriptTypeList}
config.global_match_win = {script_type: 0 for script_type in config.scriptTypeList}
config.total_want_win = config.total_want_winset1

for i in config.scriptTypeList:
    config.ScriptConfig(i)

while (config.win < 100):

    try:
        Functions_1SET.all_script(driver)
    except Exception as e:
        config.log(f"ERROR SCRIPT : {e}", 'error', False)
    else:
        for i in config.scriptTypeList:
            config.switchScript('1SET')
            config.ScriptConfig(i).reset()
        sucess = False
        while not sucess:
            try:
                driver.get(config.site_url)
            except:
                continue
            else:
                sucess = True

print('TOTAL WIN : ' + str(config.win))
