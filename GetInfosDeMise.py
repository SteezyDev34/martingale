# GetInfosDeMise.py
#RÉCUPRER LES PERTE 40 A DE LA LIGUE
from config import GSheets

def get_compet_recup_ok():
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
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
def get_perte_en_cours(ligue_name):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
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
#INFOS DE MISE
#SUPPRIMER LA PERTE RRÉCUPÉRÉE DU TABLEAU
def del_perte_en_cours(rows):
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
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
#RÉCUPÉRER LES PERTES GÉNÉRALES
def get_perte_generale():
    # open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
    sh = GSheets.open('BOT 1XBET PYTHON')
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
def main(ligue_name,rattrape_perte,perte,wantwin,mise,increment,proba40A):
    print("RECHERCHDES DES INFOS DE MISE...")
    #ON RÉCUPÈRE LES PERTES EN COURS SELON LA LIGUE
    infos = get_perte_en_cours(ligue_name)
    if infos != False:
        lost_compet = infos[3].strip().lower()
        if proba40A >0.40:
            perte = (infos[0].replace(",", "."))
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
                mise = 0.5
                increment = 0
                wantwin = 1
        print("perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    else:
        if rattrape_perte == 0:
            if int(get_perte_generale()) > 0.2:
                rattrape_perte = 1
        elif rattrape_perte == 1:
            rattrape_perte = 2
        print("retour perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))
    return [perte,wantwin,mise,increment,rattrape_perte]