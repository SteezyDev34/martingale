import pygsheets
GSheets = pygsheets.authorize(service_file='auxobetting-7a3cf182ba61.json')
match_list = []
matchlist_file_name = 'matchlist30A'
running_file_name = 'running30A'
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
win = 0
mise = 0.69
perte = 0
wantwin = 1
increment = 0
cote = 2.4
score_to_start = [
    "00(0)00(0)",
    "00(15)00(0)",
    "00(0)00(15)"
]