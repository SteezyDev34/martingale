# Function_GetMatchDone
#RÉCUPÉRER LES MATCHS EFFECTUÉS
def main(matchlist_file_name):
    get_matchlist_file = open(matchlist_file_name+".txt", "r")
    get_matchlist = get_matchlist_file.read()
    get_matchlist_file.close()
    match_list = get_matchlist.split('\n')
    return match_list
