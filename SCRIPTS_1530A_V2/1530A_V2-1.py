#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de lancement — Stratégies 15A + 30A + 300 (architecture V2).

Utilise la nouvelle boucle all_script_v2() avec BaseScript / ScriptFactory.
Aucun fichier existant n'a été modifié.

Lancement :
    python "SCRIPTS 1530A_V2/1530A_V2-1.py"
"""

import os
import sys
import time
import traceback

# --- Résolution du chemin du projet ---
current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
project_directory = os.path.dirname(parent_directory)
sys.path.append(project_directory)

# --- Vérification des dépendances (sauf PyCharm) ---
if os.getenv('PYCHARM_HOSTED') != '1':
    import VenvDependencyManager
    VenvDependencyManager.main()

from art import *

# --- Chargement de la configuration globale ---
import config

# --- Détection automatique du type et numéro de script depuis le nom de fichier ---
file_name = os.path.basename(__file__)
name_part = os.path.splitext(file_name)[0]
parts = name_part.split('-')

if len(parts) > 1:
    config.scriptType = parts[0]        # ex: '1530A_V2'
    config.script_num = int(parts[1])   # ex: 1
    localhost_raw = str(config.scriptType) + str(config.script_num)
    config.localhost = ''.join(c for c in localhost_raw if c.isdigit())
    if int(config.localhost) < 1024:
        config.localhost = 1024 + int(config.localhost)
    config.log_clear_line(3)
    print(f"{config.PURPLE}{text2art(f'Start V2 {config.scriptType} {config.script_num}')}")
else:
    print("Format de nom de fichier incorrect (attendu : NOM-NUM.py).")
    sys.exit(1)

# --- Lancement de Chrome ---
config.localhost = 43151
command = (
    f'open -na "Google Chrome" --args '
    f'--remote-debugging-port={config.localhost} '
    f'--user-data-dir="$HOME/ChromeDebugProfile{config.localhost}"'
)
print(command)

from ChromeDriver.SetDriver import get_script_driver

num_fenetre = 1
time.sleep((num_fenetre - 1) * 3)
driver = get_script_driver(num_fenetre)

# --- Import de la nouvelle boucle V2 ---
from core.martingale.all_script_v2 import all_script_v2
from Functions.GetJsonData import DispatchPerte
from Functions.ScriptRechercheDeMatch import classementeDeMatch, newclassementeDeMatch

# --- Classement optionnel des matchs ---
confirmation = input("Classement ? (Y/N) : ")
config.log_clear_line()

if confirmation.strip().upper() in ('Y', 'O'):
    type_classement = input("Type de classement ? (1=simple / 2=complet) : ")
    config.log_clear_line()
    if type_classement.strip() == '1':
        config.log("-" * 60, 'info', False, False, False)
        print("Classement simple en cours")
        config.log("-" * 60, 'info', False, False, False)
        classementeDeMatch(driver)
    else:
        config.log("-" * 60, 'info', False, False, False)
        print("Classement complet en cours")
        config.log("-" * 60, 'info', False, False, False)
        newclassementeDeMatch(driver)
        #classementeDeMatch(driver)

# ------------------------------------------------------------------
# Configuration des stratégies actives
#
#   Modifier cette liste pour changer les stratégies jouées :
#       ['15A', '30A', '300']   ← toutes les trois
#       ['15A', '30A']          ← sans 300
#       ['15A']                 ← seulement 15A
# ------------------------------------------------------------------
STRATEGIES_ACTIVES = ['15A', '30A', '300']

config.in_stat = True
config.scriptTypeList = STRATEGIES_ACTIVES

# Initialisation des instances ScriptConfig (chargement depuis l'API)
for script_type in config.scriptTypeList:
    config.ScriptConfig(script_type)

# Initialisation des compteurs par stratégie
config.winmatch = {st: 0 for st in config.scriptTypeList}
config.global_match_win = {st: 0.0 for st in config.scriptTypeList}

config.log(
    f"Stratégies actives : {', '.join(config.scriptTypeList)}",
    'success', False
)

# ------------------------------------------------------------------
# Boucle principale — 100 victoires max
# ------------------------------------------------------------------
while config.win < 100:
    try:
        all_script_v2(driver)

    except KeyboardInterrupt:
        config.log("Arrêt manuel du script (Ctrl+C)", 'warning', False)
        break

    except Exception as e:
        # Log complet avec fichier / ligne / fonction
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            last_frame = tb[-1]
            config.log(
                f"ERREUR : {e} | "
                f"Fichier : {last_frame.filename} | "
                f"Ligne : {last_frame.lineno} | "
                f"Fonction : {last_frame.name}",
                'error', False
            )
            config.log(f"Traceback complet :\n{traceback.format_exc()}", 'error', False)
        else:
            config.log(f"ERREUR : {e}", 'error', False)

    else:
        # Dispatch des pertes résiduelles après chaque match
        if config.perte > 0:
            DispatchPerte()

        # Remise à zéro des compteurs pour le prochain match
        for st in config.scriptTypeList:
            config.switchScript(st)
            config.ScriptConfig(st).reset()
            config.init_variable()
            config.switchScript(st)
            DispatchPerte()
            config.global_match_win[st] = 0.0
            config.winmatch[st] = 0

    # Retour à la page tennis pour le prochain match
    retour_ok = False
    while not retour_ok:
        try:
            driver.get(config.site_url)
            retour_ok = True
        except Exception:
            time.sleep(2)

print(f"TOTAL WIN : {config.win}")
