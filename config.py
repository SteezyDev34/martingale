import pygsheets
import os
import datetime
import mysql.connector

projectPath = os.path.dirname(os.path.abspath(__file__))
GSheets = pygsheets.authorize(service_file=projectPath+'/GsheetsJson/auxobetting-a36473795856.json')
#Initialisation des varables
script_num = 0 # Numéro du Script
GsheetName = "BOT 1XBET PYTHON" # Nom du gsheets ou sont stocké les données
SheetsNum = 0
win = 0 # Nombre de victoire
cote = 3
scriptType = ""

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
matchlist_file_name=""
running_file_name=""
match_list = [] #List des matchs
match_done_key = ""#Nom du match dans Gsheets
match_found = 0 # Match valide trouvé
mise = 0.2
probamini = 0.4
cotemini = 1
perte = 0
wantwin = 0.2
increment = 0
recup40 = 0
recup30 = 0
running_file_name = ""
rattrape_perte = 0
matchlist_file_name = ""
print_running_text = False
print_match_live_text = False
error = False

def init_variable():
    global mise, perte, wantwin,increment, probamini, cotemini,recup40,recup30
    global running_file_name,matchlist_file_name,print_running_text,rattrape_perte
    global print_match_live_text,devMode,match_list,match_done_key,match_found
    global error
    match_list = [] #List des matchs
    match_done_key = ""#Nom du match dans Gsheets
    match_found = 0 # Match valide trouvé
    sh = GSheets.open(GsheetName)
    wk1 = sh[SheetsNum]
    print(wk1.title)
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
    recup40 = float(wk1.get_value('B14').replace(',','.'))
    recup30 = float(wk1.get_value('B15').replace(',','.'))
    running_file_name = projectPath+'/SCRIPTS '+scriptType+'/running'
    rattrape_perte = 0
    matchlist_file_name = projectPath+'/SCRIPTS '+scriptType+'/matchlist'
    print_running_text = False
    print_match_live_text = False
    devMode = wk1.get_value('B13')
    if devMode.lower() == "true":
        devMode = True
    else:
        devMode = False
    error = False

# Obtenir la date actuelle et la formater
def saveLog(txt, matchname=newmatch):
    date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
    nom_de_base = projectPath+"/Logs/logScript"+scriptType+"-"+ str(script_num) + '-' + str(matchname)

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
