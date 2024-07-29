import pygsheets
import os

print('config 30A')
GSheets = pygsheets.authorize(service_file='auxobetting-a36473795856.json')
match_list = []
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
script_num = 0
#Ouverture du Gsheets
sh = GSheets.open('BOT 1XBET PYTHON')
# On selectionne la première feuille
wk1 = sh[2]
#on récupère les différentes valeurs
win = 0
mise = wk1.get_value('B11').replace(',','.')
perte = 0
wantwin = wk1.get_value('B8').replace(',','.')
increment = wk1.get_value('B9').replace(',','.')
recup40 = wk1.get_value('B14').replace(',','.')
recup30 = wk1.get_value('B15').replace(',','.')
cote = 3
probamini = 0.5
cotemini = 0.3
def init_variable():
    global mise, perte, wantwin, increment, probamini, cotemini
    mise = float(wk1.get_value('B11').replace(',', '.'))
    print('init mise : '+str(mise))
    probamini = float(wk1.get_value('B2').replace(',', '.'))
    print('init probamini : ' + str(probamini))
    cotemini = float(wk1.get_value('B3').replace(',', '.'))
    print('init cotemini : ' + str(cotemini))
    perte = 0
    print('init perte : ' + str(perte))
    wantwin = float(wk1.get_value('B8').replace(',', '.'))
    increment = float(wk1.get_value('B9').replace(',', '.'))
init_variable()
rattrape_perte = 0
matchlist_file_name = 'matchlist30A'
running_file_name = 'running30A'
score_to_start = [
    "00(0)00(0)"
    "00(15)00(0)",
    "00(0)00(15)",
    "00(15)00(15)"
]
"""score_to_start = [
    "00(0)00(0)",
    "00(15)00(0)",
    "00(0)00(15)",
    "00(15)00(15)",
    "00(30)00(15)",
    "00(15)00(30)",
    "00(30)00(0)",
    "00(0)00(30)"
]"""
ligue_name = ""
match_Url = ""
newmatch = ""
proba40A = 0
saved_set = ""
set_actuel = ""
jeu_actuel = ""
score_actuel = False
saved_score = False
numset = ""
set = ""
gain = 0
error = False
print_running_text = False
print_match_live_text = False
# On définie le mode développement ou production
# Ouverture du Gsheets
sh = GSheets.open('BOT 1XBET PYTHON')
# On selectionne la première feuille
devMode = wk1.get_value('B13')
if devMode.lower() == "true":
    devMode = True
else:
    devMode = False

import datetime

# Obtenir la date actuelle et la formater
date_actuelle = datetime.datetime.now().strftime("%d-%m-%Y")
def saveLog(txt, matchname=newmatch):
    date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
    nom_de_base = "logScript30A-" + str(script_num) + '-' + str(matchname)

    # Créer le nom de fichier avec la date
    nom_du_fichier = f"{nom_de_base}-{date_actuelle}.txt"

    # Créer le répertoire s'il n'existe pas
    nom_du_repertoire = os.path.dirname(nom_du_fichier)
    if nom_du_repertoire and not os.path.exists(nom_du_repertoire):
        os.makedirs(nom_du_repertoire)

    # Ouvrir le fichier en mode ajout
    with open(nom_du_fichier, 'a+') as fichier:
        # Vérifier si le fichier est non vide
        fichier.seek(0)
        contenu = fichier.read()

        # Ajouter un saut de ligne si le fichier n'est pas vide
        if contenu:
            fichier.write('\n')
        # Écrire le texte à la fin du fichier
        heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
        fichier.write(str(heure_actuelle) + ' : ' + str(txt))
        print(str(txt))