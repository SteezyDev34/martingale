import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetAndPlaceBet import GetAndPlaceBet
from Functions.GetIfGameStart import GetIfGameStart, GetIfGameEnd
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    driver.switch_to.window(driver.window_handles[0])
    result = False
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)

    # --------
    config.match_found = True
    if config.match_found and not config.error:
        AddRunning.main(config.script_num, config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.teams = GetPlayersName(driver)
        newmatchFromUrl(driver)

        config.log('RECHERCHE INFOS DE MISE', 'title', False)
        infosperte = getGlobalPerte()
        if infosperte and config.perte == 0:
            if float(infosperte['perte']) > 1:
                SendGlobalPerte(config.scriptType, -1)
                config.perte = 1
                config.rattrape_perte = 1
            elif float(infosperte['perte']) <= 0.2:
                config.perte = float(infosperte['perte'])
                m = 0 - config.perte
                SendGlobalPerte(config.scriptType, m)
                config.perte = float(infosperte['perte'])
        config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
    print('error ', config.error)
    GetSetActuel(driver)
    if not config.set_actuel:
        GetSetActuel(driver)

    ##PREPARATTION PREMIER PARIS
    FirstGameBet(driver)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    RetourTpsReg(driver)
    GetSetActuel(driver)
    passageset = False
    winmatch = 0
    config.lose = False
    print('error', config.match_end)
    while not config.error and not config.match_end:
        GetJeuActuel(driver)
        # WAIT FOR GAME START
        if passageset:

            GetSetActuel(driver)
            config.newset = int(config.set_actuel) + 1
            config.score_actuel = '0:0'
            config.game_start = True
            if config.rattrape_perte == 1:
                config.error = False
                txtlog = "passage set 2"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                if result != 'WIN':
                    time.sleep(30)
                FirstGameBet(driver)
                GetIfGameStart(driver)
            elif config.perte > 0:
                DispatchPerte()
                config.init_variable()
                txtlog = "passage set 2 restart"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                if result != 'WIN':
                    time.sleep(30)
                FirstGameBet(driver)
                GetIfGameStart(driver)
            else:
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
                print("erreur perte en 1 set")
                DispatchPerte()
        elif result == 'WIN':
            config.error = False
            config.log("Restart", config.newmatch)
            FirstGameBet(driver)
            GetIfGameStart(driver)
        elif config.jeu_actuel >= 12:
            GetJeuActuel(driver)
            GetIfGameStart(driver)
            while config.score_actuel != "0:0":
                print('possible tie break, attente debut ...')
                result = GetResult(driver)
                if result == "WIN":
                    config.perte = 0
                    config.init_variable()
                    config.global_match_win = config.global_match_win + config.netprofit
                    winmatch = winmatch + 1
                    DeleteBet(driver)
                    result = 'WIN'
                    config.error = True
                GetScoreActuel(driver)
                GetIfGameEnd(driver)
            GetJeuActuel(driver)
            if config.jeu_actuel == 13:
                print('Tie break en cours attente début')
                while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                    GetScoreActuel(driver)
                    if not GetIfMatchPage(driver):
                        config.error = True
                        break
                print('tie break commencé... attente fin')
                GetIfGameEnd(driver)
            passageset = True
            time.sleep(30)
            continue
        else:
            config.game_start = False
            if str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.newset = int(config.set_actuel) + 1
                config.log(txtlog, config.newmatch)
                DeleteBet(driver)
                txtlog = 'Wait 30 sec'
                config.log(txtlog, config.newmatch)
                time.sleep(30)
                continue
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart(driver)
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        txtlog = "JEU COMMENCÉ ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        if config.match_end:
            break
        GetAndPlaceBet(driver)
        result = GetResult(driver)

        print("result : " + result)

        if result == 'LOSE':
            GetIfGameEnd(driver)
            # VÉRIFCATION DU SET ACTUEL
            GetSetActuel(driver)

            if not config.set_actuel:
                GetSetActuel(driver)
            config.log('set ' + str(config.set_actuel) + ' - nex set ' + str(config.newset))
            if str(int(config.newset) - 1) == str(config.set_actuel):  ## si on est toujours sur le meme set
                config.log('on est toujours sur le meme set', config.newmatch)
                ##VALIDATION DU PARIS SI SCORE OK
                validate_bet = False
                tentative = 0
                while not validate_bet and not config.error and tentative < 3:
                    # VÉRIFICATION DU SCORE ACTUEL
                    tentative = tentative + 1
                    print('tentative validation ' + str(tentative))
                    GetScoreActuel(driver)
                    if config.score_actuel == "0:0" and not config.game_start:
                        txtlog = "GAME NOT START"
                        config.log(txtlog, config.newmatch)
                    elif config.score_actuel == "0:0" and config.game_start:
                        txtlog = "GAME PASS WITHOUT VALIDATE ON FIRST"
                        config.log(txtlog, config.newmatch)
                        config.game_start = False
                        break
                    elif config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:40":
                        print("GAME PASS WITHOUT VALIDATE #2#")
                        config.game_start = False
                        GetIfGameEnd(driver)
                        break
                    if ValidationDuParis(driver, True):
                        validate_bet = True
                    else:
                        FirstGameBet(driver)
                        validate_bet = True
                # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                RetourTpsReg(driver)
            elif str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.newset = int(config.set_actuel) + 1
                config.log(txtlog, config.newmatch)
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
            print("#RECHERCHE INFOS DE MISE")
            infosperte = getGlobalPerte()
            print("PERTE : ")
            if infosperte:
                if float(infosperte['perte']) > 1:
                    SendGlobalPerte(config.scriptType, -1)
                    config.perte = 1
                    config.rattrape_perte = 1
                elif float(infosperte['perte']) <= 0.2:
                    config.perte = float(infosperte['perte'])
                    m = 0 - config.perte
                    SendGlobalPerte(config.scriptType, m)
                    config.perte = float(infosperte['perte'])
            config.rattrape_perte = 1
            config.log(f'Net profit: {config.global_match_win}')
            if float(config.global_match_win) >= 1:
                break
        if config.match_end:
            break
    if config.perte > 0.2:
        DispatchPerte()
    config.global_match_win = 0
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
