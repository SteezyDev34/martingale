import inspect
import time

import config
from Functions import GetLigueName, RedisIPC
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
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
from Functions.Managers.MatchManager import match_manager
from Functions.Managers.ScriptManager import script_manager
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    GetIfNewSite(driver)
    # Nettoyer le script inactif
    script_manager.stop_script(config.scriptType, config.script_num)

    # Initialize dictionary to store all scores
    config.all_scores = {}

    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)
    # --------
    print('error 0', config.error)
    # Indique qu'un match a été trouvé
    config.match_found = True

    # Si un match est trouvé et qu'il n'y a pas d'erreur
    if config.match_found and not config.error:
        # Démarre le script avec le type et numéro spécifiés
        script_manager.start_script(config.scriptType, config.script_num)

        # Get league name and match URL
        ligue_info = GetLigueName.fromUrl(driver)
        config.ligue_name = ligue_info[0]
        config.match_Url = ligue_info[1]

        # Récupère les noms des joueurs/équipes
        config.teams = GetPlayersName(driver)

        # Vérifie si c'est un nouveau match depuis l'URL
        newmatchFromUrl(driver)
        print('error 4', config.error)
        # Met à jour le statut du match dans le gestionnaire de matchs
        match_manager.add_match(config.newmatch)
        print('error 5', config.error)
        config.log("-" * 60, "success", False, False, False)
        config.log(f'MATCH OK : {str(config.teams)} | {config.ligue_name}', 'success', False, 0, False)
        config.log("-" * 60, "success", False, False, False)

    if config.error:
        print("❌ Une erreur est survenue, arrêt du script.")
        return False

    for scriptType in config.scriptTypeList:
        RedisIPC.set_running(scriptType, True, config.newmatch)
        config.switchScript(scriptType)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        config.ScriptConfig(scriptType).reset()
        config.init_variable()
        if config.perte == 0:
            get1setGlobalPerte()
        if config.perte == 0:
            getGlobalPerte()
        config.log_clear_line()

        # END RECHERCHE INFOS DE MISE
    GetScoreActuel(driver)
    if not config.set_actuel:
        config.error = True
    firstjeu = True
    current_game = int(config.jeu_actuel)
    allfirstgamebet = False
    while not allfirstgamebet:
        allfirstgamebet = True
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            # Check if all script types have global_match_win > 1
            all_below_one = all(
                float(config.global_match_win[st]) >= float(config.total_want_win[scriptType]) for st in
                config.scriptTypeList)
            if all_below_one:
                for st in config.scriptTypeList:
                    config.log(f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                return True
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
            else:
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} /{config.total_want_win[scriptType]}')
                config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                RedisIPC.set_running(config.scriptType, False, config.newmatch)
                continue

            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)
            if not config.validated_bet:
                allfirstgamebet = False

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    print(f'{config.PURPLE}-' * 30)
    print(f'{config.PURPLE}FIRST GAME DONE')
    print(f'{config.PURPLE}-' * 30)
    waitendgame = True
    firstjeu = True
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        if (config.validated_bet and int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) and int(
                config.set_actuel) == int(
            config.validated_bet.get('set'))) or config.scriptType == '15V1' or config.scriptType == '15V2':
            waitendgame = False
            break

    if waitendgame:
        GetIfGameEnd(driver)
    RetourTpsReg(driver)
    passageset = False
    RedisIPC.set_running(config.scriptType, True, config.newmatch)
    while not config.error:
        GetJeuActuel(driver)

        # WAIT FOR GAME START
        if passageset:
            GetSetActuel(driver)
            config.game_start = True
            passageset = False
            # if config.rattrape_perte == 1:
            if passageset:
                config.error = False
                txtlog = f"passage set {config.newset}"
                config.newset = int(config.set_actuel) + 1
                print(txtlog)
                config.log(txtlog, config.newmatch)
                txtlog = "attente 30 sec"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                for scriptType in config.scriptTypeList:
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
                        RedisIPC.set_running(config.scriptType, False, config.newmatch)
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
                            if config.perte == 0:
                                get1setGlobalPerte()
                            config.error = False
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)

                        else:
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"FIN {config.scriptType}", 'success', False)
                            RedisIPC.set_running(config.scriptType, False, config.newmatch)
                            continue
                    else:
                        firstjeu = True
                        FirstGameBet(driver)
            elif config.perte > 0:
                for i in config.scriptTypeList:
                    config.switchScript(i)
                    config.ScriptConfig(i).reset()
                    DispatchPerte()
                    config.init_variable()
                    txtlog = "passage set 2 restart"
                    config.log(txtlog, config.newmatch)
                allfirstgamebet = False
                while not allfirstgamebet:
                    allfirstgamebet = True
                    for scriptType in config.scriptTypeList:
                        config.switchScript(scriptType)
                        # Check if all script types have global_match_win > 1
                        all_below_one = all(
                            float(config.global_match_win[st]) >= float(config.total_want_win[scriptType]) for st in
                            config.scriptTypeList)
                        if all_below_one:
                            for st in config.scriptTypeList:
                                config.log(f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                                        'success', False)
                            return True
                        if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        else:
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} /{config.total_want_win[scriptType]}')
                            config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                            RedisIPC.set_running(config.scriptType, False, config.newmatch)
                            continue

                        ##PREPARATTION PREMIER PARIS
                        FirstGameBet(driver)
                        if not config.validated_bet:
 
                            allfirstgamebet = False

                firstjeu = True
            else:
                frame = inspect.currentframe()
                if frame is not None:
                    info = inspect.getframeinfo(frame)
                    filename = info.filename
                    lineno = info.lineno
                    funcname = info.function
                else:
                    filename = __file__
                    lineno = -1
                    funcname = 'unknown'
                config.log(
                    f'Error in file {filename} at line {lineno} in function {funcname}',
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
                print('firstjeu', firstjeu)
                print('current_game', current_game)
                time.sleep(2)
                firstjeu = False
                current_game = config.jeu_actuel
            else:
                config.log('verification du jeu actuel dans tous les script')
                ok = True
                for scriptType in config.scriptTypeList:
                    config.switchScript(scriptType)
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')

                    else:
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                        config.log(f"FIN {config.scriptType}", 'success', False)
                        RedisIPC.set_running(config.scriptType, False, config.newmatch)
                        continue
                    if not config.validated_bet or config.jeu_actuel > int(config.validated_bet.get('jeu', -1)):
                        ok=False
                        config.log(f"jeu actuel {config.jeu_actuel} non validé par le paris {config.validated_bet}", 'error', False)
                    else:
                        config.log(f"jeu actuel {config.jeu_actuel} validé par le paris {config.validated_bet}", 'success', False)
                if ok:
                    GetIfGameEnd(driver)
        # JEU FINI ON PREPARE LE IPROCHAIN BET
        txtlog = "JEU FINI ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        current_game = int(config.jeu_actuel)
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
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
                RedisIPC.set_running(config.scriptType, False, config.newmatch)
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
                print('GetAndPlaceBet')
                print(config.global_match_win)
            if config.result == 'RUN':
                print('RUN')
                continue
            GetScoreActuel(driver)
            if config.validated_bet:
                vb_jeu = int(config.validated_bet.get('jeu', -1))
                vb_set = int(config.validated_bet.get('set', -1))
                if int(config.jeu_actuel) == vb_jeu - 1 and int(config.set_actuel) == vb_set:
                    print('set du paris supérieur!')
                    DeleteBet(driver)
                    continue
            if config.validated_bet.get('result') is None:
                print('result', config.validated_bet.get('result'))
                GetResult(driver)

            if config.validated_bet.get('result') == 'LOSE':
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
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte)
                    config.log(txtlog, config.newmatch)
                    print('Revert perte : ', config.perte)
                    DeleteBet(driver)
                    txtlog = 'Wait 30 sec'
                    config.log(txtlog, config.newmatch)
                    break
                else:
                    print("ERROR : ecup set " + str(config.set_actuel))
                    config.error = True
            elif config.validated_bet.get('result') == 'WIN':
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                config.ScriptConfig(scriptType).reset()
                config.init_variable()
                DeleteBet(driver)
                if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                    print("#RECHERCHE INFOS DE MISE")
                    getGlobalPerte()
                    if config.perte == 0:
                        get1setGlobalPerte()
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
                                # firstjeu = True
                                current_game = int(config.jeu_actuel)
                    current_game = int(config.jeu_actuel)
                else:
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"FIN {config.scriptType}", 'success', False)
                    RedisIPC.set_running(config.scriptType, False, config.newmatch)
        if not GetIfMatchPage(driver):
            config.error = True
            break
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript(i)
        RedisIPC.set_running(config.scriptType, False, config.newmatch)

        print('perte', config.perte)
        DispatchPerte()
        config.ScriptConfig(i).reset()
        config.init_variable()
        config.global_match_win[i] = 0.0  # Initialize win counter for script type (float)
        config.winmatch[i] = 0  # Initialize match counter for script type
    config.all_scores = {}
    # Supprimer le match de la base de données
    match_manager.remove_match(config.newmatch)

    # Nettoyer le script en cours
    script_manager.stop_script(config.scriptType, config.script_num)

    DeleteBet(driver)
    return True
