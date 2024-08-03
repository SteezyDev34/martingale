import pygsheets
import os
import datetime
import requests
import json
proxy = {
    "http": "http://auxobettingproxy:Scorpion971@209.200.239.22:51523",
    "https": "http://auxobettingproxy:Scorpion971@209.200.239.22:51523",
}
def getJsonData(url):
    i =0
    while i<2:
        i+=1
        print(proxy)
        # URL du lien JSON de la strategy
        try:
            # Envoyer une requête GET à l'URL
            response = requests.get(url,proxies=proxy)
            # Vérifier que la requête a réussi
            response.raise_for_status()
            # Parser le JSON depuis la réponse
            strategy = response.json()[0]
            # Afficher les données pour vérification
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des données : {e}")
        except json.JSONDecodeError as e:
            print(f"Erreur lors du parsing du JSON : {e}")
        else:
            return strategy

projectPath = os.path.dirname(os.path.abspath(__file__))
#Initialisation des varables
script_num = 0 # Numéro du Script
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
match_found = False # Match valide trouvé
mise = 0.2
probamini = 0.4
cotemini = 1
cotebase = 1
misemax = 0
perte = 0
wantwin = 0.2
nb_tour = 1
increment = 0
recup40 = 0
recup30 = 0
rattrape_perte = 0
print_running_text = False
print_match_live_text = False
error = False

def init_variable():
    global mise, perte, wantwin,increment, probamini, cotemini,recup40,recup30
    global running_file_name,matchlist_file_name,print_running_text,rattrape_perte
    global print_match_live_text,devMode,match_list,match_done_key,match_found
    global error,cotebase,nb_tour,restart_set2
    match_list = [] #List des matchs
    match_done_key = ""#Nom du match dans Gsheets
    match_found = False # Match valide trouvé
    url = "https://auxobetting.fr/strategy"+scriptType+"/"
    print(url)
    strategy = getJsonData(url)
    mise = float(strategy["mise"])
    print('init mise : '+str(mise))
    probamini = float(strategy["proba_mini"])
    print('init probamini : ' + str(probamini))
    cotemini = float(strategy["cote_recup"])
    print('init cotemini : ' + str(cotemini))
    cotebase = float(strategy["cote_base"])
    print('init cotebase : ' + str(cotebase))
    nb_tour = float(strategy["nb_tour"])
    print('init nb_tour : ' + str(nb_tour))
    restart_set2 = float(strategy["restart_set2"])
    print('init restart_set2 : ' + str(restart_set2))
    perte = 0
    print('init perte : ' + str(perte))
    wantwin = float(strategy["wantwin"])
    increment = float(strategy["increment"])
    recup40 = float(strategy["mtt_recup"])
    recup30 = float(strategy["mtt_recup"])
    running_file_name = projectPath+'/SCRIPTS '+scriptType+'/running'
    rattrape_perte = 0
    matchlist_file_name = projectPath+'/SCRIPTS '+scriptType+'/matchlist'
    print_running_text = False
    print_match_live_text = False
    devMode = strategy["devmode"]
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
        try:
            fichier.write(str(heure_actuelle) + ' : ' + str(txt))
        except:
            print('erreur de log')
        print(str(txt))
