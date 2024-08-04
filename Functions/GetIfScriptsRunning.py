#Function_getIfScriptsRunning
import re
import config


#EST CE QUE LE SCRIPT EST EN COURS
def GetIfScriptsRunning():
    go = False
    txtlog = ""
    if not config.print_running_text:
        txtlog = "Est ce que le script peut y aller?"
        config.saveLog(txtlog, 0, config.newmatch)
    while not go:
        if not config.print_running_text:
            txtlog = "Script : " + str(config.script_num)
            config.saveLog(txtlog, 0, config.newmatch)
        if config.script_num > 1:  #si le script n'est pas le 1 car il doit forcément se lancer
            autre_script = 1
            while autre_script < config.script_num:
                # on ouvre le fichier texte en mode lecture
                get_running_file = open(config.running_file_name + ".txt", "r")
                #on lit le contenu du fichier
                get_running = get_running_file.read()
                #on ferme le fichier
                get_running_file.close()
                #si on ne trouve pas un script inférieur on
                if len(re.findall(str(autre_script), get_running)) <= 0:
                    #on passe go à False car le script ne peut pas démarrer
                    go = False
                    #on arrête la boucle
                    if not config.print_running_text:
                        txtlog = "script " + str(config.script_num) + " STOP!"
                        config.saveLog(txtlog,1, config.newmatch)
                        print(txtlog)
                        config.print_running_text = True
                    break
                #on passe au script inférieur suivant
                autre_script = autre_script + 1
            if autre_script == config.script_num:
                if not config.print_running_text:
                    txtlog = "script " + str(config.script_num) + " GO!"
                    config.saveLog(txtlog,1, config.newmatch)
                    print(txtlog)
                    config.print_running_text = True
                go = True
                break
        else:
            if not config.print_running_text:
                txtlog = "script " + str(config.script_num) + " GO!"
                config.saveLog(txtlog,1, config.newmatch)
            go = True
            config.print_running_text = True
            break

    return go
