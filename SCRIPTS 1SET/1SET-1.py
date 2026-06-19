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
import subprocess
import time

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

num_fenetre = 2
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
        if "HTTPConnectionPool" in str(e) and "Read timed out" in str(e):
            config.log(f"ERROR SCRIPT : {e}", 'error', False)
            # 1) Essayer d'envoyer Ctrl+W pour fermer l'onglet proprement
            try:
                from selenium.webdriver.common.keys import Keys
                try:
                    body = driver.find_element('tag name', 'body')
                except Exception:
                    try:
                        body = driver.find_element_by_tag_name('body')
                    except Exception:
                        body = None
                if body:
                    body.send_keys(Keys.CONTROL + 'w')
            except Exception:
                pass

            # 2) Essayer de fermer la session webdriver
            try:
                try:
                    driver.quit()
                except Exception:
                    try:
                        driver.close()
                    except Exception:
                        pass
            except Exception:
                pass

            # 3) Si Chrome a planté, tuer le processus écoutant sur le port de debug distant
            def kill_process_listening_on_port(port):
                try:
                    cmd = f'netstat -ano -p tcp | findstr :{port}'
                    out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                    lines = [l.strip() for l in out.splitlines() if l.strip()]
                    pids = set()
                    for line in lines:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            if pid.isdigit():
                                pids.add(pid)
                    for pid in pids:
                        try:
                            subprocess.call(['taskkill', '/F', '/PID', pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            pass
                except subprocess.CalledProcessError:
                    pass
                except Exception:
                    pass

            try:
                kill_process_listening_on_port(config.localhost)
            except Exception:
                pass

            # Petite pause pour laisser le système libérer les ressources
            time.sleep(2)

            # 4) Relancer le driver (une tentative simple)
            try:
                driver = get_script_driver(num_fenetre)
            except Exception as e2:
                config.log(f"ERROR: impossible de relancer le driver: {e2}", 'error', False)
                raise
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
