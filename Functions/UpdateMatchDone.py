# UpdateMatchDone
#MISE A JOUR DES MATCHS EFFECTUÉS
def main(action, values,matchlist_file_name):
    if action == "add":
        newmatch = values
        get_matchlist_file = open(matchlist_file_name+".txt", "a")
        get_matchlist_file.write(
            "\n" + str(newmatch))
        get_matchlist_file.close()
    elif action == "del":
        get_matchlist_file = open(matchlist_file_name+".txt", "r")
        get_matchlist = get_matchlist_file.read()
        get_matchlist_file.close()
        match_list = get_matchlist.replace("\n" + str(values), "")
        get_matchlist_file = open(matchlist_file_name+".txt", "w")
        get_matchlist_file.write(match_list)
        get_matchlist_file.close()