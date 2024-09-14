import random
import time
from Functions.DeleteBet import DeleteBet
from Functions.GetIfGameStart import GetIfGameStart30A
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetMise import GetMise
from Functions.GetBet import GetBet, GetNextBet
from Functions.GetPlayersName import GetPlayersName
from Functions.GetScoreActuel import GetScoreActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.PlacerMise import PlacerMise
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.retour_section_tps_reglementaire import RetourTpsReg
from Functions.ValidationDuParis import ValidationDuParis
import config
from Functions import GetLigueName, VerificationMatchTrouve, Functions_stats, Functions_stats1, AddRunning
from Functions import Functions_1XBET
import re
from Functions.AfficherParis import AfficherParis
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetJsonData import getPerte, delPerte,DispatchPerte

def all_script(driver):
    lose = True

    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()

    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver):
        config.error = True
    # --------

    if config.match_found and not config.error:
        AddRunning.main(config.script_num, config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.newmatch = VerificationMatchTrouve.fromUrl(driver, config.matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = GetPlayersName(driver)
        if 'wta' in config.ligue_name.lower() or 'féminin' in config.ligue_name.lower() or 'femmes' in config.ligue_name.lower() or 'women' in config.ligue_name.lower():
            config.proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
            # config.proba40A = 0.5
        else:
            config.proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            # config.proba40A = 0.5
            if config.proba40A == 0:
                config.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1], driver, config.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infosperte = getPerte()
        print("PERTE : ")
        print(infosperte)
        if infosperte:
            config.perte = float(infosperte['perte'])
            delPerte(infosperte['id'])
            config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
        config.set_actuel = GetSetActuel(driver)
        config.saved_set = config.set_actuel
        if not config.set_actuel:
            config.error = True
    ##PREPARATTION PREMIER PARIS
    config.saveLog('PREPARATION DU PREMIER PARIS', config.newmatch)
    bet_15a = False
    first_game_pass = False
    while not bet_15a and not config.error:
        # Affichage de la liste des paris
        config.saveLog('On vérifie le score', config.newmatch)
        GetScoreActuel(driver)
        if config.score_actuel == "15:15" or config.score_actuel == "0:15" or config.score_actuel == "15:0" or config.score_actuel == "30:30" or config.score_actuel == "30:15" or config.score_actuel == "15:30" or config.score_actuel == "30:0" or config.score_actuel == "0:30" or config.score_actuel == "30:40" or config.score_actuel == "40:30" or config.score_actuel == "0:40" or config.score_actuel == "15:40" or config.score_actuel == "40:40" or config.score_actuel == "A:40" or config.score_actuel == "40:A" or config.score_actuel == "40:0" or config.score_actuel == "40:15":
            first_game_pass = True
            config.saveLog('score : '+config.score_actuel+' ...first game passss', config.newmatch)
            bet_15a = True
            gamestart = True
        # Affichage de la liste des parisdcs
        config.saveLog('Affichage de la liste des paris', config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            break
        # On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel', config.newmatch)
        if first_game_pass:
            if not GetNextBet(driver):
                config.error = True
                config.saveLog('error recup jeu #ERR345', config.newmatch)
        else:
            if not GetBet(driver):
                config.error = True
                config.saveLog('error recup jeu #ERR345', config.newmatch)

        config.saveLog('Premier PAris 15A cliqué', config.newmatch)
        config.saveLog("on attebnd 2 sec que la paris s'affiche bien pour recuprer la cote", config.newmatch)
        time.sleep(2)
        GetMise(driver)
        print('cotemini : ' + str(config.cotemini) + ' cote : ' + str(config.cote))
        print('proba mini : ' + str(config.probamini) + ' proba : ' + str(config.proba40A))
        if config.proba40A < config.probamini and config.cote < config.cotemini and (config.perte<=0 or not config.perte):
            bet_15a = True
            config.error = True
            config.saveLog('Cote trop faible 0,2', config.newmatch)
            break

        tentative_placermise = 0
        validate_bet = False
        config.saveLog('On place la mise', config.newmatch)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 5:
            tentative_placermise += 1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris', config.newmatch)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 10:
            # VÉRIFICATION DU SCORE ACTUEL
            GetScoreActuel(driver)
            config.saved_score = config.score_actuel
            if config.score_actuel == "15:15":
                config.error = True
                print("15A leave!")
                DeleteBet(driver)
                ###ajouter ici les actions avant de reprendre
                break
            else:
                gamestart = True
                config.saveLog("GAME START", config.newmatch)
            if ValidationDuParis(driver):
                validate_bet = True
                config.jeu_actuel += 1
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                bet_15a = True
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
    config.saveLog("retour tps reg 1", config.newmatch)
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
            if config.rattrape_perte != 9:
                config.error = False
                config.saveLog("passage set 2", config.newmatch)
                config.saveLog("attente 30 sec", config.newmatch)
            else:
                config.error = True
                print("erreur perte en 1 set")

        elif config.jeu_actuel==13:
            while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                print('possible tie break, attente debut ...')
                GetScoreActuel(driver)
                if config.score_actuel == "15:15":
                    print("WIN")
                    bet_15a = True
                    send_mise = True
                    result = True
                    lose = False
                GetJeuActuel(driver)
                if config.jeu_actuel == 1:
                    break
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
        config.saveLog("JEU COMMENCÉ ON PREPARE LE PROCHAIN BET", config.newmatch)
        bet_15a = False
        while not bet_15a and not config.error:
            config.saved_set = config.set_actuel
            config.set_actuel = False
            config.saveLog("vide sec actu " + str(config.set_actuel), config.newmatch)
            GetSetActuel(driver)
            newset = int(config.saved_set) + 1
            if not config.set_actuel:
                config.error = True
            config.saveLog('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set), config.newmatch)
            if str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                config.saveLog("SI ON EST SUR LE PROCHAIN SET", config.newmatch)
                passageset = True
                result = True
                lose = True
                config.score_actuel = '40:0'
                config.saveLog('Passage prochain set', config.newmatch)
                DeleteBet(driver)
                config.saveLog('Waiit 30 sec', config.newmatch)
                time.sleep(30)

            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris', config.newmatch)
            if not AfficherParis(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
            if passageset:
                config.perte = config.perte-config.mise
                if not GetBet(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    bet_15a = True
            else:
                if not GetNextBet(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    bet_15a = True

            config.saveLog('prochain PAris 15A cliqué', config.newmatch)
            config.saveLog("on attebnd 2 sec que la paris s'affiche bien pour recuprer la cote", config.newmatch)
            time.sleep(2)
        # ON ENVOIE LA MISE
        config.saveLog("ON ENVOIE LA MISE", config.newmatch)
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
            if passageset or config.score_actuel == '0:30' or config.score_actuel == '30:0':
                config.saveLog('LOSE', config.newmatch)
                validate_bet = False
                tentative = 0
                gamestart = False
                lose = True
                result = True
                passageset = False

                config.saved_set = config.set_actuel
                config.set_actuel = False
                config.saveLog("vide sec actu " + str(config.set_actuel), config.newmatch)
                GetSetActuel(driver)
                newset = int(config.saved_set) + 1
                if not config.set_actuel:
                    config.error = True
                config.saveLog('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set), config.newmatch)
                if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.saveLog('on est toujours sur le meme set', config.newmatch)
                    if config.jeu_actuel > 13:#SI TIE BREAK
                        config.saveLog("jeu " + str(config.jeu_actuel), config.newmatch)
                        config.saveLog("attente fin de tie break", config.newmatch)
                        passageset = True
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while not validate_bet and not config.error:
                            # VÉRIFICATION DU SCORE ACTUEL
                            GetScoreActuel(driver)
                            if config.score_actuel == False:
                                config.error = True
                                config.saveLog("error pendant la récupération du score", config.newmatch)
                                break
                            if (config.score_actuel == "0:15" or config.score_actuel == "15:15" or config.score_actuel == "15:0" or config.score_actuel == "0:30" or config.score_actuel == "15:30" or config.score_actuel == "30:15" or config.score_actuel == "30:0" or config.score_actuel == "40:15" or config.score_actuel == "40:0"or config.score_actuel == "15:40" or config.score_actuel == "0:40" or config.score_actuel == "30:40" or config.score_actuel == "40:30" or config.score_actuel == "40:40") and gamestart:
                                validate_bet = False
                                config.jeu_actuel += 1
                                config.saveLog("GAME PASS WITHOUT VALIDATE", config.newmatch)
                                gamestart = False
                                result = True
                                lose = True
                                findbtn = True

                                ###ajouter ici les actions avant de reprendre
                            elif config.score_actuel == "15:15":
                                config.error = True
                                config.saveLog("15A leave!", config.newmatch)
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
                    config.saveLog("SI ON EST SUR LE PROCHAIN SET", config.newmatch)
                    findset = True
                    findbtn = True
                    validate = True
                    passageset = True
                    result = True
                    lose = True
                    config.score_actuel = '40:0'
                    config.saveLog('Passage prochain set', config.newmatch)
                    DeleteBet(driver)
                    config.saveLog('Waiit 30 sec', config.newmatch)
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + str(config.set_actuel))
                    config.error = True
            elif config.score_actuel == '15:15':
                result = True
                lose = False
                winmatch = True
                DeleteBet(driver)
                config.saveLog('WIN', config.newmatch)
            else:
                result = False
                # config.set_actuel = "nac"
                # GetSetActuel(driver)
                # config.saved_set = config.set_actuel
                if not config.set_actuel:
                    config.error = False
                else:
                    if config.saved_score != config.score_actuel:
                        config.saveLog(str(config.score_actuel), config.newmatch)
                        config.saved_score = config.score_actuel
                    numset = int(config.set_actuel.split(' ')[0])
                    newset = int(config.set_actuel.split(' ')[0]) + 1
                    if re.search('15', config.score_actuel):
                        timesleep = 1
                    else:
                        timesleep = 20
        if lose and not config.error:
            print('lose : ' + str(config.perte))
        elif not lose and not config.error:
            config.win += 1
            config.perte = 0
            try:
                DeleteBet(driver)
            except:
                print('cpn-bet__remove not found')
            break
    if config.perte >0.2:
        DispatchPerte()
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
