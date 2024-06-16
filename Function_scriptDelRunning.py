#Function_scriptDelRunning
#SCRIPT NON EN COURS DONC SUPPRIMER NUM SCRIPT DU FICHIER RUNNING
def scriptDelRunning(script_num,running_file_name):
    #on ouvre le fichier text en mode lecture
    get_running_file = open(running_file_name+".txt", "r")
    #on lit le contenu du fichier
    get_running = get_running_file.read()
    #on ferme le fichier
    get_running_file.close()
    #on supprime le numéro du script au format #num#
    match_list = get_running.replace("#" + str(script_num) + "#", "")
    # on supprime le numéro du script au format num
    match_list = match_list.replace(str(script_num), "")
    # on ouvre le fichier en mide ecriture
    get_running_file = open(running_file_name+".txt", "w")
    # on remplace le contenu du fichier sans le numéro du script
    get_running_file.write(match_list)
    # on ferme le fichier
    get_running_file.close()
