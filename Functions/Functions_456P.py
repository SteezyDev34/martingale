import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.Authenticator import loginProcess, is_logged_in
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetIfGameStart import GetIfGameEnd, GetIfGameStart
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJsonData import DispatchPerte, getGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    # driver.switch_to.window(driver.window_handles[0])
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
    if config.error:
        return False
    if not is_logged_in(driver):
        print('not logged in ')
        loginProcess(driver)
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        if config.perte == 0:
            getGlobalPerte()
        # END RECHERCHE INFOS DE MISE
    GetScoreActuel(driver)
    if not config.set_actuel:
        config.error = True
    firstjeu = True
    current_game = int(config.jeu_actuel)
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        # Check if all script types have global_match_win > 1
        all_below_one = all(
            float(config.global_match_win[st]) >= config.total_want_win for st in config.scriptTypeList)
        if all_below_one:
            for st in config.scriptTypeList:
                config.log(f' {st} : Net profit: {config.global_match_win[st]}', 'success', False)
            return True
        if float(config.global_match_win[scriptType]) < config.total_want_win:
            config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
        else:
            config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
            config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
            continue
        ##PREPARATTION PREMIER PARIS
        FirstGameBet(driver)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    print('FIRST GAME DONE')
    waitendgame = True
    firstjeu = True
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        if config.validated_bet and int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) and int(
                config.set_actuel) == int(
            config.validated_bet.get('set')):
            waitendgame = False
            break

    if waitendgame:
        GetIfGameEnd(driver)
    RetourTpsReg(driver)
    passageset = False
    while not config.error:
        GetJeuActuel(driver)
        # WAIT FOR GAME START
        if passageset:
            if not is_logged_in(driver):
                print('not logged in ')
                loginProcess(driver)
            GetSetActuel(driver)
            config.game_start = True
            if config.rattrape_perte == 1:
                config.error = False
                txtlog = f"passage set {config.newset}"
                config.newset = int(config.set_actuel) + 1
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                for scriptType in config.scriptTypeList:
                    if not is_logged_in(driver):
                        print('not logged in ')
                        loginProcess(driver)
                    config.switchScript(scriptType)
                    # Check if all script types have global_match_win > 1
                    all_below_one = all(
                        float(config.global_match_win[st]) >= config.total_want_win for st in config.scriptTypeList)
                    if all_below_one:
                        for st in config.scriptTypeList:
                            config.log(f' {st} : Net profit: {config.global_match_win[st]}', 'success', False)
                        return True
                    if float(config.global_match_win[scriptType]) < config.total_want_win:
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                    else:
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                        config.log(f"FIN {config.scriptType}", 'success', False)
                        continue
                    config.result = GetResult(driver)
                    if config.result == 'WIN':
                        config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                            config.netprofit)
                        config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                        config.ScriptConfig(scriptType).reset()
                        config.init_variable()
                        DeleteBet(driver)
                        if float(config.global_match_win[scriptType]) < config.total_want_win:
                            print("#RECHERCHE INFOS DE MISE")

                            getGlobalPerte()
                            config.error = False
                            config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)

                        else:
                            config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
                            config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                            continue
                    else:
                        firstjeu = True
                        FirstGameBet(driver)
            elif config.perte > 0:
                DispatchPerte()
                config.init_variable()
                txtlog = "passage set 2 restart"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                if config.result != 'WIN':
                    time.sleep(30)
                FirstGameBet(driver)
                firstjeu = True
            else:
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
                print("erreur perte en 1 set")
                DispatchPerte()
        else:
            if str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.newset = int(config.set_actuel) + 1
                config.log(txtlog, config.newmatch)
                DeleteBet(driver)
                continue
            print('ATTENTE DEBUT DE JEU')
            GetIfGameStart(driver)
        # JEU FINI ON PREPARE LE IPROCHAIN BET
        txtlog = "JEU START ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        current_game = int(config.jeu_actuel)
        for scriptType in config.scriptTypeList:
            if not is_logged_in(driver):
                print('not logged in ')
                loginProcess(driver)
            config.switchScript(scriptType)
            print('passage prochain script ', scriptType)
            # Check if all script types have global_match_win > 1
            all_below_one = all(
                float(config.global_match_win[st]) >= config.total_want_win for st in config.scriptTypeList)
            if all_below_one:
                for st in config.scriptTypeList:
                    config.log(f' {scriptType} Net profit: {config.global_match_win[st]}', 'success', False)
                return True
            if float(config.global_match_win[scriptType]) < config.total_want_win:
                config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
            else:
                config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
                config.log(f"FIN {config.scriptType}", 'success', False)
                continue
            if config.jeu_actuel == 13:
                config.log('Tie break en cours attente début')
                while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                    GetScoreActuel(driver)
                    if not GetIfMatchPage(driver):
                        config.error = True
                        break
                config.log('tie break commencé... attente fin')
                GetIfGameEnd(driver)
                passageset = True
                break
            elif config.jeu_actuel == 12:
                GetJeuActuel(driver)
                GetIfGameStart(driver)
                while config.score_actuel != "0:0":
                    print('possible tie break, attente debut ...')
                    GetIfGameEnd(driver)
                    GetScoreActuel(driver)
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
                break
            else:
                # GetAndPlaceBet(driver)
                print(config.global_match_win)
            if config.result == 'RUN':
                print('RUN')
                continue
            GetScoreActuel(driver)
            if config.validated_bet:
                if int(config.jeu_actuel) < int(config.validated_bet.get('jeu')) and int(config.set_actuel) == int(
                        config.validated_bet.get('set')):
                    print('already bet')
                    continue
            print('get result')
            config.result = GetResult(driver)
            if config.result == 'LOSE':
                # VÉRIFCATION DU SET ACTUEL
                GetScoreActuel(driver)
                if not config.set_actuel:
                    config.error = True
                config.log('set ' + str(config.set_actuel) + ' - nex set ' + str(config.newset))
                if str(int(config.newset) - 1) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.log('on est toujours sur le meme set', config.newmatch)
                    ##VALIDATION DU PARIS SI SCORE OK
                    validate_bet = False
                    tentative = 0
                    # VÉRIFICATION DU SCORE ACTUEL
                    tentative = tentative + 1
                    print('tentative validation ' + str(tentative))
                    FirstGameBet(driver)
                    firstjeu = True
                elif str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    txtlog = " ON EST SUR LE PROCHAIN SET"
                    passageset = True
                    config.newset = int(config.set_actuel) + 1
                    config.log(txtlog, config.newmatch)
                    DeleteBet(driver)
                    txtlog = 'Wait 30 sec'
                    config.log(txtlog, config.newmatch)
                    break
                else:
                    print("ERROR : ecup set " + str(config.set_actuel))
                    config.error = True

            elif config.result == 'WIN':
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                config.ScriptConfig(scriptType).reset()
                config.init_variable()
                DeleteBet(driver)
                if float(config.global_match_win[scriptType]) < config.total_want_win:
                    print("#RECHERCHE INFOS DE MISE")
                    getGlobalPerte()
                    config.error = False
                    config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
                    config.log(f"Restart {config.scriptType}", 'success', False)
                    ##VALIDATION DU PARIS SI SCORE OK
                    FirstGameBet(driver)
                    firstjeu = True
                else:
                    config.log(f' {scriptType} Net profit: {config.global_match_win[scriptType]}')
                    config.log(f"FIN {config.scriptType}", 'success', False)
        if current_game == int(config.jeu_actuel):
            for scriptType in config.scriptTypeList:
                config.switchScript(scriptType)
                if config.validated_bet and int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) and int(
                        config.set_actuel) == int(
                    config.validated_bet.get('set')) and float(
                    config.global_match_win[scriptType]) < config.total_want_win and not config.validated_bet.get(
                    'result'):
                    continue
            GetIfGameEnd(driver)
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript('456P')
        config.ScriptConfig(i).reset()
        config.init_variable()
        config.switchScript(i)
        DispatchPerte()
        config.global_match_win[i] = 0  # Initialize win counter for script type
        config.winmatch[i] = 0  # Initialize match counter for script type
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
