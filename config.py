import pygsheets
GSheets = pygsheets.authorize(service_file='/Users/steezy/PycharmProjects/mrtingal/auxobetting-a36473795856.json')
match_list = []
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
script_num = 0
#Ouverture du Gsheets
sh = GSheets.open('BOT 1XBET PYTHON')
# On selectionne la première feuille
wk1 = sh[0]
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
    probamini = float(wk1.get_value('B2').replace(',', '.'))
    cotemini = float(wk1.get_value('B3').replace(',', '.'))
    perte = 0
    wantwin = float(wk1.get_value('B8').replace(',', '.'))
    increment = float(wk1.get_value('B9').replace(',', '.'))
    increment = float(wk1.get_value('B9').replace(',', '.'))
    recup40 = wk1.get_value('B14').replace(',', '.')
    recup30 = wk1.get_value('B15').replace(',', '.')

init_variable()
print('mise'+str(mise))
rattrape_perte = 0
matchlist_file_name = '/Users/steezy/PycharmProjects/mrtingal/matchlist_proba'
running_file_name = '/Users/steezy/PycharmProjects/mrtingal/running_proba'
score_to_start = [
    "00(0)00(0)"
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
devMode = wk1.get_value('B13')
if devMode.lower() == "true":
    devMode = True
else:
    devMode = False

import datetime

# Obtenir la date actuelle et la formater
date_actuelle = datetime.datetime.now().strftime("%d-%m-%Y")
def saveLog(txt):

    # Nom de base du fichier
    nom_de_base = "logScript40A-"+str(script_num)

    # Créer le nom de fichier avec la date
    nom_du_fichier = f"{nom_de_base}-{date_actuelle}.txt"

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
        fichier.write(str(heure_actuelle)+' : '+str(txt))
    if devMode:
        print(str(txt))