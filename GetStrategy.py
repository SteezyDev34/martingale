import pygsheets
GSheets = pygsheets.authorize(service_file='auxobetting-a36473795856.json')

def GetStrategy(sh):
    sh = GSheets.open('BOT 1XBET PYTHON')
    # On selectionne la première feuille
    wk1 = sh[0]
    #on récupère les différentes valeurs
    data = {
    'mise' : float(wk1.get_value('B11').replace(",", ".")),
    'perte' : float(wk1.get_value('B12').replace(",", ".")),
    'wantwin' : float(wk1.get_value('B8').replace(",", ".")),
    'increment' : float(wk1.get_value('B9').replace(",", ".")),
    'cote' : float(wk1.get_value('B10').replace(",", ".")),
    'continueSet2' : wk1.get_value('B7'),
    'RestartOnSet2' : wk1.get_value('B6'),
    'RecupMiseEnCours' : wk1.get_value('B5'),
    'NbToWin40A' : float(wk1.get_value('B4')),
    'cotePourRecupPerte' : float(wk1.get_value('B3').replace(",", "."))
    }
    return data

#DataGetStrategy = GetStrategy(sh)
#print(DataGetStrategy['increment'])