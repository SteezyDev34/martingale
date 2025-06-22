import json
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetJsonData import SendGlobalPerte, getPerte, set1DispatchPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch1set
from Functions.VerificationMatchTrouve import newmatchFromUrl


def all_script(driver):
    # driver.switch_to.window(driver.window_handles[0])
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    config.all_scores = {}

    # --------
    # SCRIPT RECHERCHE DE MATCH
    rechercheDeMatch1set(driver)

    # --------
    if config.match_found and not config.error:
        AddRunning.main(config.script_num, config.running_file_name)
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.teams = GetPlayersName(driver)
        newmatchFromUrl(driver)
        if not config.win_type:
            config.win_type = input("Quel est le win type V1/V2")

        config.log('RECHERCHE INFOS DE MISE', 'title', False)
        infosperte = getPerte()
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
            GetSetActuel(driver)
            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)

    config.lose = False
    while not config.error:
        # Read and iterate through bets from validated_bets.json
        with open('validated_bets.json', 'r') as f:
            validated_bets = json.load(f)
            for bet in validated_bets:
                print(bet)
                time.sleep(500)
                exit()
                for scriptType in config.scriptTypeList:
                    config.switchScript(scriptType)
                    # Check if all script types have global_match_win > 1
                    all_below_one = all(
                        float(config.global_match_win[st]) > float(config.total_want_win[st]) for st in
                        config.scriptTypeList)
                    if all_below_one:
                        for st in config.scriptTypeList:
                            config.log(f'Net profit: {config.global_match_win[st]}', 'success', False)
                        return True
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                    elif int(config.nb_tour[scriptType]) <= int(config.winmatch[scriptType]):
                        config.log(f'Net profit: {config.global_match_win[scriptType]}')
                        config.log(f'Nombre de tour {scriptType} atteint: {config.nb_tour[scriptType]}')
                        continue
                    ##ATTENTE QUE LE QT SE TERMINE
                    saved_set = config.set_actuel
                    while int(saved_set) == int(config.set_actuel):
                        GetScoreActuel(driver)
                    txtlog = "SET TERMINÉ ON VERIFIE LE SCORE"
                    config.log(txtlog, config.newmatch)
                    config.result = GetResult(driver)
                if config.result == 'LOSE':
                    set1DispatchPerte()
                    config.error = 'LOSE'
                    break
                elif config.result == 'WIN':
                    config.perte = 0
                    config.init_variable()
                    config.global_match_win = config.global_match_win + config.netprofit
                    DeleteBet(driver)
                    config.log(f'Net profit: {config.global_match_win}')
                    config.error = 'WIN'
                    break
                    ##PREPARATTION PREMIER PARIS

    if config.perte > 0.2:
        set1DispatchPerte()
    config.global_match_win = 0
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
