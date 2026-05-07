import inspect
import time

from Functions.PlacerMise import PlacerMise
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
        # Récupérer le lien SofaScore stocké localement (table matches_todo.link)
        try:
            sofascore_link = match_manager.get_match_link(config.newmatch)
            if sofascore_link:
                config.log(f"Lien SofaScore trouvé localement: {sofascore_link}", 'info', False, 1)
            else:
                config.log('Aucun lien SofaScore trouvé localement.', 'warning', False, 1)
        except Exception as e:
            config.log(f"Erreur lors de la récupération du lien SofaScore: {e}", 'warning', True)

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
        config.switchScript(scriptType)
        RedisIPC.set_running(config.scriptType, True)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        config.ScriptConfig(scriptType).reset()
        config.init_variable()
        if config.perte == 0:
            getGlobalPerte()
        if config.perte == 0:
            get1setGlobalPerte()
        if config.perte == 0:
            # Récupération de perte cross-script via Redis si disponible
            if RedisIPC:
                mtt_recup = getattr(config, 'mtt_recup', 0.0)
                if mtt_recup > 0 and RedisIPC.deduct_amount_from_largest(mtt_recup):
                    config.perte = mtt_recup
                RedisIPC.set_loss(config.scriptType, config.perte)
            
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
                RedisIPC.set_running(config.scriptType, False)
                continue

            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)
            if not config.validated_bet:
                allfirstgamebet: False
    passageset = False
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
                config.newset = int(config.jeu_actuel) + 1
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
                        RedisIPC.set_running(config.scriptType, False)
                        continue
                    config.result = GetResult(driver)
                    if config.result == 'WIN':
                        config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                            config.netprofit)
                        config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                        config.init_variable()
                        if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                            print("#RECHERCHE INFOS DE MISE")
                            config.perte = 0
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte)
                            config.wantwin =0.2
                            # Récupération de perte cross-script via Redis si disponible
                            if RedisIPC:
                                mtt_recup = getattr(config, 'mtt_recup', 0.0)
                                if mtt_recup > 0 and RedisIPC.deduct_amount_from_largest(mtt_recup):
                                    config.perte = mtt_recup
                            if config.perte == 0:
                                getGlobalPerte()
                            if config.perte == 0:
                                get1setGlobalPerte()
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte)
                            config.error = False
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)

                        else:
                            config.ScriptConfig(scriptType).reset()
                            DeleteBet(driver)

                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"FIN {config.scriptType}", 'success', False)
                            RedisIPC.set_running(config.scriptType, False)
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
                            RedisIPC.set_running(config.scriptType, False)
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
            if str(config.newset) == str(config.jeu_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                config.newset = int(config.jeu_actuel) + 1
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
                        RedisIPC.set_running(config.scriptType, False)
                        continue
        # JEU FINI ON PREPARE LE IPROCHAIN BET

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
                passageset = False
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
                passageset = False
                break
            else:
                GetAndPlaceBet(driver)
                print('GetAndPlaceBet')
                print(config.global_match_win)
            if config.result == 'RUN':
                print('RUN')
                continue
            GetScoreActuel(driver)
            if not config.validated_bet or config.validated_bet.get('result') is None:
                print('result', config.validated_bet.get('result'))
                GetResult(driver)

            if config.validated_bet.get('result') == 'LOSE':
                # VÉRIFCATION DU SET ACTUEL
                GetScoreActuel(driver)
                if not config.set_actuel:
                    config.error = True
                print(str(int(config.looking_game)) , str(config.jeu_actuel))
                if str(int(config.looking_game)) == str(config.jeu_actuel) and config.score_actuel != "0:0":  ## si on est toujours sur le meme set
                    config.log('on est toujours sur le meme jeu', config.newmatch)
                    ##VALIDATION DU PARIS SI SCORE OK
                    validate_bet = False
                    tentative = 0
                    attempts = 3
                    if config.scriptType in ['15V1', '15V2']:
                        attempts = 2
                        while not validate_bet and not config.error and tentative < attempts:
                            # VÉRIFICATION DU SCORE ACTUEL
                            tentative = tentative + 1
                            print('tentative validation ' + str(tentative))
                            if ValidationDuParis(driver, True):
                                validate_bet = True
                                if config.scriptType in ['15V1', '15V2']:
                                    def _last_numero_point():
                                        try:
                                            if not config.all_scores:
                                                return None
                                            # support list-like or dict-like structures
                                            if isinstance(config.all_scores, dict):
                                                vals = list(config.all_scores.values())
                                                if not vals:
                                                    return None
                                                last = vals[-1]
                                            else:
                                                last = config.all_scores[-1]
                                            return int(last['numero_point'])
                                        except Exception:
                                            return None

                                    target = None
                                    try:
                                        target = int(config.validated_bet['numero_point']) - 1
                                    except Exception:
                                        target = None

                                    # attendre que le dernier score enregistré corresponde au point attendu
                                    config.log(f'Attente du point {target} pour valider le pari', 'info', indent=3)
                                    while not config.error:
                                        last = _last_numero_point()
                                        config.log(f'Last point: {last}, Target point: {target}', 'debug', indent=4)
                                        if config.score_actuel == "0:0":
                                            break
                                        if last is None or target is None:
                                            break
                                        if last >= target:
                                            break
                                        
                                        GetScoreActuel(driver)
                                        time.sleep(0.1)
                        else:
                            if config.scriptType in ['15V1', '15V2']:
                                continue
                            config.log('validation du paris impossible, tentative firstgamebet ' + str(tentative), config.newmatch)
                            FirstGameBet(driver)
                            validate_bet = True
                            firstjeu = True
                            current_game = int(config.jeu_actuel)
                else:
                    config.log('on est pas sur le meme jeu', config.newmatch)
                    # Vérifier que le point parié existe dans l'historique du jeu
                    matching_set_jeu = [v for v in config.all_scores.values()
                                        if v.get('set') is not None
                                        and v.get('jeu') is not None
                                        and config.validated_bet.get('set') is not None
                                        and config.validated_bet.get('jeu') is not None
                                        and int(v.get('set')) == int(config.validated_bet.get('set'))
                                        and int(v.get('jeu')) == int(config.validated_bet.get('jeu'))]
                    if matching_set_jeu:
                        try:
                            max_point = max(int(x.get('numero_point', 0)) for x in matching_set_jeu)+1
                        except Exception:
                            max_point = None
                        try:
                            bet_point = int(config.validated_bet.get('numero_point'))
                        except Exception:
                            bet_point = None
                        if bet_point is not None and max_point is not None and bet_point > max_point:
                            # Le jeu s'est terminé avant le point parié — annuler ce pari validé
                            result = 'CANCEL'
                            config.log(f"Bet cancelled: bet point {bet_point} > max point {max_point} in game", 'warning', False, 2)
                            config.validated_bet['result'] = result
                            # marquer pour traitement extérieur (extraction des pertes)
                            config.log(f'pertes en cours de calcul pour annulation du pari, mise: {config.perte}', 'info', False, 2)
                            config.perte = config.perte + config.validated_bet['montant']
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte)
                            config.log(f"Marked loss for cancelled bet, perte: {config.perte}", 'info', False, 2)
                    FirstGameBet(driver)
                    firstjeu = True
            
            elif config.validated_bet.get('result') == 'WIN':
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                mtt_recup = getattr(config, 'mtt_recup', 0.0)
                if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.is_match_running(config.newmatch, exclude_script_types=config.scriptType):
                    print("#RECHERCHE INFOS DE MISE")
                    config.perte = 0
                    config.wantwin =0.2
                    if RedisIPC:
                        RedisIPC.set_loss(config.scriptType, config.perte)
                    #
                    # ---------------------------------------------------------------------------
                    # Récupération de perte cross-script via Redis (priorité sur l'API)
                    # Déduit mtt_recup de la perte Redis la plus élevée tous scripts confondus.
                    # Si Redis est indisponible ou qu'il n'y a rien à déduire
                    # ---------------------------------------------------------------------------
                    if RedisIPC:
                        mtt_recup = getattr(config, 'mtt_recup', 0.0)
                        if mtt_recup > 0 and RedisIPC.deduct_amount_from_largest(mtt_recup):
                            config.perte = mtt_recup
                            RedisIPC.set_loss(config.scriptType, config.perte)
                    # ---------------------------------------------------------------------------
                    #
                    if config.perte == 0:
                        getGlobalPerte()
                    if config.perte == 0:
                        get1setGlobalPerte()
                    '''if config.perte > 0:
                        GetIfGameEnd(driver)'''
                    if RedisIPC:
                        RedisIPC.set_loss(config.scriptType, config.perte)
                    config.error = False
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    #config.log(f"Restart {config.scriptType}", 'success', False)
                    # VÉRIFCATION DU SET ACTUEL
                    if not config.set_actuel:
                        config.error = True
                    print(str(int(config.looking_game)) , str(config.jeu_actuel))
                    if str(int(config.looking_game)) == str(config.jeu_actuel) and config.score_actuel != "0:0":  ## si on est toujours sur le meme set
                        #config.ScriptConfig(scriptType).reset()
                        #config.log('on est toujours sur le meme set', config.newmatch)
                        ##VALIDATION DU PARIS SI SCORE OK
                        validate_bet = False
                        tentative = 0
                        attempts = 3
                        if config.scriptType in ['15V1', '15V2']:
                            attempts = 1
                        while not validate_bet and not config.error and tentative < attempts:
                            # VÉRIFICATION DU SCORE ACTUEL
                            tentative = tentative + 1
                            print('tentative validation ' + str(tentative))
                            PlacerMise(driver)
                            if ValidationDuParis(driver, True):
                                validate_bet = True
                                if config.scriptType in ['15V1', '15V2']:
                                    def _last_numero_point():
                                        try:
                                            if not config.all_scores:
                                                return None
                                            # support list-like or dict-like structures
                                            if isinstance(config.all_scores, dict):
                                                vals = list(config.all_scores.values())
                                                if not vals:
                                                    return None
                                                last = vals[-1]
                                            else:
                                                last = config.all_scores[-1]
                                            return int(last['numero_point'])
                                        except Exception:
                                            return None

                                    target = None
                                    try:
                                        target = int(config.validated_bet['numero_point']) - 1
                                    except Exception:
                                        target = None

                                    # attendre que le dernier score enregistré corresponde au point attendu
                                    config.log(f'Attente du point {target} pour valider le pari', 'info', indent=3)
                                    while not config.error:
                                        last = _last_numero_point()
                                        config.log(f'Last point: {last}, Target point: {target}', 'debug', indent=4)
                                        if config.score_actuel == "0:0":
                                            break
                                        if last is None or target is None:
                                            break
                                        if last >= target:
                                            break
                                        
                                        GetScoreActuel(driver)
                                        time.sleep(0.1)
                            else:
                                if config.scriptType in ['15V1', '15V2']:
                                    continue
                                config.log('after win validation du paris impossible, tentative firstgamebet ' + str(tentative), config.newmatch)
                                FirstGameBet(driver)
                                validate_bet = True
                                # firstjeu = True
                                current_game = int(config.jeu_actuel)
                    else:
                        config.ScriptConfig(scriptType).reset()
                        config.log('on est pas sur le meme jeu', config.newmatch)
                        FirstGameBet(driver)
                        # firstjeu = True
                    current_game = int(config.jeu_actuel)
                else:
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"FIN {config.scriptType}", 'success', False)
                    RedisIPC.set_running(config.scriptType, False)
        if not GetIfMatchPage(driver):
            config.error = True
            break
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript(i)
        RedisIPC.set_running(config.scriptType, False)
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
