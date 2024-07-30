import time

from Functions.DeleteBet import DeleteBet
from Functions.GetIfGameStart import GetIfGameStart
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetMise import GetMise4030
from Functions.GetScoreActuel import GetScoreActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.PlacerMise import PlacerMise4030
from Functions.GetBet4015 import GetBet4015, GetNextBet4015
from Functions.ScriptRechercheDeMatch import rechercheDeMatch4030

from Functions.ValidationDuParis import ValidationDuParis4030
import config
from Functions import Functions_gsheets
from Functions import Functions_1XBET
import re

from Functions.Function_AfficherParis4030 import AfficherParis4030
from Functions.Function_scriptDelRunning import scriptDelRunning

from Functions.retour_section_tps_reglementaire import RetourTpsReg

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
    while not rechercheDeMatch4030(driver):
        config.error = True
    # --------


    print('config.ligue_name : '+config.ligue_name)

    ##PREPARATTION PREMIER PARIS
    config.saveLog('PREPARATION DU PREMIER PARIS',config.newmatch)
    bet_40a = False
    while not bet_40a and not config.error:
        #Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris',config.newmatch)
        if not AfficherParis4030(driver):
            config.error = True
            break
        #On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel',config.newmatch)
        jeu = GetBet4015(driver)

        if not jeu[0]:
            config.error = True
            config.saveLog('error recup jeu #ERR345',config.newmatch)
        else:
            win_scor15 = jeu[1]
        config.saveLog('Premier PAris 40A cliqué',config.newmatch)
        send_mise = 0
        #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise4030(driver)
        print('perte'+str(config.perte))
        if config.proba40A < 0.39 and config.cote < 3.4:
            if config.perte >0:
                print('teretet')
                #Functions_gsheets.suivi_lost4030()
            #bet_40a = True
            #config.error = True
            #config.saveLog('Cote trop faible 0,2',config.newmatch)
            #break
        tentative_placermise = 0
        validate_bet = False
        config.saveLog('On place la mise',config.newmatch)
        while not PlacerMise4030(driver,config.mise) and not config.error and tentative_placermise < 5:
            tentative_placermise+=1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris',config.newmatch)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 30:
            # VÉRIFICATION DU SCORE ACTUEL
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if config.score_actuel == "0:0" and not gamestart:
                config.saveLog("GAME NOT START",config.newmatch)
            elif config.score_actuel == "0:0" and gamestart:
                validate_bet = True
                config.jeu_actuel += 1
                config.saveLog("GAME PASS WITHOUT VALIDATE ON FIRST",config.newmatch)
                gamestart = False
                result = True
                lose = True
                findbtn = True
                if win_scor15 == '15:40':
                    win_scor15 = '40:15'
                else:
                    win_score15 = '15:40'
            else:
                gamestart = True
                config.saveLog("GAME START",config.newmatch)
            if ValidationDuParis4030(driver, config.mise):
                validate_bet = True
                bet_40a = True
                config.jeu_actuel +=1
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                config.saveLog("prochain jeu : " + str(config.jeu_actuel), config.newmatch)
                config.saveLog("wantwin : " + str(config.wantwin), config.newmatch)
                config.saveLog("perte : " + str(config.perte), config.newmatch)
                config.saveLog("mise : " + str(config.mise), config.newmatch)
                config.saveLog("increment : " + str(config.increment), config.newmatch)
            else:
                GetJeuActuel(driver)
                tentative = tentative + 1
                validate_bet = True
                config.saveLog("Erreur lor de la validation, nouvelle tentative",config.newmatch)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    config.saveLog("retour tps reg 1",config.newmatch)
    RetourTpsReg(driver)
    ### AND PREPARE FIRST GAME
    passageset = False
    winmatch = 0
    config.lose =False
    lose = False
    while (winmatch <= 0 and not config.error):
        print("wzit")
        # WAIT FOR GAME START
        if passageset:
            print("passage àà")
            config.score_actuel = '0:0'
            gamestart = 1
            config.jeu_actuel = 0
            if config.rattrape_perte > 0:
                config.error = False
                config.saveLog("passage set 2",config.newmatch)
                config.saveLog("attente 30 sec",config.newmatch)
                time.sleep(30)
            else:
                config.error = True
                print("erreur perte en 1 set")
        elif str(config.jeu_actuel) == '13':
            while config.score_actuel != "0:1" and config.score_actuel != "1:0":
                GetScoreActuel(driver)
                time.sleep(30)
            while config.score_actuel != "0:0":
                GetScoreActuel(driver)
                time.sleep(30)
            gamestart = 0
        else:
            gamestart = False
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        config.saveLog("JEU COMMENCÉ ON PREPARE LE PROCHAIN BET",config.newmatch)
        bet_40a = False
        while not bet_40a and not config.error:

            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris',config.newmatch)
            if not AfficherParis4030(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            GetJeuActuel(driver)
            config.saveLog('liste des paris affichée, On recherche le jeu actuel',config.newmatch)
            if passageset:
                print("jeu 1 > "+str(config.jeu_actuel))
                jeu = GetBet4015(driver)
                passageset = False
            else:
                print("jeu > " + str(config.jeu_actuel))
                jeu = GetNextBet4015(driver)
            if not jeu[0]:
                config.error = True
                config.saveLog('error recup jeu #ERR345',config.newmatch)
            else:
                win_score15 = jeu[1]
                bet_40a = True

            config.saveLog('prochain PAris 40A cliqué',config.newmatch)
        # ON ENVOIE LA MISE
        config.saveLog("ON ENVOIE LA MISE",config.newmatch)
        send_mise = False
        GetMise4030(driver)
        while not send_mise and not config.error:
            if PlacerMise4030(driver, config.mise):
                send_mise = True
            else:
                config.error = True
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        config.saveLog("ON ATTEND LE RESULTAT POUR VALIDER LE PARIS",config.newmatch)
        validate_bet = False
        config.saved_score = ""
        config.saved_set = ""
        timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
        result = False
        RetourTpsReg(driver)
        while not result and not config.error:
            time.sleep(timesleep)
            saved_score = config.score_actuel
            GetScoreActuel(driver)
            if not config.score_actuel:
                config.error = True
                break
            if config.score_actuel == '0:0' and saved_score == win_score15:
                result = True
                lose = False
                winmatch = True
                DeleteBet(driver)
                config.saveLog('WIN',config.newmatch)
            elif config.score_actuel == '0:0' and saved_score != win_score15:
                config.saveLog('LOSE',config.newmatch)
                validate_bet = False
                tentative = 0
                gamestart = False
                lose = True
                result = True

                config.saved_set = config.set_actuel
                config.set_actuel = False
                config.saveLog("vide sec actu " + str(config.set_actuel),config.newmatch)
                GetSetActuel(driver)
                newset = int(config.saved_set) +1
                if not config.set_actuel:
                    config.error = True
                config.saveLog('set ' + str(config.set_actuel)+' - saved set '+str(config.saved_set),config.newmatch)
                if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.saveLog('on est toujours sur le meme set',config.newmatch)

                    if config.jeu_actuel >= 13:  # SI TIE BREAK
                        config.saveLog("jeu "+str(config.jeu_actuel),config.newmatch)
                        config.saveLog("attente fin de tie break",config.newmatch)
                        passageset = True
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while not validate_bet and not config.error:
                            # VÉRIFICATION DU SCORE ACTUEL
                            GetScoreActuel(driver)
                            if config.score_actuel == False:
                                config.error = True
                                config.saveLog("error pendant la récupération du score",config.newmatch)
                            if config.score_actuel == "0:0" and not gamestart:
                                config.saveLog("GAME NOT START",config.newmatch)
                            elif config.score_actuel == "0:0" and gamestart:
                                validate_bet = False
                                config.jeu_actuel += 1
                                config.saveLog("GAME PASS WITHOUT VALIDATE",config.newmatch)
                                gamestart = False
                                result = True
                                lose = True
                                findbtn = True
                                ###ajouter ici les actions avant de reprendre
                            else:
                                gamestart = True
                            if ValidationDuParis4030(driver,config.mise):
                                validate_bet = True
                                config.jeu_actuel += 1
                                config.perte = float(config.perte) + float(config.mise)
                                config.wantwin = float(config.wantwin) + float(config.increment)
                                bet_40a = True
                                config.saveLog("prochain jeu : " + str(config.jeu_actuel),config.newmatch)
                                config.saveLog("wantwin : " + str(config.wantwin),config.newmatch)
                                config.saveLog("perte : " + str(config.perte),config.newmatch)
                                config.saveLog("mise : " + str(config.mise),config.newmatch)
                                config.saveLog("increment : " + str(config.increment),config.newmatch)
                            else:
                                getjeu = config.jeu_actuel
                                GetJeuActuel(driver)
                                tentative = tentative + 1
                                if getjeu != config.jeu_actuel+1:
                                    validate_bet = False
                                    config.jeu_actuel =int(config.jeu_actuel)+ 1
                                    print("GAME PASS WITHOUT VALIDATE #2#")
                                    gamestart = False
                                    result = True
                                    lose = True
                                    findbtn = True
                                    break
                        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                        config.saveLog("retour tps reg 3",config.newmatch)
                        RetourTpsReg(driver)
                elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    config.saveLog("SI ON EST SUR LE PROCHAIN SET",config.newmatch)
                    findset = True
                    findbtn = True
                    validate = True
                    passageset = True
                    result = True
                    lose = True
                    config.score_actuel = '0:0'
                    config.saveLog('Passage prochain set',config.newmatch)
                    DeleteBet(driver)
                    config.saveLog('Waiit 30 sec',config.newmatch)
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
                        config.saveLog(str(config.score_actuel),config.newmatch)
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
            print('lllose')
            try:
                DeleteBet(driver)
            except:
                print('cpn-bet__remove not found')

            config.perte = 0
            config.mise = 0.2
            config.increment = 0
            config.wantwin = 0.2
            break
        else :
            print('no lose')
            print(winmatch)
            print(config.error)
    if config.perte > 0:
        perte = config.perte
        while perte > 5:
            config.perte = 5
            config.wantwin = 0
            config.mise = 0.5
            Functions_gsheets.suivi_lost30()
            perte = perte - 5
            """if perte>1:
                comp_list = ['wta', 'atp', 'challenger']
                config.ligue_name = random.choice(comp_list)
                config.perte = 1
                config.wantwin = 0
                config.mise = 0.61
                Functions_gsheets.suivi_lost30()
                perte = perte - 1"""

        config.mise = (float(config.wantwin) + float(perte)) / (float(config.cote) - 1)
        config.mise = round(config.mise, 2)
        config.perte= perte
        Functions_gsheets.suivi_lost4030()
    infos = [config.win, config.perte, config.wantwin, config.mise]
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return infos
