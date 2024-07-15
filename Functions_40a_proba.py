import random
import time

from DeleteBet import DeleteBet
from GetIfGameStart import GetIfGameStart
from Function_GetJeuActuel import GetJeuActuel
from Function_GetMise import GetMise
from GetScoreActuel import GetScoreActuel
from Function_GetSetActuel import GetSetActuel
from PlacerMise import PlacerMise
from GetBet40A import GetBet40A, GetNextBet40A
from ScriptRechercheDeMatch import rechercheDeMatch

from ValidationDuParis import ValidationDuParis
import config
import Functions_gsheets
import Functions_1XBET
import re

from Function_AfficherParis40A import AfficherParis40A
from Function_scriptDelRunning import scriptDelRunning


from retour_section_tps_reglementaire import RetourTpsReg

score_gamestart_list = [
    '15:0',
    '0:15',
    '15:15',
    '30:15',
    '15:30',
    '40:15',
    '15:40',
    '0:30',
    '30:0',
    '30:30',
    '30:40',
    '40:30',
    '0:40',
    '40:0',
    '40:40',
    'A:40',
    '40:A'
]


def all_script(driver):

    # Mise à jour du fichier txt des script en cours
    scriptDelRunning(config.script_num, config.running_file_name)


    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver):
        config.error = True
    # --------



    ##PREPARATTION PREMIER PARIS
    txtlog = 'PREPARATION DU PREMIER PARIS'
    config.saveLog(txtlog, config.newmatch)
    print(txtlog)
    bet_40a = False
    while not bet_40a and not config.error:
        #Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris', config.newmatch)
        if not AfficherParis40A(driver):
            config.error = True
            break
        #On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel', config.newmatch)
        if not GetBet40A(driver):
            config.error = True
            config.saveLog('error recup jeu #ERR345', config.newmatch)

        config.saveLog('Premier PAris 40A cliqué', config.newmatch)
        send_mise = 0
        #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        print('cotemini : '+str(config.cotemini)+' cote : '+str(config.cote))
        print('proba mini : ' + str(config.probamini)+' proba : '+str(config.proba40A))
        if float(config.proba40A) < float(config.probamini) and float(config.cote) < float(config.cotemini):
            print('perte? '+str(config.perte))
            if config.perte > 0:
                Functions_gsheets.suivi_lost()
                bet_30a = True
                config.error = True
                txtlog ='Cote et proba trop faible > sheets'
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                break
            else:
                bet_30a = True
                config.error = True
                txtlog = 'Cote et proba trop faible 0,2'
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                break
        elif 'itf' in config.ligue_name and 'qualification' in config.ligue_name:
            Functions_gsheets.suivi_lost()
            #bet_30a = True
            #config.error = True
            #txtlog = 'itf qualif > LEAVE!'
            #print(txtlog)
            #config.saveLog(txtlog, config.newmatch)
            #break
        else:
            print('!!!!!macth ok pour continuer')


        tentative_placermise = 0
        validate_bet = False
        txtlog = 'On place la mise'
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 5:
            tentative_placermise+=1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris', config.newmatch)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 30:
            # VÉRIFICATION DU SCORE ACTUEL
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if config.score_actuel == "0:0" and not gamestart:
                txtlog = "GAME NOT START"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
            elif config.score_actuel == "0:0" and gamestart:
                validate_bet = True
                config.jeu_actuel += 1
                txtlog = "GAME PASS WITHOUT VALIDATE ON FIRST"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                gamestart = False
                result = True
                lose = True
                findbtn = True
            elif config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:40":
                config.error = True
                txtlog = "40A leave!"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                DeleteBet(driver)
                break
            else:
                gamestart = True
                txtlog = "GAME START"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
            if ValidationDuParis(driver):
                validate_bet = True
                config.jeu_actuel += 1
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                bet_40a = True
                config.saveLog("prochain jeu : " + str(config.jeu_actuel), config.newmatch)
                config.saveLog("wantwin : " + str(config.wantwin), config.newmatch)
                config.saveLog("perte : " + str(config.perte), config.newmatch)
                config.saveLog("mise : " + str(config.mise), config.newmatch)
                config.saveLog("increment : " + str(config.increment), config.newmatch)
            else:
                GetJeuActuel(driver)
                tentative = tentative + 1
                validate_bet = True
                config.saveLog("Erreur lor de la validation, nouvelle tentative", config.newmatch)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    RetourTpsReg(driver)
    ### AND PREPARE FIRST GAME

    passageset = False
    winmatch = 0
    config.lose =False
    while (winmatch <= 0 and not config.error):
        # WAIT FOR GAME START
        if passageset:
            config.score_actuel = '0:0'
            gamestart = 1
            config.jeu_actuel = 0
            if config.rattrape_perte >= 0:
                config.error = False
                txtlog = "passage set 2"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                time.sleep(30)
            else:
                config.error = True
                print("erreur perte en 1 set")
        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        txtlog = "JEU COMMENCÉ ON PREPARE LE PROCHAIN BET"
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        bet_40a = False
        while not bet_40a and not config.error:

            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris', config.newmatch)
            if not AfficherParis40A(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
            if passageset :
                if not GetBet40A(driver):
                    config.error = True
                    passageset = False
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    bet_40a = True
            else:
                if not GetNextBet40A(driver):
                    config.error = True
                    passageset = False
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    bet_40a = True

            config.saveLog('prochain PAris 40A cliqué', config.newmatch)
        # ON ENVOIE LA MISE
        txtlog = "ON ENVOIE LA MISE"
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        send_mise = False
        GetMise(driver)
        while not send_mise and not config.error:
            if PlacerMise(driver):
                send_mise = True
            else:
                config.error = True
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        validate_bet = False
        config.saved_score = ""
        config.saved_set = ""
        timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
        result = False
        RetourTpsReg(driver)
        while not result and not config.error:
            time.sleep(timesleep)
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if not config.score_actuel:
                config.error = True
                break
            if config.score_actuel == '40:A' or config.score_actuel == 'A:40' or config.score_actuel == '40:40':
                result = True
                lose = False
                winmatch = True
                DeleteBet(driver)
                txtlog = 'WIN'
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
            elif config.score_actuel == '0:0':
                txtlog = 'LOSE'
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                validate_bet = False
                tentative = 0
                gamestart = False
                lose = True
                result = True

                config.saved_set = config.set_actuel
                config.set_actuel = False
                config.saveLog("vide sec actu " + str(config.set_actuel), config.newmatch)
                GetSetActuel(driver)
                newset = int(config.saved_set) +1
                if not config.set_actuel:
                    config.error = True
                config.saveLog('set ' + str(config.set_actuel)+' - saved set '+str(config.saved_set), config.newmatch)
                if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.saveLog('on est toujours sur le meme set', config.newmatch)

                    if config.jeu_actuel >= 13:  # SI TIE BREAK
                        txtlog = "jeu "+str(config.jeu_actuel)
                        print(txtlog)
                        config.saveLog(txtlog, config.newmatch)
                        txtlog = "attente fin de tie break"
                        print(txtlog)
                        config.saveLog(txtlog, config.newmatch)
                        passageset = True
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while not validate_bet and not config.error:
                            # VÉRIFICATION DU SCORE ACTUEL
                            GetScoreActuel(driver)
                            if config.score_actuel == False:
                                config.error = True
                                config.saveLog("error pendant la récupération du score", config.newmatch)
                            if config.score_actuel == "0:0" and not gamestart:
                                txtlog = "GAME NOT START"
                                print(txtlog)
                                config.saveLog(txtlog, config.newmatch)
                            elif config.score_actuel == "0:0" and gamestart:
                                validate_bet = False
                                config.jeu_actuel += 1
                                txtlog = "GAME PASS WITHOUT VALIDATE"
                                print(txtlog)
                                config.saveLog(txtlog, config.newmatch)
                                gamestart = False
                                result = True
                                lose = True
                                findbtn = True

                                ###ajouter ici les actions avant de reprendre
                            elif config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:40":
                                config.error = True
                                txtlog = "40A leave!"
                                print(txtlog)
                                config.saveLog(txtlog, config.newmatch)
                                DeleteBet(driver)
                                ###ajouter ici les actions avant de reprendre
                                break
                            else:
                                gamestart = True
                            if ValidationDuParis(driver):
                                validate_bet = 1
                                config.jeu_actuel += 1
                                config.perte = config.perte + config.mise
                                config.wantwin = float(config.wantwin) + float(config.increment)
                                print("prochain jeu : " + str(config.jeu_actuel))
                                print("wantwin : " + str(config.wantwin))
                                print("perte : " + str(config.perte))
                                print("mise : " + str(config.mise))
                                print("increment : " + str(config.increment))
                            else:
                                getjeu = config.jeu_actuel
                                GetJeuActuel(driver)
                                tentative = tentative + 1
                                if getjeu != config.jeu_actuel:
                                    validate_bet = False
                                    config.jeu_actuel =int(config.jeu_actuel)+ 1
                                    print("GAME PASS WITHOUT VALIDATE #2#")
                                    gamestart = False
                                    result = True
                                    lose = True
                                    findbtn = True
                                    break
                        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                        RetourTpsReg(driver)
                elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    txtlog = "SI ON EST SUR LE PROCHAIN SET"
                    print(txtlog)
                    config.saveLog(txtlog, config.newmatch)
                    findset = True
                    findbtn = True
                    validate = True
                    passageset = True
                    result = True
                    lose = True
                    config.score_actuel = '0:0'
                    txtlog = 'Passage prochain set'
                    print(txtlog)
                    config.saveLog(txtlog, config.newmatch)
                    DeleteBet(driver)
                    txtlog = 'Waiit 30 sec'
                    print(txtlog)
                    config.saveLog(txtlog, config.newmatch)
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + str(config.set_actuel))
                    config.error = True
            else:
                result = False
                #config.set_actuel = "nac"
                #GetSetActuel(driver)
                #config.saved_set = config.set_actuel
                if not config.set_actuel:
                    config.error = False
                else:
                    if config.saved_score != config.score_actuel:
                        config.saveLog(str(config.score_actuel), config.newmatch)
                        config.saved_score = config.score_actuel
                    numset = int(config.set_actuel.split(' ')[0])
                    newset = int(config.set_actuel.split(' ')[0]) + 1
                    if re.search('40', config.score_actuel):
                        timesleep = 1
                    else:
                        timesleep = 20
        if lose and not config.error:
            print('lose : ' + str(config.perte))
        elif not lose and not config.error:
            config.win += 1
            try:
                DeleteBet(driver)
            except:
                print('cpn-bet__remove not found')

            config.perte = 0
            config.mise = 0.2
            config.increment = 0
            config.wantwin = 0.2
            break
    if config.perte > 0:
        perte = config.perte
        while perte > config.recup40:
            config.perte = config.recup40
            config.wantwin = 0
            config.mise = config.recup40
            Functions_gsheets.suivi_lost()
            perte = perte - config.recup40
            if perte>1:
                comp_list = ['wta', 'atp', 'challenger']
                config.ligue_name = random.choice(comp_list)
                config.perte = config.recup30
                config.wantwin = 0
                config.mise = config.recup30
                Functions_gsheets.suivi_lost30()
                perte = perte - config.recup30
        config.init_variable()
        config.mise = (float(config.wantwin) + float(perte)) / (float(config.cote) - 1)
        config.mise = round(config.mise, 2)
        config.perte= perte
        Functions_gsheets.suivi_lost()
    infos = [config.win, config.perte, config.wantwin, config.mise]
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return infos
