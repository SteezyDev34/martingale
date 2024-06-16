import random
import time
from DeleteBet import DeleteBet
from GetIfGameStart import GetIfGameStart, GetIfGameStart30A
from Function_GetJeuActuel import GetJeuActuel
from Function_GetMise import GetMise, GetMise30A
from GetBet30A import GetBet30A, GetNextBet30A
from GetScoreActuel import GetScoreActuel
from Function_GetSetActuel import GetSetActuel
from PlacerMise import PlacerMise
from ScriptRechercheDeMatch import rechercheDeMatch
from retour_section_tps_reglementaire import RetourTpsReg
from ValidationDuParis import ValidationDuParis
import config
import Functions_gsheets
import Functions_1XBET
import re
from Function_AfficherParis40A import AfficherParis40A
from Function_scriptDelRunning import scriptDelRunning
from selenium.webdriver.common.by import By
compet_not_ok_list = [
    'cyber',
    'world',
    'ace',
    'russie'
]
score_to_start = [
"00(0)00(0)",
"00(15)00(0)",
"00(15)00(15)",
"00(0)00(15)",
]
def all_script(driver):
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning(config.script_num, config.running_file_name)
    config.init_variable()

    # --------
    # SCRIPT RECHERCHE DE MATCH
    if not rechercheDeMatch(driver):
        config.error = True
    # --------



    ##PREPARATTION PREMIER PARIS
    config.saveLog('PREPARATION DU PREMIER PARIS')
    bet_30a = False
    first_game_pass = False
    while not bet_30a and not config.error:
        # Affichage de la liste des paris
        config.saveLog('On vérifie le score')
        GetScoreActuel(driver)
        if config.score_actuel == "30:30" or config.score_actuel == "30:15" or config.score_actuel == "15:30" or config.score_actuel == "30:0" or config.score_actuel == "0:30" or config.score_actuel == "30:40" or config.score_actuel == "40:30" or config.score_actuel == "0:40" or config.score_actuel == "15:40" or config.score_actuel == "40:40" or config.score_actuel == "A:40" or config.score_actuel == "40:A" or config.score_actuel == "40:0" or config.score_actuel == "40:15":
            first_game_pass = True
            config.saveLog('score : '+config.score_actuel+' ...first game passss')
            bet_30a = True
        # Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris')
        if not AfficherParis40A(driver):
            config.error = True
            break
        # On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel')
        if not GetBet30A(driver):
            config.error = True
            config.saveLog('error recup jeu #ERR345')

        config.saveLog('Premier PAris 30A cliqué')
        config.saveLog("on attebnd 2 sec que la paris s'affiche bien pour recuprer la cote")
        time.sleep(2)
        GetMise30A(driver)
        print('perte '+str(config.perte))
        if config.proba40A < config.probamini and config.cote < config.cotemini: #and config.perte<=0:
            if config.perte > 0:
                Functions_gsheets.suivi_lost()
            bet_30a = True
            config.error = True
            config.saveLog('Cote trop faible 0,2')
            break
        tentative_placermise = 0
        validate_bet = False
        config.saveLog('On place la mise')
        while not PlacerMise(driver) and not config.error and tentative_placermise < 5:
            tentative_placermise += 1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris')
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 10:
            # VÉRIFICATION DU SCORE ACTUEL
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if config.score_actuel == "30:30":
                config.error = True
                print("30A leave!")
                DeleteBet(driver)
                ###ajouter ici les actions avant de reprendre
                break
            else:
                gamestart = True
                config.saveLog("GAME START")
            if ValidationDuParis(driver):
                validate_bet = True
                config.jeu_actuel += 1
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                bet_30a = True
                config.saveLog("prochain jeu : " + str(config.jeu_actuel))
                config.saveLog("wantwin : " + str(config.wantwin))
                config.saveLog("perte : " + str(config.perte))
                config.saveLog("mise : " + str(config.mise))
                config.saveLog("increment : " + str(config.increment))
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
    winmatch = False
    lose = False
    while not winmatch and not config.error:
        # WAIT FOR GAME START
        if passageset:
            score_actuel = '40:0'
            gamestart = 1
            config.jeu_actuel = 0
            if config.rattrape_perte == 1:
                config.error = False
                config.saveLog("passage set 2")
                config.saveLog("attente 30 sec")
            else:
                config.error = True
                print("erreur perte en 1 set")

        elif config.jeu_actuel==13:
            while config.score_actuel != "0:1" or config.score_actuel != "1:0" or config.score_actuel != "1:1" or config.score_actuel != "2:0" or config.score_actuel != "0:2":
                print('possible tie break, attente debut ...')
                GetScoreActuel(driver)
                if config.score_actuel == "30:30":
                    print("WIN")
                    bet_30a = True
                    send_mise = True
                    result = True
                    lose = False

                GetScoreActuel(driver)
            print('tie break commencé... attente fin')
            while config.score_actuel != "0:0":
                print('Tie break en cours attente du prochain set')
                GetScoreActuel(driver)
            passageset = True
            continue

        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart30A(driver)
        config.saveLog("JEU COMMENCÉ ON PREPARE LE PROCHAIN BET")
        bet_30a = False
        while not bet_30a and not config.error:
            config.saved_set = config.set_actuel
            config.set_actuel = False
            config.saveLog("vide sec actu " + str(config.set_actuel))
            GetSetActuel(driver)
            newset = int(config.saved_set) + 1
            if not config.set_actuel:
                config.error = True
            config.saveLog('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set))
            if str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                config.saveLog("SI ON EST SUR LE PROCHAIN SET")
                passageset = True
                result = True
                lose = True
                config.score_actuel = '40:0'
                config.saveLog('Passage prochain set')
                DeleteBet(driver)
                config.saveLog('Waiit 30 sec')
                time.sleep(30)

            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris')
            if not AfficherParis40A(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel')
            if passageset:
                if not GetBet30A(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345')
                else:
                    bet_30a = True
            else:
                if not GetNextBet30A(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345')
                else:
                    bet_30a = True

            config.saveLog('prochain PAris 30A cliqué')
            config.saveLog("on attebnd 2 sec que la paris s'affiche bien pour recuprer la cote")
            time.sleep(2)
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
            if passageset or config.score_actuel == '40:0' or config.score_actuel == '40:15' or config.score_actuel == '0:40' or config.score_actuel == '15:40' or config.score_actuel == '40:30' or config.score_actuel == '30:40' or config.score_actuel == '40:40' or config.score_actuel == 'A:40' or config.score_actuel == '40:A':
                config.saveLog('LOSE')
                validate_bet = False
                tentative = 0
                gamestart = False
                lose = True
                result = True
                passageset = False

                config.saved_set = config.set_actuel
                config.set_actuel = False
                config.saveLog("vide sec actu " + str(config.set_actuel))
                GetSetActuel(driver)
                newset = int(config.saved_set) + 1
                if not config.set_actuel:
                    config.error = True
                config.saveLog('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set))
                if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.saveLog('on est toujours sur le meme set')
                    if config.jeu_actuel > 13:#SI TIE BREAK
                        config.saveLog("jeu " + str(config.jeu_actuel))
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
                                break
                            if (config.score_actuel == "0:15" or config.score_actuel == "15:15" or config.score_actuel == "15:0" or config.score_actuel == "0:30" or config.score_actuel == "15:30" or config.score_actuel == "30:15" or config.score_actuel == "30:0") and gamestart:
                                validate_bet = False
                                config.jeu_actuel += 1
                                config.saveLog("GAME PASS WITHOUT VALIDATE")
                                gamestart = False
                                result = True
                                lose = True
                                findbtn = True

                                ###ajouter ici les actions avant de reprendre
                            elif config.score_actuel == "30:30":
                                config.error = True
                                config.saveLog("30A leave!")
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
                                    config.jeu_actuel += 1
                                    print("GAME PASS WITHOUT VALIDATE #2#")
                                    gamestart = False
                                    result = True
                                    lose = True
                                    findbtn = True
                                    break
                        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                        print("retour tps reg 3")
                        RetourTpsReg(driver)
                elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    config.saveLog("SI ON EST SUR LE PROCHAIN SET")
                    findset = True
                    findbtn = True
                    validate = True
                    passageset = True
                    result = True
                    lose = True
                    config.score_actuel = '40:0'
                    config.saveLog('Passage prochain set')
                    DeleteBet(driver)
                    config.saveLog('Waiit 30 sec')
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + str(config.set_actuel))
                    config.error = True
            elif config.score_actuel == '30:30':
                result = True
                lose = False
                winmatch = True
                DeleteBet(driver)
                config.saveLog('WIN')
            else:
                result = False
                # config.set_actuel = "nac"
                # GetSetActuel(driver)
                # config.saved_set = config.set_actuel
                if not config.set_actuel:
                    config.error = False
                else:
                    if config.saved_score != config.score_actuel:
                        config.saveLog(str(config.score_actuel))
                        config.saved_score = config.score_actuel
                    numset = int(config.set_actuel.split(' ')[0])
                    newset = int(config.set_actuel.split(' ')[0]) + 1
                    if re.search('30', config.score_actuel):
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
            config.mise = 0.5
            config.increment = 0
            config.wantwin = 1
            break
    if config.perte > 0:
        perte = config.perte
        while perte > 2:
            config.perte = 2
            config.wantwin = 0
            config.mise = 1
            Functions_gsheets.suivi_lost()
            perte = perte - 2
            if perte > 1:
                comp_list = ['wta', 'atp', 'challenger']
                config.ligue_name = random.choice(comp_list)
                config.perte = 1
                config.wantwin = 0
                config.mise = 0.61
                Functions_gsheets.suivi_lost30()
                perte = perte - 1

        config.mise = (float(config.wantwin) + float(perte)) / (float(config.cote) - 1)
        config.mise = round(config.mise, 2)
        config.perte = perte
        Functions_gsheets.suivi_lost()
    config.init_variable()
    infos = [config.win, config.perte, config.wantwin, config.mise]
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return infos
