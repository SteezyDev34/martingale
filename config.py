import pygsheets
GSheets = pygsheets.authorize(service_file='auxobetting-7a3cf182ba61.json')
match_list = []
matchlist_file_name = '../matchlist'
running_file_name = '../running'
match_done_key = ""#Nom du match dans Gsheets
match_found = 0
