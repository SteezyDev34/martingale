import re
from config import GSheets
global GSheets
#SUIVIS LOST 40 A
def suivi_lost(values):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[6]
    row = wk1.get_all_values()
    rows = len(row)
    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        wk1.update_row(rows,values, col_offset=0)
    else:
        wk1.insert_rows(0, number=1, values=values, inherit=False)
# SUIVIS LOST 30 A
def suivi_lost30(values):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[7]
    row = wk1.get_all_values()
    rows = len(row)
    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        wk1.update_row(rows,values, col_offset=0)
    else:
        wk1.insert_rows(0, number=1, values=values, inherit=False)
# SUIVIS LOST 15 A
def suivi_lost15(values):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[8]
    row = wk1.get_all_values()
    rows = len(row)
    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        wk1.update_row(rows,values, col_offset=0)
    else:
        wk1.insert_rows(0, number=1, values=values, inherit=False)
#MISE A JOUR DES PERTE GENERAL
def update_lost(row, values):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[1]
    # Updates values in a row from 1st column
    wk1.update_row(row + 4, [values], col_offset=1)

#RÉCUPRER LES PERTE 30 A DE LA LIGUE
def get_perte_en_cours30A(ligue_name):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[7]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    rows = len(row)
    i=0


    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        return False
    else:
        compet_recup_ok_list = ['double', 'qualification', 'couple', 'itf', 'challenger']
        try:
            if any(compet_ok in ligue_name for compet_ok in
               compet_recup_ok_list):
                print('mauvaise ligue')

                return False
            else:
                while rows != 0:
                    data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
                    print("dat find :"+data[3] )
                    data.append(rows)
                    print("compet ok in : "+str(data))
                    break
                return data
        except:
            return False
#RÉCUPRER LES PERTE 15 A DE LA LIGUE
def get_perte_en_cours15A(ligue_name):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[8]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    rows = len(row)
    i=0


    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        return False
    else:
        compet_recup_ok_list = ['master', 'double', 'couple']
        try:
            if any(compet_ok in ligue_name for compet_ok in
               compet_recup_ok_list):
                return False
            else:
                while rows != 0:
                    data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
                    print("dat find :"+data[3] )
                    data.append(rows)
                    print("compet ok in : "+str(data))
                    break
                return data
        except:
            return False

#SUPPRIMER LA PERTE RRÉCUPÉRÉE DU TABLEAU 30 A
def del_perte_en_cours30A(rows):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[7]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    nbrows = len(row)
    if rows ==0:
        wk1.update_row(rows, ["","","",""], col_offset=0)
    elif nbrows == 1:
        wk1.update_row(rows, ["", "", "", ""], col_offset=0)
    else:
        wk1.delete_rows(rows, number=1)
# SUPPRIMER LA PERTE RRÉCUPÉRÉE DU TABLEAU 15  A
def del_perte_en_cours15A(rows):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[8]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    nbrows = len(row)
    if rows ==0:
        wk1.update_row(rows, ["","","",""], col_offset=0)
    elif nbrows == 1:
        wk1.update_row(rows, ["", "", "", ""], col_offset=0)
    else:
        wk1.delete_rows(rows, number=1)

#MISEE A JOURR PERTE
def maj_perte(col, val, x):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[0]
    # Updates values in a row from 1st column
    if col == 1:
        z = "C" + str(x)
    elif col == 2:
        z = "D" + str(x)
    elif col == 3:
        z = "E" + str(x)
    elif col == 4:
        z = "F" + str(x)
    elif col == 5:
        z = "G" + str(x)
    elif col == 6:
        z = "H" + str(x)
    elif col == 7:
        z = "J" + str(x)
    elif col == 8:
        z = "I" + str(x)
    elif col == 9:
        z = "K" + str(x)
    wk1.update_value(z, val)

#INFOS DE MISE 30A
def get_infos_de_mise30A(ligue_name,rattrape_perte,perte,wantwin,mise,increment):
    print("RECHERCHDES DES INFOS DE MISE...")
    infos = get_perte_en_cours30A(ligue_name)
    if infos != False:
        lost_compet = infos[3]
        perte = float(infos[0].replace(",", "."))
        wantwin = float(infos[1].replace(",", "."))
        mise = float(infos[2].replace(",", "."))
        rattrape_perte = 1
        del_perte_en_cours30A(infos[4])
        print("1 perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    else:
        if rattrape_perte == 0:
            if int(get_perte_generale()) > 0.2:
                rattrape_perte = 1
        print("3 perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    return [perte,wantwin,mise,increment,rattrape_perte]
#INFOS DE MISE 15A
def get_infos_de_mise15A(ligue_name,rattrape_perte,perte,wantwin,mise,increment):
    print("RECHERCHDES DES INFOS DE MISE...")
    infos = get_perte_en_cours15A(ligue_name)
    if infos != False:
        lost_compet = infos[3]
        perte = float(infos[0].replace(",", "."))
        wantwin = float(infos[1].replace(",", "."))
        mise = float(infos[2].replace(",", "."))
        rattrape_perte = 1
        del_perte_en_cours15A(infos[4])
        print("1 perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    else:
        if rattrape_perte == 0:
            if int(get_perte_generale()) > 0.2:
                rattrape_perte = 1
        print("3 perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    return [perte,wantwin,mise,increment,rattrape_perte]

