import json

from selenium.webdriver.common.by import By

import config
from Functions import Functions_1XBET, VerificationMatchTrouve
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
    config.match_found = rechercheDeMatch1set(driver)
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
    try:
        # RECUPERATION DES LIGUES EN COURS
        config.log(' Récupération des ligues', 'info', True, 1)
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ')
    except:
        config.log('ligues introuvables!', 'warning', True, 2)
        return False
    else:
        config.log('ligues trouvées!', 'success', True, 2)
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                config.log('nom ligues introuvalbe!', 'warning', False, 2)
                config.log_clear_line()
                config.error = False
                continue
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            config.log(' ' + config.ligue_name, 'info', False, 2)
            # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
            try:
                config.log('Récupération des matchs', 'info', False, 3)
                config.log_clear_line()
                bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                    'dashboard-champ__game')
            except:
                config.log('Listes des matchs introuvables!', 'warning', False, 3)
                # s'il y une erreur on passe au suivant
                continue
            else:
                if len(bet_items) <= 0:
                    config.log('Listes des matchs introuvables!', 'warning', False, 3)
                    # s'il y une erreur on passe au suivant
                    config.log_clear_line(2)
                    continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                for bet_item in bet_items:

                    # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                    config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                   config.matchlist_file_name)
                    config.newmatch = config.newmatch[1]
                    config.log(config.newmatch, 'info', False, 4)

                    # Check if newmatch exists in JSON file
                    try:
                        with open(config.matchlist_file_name, 'r') as f:
                            match_data = json.load(f)
                            # Vérifie si config.newmatch est présent dans l'URL du fichier JSON
                            for match in match_data:
                                if 'url' in match and config.newmatch in match['url']:
                                    driver.get(bet_item.find_elements(By.CLASS_NAME,
                                                                      'dashboard-game-block__link')[
                                        0].get_attribute(
                                        "href"))
                                    config.switchScript(config.scriptType)
                                    GetScoreActuel(driver)
                                    config.validated_bet = match
                                    ##ATTENTE QUE LE QT SE TERMINE
                                    if int(config.set_actuel) == int(config.validated_bet['set']):
                                        print('1ER SET NON TERMINÉ')
                                        continue
                                    GetScoreActuel(driver)
                                    txtlog = "SET TERMINÉ ON VERIFIE LE SCORE"
                                    config.log(txtlog, config.newmatch)
                                    config.result = GetResult(driver)
                                    if config.result == 'LOSE':
                                        config.perte = float(config.validated_bet['montant']) * float(
                                            config.validated_bet['cote'])
                                        set1DispatchPerte()
                                        config.error = 'LOSE'
                                        Functions_1XBET.update_match_done("del", config.newmatch,
                                                                          config.matchlist_file_name)
                                        break
                                    elif config.result == 'WIN':
                                        # Load and process validated bets from JSON file
                                        validated_bets_file = f"{config.scriptType}_validated_bets.json"
                                        try:
                                            with open(validated_bets_file, 'r') as f:
                                                validated_bets = json.load(f)

                                        except FileNotFoundError:
                                            config.log(f"No validated bets file found for {config.scriptType}",
                                                       "warning",
                                                       False)
                                        except json.JSONDecodeError:
                                            config.log(f"Error reading validated bets file for {config.scriptType}",
                                                       "error",
                                                       False)

                                        # Remove the bet entry from the JSON file
                                        with open(validated_bets_file, 'r') as f:
                                            validated_bets = json.load(f)
                                        validated_bets.remove(config.validated_bet)
                                        with open(validated_bets_file, 'w') as f:
                                            json.dump(validated_bets, f)
                                        config.perte = 0
                                        config.error = 'WIN'
                                        Functions_1XBET.update_match_done("del", config.newmatch,
                                                                          config.matchlist_file_name)


                    except:
                        pass

    DeleteBet(driver)
    return True
