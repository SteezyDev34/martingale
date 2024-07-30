#Function_scriptDelRunning
import config
#SCRIPT NON EN COURS DONC SUPPRIMER NUM SCRIPT DU FICHIER RUNNING
def scriptDelRunning():
    try:
        # Ouvrir le fichier en mode lecture, ou le créer s'il n'existe pas
        with open(config.running_file_name + ".txt", "r") as get_running_file:
            # Lire le contenu du fichier
            get_running = get_running_file.read()
    except FileNotFoundError:
        # Si le fichier n'existe pas, créer un fichier vide
        get_running = ""

    # Supprimer le numéro du script au format #num#
    match_list = get_running.replace("#" + str(config.script_num) + "#", "")
    # Supprimer le numéro du script au format num
    match_list = match_list.replace(str(config.script_num), "")

    # Ouvrir le fichier en mode écriture
    with open(config.running_file_name + ".txt", "w") as get_running_file:
        # Remplacer le contenu du fichier sans le numéro du script
        get_running_file.write(match_list)
