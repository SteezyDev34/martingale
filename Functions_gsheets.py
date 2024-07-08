import pygsheets
global gc
gc = pygsheets.authorize(service_file='auxobetting-7a3cf182ba61.json')
import config
#SUIVIS LOST 40 A
def suivi_lost():
    config.saveLog("AJOUT DES PARTES DANS LE SHEET")
    values = [config.perte, config.wantwin, config.mise, config.ligue_name]
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[6]
    row = wk1.get_all_values()
    rows = len(row)
    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        wk1.update_row(rows,values, col_offset=0)
    else:
        wk1.insert_rows(0, number=1, values=values, inherit=False)
    config.perte = 0
    config.rattrape_perte = 1
    config.mise = 0.2
    config.wantwin = 0.2
# SUIVIS LOST 30 A
def suivi_lost30():
    values = [config.perte, config.wantwin, config.mise, config.ligue_name]
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
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
    sh = gc.open('BOT 1XBET PYTHON')
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
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[1]
    # Updates values in a row from 1st column
    wk1.update_row(row + 4, [values], col_offset=1)
#RÉCUPRER LES PERTE 40 A DE LA LIGUE
def get_perte_en_cours(ligue_name):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[6]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    rows = len(row)
    i=0


    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        return False
    else:
        #LISTE DES COMPET QUI PEUVENT FAIRE DU RATTRAPAGE
        compet_recup_ok_list = get_compet_recup_ok()
        compet_ok_list = compet_recup_ok_list[0]
        compet_not_ok_list = compet_recup_ok_list[1]
        try:
            if any(compet_ok in ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in ligue_name for
                compet_not_ok in compet_not_ok_list):

                while rows != 0:
                    data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
                    print('get suiv ' + ligue_name)
                    print('get data ' + data[3])
                    if 'wta' in ligue_name.lower() or 'atp' in ligue_name.lower() or 'itf' in ligue_name.lower() or 'challenger' in ligue_name.lower():
                        data[3] = ligue_name
                        data.append(rows)
                        success = 1
                        print("compet ok in")
                        break
                    elif data[3].strip().lower() == ligue_name.lower():
                        data.append(rows)
                        success = 1
                        print("compet ok in")
                        break
                    else:
                        print('not : ' + data[3])
                        rows = rows - 1

                return data
            else:
                return False

        except Exception as e:
            print(e)
            return False
#RÉCUPRER LES PERTE 30 A DE LA LIGUE
def get_perte_en_cours30A(ligue_name):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[7]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    rows = len(row)
    i=0


    if rows ==1 and wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)==['', '', '','']:
        return False
    else:
        compet_recup_ok_list = ['double', 'couple']
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
    sh = gc.open('BOT 1XBET PYTHON')
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
#SUPPRIMER LA PERTE RRÉCUPÉRÉE DU TABLEAU
def del_perte_en_cours(rows):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[6]
    # Updates values in a row from 1st column
    row = wk1.get_all_values()
    nbrows = len(row)
    if rows ==0:
        wk1.update_row(rows, ["","","",""], col_offset=0)
    elif nbrows == 1:
        wk1.update_row(rows, ["", "", "", ""], col_offset=0)
    else:
        wk1.delete_rows(rows, number=1)
#SUPPRIMER LA PERTE RRÉCUPÉRÉE DU TABLEAU 30 A
def del_perte_en_cours30A(rows):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
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
    sh = gc.open('BOT 1XBET PYTHON')
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
#RÉCUPÉRER LES PERTES GÉNÉRALES
def get_perte_generale():
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[0]
    # Updates values in a row from 1st column
    print(wk1.get_value('B4'))
    try:
        float(wk1.get_value('B4').replace(",", "."))
    except:
        return 0
    else:
        return float(wk1.get_value('B4').replace(",", "."))
#MISEE A JOURR PERTE
def maj_perte(col, val, x):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
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
#INFOS DE MISE
def get_infos_de_mise(ligue_name,rattrape_perte,perte,wantwin,mise,increment,F40A):
    print("RECHERCHDES DES INFOS DE MISE...")
    #ON RÉCUPÈRE LES PERTES EN COURS SELON LA LIGUE
    infos = get_perte_en_cours(ligue_name)
    if infos != False:
        lost_compet = infos[3].strip().lower()
        print('lname = '+ligue_name)
        print('lnamecomp = ' + lost_compet)
        if ligue_name == lost_compet:
            perte = float(infos[0].replace(",", "."))
            wantwin = float(infos[1].replace(",", "."))
            mise = float(infos[2].replace(",", "."))
            if rattrape_perte == 2:
                rattrape_perte = 2
            else:
                rattrape_perte =1
            del_perte_en_cours(infos[4])
        elif rattrape_perte == 0:
            if int(get_perte_generale()) > 0.2:
                rattrape_perte = 1
                perte = 0
                mise = 0.2
                increment = 0
                wantwin = 2
        print("1 perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    else:
        print('aucun rattrapage recup #109U')
        if rattrape_perte == 0:
            if int(get_perte_generale()) > 0.2:
                rattrape_perte = 1
        elif rattrape_perte == 1:
            rattrape_perte = 2
        print("retour perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    return [perte,wantwin,mise,increment,rattrape_perte]
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
        print('gsheets infos false')
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
def get_compet_ok():
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[9]
    row = wk1.get_all_values()
    rows = len(row)
    compet_ok_list = []
    compet_not_ok_list = []
    while rows != 1:
        data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
        if data[0] != "":
            compet_ok_list.append(data[0])
        if data[1] != "":
            compet_not_ok_list.append(data[1])
        rows = rows - 1
    print('compet_ok_list')
    print(compet_ok_list)
    print('compet_not_ok_list')
    print(compet_not_ok_list)

    return[compet_ok_list,compet_not_ok_list]
def get_compet_recup_ok():
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = gc.open('BOT 1XBET PYTHON')
    # select the sheet
    wk1 = sh[10]
    row = wk1.get_all_values()
    rows = len(row)
    compet_RECUP_ok_list = []
    compet_RECUP_not_ok_list = []
    while rows != 1:
        data = wk1.get_row(rows, returnas='matrix', include_tailing_empty=True)
        if data[0] != "":
            compet_RECUP_ok_list.append(data[0])
        if data[1] != "":
            compet_RECUP_not_ok_list.append(data[1])
        rows = rows - 1
    print('compet_RECUP_ok_list')
    print(compet_RECUP_ok_list)
    print('compet_RECUP_not_ok_list')
    print(compet_RECUP_not_ok_list)

    return[compet_RECUP_ok_list,compet_RECUP_not_ok_list]