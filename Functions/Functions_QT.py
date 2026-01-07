import config
from Functions import Functions_1XBET
from Functions import GetLigueName
from Functions.DeleteBet import DeleteBet
from Functions.FisrtQTBet import FirstQTBet
from Functions.Function_GetSetActuel import GetQTActuel
from Functions.GetIfGameStart import GetIfQTEnd, GetIfQTStart
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.ScriptRechercheDeMatch import rechercheDeMatchNBA
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    driver.switch_to.window(driver.window_handles[0])
    result = False
    # --------
    # SCRIPT RECHERCHE DE MATCH
    while not rechercheDeMatchNBA(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)

    # --------
    config.match_found = True
    if config.match_found and not config.error:
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.teams = GetPlayersName(driver)
        newmatchFromUrl(driver)

        config.log('RECHERCHE INFOS DE MISE', 'title', False)
        infosperte = getGlobalPerte()
        if infosperte and config.perte == 0:
            if float(infosperte['perte']) > 20:
                SendGlobalPerte(config.scriptType, -20)
                config.perte = 20
                config.rattrape_perte = 1
            elif float(infosperte['perte']) <= 20:
                config.perte = float(infosperte['perte'])
                m = 0 - config.perte
                SendGlobalPerte(config.scriptType, m)
                config.perte = float(infosperte['perte'])
        config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        print('wintwin', config.wantwin)
        GetQTActuel(driver)
        ##PREPARATTION PREMIER PARIS
        FirstQTBet(driver)

    GetIfQTStart(driver)
    config.lose = False
    while not config.error:
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            # Check if all script types have global_match_win > 1
            all_below_one = all(
                float(config.global_match_win[st]) > config.total_want_win for st in config.scriptTypeList)
            if all_below_one:
                for st in config.scriptTypeList:
                    config.log(f'Net profit: {config.global_match_win[st]}', 'success', False)
                return True
            if float(config.global_match_win[scriptType]) < 0.2:
                config.log(f'Net profit: {config.global_match_win[scriptType]}')
            elif int(config.nb_tour) <= int(config.winmatch[scriptType]):
                config.log(f'Net profit: {config.global_match_win[scriptType]}')
                config.log(f'Nombre de tour {scriptType} atteint: {config.nb_tour}')
                continue
            ##ATTENTE QUE LE QT SE TERMINE
            GetIfQTEnd(driver)
            txtlog = "QT TERMINÉ ON PREPARE LE PROCHAIN BET"
            config.log(txtlog, config.newmatch)
            result = GetResult(driver)
            GetQTActuel(driver)
            if result == 'LOSE':
                FirstQTBet(driver)
            elif result == 'WIN':
                config.perte = 0
                config.init_variable()
                config.global_match_win = config.global_match_win + config.netprofit
                DeleteBet(driver)
                config.log(f'Net profit: {config.global_match_win}')
                continue
            ##PREPARATTION PREMIER PARIS

        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
        RetourTpsReg(driver)
        GetIfQTStart(driver)

    if config.perte > 0.2:
        DispatchPerte()
    config.global_match_win = 0
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
