import inspect
import time

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtQTBet import FirstGameBet
from Functions.Function_GetQTScoreActuel import GetJeuActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.GetAndPlaceBet import GetAndPlaceBet
from Functions.GetIfGameStart import GetIfGameEnd
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJsonData import DispatchPerte, getGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.ValidationDuParis import ValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def all_script(driver):
    driver.switch_to.window(driver.window_handles[0])
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    # --------
    # SCRIPT RECHERCHE DE MATCH
    """ while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)
    """
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
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        getGlobalPerte()
        # END RECHERCHE INFOS DE MISE
    GetSetActuel(driver)
    if not config.set_actuel:
        config.error = True

    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        ##PREPARATTION PREMIER PARIS
        FirstGameBet(driver)

    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    RetourTpsReg(driver)

    passageset = False
    while not config.error:
        GetJeuActuel(driver)
        # WAIT FOR GAME START
        if passageset:
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
                    config.switchScript(scriptType)
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
            GetIfGameEnd(driver)
        # JEU FINI ON PREPARE LE PROCHAIN BET
        txtlog = "JEU FINI ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            if float(config.global_match_win) < 1:
                config.log(f'Net profit: {config.global_match_win}')
            elif config.nb_tour <= config.winmatch:
                config.log(f'Net profit: {config.global_match_win}')
                config.log(f'Nombre de tour {scriptType} atteint: {config.nb_tour}')
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
            if config.jeu_actuel >= 12:
                config.log('Tie break possible')
            else:
                GetAndPlaceBet(driver)
            config.result = GetResult(driver)
            if config.result == 'LOSE':
                # VÉRIFCATION DU SET ACTUEL
                GetScoreActuel(driver)
                if not config.set_actuel:
                    config.error = True
                config.log('set ' + str(config.set_actuel) + ' - nex set ' + str(config.newset))
                if str(int(config.newset) - 1) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.log('on est toujours sur le meme set', config.newmatch)
                    if config.jeu_actuel >= 12:
                        continue
                    ##VALIDATION DU PARIS SI SCORE OK
                    validate_bet = False
                    tentative = 0
                    while not validate_bet and not config.error and tentative < 3:
                        # VÉRIFICATION DU SCORE ACTUEL
                        tentative = tentative + 1
                        print('tentative validation ' + str(tentative))
                        if ValidationDuParis(driver, True):
                            validate_bet = True
                elif str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    txtlog = " ON EST SUR LE PROCHAIN SET"
                    passageset = True
                    config.newset = int(config.set_actuel) + 1
                    config.log(txtlog, config.newmatch)
                    DeleteBet(driver)
                    txtlog = 'Wait 30 sec'
                    config.log(txtlog, config.newmatch)
                    time.sleep(30)
                    break
                else:
                    print("ERROR : ecup set " + str(config.set_actuel))
                    config.error = True
            elif config.result == 'WIN':
                config.perte = 0
                config.global_match_win = config.global_match_win + config.netprofit
                config.winmatch = config.winmatch + 1
                DeleteBet(driver)
                if float(config.global_match_win) < 1:
                    print("#RECHERCHE INFOS DE MISE")
                    getGlobalPerte()
                    config.error = False
                    config.log(f"Restart {config.scriptType}", 'success', False)
                    FirstGameBet(driver)
                else:
                    config.log(f"FIN {config.scriptType}", 'success', False)

    if config.perte > 0.2:
        DispatchPerte()
    config.global_match_win = 0
    print("update : " + config.newmatch)
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
