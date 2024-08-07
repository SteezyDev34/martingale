import time

from Functions.DeleteBet import DeleteBet
from Functions.GetIfGameStart import GetIfGameStart
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetMise import GetMise
from Functions.GetPlayersName import GetPlayersName
from Functions.GetScoreActuel import GetScoreActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.PlacerMise import PlacerMise
from Functions.GetBet import GetBet, GetNextBet
from Functions.ScriptRechercheDeMatch import rechercheDeMatch

from Functions.ValidationDuParis import ValidationDuParis
import config
from Functions import GetLigueName, VerificationMatchTrouve, Functions_stats, Functions_stats1
from Functions import Functions_1XBET
import re
from Functions.AfficherParis import AfficherParis
from Functions.Function_scriptDelRunning import scriptDelRunning

from Functions.retour_section_tps_reglementaire import RetourTpsReg
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
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.newmatch = VerificationMatchTrouve.fromUrl(driver, config.matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = GetPlayersName(driver)
        if 'wta' in config.ligue_name.lower() or 'féminin' in config.ligue_name.lower() or 'femmes' in config.ligue_name.lower() or 'women' in config.ligue_name.lower():
            config.proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
            #config.proba40A = 0.5
        else:
            config.proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            #config.proba40A = 0.5
            if config.proba40A ==  0:
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
    bet_40a = False
    while not bet_40a and not config.error:
        txtlog = 'PREPARATION DU PREMIER PARIS'
        config.saveLog(txtlog, config.newmatch)
        print(txtlog)
        #Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris', config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            break
        #On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel', config.newmatch)
        if not GetBet(driver):
            config.error = True
            config.saveLog('error recup jeu #ERR345', config.newmatch)

        config.saveLog('Premier PAris 40A cliqué', config.newmatch)
        send_mise = 0
        #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        print('cotemini : '+str(config.cotemini)+' cote : '+str(config.cote))
        print('proba mini : ' + str(config.probamini)+' proba : '+str(config.proba40A))
        print('Rattrapage : ' +str(config.rattrape_perte))
        if float(config.proba40A) < float(config.probamini) and float(config.cote) < float(config.cotemini):
            print('perte? '+str(config.perte))
            DispatchPerte()
            bet_30a = True
            config.error = True
            txtlog = 'Cote et proba trop faible 0,2'
            print(txtlog)
            config.saveLog(txtlog, config.newmatch)
            break
        elif 'itf' in config.ligue_name and 'qualification' in config.ligue_name:
            print('perte? '+str(config.perte))
            DispatchPerte()
            bet_30a = True
            config.error = True
            txtlog = 'itf qualif > LEAVE!'
            print(txtlog)
            config.saveLog(txtlog, config.newmatch)
            break
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
    while (float(winmatch) < float(config.nb_tour) and not config.error):
        # WAIT FOR GAME START
        if passageset:
            config.saved_set = ""
            config.set_actuel = GetSetActuel(driver)
            config.score_actuel = '0:0'
            gamestart = 1
            config.jeu_actuel = 0
            if config.rattrape_perte == 1:
                config.error = False
                txtlog = "passage set 2"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                time.sleep(30)
            elif config.perte >0:
                DispatchPerte()
                config.init_variable()
                txtlog = "passage set 2 restart"
                print(txtlog)
                config.saveLog(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                time.sleep(30)
            else:
                config.error = True
                print("erreur perte en 1 set")
        elif config.jeu_actuel == 13:
            while config.score_actuel !="0:1" or config.score_actuel != "1:0":
                print("wait start tie break")
            while config.score_actuel !="0:0":
                print("wait start tie break")
            time.sleep(60)
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
            if not AfficherParis(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
            if passageset :
                if not GetBet(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    print('passageset premier jeu ok')
                    passageset = False
                    bet_40a = True
            else:
                if not GetNextBet(driver):
                    config.error = True
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                else:
                    print('passage prochain jeu')
                    passageset = False
                    bet_40a = True

            config.saveLog('prochain PAris 40A cliqué', config.newmatch)
        # ON ENVOIE LA MISE
        txtlog = "ON ENVOIE LA MISE"
        print(txtlog)
        config.saveLog(txtlog, config.newmatch)
        send_mise = False
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
                winmatch += 1
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
            config.perte = 0
            try:
                DeleteBet(driver)
            except:
                print('cpn-bet__remove not found')
            break
    DispatchPerte()
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
