import random
import time
from Functions.DeleteBet import DeleteBet
from Functions.GetIfGameStart import GetIfGameStart, GetIfGameStart30A, GetIfGameEnd
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetMise import GetMise
from Functions.GetBet import GetBet
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.PlacerMise import PlacerMise
from Functions.ScriptRechercheDeMatch import rechercheDeMatch

from Functions.ValidationDuParis import ValidationDuParis
import config
from Functions import GetLigueName, VerificationMatchTrouve, Functions_stats, Functions_stats1, AddRunning
from Functions import Functions_1XBET
import re
from Functions.AfficherParis import AfficherParis
from Functions.Function_scriptDelRunning import scriptDelRunning

from Functions.retour_section_tps_reglementaire import RetourTpsReg
from Functions.GetJsonData import getPerte, delPerte,DispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.FisrtGameBet import FirstGameBet
def all_script(driver):
    driver.switch_to.window(driver.window_handles[0])
    lose = True
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver):
        config.error = True
    # --------
    config.match_found = True
    if config.match_found and not config.error:
        AddRunning.main(config.script_num,config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.newmatch = VerificationMatchTrouve.fromUrl(driver, config.matchlist_file_name)[1]

        print("#RECHERCHE INFOS DE MISE")
        infosperte = getGlobalPerte()
        print("PERTE : ")
        if infosperte:
            if float(infosperte['perte']) > 100:
                SendGlobalPerte(config.scriptType, -5)
                config.perte = 5
            elif float(infosperte['perte']) > 50:
                SendGlobalPerte(config.scriptType, -3)
                config.perte = 3
            elif float(infosperte['perte']) > 20:
                SendGlobalPerte(config.scriptType, -2)
                config.perte = 2
            elif float(infosperte['perte']) > 10:
                SendGlobalPerte(config.scriptType, -1)
                config.perte = 1
            elif float(infosperte['perte']) > 1:
                SendGlobalPerte(config.scriptType, -1)
                config.perte = 1
            elif float(infosperte['perte']) <= 1:
                config.perte = float(infosperte['perte'])
                m = 0 - config.perte
                SendGlobalPerte(config.scriptType, m)
                config.perte = float(infosperte['perte'])
            config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
        GetSetActuel(driver)
        config.saved_set = config.set_actuel

        if not config.set_actuel:
            config.error = True


    ##PREPARATTION PREMIER PARIS
    FirstGameBet(driver)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    RetourTpsReg(driver)

    passageset = False
    winmatch = 0
    config.lose =False
    while (float(winmatch) < float(config.nb_tour) and not config.error):
        # WAIT FOR GAME START
        if passageset:
            score_actuel = '40:0'
            gamestart = 1
            config.jeu_actuel = 0
            config.error = False
            config.saveLog("passage set 2", config.newmatch)
            config.saveLog("attente 30 sec", config.newmatch)
            time.sleep(30)
            FirstGameBet(driver)
        elif (config.jeu_actuel+1)==13:
            GetJeuActuel(driver)
            GetIfGameEnd(driver)
            while config.score_actuel != "0:0":
                print('possible tie break, attente debut ...')
                if config.score_actuel == "30:30":
                    print("WIN")
                    bet_30a = True
                    send_mise = True
                    result = True
                    lose = False
                    print('attende un peu que le score c')
                    while config.score_actuel == "30:30":
                        GetScoreActuel(driver)
                GetScoreActuel(driver)
            GetJeuActuel(driver)
            if config.jeu_actuel==13:
                while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                    print('Tie break en cours attente début')
                    GetScoreActuel(driver)
                    time.sleep(30)
                print('tie break commencé... attente fin')
                time.sleep(60)
            passageset = True
            continue
        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameEnd(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        txtlog = "JEU COMMENCÉ ON PREPARE LE PROCHAIN BET"
        config.saveLog(txtlog, config.newmatch)
        bet_40a = False
        tentative = 0
        passageset = False
        while not bet_40a and not config.error:
            # Affichage de la liste des paris
            config.saveLog('Affichage de la liste des paris', config.newmatch)
            if not AfficherParis(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.saveLog('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
            if not GetBet(driver, True):
                tentative = tentative + 1
                if tentative > 5:
                    config.saveLog('error recup jeu #ERR345', config.newmatch)
                    config.error = True
                    tentative=0
                continue
            else:
                print('passage prochain jeu')
                bet_40a = True
            config.saveLog('prochain PAris 40A cliqué', config.newmatch)

        # ON ENVOIE LA MISE
        txtlog = "ON ENVOIE LA MISE"
        config.saveLog(txtlog, config.newmatch)
        send_mise = False
        # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        while not send_mise and not config.error:
            if PlacerMise(driver):
                send_mise = True
            else:
                config.error = True
        result = GetResult(driver)
        if result == 'LOSE':
            ##VALIDATION DU PARIS SI SCORE OK
            validate_bet = False
            tentative = 0
            while not validate_bet and not config.error and tentative < 3:
                # VÉRIFICATION DU SCORE ACTUEL
                GetScoreActuel(driver)
                if config.score_actuel == False:
                    config.error = True
                    config.saveLog("error pendant la récupération du score", config.newmatch)
                    break
                if (
                        config.score_actuel == "0:15" or config.score_actuel == "15:15" or config.score_actuel == "15:0") and gamestart:
                    config.saveLog("GAME PASS WITHOUT VALIDATE", config.newmatch)
                    FirstGameBet(driver)
                    break
                    ###ajouter ici les actions avant de reprendre
                elif config.score_actuel == "15:15":
                    config.error = True
                    config.saveLog("15A leave!", config.newmatch)
                    FirstGameBet(driver)
                    ###ajouter ici les actions avant de reprendre
                    break
                else:
                    gamestart = True
                if ValidationDuParis(driver):
                    validate_bet = True
                    config.perte = config.perte + config.mise
                    config.wantwin = float(config.wantwin) + float(config.increment)
            # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
            RetourTpsReg(driver)
            GetIfGameEnd(driver)
            #VÉRIFCATION DU SET ACTUEL
            config.saved_set = config.set_actuel
            GetSetActuel(driver)
            newset = int(config.saved_set) + 1
            if not config.set_actuel:
                config.error = True
            config.saveLog('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set), config.newmatch)
            if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                config.saveLog('on est toujours sur le meme set', config.newmatch)
                if (config.jeu_actuel+1) >= 13:#SI TIE BREAK
                    config.saveLog("jeu " + str(config.jeu_actuel), config.newmatch)
                    config.saveLog("attente fin de tie break", config.newmatch)
                    passageset = True

            elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.perte = config.perte-config.mise
                config.saveLog(txtlog, config.newmatch)
                DeleteBet(driver)
                txtlog = 'Wait 30 sec'
                config.saveLog(txtlog, config.newmatch)
                time.sleep(30)
            else:
                print("ERROR : recup set " + str(config.set_actuel))
                config.error = True
        elif result== 'WIN':
            config.perte = 0
            winmatch = winmatch +1
            passageset = True
            DeleteBet(driver)
            print("#RECHERCHE INFOS DE MISE")
            infosperte = getGlobalPerte()
            print("PERTE : ")
            if infosperte:
                if float(infosperte['perte']) > 100:
                    SendGlobalPerte(config.scriptType, -5)
                    config.perte = 5
                elif float(infosperte['perte']) > 50:
                    SendGlobalPerte(config.scriptType, -3)
                    config.perte = 3
                elif float(infosperte['perte']) > 20:
                    SendGlobalPerte(config.scriptType, -2)
                    config.perte = 2
                elif float(infosperte['perte']) > 10:
                    SendGlobalPerte(config.scriptType, -1)
                    config.perte = 1
                elif float(infosperte['perte']) > 1:
                    SendGlobalPerte(config.scriptType, -1)
                    config.perte = 1
                elif float(infosperte['perte']) <= 1:
                    config.perte = float(infosperte['perte'])
                    m = 0 - config.perte
                    SendGlobalPerte(config.scriptType, m)
                    config.perte = float(infosperte['perte'])
                config.rattrape_perte = 1
    if config.perte >0.2:
        DispatchPerte()
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True