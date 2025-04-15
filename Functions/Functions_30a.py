import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, VerificationMatchTrouve, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetAndPlaceBet import GetAndPlaceBet
from Functions.GetIfGameStart import GetIfGameEnd
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    driver.switch_to.window(driver.window_handles[0])
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
        print("PERTE : ")
        if infosperte and config.perte == 0:
            if float(infosperte['perte']) > 100:
                SendGlobalPerte(config.scriptType, -20)
                config.perte = 20
                config.rattrape_perte = 1
            elif float(infosperte['perte']) > 10:
                SendGlobalPerte(config.scriptType, -10)
                config.perte = 10
                config.rattrape_perte = 1
            elif float(infosperte['perte']) > 1:
                SendGlobalPerte(config.scriptType, -1)
                config.perte = 1
                config.rattrape_perte = 1
            elif float(infosperte['perte']) >= 0.2:
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
            current_frame = inspect.currentframe()
            config.log(
                f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                'error', True)

    ##PREPARATTION PREMIER PARIS
    FirstGameBet(driver)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    RetourTpsReg(driver)

    passageset = False
    winmatch = 0
    config.lose = False
    result = False
    while (float(winmatch) <= float(config.nb_tour)) and not config.error:
        GetJeuActuel(driver)
        # WAIT FOR GAME START
        if passageset:
            score_actuel = '40:0'
            gamestart = True
            config.jeu_actuel = 0
            config.error = False
            config.log("passage set 2", config.newmatch)
            config.log("attente 30 sec", config.newmatch)
            time.sleep(30)
            FirstGameBet(driver)
        elif result == 'WIN':
            config.error = False
            config.log("Restart", config.newmatch)
            FirstGameBet(driver)
        elif config.jeu_actuel == 12:
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
            if config.jeu_actuel == 13:
                while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                    print('Tie break en cours attente début')
                    GetScoreActuel(driver)
                    time.sleep(30)
                print('tie break commencé... attente fin')
                time.sleep(60)
            passageset = True
            continue
        else:
            gamestart = False
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameEnd(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        txtlog = "JEU COMMENCÉ ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        GetAndPlaceBet(driver)
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
                    config.log("error pendant la récupération du score", config.newmatch)
                    break
                if (
                        config.score_actuel == "0:30" or config.score_actuel == "15:30" or config.score_actuel == "30:15" or config.score_actuel == "30:0") and gamestart:
                    config.log("GAME PASS WITHOUT VALIDATE", config.newmatch)
                    FirstGameBet(driver)
                    break
                    ###ajouter ici les actions avant de reprendre
                elif config.score_actuel == "30:30":
                    config.error = True
                    config.log("30A leave!", config.newmatch)
                    FirstGameBet(driver)
                    ###ajouter ici les actions avant de reprendre
                    break
                else:
                    gamestart = True
                if ValidationDuParis(driver, True):
                    validate_bet = True
                else:
                    GetAndPlaceBet(driver)
            # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
            RetourTpsReg(driver)
            GetIfGameEnd(driver)
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
                    config.log("jeu " + str(config.jeu_actuel), config.newmatch)
                    config.log("attente fin de tie break", config.newmatch)

            elif str(newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.perte = config.perte - config.mise
                config.log(txtlog, config.newmatch)
                DeleteBet(driver)
                txtlog = 'Wait 30 sec'
                config.log(txtlog, config.newmatch)
                time.sleep(30)
            else:
                print("ERROR : recup set " + str(config.set_actuel))
                config.error = True
        elif result == 'WIN':
            config.perte = 0
            config.init_variable()
            config.global_match_win = config.global_match_win + config.netprofit
            winmatch = winmatch + 1
            DeleteBet(driver)
            # GetIfGameEnd(driver)
            if float(winmatch) >= float(config.nb_tour):
                break
            print("#RECHERCHE INFOS DE MISE")
            infosperte = getGlobalPerte()
            print("PERTE : ")
            if infosperte:
                if float(infosperte['perte']) > 100:
                    SendGlobalPerte(config.scriptType, -20)
                    config.perte = 20
                    config.rattrape_perte = 1
                elif float(infosperte['perte']) > 10:
                    SendGlobalPerte(config.scriptType, -10)
                    config.perte = 10
                    config.rattrape_perte = 1
                elif float(infosperte['perte']) > 1:
                    SendGlobalPerte(config.scriptType, -1)
                    config.perte = 1
                    config.rattrape_perte = 1
                elif float(infosperte['perte']) > 0:
                    config.perte = float(infosperte['perte'])
                    m = 0 - config.perte
                    SendGlobalPerte(config.scriptType, m)
                    config.perte = float(infosperte['perte'])
                config.rattrape_perte = 1
            config.log(f'Net profit: {config.global_match_win}')
            if config.perte == 0 and config.global_match_win >= 1:
                config.global_match_win = 0
                break
            elif config.nb_tour == winmatch:
                break

    if config.perte > 0.2:
        DispatchPerte()
    print("error ", config.error)
    config.global_match_win = 0
    print("update " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
