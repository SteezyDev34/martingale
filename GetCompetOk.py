from config import GSheets
global GSheets
def main():
    # on ouvre le fichier gsheets
    sh = GSheets.open('BOT 1XBET PYTHON')
    # on selectionne la feuille
    wk1 = sh[9]
    # on récupère les valeurs
    row = wk1.get_all_values()
    # le nombre de lignes
    rows = len(row)
    # création des tableaux
    compet_ok_list = []
    compet_not_ok_list = []

    while rows != 1:# tant qu'il y a plus d'une ligne car ligne 1 = entete
        # on récupère la ligne
        data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
        # on ajoute l'infos de la colonne 1
        if data[0] != "":
            compet_ok_list.append(data[0])
        # on ajoute l'infos de la colonne 2
        if data[1] != "":
            compet_not_ok_list.append(data[1])
        # on passe à la ligne du dessus
        rows = rows - 1
    print('compet ok recupéré : ',compet_ok_list)
    print('compet non ok recupéré : ',compet_not_ok_list)

    return[compet_ok_list,compet_not_ok_list]