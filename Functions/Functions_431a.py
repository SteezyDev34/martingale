import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.Authenticator import is_logged_in, loginProcess
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.Functions_1XBET import update_match_done
from Functions.GetAndPlaceBet import GetAndPlaceBet
from Functions.GetIfGameStart import GetIfGameEnd, GetIfGameStart
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, get1setGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    GetIfNewSite(driver)
    # driver.switch_to.window(driver.window_handles[0])
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    config.all_scores = {}
    # --------
    # SCRIPT RECHERCHE DE MATCH
    print('test')
    while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)
    print('test2')
    print('error', config.error)
    # if not is_logged_in(driver):
    # print('not logged in ')
    # loginProcess(driver)
    # --------
    config.match_found = True
    if config.match_found and not config.error:
        print('config.script_num', config.script_num)
        print('config.running_file_name', config.running_file_name)
        AddRunning.main(config.script_num, config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.teams = GetPlayersName(driver)
        newmatchFromUrl(driver)
        update_match_done("add", config.newmatch, config.matchlist_file_name)
    print('error', config.error)
    if config.error:
        return False
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        if config.perte == 0:
            get1setGlobalPerte()
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
                        float(config.global_match_win[st]) >= float(config.total_want_win[st]) for st in
                        config.scriptTypeList)
                    if all_below_one:
                        for st in config.scriptTypeList:
                            config.log(
                                f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                                'success', False)
                        return True
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    else:
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                        continue
                    config.result = GetResult(driver)
                    if config.result == 'WIN':
                        config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                            config.netprofit)
                        config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                        config.ScriptConfig(scriptType).reset()
                        config.init_variable()
                        DeleteBet(driver)
                        if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                            print("#RECHERCHE INFOS DE MISE")

                            getGlobalPerte()
                            config.error = False
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)

                        else:
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"FIN {config.scriptType}", 'success', False)
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
            if firstjeu or int(current_game) != int(config.jeu_actuel):
                print('firstgame')
                time.sleep(2)
                firstjeu = False
                current_game = config.jeu_actuel
            else:
                GetIfGameEnd(driver)
        # JEU FINI ON PREPARE LE IPROCHAIN BET
        txtlog = "JEU FINI ON PREPARE LE PROCHAIN BET"
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
                float(config.global_match_win[st]) >= float(config.total_want_win[st]) for st in
                config.scriptTypeList)
            if all_below_one:
                for st in config.scriptTypeList:
                    config.log(f' {st} Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                return True
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
            else:
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
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
                GetAndPlaceBet(driver)
                print(config.global_match_win)
            if config.result == 'RUN':
                print('RUN')
                continue
            GetScoreActuel(driver)
            if config.validated_bet:
                if int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) - 1 and int(config.set_actuel) == int(
                        config.validated_bet.get('set')):
                    print('set du paris supérieur!')
                    continue
            if config.validated_bet.get('result') is None:
                print('result', config.validated_bet.get('result'))
                GetResult(driver)


            if config.validated_bet.get('result') == 'WIN':
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                config.ScriptConfig(scriptType).reset()
                config.init_variable()
                DeleteBet(driver)
                if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                    print("#RECHERCHE INFOS DE MISE")
                    getGlobalPerte()
                    config.error = False
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"Restart {config.scriptType}", 'success', False)
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
                        while not validate_bet and not config.error and tentative < 3:
                            # VÉRIFICATION DU SCORE ACTUEL
                            tentative = tentative + 1
                            print('tentative validation ' + str(tentative))
                            if ValidationDuParis(driver, True):
                                validate_bet = True
                            else:
                                FirstGameBet(driver)
                                validate_bet = True
                                firstjeu = True
                                current_game = int(config.jeu_actuel)
                    current_game = int(config.jeu_actuel)
                else:
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"FIN {config.scriptType}", 'success', False)
            else:
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
                    while not validate_bet and not config.error and tentative < 3:
                        # VÉRIFICATION DU SCORE ACTUEL
                        tentative = tentative + 1
                        print('tentative validation ' + str(tentative))
                        if ValidationDuParis(driver, True):
                            validate_bet = True
                        else:
                            FirstGameBet(driver)
                            validate_bet = True
                            firstjeu = True
                            current_game = int(config.jeu_actuel)
                elif str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    txtlog = " ON EST SUR LE PROCHAIN SET"
                    passageset = True
                    config.newset = int(config.set_actuel) + 1
                    for scriptType in config.scriptTypeList:
                        config.switchScript(scriptType)
                        if config.validated_bet.get('montant'):
                            config.perte -= float(config.validated_bet.get('montant'))
                    config.log(txtlog, config.newmatch)
                    print('Revert perte : ', config.perte)
                    DeleteBet(driver)
                    txtlog = 'Wait 30 sec'
                    config.log(txtlog, config.newmatch)
                    break
                else:
                    print("ERROR : ecup set " + str(config.set_actuel))
                    config.error = True
        GetIfMatchPage(driver)
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript(i)
        print('perte', config.perte)
        DispatchPerte()
        config.ScriptConfig(i).reset()
        config.init_variable()
        config.global_match_win[i] = 0  # Initialize win counter for script type
        config.winmatch[i] = 0  # Initialize match counter for script type
    config.all_scores = {}
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
