import random
import time

from DeleteBet import DeleteBet
from GetIfGameStart import GetIfGameStart
from Function_GetJeuActuel import GetJeuActuel
from Function_GetMise import GetMise
from GetScoreActuel import GetScoreActuel
from Function_GetSetActuel import GetSetActuel
from PlacerMise import PlacerMise
from GetBet4030 import GetBet4030, GetNextBet4030
from GetBet4015 import GetBet4015, GetNextBet4015
from ScriptRechercheDeMatch import rechercheDeMatch4030

from ValidationDuParis import ValidationDuParis
import config
import Functions_gsheets
import Functions_1XBET
import re

from Function_AfficherParis4030 import AfficherParis4030
from Function_scriptDelRunning import scriptDelRunning

from selenium.webdriver.common.by import By


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
    print('reeee')

    # Mise à jour du fichier txt des script en cours
    scriptDelRunning(config.script_num, config.running_file_name)

    # --------
    # SCRIPT RECHERCHE DE MATCH
    if not rechercheDeMatch4030(driver):
        config.error = True
    # --------



    ##PREPARATTION PREMIER PARIS
    config.saveLog('PREPARATION DU PREMIER PARIS')
    bet_40a = False
    while not bet_40a and not config.error:
        #Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris')
        if not AfficherParis4030(driver):
            config.error = True
            break
        #On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel')
        jeu = GetBet4030(driver)

        if not jeu[0]:
            config.error = True
            config.saveLog('error recup jeu #ERR345')
        else:
            win_score30 = jeu[1]
        config.saveLog('Premier PAris 40A cliqué')
        send_mise = 0
        #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        if config.proba40A < 0.39 and config.cote < 3.4:
            if config.perte >0:
                Functions_gsheets.suivi_lost()
            #bet_40a = True
            #config.error = True
            #config.saveLog('Cote trop faible 0,2')
            #break
        tentative_placermise = 0
        validate_bet = False
        config.saveLog('On place la mise')
        while not PlacerMise(driver) and not config.error and tentative_placermise < 5:
            tentative_placermise+=1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris')
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 30:
            # VÉRIFICATION DU SCORE ACTUEL
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if config.score_actuel == "0:0" and not gamestart:
                config.saveLog("GAME NOT START")
            elif config.score_actuel == "0:0" and gamestart:
                validate_bet = True
                config.jeu_actuel += 1
                config.saveLog("GAME PASS WITHOUT VALIDATE ON FIRST")
                gamestart = False
                result = True
                lose = True
                findbtn = True
                if win_score30 == '30:40':
                    win_score30 = '40:30'
                else:
                    win_score30 = '30:40'
            else:
                gamestart = True
                config.saveLog("GAME START")
            if ValidationDuParis(driver):
                validate_bet = True
                bet_40a = True
            else:
                GetJeuActuel(driver)
                tentative = tentative + 1
                validate_bet = True
                config.saveLog("Erreur lor de la validation, nouvelle tentative")

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    config.saveLog("retour tps reg 1")
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
                config.saveLog("passage set 2")
                config.saveLog("attente 30 sec")
                time.sleep(30)
                passageset = False
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
            passageset = False
            gamestart = 0
        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        config.saveLog("JEU COMMENCÉ ON PREPARE LE PROCHAIN BET")
        bet_40a = False
        while not bet_40a and not config.error:

            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris')
            if not AfficherParis4030(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel')
            if config.jeu_actuel == 1:
                jeu = GetBet4030(driver)
            else:
                jeu = GetNextBet4030(driver)
            if not jeu[0]:
                config.error = True
                config.saveLog('error recup jeu #ERR345')
            else:
                win_score30 = jeu[1]
                bet_40a = True

            config.saveLog('prochain PAris 40A cliqué')
        # ON ENVOIE LA MISE
        config.saveLog("ON ENVOIE LA MISE")
        send_mise = False
        GetMise(driver)
        while not send_mise and not config.error:
            if PlacerMise(driver):
                send_mise = True
            else:
                config.error = True
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        config.saveLog("ON ATTEND LE RESULTAT POUR VALIDER LE PARIS")
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
            print('win score 30 = '+ win_score30)
            if not config.score_actuel:
                print('test scorree actuel')
                config.error = True
                break
            print(f"score_actuel: {config.score_actuel} (type: {type(config.score_actuel)})")
            print(f"saved_score: {saved_score} (type: {type(saved_score)})")
            print(f"win_score30: {win_score30} (type: {type(win_score30)})")
            if config.score_actuel == '0:0' and saved_score == win_score30:
                result = True
                lose = False
                winmatch = True
                DeleteBet(driver)
                config.saveLog('WIN')
            elif config.score_actuel == '0:0' and saved_score != win_score30:
                config.saveLog('LOSE')
                validate_bet = False
                tentative = 0
                gamestart = False
                lose = True
                result = True

                config.saved_set = config.set_actuel
                config.set_actuel = False
                config.saveLog("vide sec actu " + str(config.set_actuel))
                GetSetActuel(driver)
                newset = int(config.saved_set) +1
                if not config.set_actuel:
                    config.error = True
                config.saveLog('set ' + str(config.set_actuel)+' - saved set '+str(config.saved_set))
                if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.saveLog('on est toujours sur le meme set')

                    if config.jeu_actuel >= 13:  # SI TIE BREAK
                        config.saveLog("jeu "+str(config.jeu_actuel))
                        config.saveLog("attente fin de tie break")
                        passageset = True
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while not validate_bet and not config.error:
                            # VÉRIFICATION DU SCORE ACTUEL
                            GetScoreActuel(driver)
                            if config.score_actuel == False:
                                config.error = True
                                config.saveLog("error pendant la récupération du score")
                            if config.score_actuel == "0:0" and not gamestart:
                                config.saveLog("GAME NOT START")
                            elif config.score_actuel == "0:0" and gamestart:
                                validate_bet = False
                                config.jeu_actuel += 1
                                config.saveLog("GAME PASS WITHOUT VALIDATE")
                                gamestart = False
                                result = True
                                lose = True
                                findbtn = True
                                ###ajouter ici les actions avant de reprendre
                            else:
                                gamestart = True
                            if ValidationDuParis(driver):
                                validate_bet = True
                                config.jeu_actuel += 1
                                config.perte = float(config.perte) + float(config.mise)
                                config.wantwin = float(config.wantwin) + float(config.increment)
                                bet_40a = True
                                config.saveLog("prochain jeu : " + str(config.jeu_actuel))
                                config.saveLog("wantwin : " + str(config.wantwin))
                                config.saveLog("perte : " + str(config.perte))
                                config.saveLog("mise : " + str(config.mise))
                                config.saveLog("increment : " + str(config.increment))
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
                        config.saveLog("retour tps reg 3")
                        RetourTpsReg(driver)
                elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    config.saveLog("SI ON EST SUR LE PROCHAIN SET")
                    findset = True
                    findbtn = True
                    validate = True
                    passageset = True
                    result = True
                    lose = True
                    config.score_actuel = '0:0'
                    config.saveLog('Passage prochain set')
                    DeleteBet(driver)
                    config.saveLog('Waiit 30 sec')
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
                        config.saveLog(str(config.score_actuel))
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
        while perte > 1:
            config.perte = 1
            config.wantwin = 0
            config.mise = 0.5
            Functions_gsheets.suivi_lost()
            perte = perte - 1
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
        Functions_gsheets.suivi_lost()
    infos = [config.win, config.perte, config.wantwin, config.mise]
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return infos
