print('START')
import os

#Chargement de Chrome driver
from ChromeDriver.SetDriver5 import driver

#Chargement des variables globales
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
    print(f"SCRIPT TYPE : {config.scriptType}")
    print(f"SCRIPT NUM : {config.script_num}")
else:
    print("Le format du nom du fichier est incorrect.")
    exit()


#Chargement des fonctions
from Functions import Functions_15a
from Functions.GetJsonData import DispatchPerte



while (config.win < 100):
    config.init_variable()

    try:
        Functions_15a.all_script(driver)
    except Exception as e:
        print(f"ERROR SCRIPT : {e}")
    if config.perte > 0:
        DispatchPerte()
    try:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    except:
        driver.get('https://1xbet.com/fr/live/Tennis/')
print('TOTAL WIN : '+str(config.win))