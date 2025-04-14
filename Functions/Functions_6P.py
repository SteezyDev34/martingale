import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, VerificationMatchTrouve, AddRunning
from Functions.AfficherParis import AfficherParis
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetBet import GetBet
from Functions.GetIfGameStart import GetIfGameStart, GetIfGameEnd
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.GetMise import GetMise
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    lose = True
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver) and not config.error:
        current_frame = inspect.currentframe()
        config.log(
            f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
            'error', True)
    # --------
    config.match_found = True
    if config.match_found and not config.error:
        AddRunning.main(config.script_num, config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.newmatch = VerificationMatchTrouve.fromUrl(driver, config.matchlist_file_name)[1]

        print("#RECHERCHE INFOS DE MISE")
        infosperte = getGlobalPerte()
        if infosperte:
            """if float(infosperte['perte']) > 100:
                SendGlobalPerte(config.scriptType, -20)
                config.perte = 20
            elif float(infosperte['perte']) > 50:
                SendGlobalPerte(config.scriptType, -10)
                config.perte = 10
            elif float(infosperte['perte']) > 20:
                SendGlobalPerte(config.scriptType, -5)
                config.perte = 5
            elif float(infosperte['perte']) > 10:
                SendGlobalPerte(config.scriptType, -3)
                config.perte = 3
            el"""
            if float(infosperte['perte']) > 1:
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
    config.lose = False
    while (float(winmatch) < float(config.nb_tour) and not config.error):
        # WAIT FOR GAME START
        if passageset:
            config.saved_set = ""
            config.set_actuel = GetSetActuel(driver)
            config.score_actuel = '0:0'
            gamestart = 1
            if config.rattrape_perte == 1:
                config.error = False
                txtlog = "passage set 2"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                time.sleep(30)
                FirstGameBet(driver)
            elif config.perte > 0:
                DispatchPerte()
                config.init_variable()
                txtlog = "passage set 2 restart"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                time.sleep(30)
                FirstGameBet(driver)
            else:
                config.error = True
                print("erreur perte en 1 set")
                DispatchPerte()
        elif (config.jeu_actuel + 1) == 13:
            while config.score_actuel != "0:1" and config.score_actuel != "1:0":
                print("wait start tie break")
                print('score actuel : ' + config.score_actuel)
                saveset = config.set_actuel
                GetSetActuel(driver)
                if saveset != config.set_actuel:
                    break
                time.sleep(30)
                GetScoreActuel(driver)
            while config.score_actuel != "0:0":
                print("wait end tie break")
                print('score actuel : ' + config.score_actuel)
                time.sleep(30)
                GetScoreActuel(driver)
            passageset = True
            time.sleep(30)
            continue
        else:
            gamestart = False
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        txtlog = "JEU COMMENCÉ ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        bet_40a = False
        tentative = 0
        while not bet_40a and not config.error:
            # Affichage de la liste des paris
            config.log('Affichage de la liste des paris', config.newmatch)
            if not AfficherParis(driver):
                config.error = True
                break
            # On recherche le jeu actuel
            config.log('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
            if not GetBet(driver, True):
                tentative = tentative + 1
                if tentative > 5:
                    config.log('error recup jeu #ERR345', config.newmatch)
                    config.error = True
                    tentative = 0
                continue
            else:
                print('passage prochain jeu')
                bet_40a = True
            config.log('prochain PAris 40A cliqué', config.newmatch)

        # ON ENVOIE LA MISE
        txtlog = "ON ENVOIE LA MISE"
        config.log(txtlog, config.newmatch)
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
            # VÉRIFCATION DU SET ACTUEL
            config.saved_set = config.set_actuel
            GetSetActuel(driver)
            newset = int(config.saved_set) + 1
            if not config.set_actuel:
                config.error = True
            config.log('set ' + str(config.set_actuel) + ' - saved set ' + str(config.saved_set), config.newmatch)
            if str(config.saved_set) == str(config.set_actuel):  ## si on est toujours sur le meme set
                config.log('on est toujours sur le meme set', config.newmatch)

                if (config.jeu_actuel + 1) >= 13:  # SI TIE BREAK
                    txtlog = "jeu " + str(config.jeu_actuel)
                    print(txtlog)
                    config.log(txtlog, config.newmatch)
                    txtlog = "attente fin de tie break"
                    print(txtlog)
                    config.log(txtlog, config.newmatch)
                    passageset = True
                else:
                    ##VALIDATION DU PARIS SI SCORE OK
                    validate_bet = False
                    tentative = 0
                    while not validate_bet and not config.error and tentative < 3:
                        # VÉRIFICATION DU SCORE ACTUEL
                        tentative = tentative + 1
                        print('tentative validation ' + str(tentative))
                        GetScoreActuel(driver)
                        if config.score_actuel == "0:0" and not gamestart:
                            txtlog = "GAME NOT START"
                            config.log(txtlog, config.newmatch)
                        elif config.score_actuel == "0:0" and gamestart:
                            txtlog = "GAME PASS WITHOUT VALIDATE ON FIRST"
                            config.log(txtlog, config.newmatch)
                            gamestart = False
                            break
                        elif config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:40":
                            print("GAME PASS WITHOUT VALIDATE #2#")
                            gamestart = False
                            GetIfGameEnd(driver)
                            break
                        else:
                            gamestart = True
                            txtlog = "GAME START"
                            config.log(txtlog, config.newmatch)
                        if ValidationDuParis(driver, True):
                            validate_bet = True
                            config.perte = float(config.perte) + float(config.mise)
                            config.wantwin = float(config.wantwin) + float(config.increment)
                            # Calculate net profit based on stake, odds and losses
                            config.netprofit = (float(config.mise) * float(config.cote)) - float(config.perte)
                            config.log(f'Potential Net profit: {config.netprofit}')
                    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                    RetourTpsReg(driver)
            elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                config.log(txtlog, config.newmatch)
                passageset = True
                DeleteBet(driver)
                txtlog = 'Wait 30 sec'
                config.log(txtlog, config.newmatch)
                time.sleep(30)
            else:
                print("ERROR : ecup set " + str(config.set_actuel))
                config.error = True
        elif result == 'WIN':
            config.perte = 0
            config.init_variable()
            config.global_match_win = config.global_match_win + config.netprofit
            winmatch = winmatch + 1
            DeleteBet(driver)
            passageset = True
            print("#RECHERCHE INFOS DE MISE")
            infosperte = getGlobalPerte()
            if infosperte:
                """if float(infosperte['perte']) > 100:
                    SendGlobalPerte(config.scriptType, -20)
                    config.perte = 20
                elif float(infosperte['perte']) > 50:
                    SendGlobalPerte(config.scriptType, -10)
                    config.perte = 10
                elif float(infosperte['perte']) > 20:
                    SendGlobalPerte(config.scriptType, -5)
                    config.perte = 5
                elif float(infosperte['perte']) > 10:
                    SendGlobalPerte(config.scriptType, -3)
                    config.perte = 3
                el"""
                if float(infosperte['perte']) > 1:
                    SendGlobalPerte(config.scriptType, -1)
                    config.perte = 1
                elif float(infosperte['perte']) <= 1:
                    config.perte = float(infosperte['perte'])
                    m = 0 - config.perte
                    SendGlobalPerte(config.scriptType, m)
                    config.perte = float(infosperte['perte'])
                config.rattrape_perte = 1
            if config.perte == 0 and config.global_match_win >= 1:
                config.log(f'Net profit: {config.global_match_win}')
                config.global_match_win = 0
                break
    if config.perte > 0.2:
        DispatchPerte()
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
