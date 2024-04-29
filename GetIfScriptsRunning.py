#Function_getIfScriptsRunning
import re
#EST CE QUE LE SCRIPT EST EN COURS
def main(script_num,running_file_name):
    go = True
    if script_num > 1:#si le script n'est pas le 1 car il doit forcément se lancer
        autre_script = 1
        while autre_script < script_num:
            # on ouvre le fichier texte en mode lecture
            get_running_file = open(running_file_name+".txt", "r")
            #on lit le contenu du fichier
            get_running = get_running_file.read()
            #on ferme le fichier
            get_running_file.close()
            #si on ne trouve pas un script inférieur on
            if len(re.findall(str(autre_script), get_running)) <= 0:
                #on passe go à False car le script ne peut pas démarrer
                go = False
                #on arrete la boucle
                break
            #on passe au script inférieur suivant
            autre_script = autre_script + 1
    return go