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
from Functions.ValidationDuParis import ValidationDuParis, QuickValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def _dernier_numero_point() -> int | None:
    """
    Lit le numéro du dernier point enregistré dans config.all_scores (dict ou
    liste selon le contexte d'appel). Retourne None si aucun score enregistré
    ou en cas d'erreur.
    """
    try:
        if not config.all_scores:
            return None
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


def _attendre_point_valide_15v(driver):
    """
    Pour 15V1/15V2 : attend que le dernier point enregistré (config.all_scores)
    corresponde au point sur lequel le pari a été validé (numero_point - 1),
    avant de laisser la boucle principale continuer. Factorisée : cette même
    logique était copiée-collée 4 fois à l'identique dans ce fichier
    (cf. AUDIT_MARTINGALE_TENNIS.md §2 sur la duplication de code).
    """
    target = None
    try:
        target = int(config.validated_bet['numero_point']) - 1
    except Exception:
        target = None

    config.log(f'Attente du point {target} pour valider le pari', 'info', indent=3)
    while not config.error:
        last = _dernier_numero_point()
        config.log(f'Last point: {last}, Target point: {target}', 'debug', indent=4)
        if config.score_actuel == "0:0":
            break
        if last is None or target is None:
            break
        if last >= target:
            break
        GetScoreActuel(driver)
        time.sleep(0.1)


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


        # Déterminer l'identifiant du match depuis l'URL
        try:
            newmatchFromUrl(driver)
        except Exception as e:
            config.log(f"Impossible de déterminer newmatch depuis l'URL: {e}", 'warning', False, 1)

        # Récupérer le lien SofaScore stocké localement (table matches_todo.link)
        try:
            print(config.newmatch)
            sofascore_link = match_manager.get_match_link(config.newmatch)
            print(f"lien SofaScore récupéré localement: {sofascore_link}")
            config.sofascore_link = sofascore_link or ''
            if sofascore_link and isinstance(sofascore_link, str) and sofascore_link.startswith('http'):
                config.log(f"Lien SofaScore trouvé localement: {sofascore_link}", 'info', False, 1)
                # Ouvrir le lien dans un nouvel onglet et revenir à l'onglet original
                try:
                    original_handle = driver.current_window_handle
                    new_handle = None
                    try:
                        # Selenium 4 : ouvrir un nouvel onglet de façon fiable
                        driver.switch_to.new_window('tab')
                        driver.get(sofascore_link)
                        new_handle = driver.current_window_handle
                    except Exception:
                        # fallback : utiliser execute_script si new_window n'est pas supporté
                        old_handles = set(driver.window_handles)
                        driver.execute_script("window.open(arguments[0], '_blank');", sofascore_link)
                        time.sleep(0.5)
                        new_handles = set(driver.window_handles)
                        new_tab_handles = list(new_handles - old_handles)
                        if new_tab_handles:
                            new_handle = new_tab_handles[0]
                            try:
                                driver.switch_to.window(new_handle)
                            except Exception:
                                pass

                    if new_handle:
                        # revenir à l'onglet original
                        try:
                            driver.switch_to.window(original_handle)
                        except Exception:
                            pass
                        setattr(config, 'sofascore_tab_handle', new_handle)
                        setattr(config, 'original_tab_handle', original_handle)
                        config.log("Onglet SofaScore ouvert.", 'info', False, 1)
                        from Functions.SofascoreWatcher import start_sofascore_watcher
                        start_sofascore_watcher()
                    else:
                        config.log("Impossible d'ouvrir le nouvel onglet SofaScore.", 'warning', False, 1)
                except Exception as e:
                    config.log(f"Erreur lors de l'ouverture de l'onglet SofaScore: {e}", 'warning', True)
            else:
                # Construire l'URL de l'API auxotracker avec encodage des noms et date du jour
                date_str = time.strftime("%Y-%m-%d")
                p1_enc = config.teams[0].replace(' ', '%20')
                p2_enc = config.teams[1].replace(' ', '%20')
                base_api = "https://api.auxotracker.p-com.studio/api/matches/tennis/link"
                api_url = f"{base_api}?team1={p1_enc}&team2={p2_enc}&date={date_str}"
        except Exception as e:
            config.log(f"Erreur lors de la récupération du lien SofaScore: {e}", 'warning', True)

        

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
            '''if RedisIPC:
                config.perte = RedisIPC.deduct_amount_from_largest()
                RedisIPC.set_loss(config.scriptType, config.perte)'''
            #if RedisIPC.deduct_amount_from_largest(config.mtt_recup):
                #config.wantwin = config.mtt_recup
            config.perte = RedisIPC.deduct_largest(config.newmatch)
        RedisIPC.set_loss(config.scriptType, config.perte, matchname=config.newmatch)
            
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
            # Calcul manquant à cet endroit avant ce fix : total_gain était référencé
            # ligne suivante sans jamais être défini dans ce bloc (NameError garanti
            # si la branche était atteinte) — cf. AUDIT_MARTINGALE_TENNIS.md, calcul
            # identique à celui déjà fait plus loin dans ce même fichier.
            total_gain = RedisIPC.get_total_gain(config.newmatch) - RedisIPC.get_total_loss(config.newmatch)
            if all_below_one and not RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                for st in config.scriptTypeList:
                    config.log(f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                return True
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
            elif total_gain < float(config.total_gain_wanted):
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                config.log(f"Restart {config.scriptType}", 'success', False)

            else:
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} /{config.total_want_win[scriptType]}')
                config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                RedisIPC.set_running(config.scriptType, False)
                continue

            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)
            if not config.validated_bet:
                # Bug corrigé : "allfirstgamebet: False" était une annotation de type
                # (aucun effet), pas une affectation — il manquait le "=". Sans ce fix,
                # la boucle "while not allfirstgamebet" pouvait sortir prématurément
                # alors qu'un pari restait à valider.
                allfirstgamebet = False
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
                    total_gain = RedisIPC.get_total_gain(config.newmatch)-RedisIPC.get_total_loss(config.newmatch)

                    if all_below_one:
                        for st in config.scriptTypeList:
                            config.log(
                                f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                                'success', False)
                        return True
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    elif total_gain < float(config.total_gain_wanted):
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        config.log(f"Restart {config.scriptType}", 'success', False)
                    else:
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                        RedisIPC.set_running(config.scriptType, False)
                    
                        continue
                    config.result = GetResult(driver)
                    if config.result == 'WIN':
                        #GetIfGameEnd(driver)
                        config.perte = RedisIPC.get_loss(config.scriptType)
                        config.netprofit = round((float(config.validated_bet.get('montant', 0)) * float(config.validated_bet.get('cote', 0))) - float(config.perte), 2)
                        config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                            config.netprofit)
                        config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                        RedisIPC.add_gain_to_all(float(config.netprofit), config.newmatch)
                        config.init_variable()

                        total_gain = RedisIPC.get_total_gain(config.newmatch)-RedisIPC.get_total_loss(config.newmatch)
                        if (float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) and total_gain < float(config.total_gain_wanted)) or total_gain < float(config.total_gain_wanted):
                            print("#RECHERCHE INFOS DE MISE")
                            config.perte = 0
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte, matchname=config.newmatch)
                            config.wantwin =0.2
                            # Récupération de perte cross-script via Redis si disponible
                            # Bug corrigé : "loss" n'était défini nulle part dans ce fichier
                            # (NameError garanti dès cette branche atteinte). config.perte
                            # vient d'être forcé à 0 juste au-dessus, donc la condition
                            # "config.perte == 0" est ici toujours vraie de toute façon —
                            # aligné sur le même bloc de Functions_431a.py qui appelle ces
                            # deux fonctions sans condition supplémentaire.
                            if config.perte == 0:
                                getGlobalPerte()
                            if config.perte == 0:
                                get1setGlobalPerte()
                            if config.perte == 0:
                                # Récupération de perte cross-script via Redis si disponible
                                '''if RedisIPC:
                                    config.perte = RedisIPC.deduct_amount_from_largest()
                                    RedisIPC.set_loss(config.scriptType, config.perte)'''
                                #if RedisIPC.deduct_amount_from_largest(config.mtt_recup):
                                    #config.wantwin = config.mtt_recup
                                config.perte = RedisIPC.deduct_largest(config.newmatch)
                            if RedisIPC:
                                RedisIPC.set_loss(config.scriptType, config.perte, matchname=config.newmatch)
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
                    #DispatchPerte()
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
                        total_gain = RedisIPC.get_total_gain(config.newmatch)-RedisIPC.get_total_loss(config.newmatch)

                        if all_below_one and not RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                            for st in config.scriptTypeList:
                                config.log(f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                                        'success', False)
                            return True
                        if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        elif total_gain < float(config.total_gain_wanted):
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)
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
                #DispatchPerte()
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
                    total_gain = RedisIPC.get_total_gain(config.newmatch)-RedisIPC.get_total_loss(config.newmatch)
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                    elif total_gain < float(config.total_gain_wanted):
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        config.log(f"Restart {config.scriptType}", 'success', False)

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
            if all_below_one and not RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
                for st in config.scriptTypeList:
                    config.log(f' {st} Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                return True
            print('is running for ',config.newmatch)
            print(RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch))
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch):
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
            else:
                if config.scriptType in ['15V1', '15V2']:
                    _attendre_point_valide_15v(driver)

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

            total_gain = RedisIPC.get_total_gain(config.newmatch)-RedisIPC.get_total_loss(config.newmatch)
            config.log(f"Gain total match {config.newmatch}: {total_gain}", 'success', False)
            if total_gain >= float(config.total_gain_wanted):
                for st in config.scriptTypeList:
                    config.global_match_win[st] = float(config.total_want_win[st])
                    config.log(f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                    config.perte = 0
                    RedisIPC.set_loss(config.scriptType, 0, matchname=config.newmatch)
                config.log(f"FIN {config.scriptType}", 'success', False)
                RedisIPC.set_running(config.scriptType, False, config.newmatch)
                return True

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
                            tentative = tentative + 1                                     # incrémenter le compteur de tentatives
                            print('tentative validation ' + str(tentative))
                            if ValidationDuParis(driver, True):                           # essayer de valider le pari sur le site
                                validate_bet = True                                       # pari validé, on sortira de la boucle while
                                if config.scriptType in ['15V1', '15V2']:
                                    _attendre_point_valide_15v(driver)
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
                    FirstGameBet(driver)
                    firstjeu = True
            
            elif config.validated_bet.get('result') == 'WIN':
                config.perte = RedisIPC.get_loss(config.scriptType)
                config.netprofit = round((float(config.validated_bet.get('montant', 0)) * float(config.validated_bet.get('cote', 0))) - float(config.perte), 2)
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.log(f"netprofit : {config.netprofit}")
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                
                
                mtt_recup = getattr(config, 'mtt_recup', 0.0)
                print("#RECHERCHE INFOS DE MISE")
                
                RedisIPC.add_gain_to_all(float(config.netprofit), config.newmatch)
                config.perte = 0
                config.wantwin =0.2
                if RedisIPC:
                    RedisIPC.set_loss(config.scriptType, config.perte, matchname=config.newmatch)
                total_gain = RedisIPC.get_total_gain(config.newmatch) - RedisIPC.get_total_loss(config.newmatch)
                config.log(f"Gain total match {config.newmatch}: {total_gain} (net gain ajouté: {config.netprofit})", 'success', False)
                if RedisIPC.get_total_loss(config.newmatch) < 10:
                    GetIfGameEnd(driver)
                print('is running for ',config.newmatch)
                config.netprofit = 0
                config.validated_bet = {}

                print(RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch))
                if (float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]) or RedisIPC.list_running(exclude_script_type=config.scriptType, matchname=config.newmatch)) and total_gain < float(config.total_gain_wanted):
                    
                    #GetIfGameEnd(driver)

                    #
                    # ---------------------------------------------------------------------------
                    # Récupération de perte cross-script via Redis (priorité sur l'API)
                    # Déduit mtt_recup de la perte Redis la plus élevée tous scripts confondus.
                    # Si Redis est indisponible ou qu'il n'y a rien à déduire
                    # ---------------------------------------------------------------------------
                    if config.perte == 0:
                        # Récupération de perte cross-script via Redis si disponible
                        '''if RedisIPC:
                            config.perte = RedisIPC.deduct_amount_from_largest()
                            RedisIPC.set_loss(config.scriptType, config.perte)'''
                        #if RedisIPC.deduct_amount_from_largest(config.mtt_recup):
                            #config.perte = config.mtt_recup
                        config.perte = RedisIPC.deduct_largest(config.newmatch)
                        
                    # ---------------------------------------------------------------------------
                    #
                    '''if config.perte == 0:
                        getGlobalPerte()
                    if config.perte == 0:
                        get1setGlobalPerte()'''
                    '''if config.perte > 0:
                        GetIfGameEnd(driver)'''
                    if RedisIPC:
                        RedisIPC.set_loss(config.scriptType, config.perte, matchname=config.newmatch)
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
                                    _attendre_point_valide_15v(driver)
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
            else :
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
                            tentative = tentative + 1                                     # incrémenter le compteur de tentatives
                            print('tentative validation ' + str(tentative))
                            if ValidationDuParis(driver, True):                           # essayer de valider le pari sur le site
                                validate_bet = True                                       # pari validé, on sortira de la boucle while
                                if config.scriptType in ['15V1', '15V2']:
                                    _attendre_point_valide_15v(driver)
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
                    FirstGameBet(driver)
                    firstjeu = True
            
        if not GetIfMatchPage(driver):
            config.error = True
            break
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript(i)
        RedisIPC.set_running(config.scriptType, False)
        print('perte', config.perte)
        #DispatchPerte()
        config.ScriptConfig(i).reset()
        config.init_variable()
        config.global_match_win[i] = 0.0  # Initialize win counter for script type (float)
        config.winmatch[i] = 0  # Initialize match counter for script type
        if hasattr(config, 'sofascore_tab_handle'):
            from Functions.SofascoreWatcher import stop_sofascore_watcher
            stop_sofascore_watcher()
            driver.switch_to.window(config.sofascore_tab_handle)
            driver.close()
            delattr(config, 'sofascore_tab_handle')
            driver.switch_to.window(config.original_tab_handle)
    config.all_scores = {}
    # Supprimer le match de la base de données
    match_manager.remove_match(config.newmatch)

    # Nettoyer le script en cours
    script_manager.stop_script(config.scriptType, config.script_num)

    DeleteBet(driver)
    return True
