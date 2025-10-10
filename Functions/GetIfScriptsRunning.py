# Function_getIfScriptsRunning
import re
import sys
import time

import config


# EST CE QUE LE SCRIPT EST EN COURS
def GetIfScriptsRunning():
    go = False
    txtlog = ""
    dot_count = 0

    while not go:
        if config.script_num > 1:  # si le script n'est pas le 1 car il doit forcément se lancer
            autre_script = 1
            sys.stdout.write("Script " + str(config.script_num) + " STOP!")
            while autre_script < config.script_num:
                # on ouvre le fichier texte en mode lecture
                get_running_file = open(config.running_file_name + ".txt", "r")
                # on lit le contenu du fichier
                get_running = get_running_file.read()
                # on ferme le fichier
                get_running_file.close()
                # si on ne trouve pas un script inférieur on
                if len(re.findall(str(autre_script), get_running)) <= 0:
                    # on passe go à False car le script ne peut pas démarrer
                    go = False
                    # on arrête la boucle
                    if not config.print_running_text:
                        config.print_running_text = True
                    # Afficher le nouveau message sur la même ligne
                    sys.stdout.write("Waiting" + "." * dot_count + "\n")
                    time.sleep(0.5)
                    config.log_clear_line()
                    # Augmenter le nombre de points jusqu'à 5, puis recommencer à 1
                    dot_count = dot_count + 1 if dot_count < 5 else 1
                    break
                # on passe au script inférieur suivant
                autre_script = autre_script + 1
            if autre_script == config.script_num:
                go = True
                break
            config.log_clear_line()
        else:
            go = True
            break
    return go


if __name__ == "__main__":
    config.script_num = 2
    config.running_file_name = "../SCRIPTS 40A/running"
    config.newmatch = 'test'

    GetIfScriptsRunning()
