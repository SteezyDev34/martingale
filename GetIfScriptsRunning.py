#Function_getIfScriptsRunning
import re
import config
#EST CE QUE LE SCRIPT EST EN COURS
def GetIfScriptsRunning(running_file_name):
    go = False
    if not config.print_running_text:
        config.saveLog('Est ce que le script peut y aller?')
    while not go:
        if not config.print_running_text:
            config.saveLog("Script : "+str(config.script_num))
        if config.script_num > 1:#si le script n'est pas le 1 car il doit forcément se lancer
            autre_script = 1
            while autre_script < config.script_num:
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
                    if not config.print_running_text:
                        config.saveLog("script " + str(config.script_num) + " STOP!")
                        config.print_running_text = True
                    break
                #on passe au script inférieur suivant
                autre_script = autre_script + 1
            if autre_script == config.script_num:
                if not config.print_running_text:
                    config.saveLog("script " + str(config.script_num) + " GO!")
                    config.print_running_text = True
                go = True
                break
        else:
            if not config.print_running_text:
                config.saveLog("first script " + str(config.script_num) + " GO!")
            go = True
            config.print_running_text = True
            break

    return go