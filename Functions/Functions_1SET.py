import json
import time
from datetime import datetime, timedelta
from time import sleep

from selenium.webdriver.common.by import By

import Functions.GetJsonData
import config
from Functions import Functions_1XBET, UpdateMatchDone
from Functions import GetLigueName, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.Functions_1XBET import remove_match_from_json_file
from Functions.GetJsonData import getPerte, set1DispatchPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
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
    print('match found ', config.match_found)
    if config.match_found and not config.error:
        sleep(1)
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
            config.perte = float(infosperte['perte'])
            Functions.GetJsonData.delPerte(infosperte['id'])
        config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            print('wintwin', config.wantwin)
            GetSetActuel(driver)
            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)
            config.perte = 0
            UpdateMatchDone.main("add", config.newmatch, config.matchlist_file_name)

    config.lose = False
    print('START CHEKING LIST')
    time.sleep(5)

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
                    newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                         'dashboard-game-block__link')[
                        0].get_attribute(
                        "href")
                    newmatch = newmatchtxt.split(
                        '-')
                    config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                    config.log(config.newmatch, 'info', False, 4)
                    print('config new match ', config.newmatch)
                    # Check if newmatch exists in JSON file
                    try:
                        with open('1SET_validated_bets.json', 'r') as f:
                            match_data = json.load(f)
                            # Vérifie si config.newmatch est présent dans l'URL du fichier JSON
                            original_tab = driver.current_window_handle  # Mémorise l'onglet actuel
                            for match in match_data:
                                print('get match')
                                if 'timestamp' in match:
                                    match_time = datetime.strptime(match['timestamp'], "%Y-%m-%d %H:%M:%S")
                                    if match_time < datetime.now() - timedelta(days=2):
                                        config.perte = float(match['montant']) * float(
                                            match['cote'])
                                        set1DispatchPerte()
                                        remove_match_from_json_file('1SET_validated_bets.json', match['url'])

                                        config.error = 'LOSE'
                                        Functions_1XBET.update_match_done("del", config.newmatch,
                                                                          config.matchlist_file_name)
                                        continue
                                if 'url' in match and config.newmatch in match['url']:
                                    div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                           'ui-game-scores')
                                    text = div_bet_score[0].text
                                    text = text.replace(
                                        '\n', '')
                                    print(text)
                                    if '6' not in text and '7' not in text:
                                        print('MATCH NON TERMINÉ SELON SCORE')
                                        continue
                                    elif '0066' in text or '0065' in text or '0056' in text:
                                        print('TIE BREAK MATCH NON TERMINÉ SELON SCORE')
                                        continue
                                    else:
                                        print('MATCH TROUVÉ')
                                    # ✅ Ouvre un nouvel onglet via JavaScript
                                    newurl = bet_item.find_elements(By.CLASS_NAME, 'dashboard-game-block__link')[
                                        0].get_attribute(
                                        "href")
                                    print('# ✅ Ouvre un nouvel onglet via JavaScript')
                                    driver.get(newurl)
                                    time.sleep(5)
                                    config.switchScript(config.scriptType)
                                    GetSetActuel(driver)
                                    config.validated_bet = match
                                    print(config.validated_bet)
                                    print(config.set_actuel)
                                    print(config.validated_bet['set'])
                                    config.ligue_name = GetLigueName.fromUrl(driver)[0]
                                    ##ATTENTE QUE LE QT SE TERMINE
                                    if int(config.set_actuel) == int(config.validated_bet['set']):
                                        print('1ER SET NON TERMINÉ')
                                        return
                                    GetScoreActuel(driver)
                                    txtlog = "SET TERMINÉ ON VERIFIE LE SCORE"
                                    config.log(txtlog, config.newmatch)
                                    config.result = GetResult(driver)
                                    if config.result == 'LOSE':
                                        config.perte = float(config.validated_bet['montant']) * float(
                                            config.validated_bet['cote'])
                                        set1DispatchPerte()
                                        remove_match_from_json_file('1SET_validated_bets.json', config.newmatch)
                                        config.error = 'LOSE'
                                        Functions_1XBET.update_match_done("del", config.newmatch,
                                                                          config.matchlist_file_name)
                                    elif config.result == 'WIN':
                                        # Load and process validated bets from JSON file
                                        remove_match_from_json_file('1SET_validated_bets.json', config.newmatch)
                                        config.perte = 0
                                        config.error = 'WIN'
                                        Functions_1XBET.update_match_done("del", config.newmatch,
                                                                          config.matchlist_file_name)
                                    return


                    except Exception as e:
                        print(e)

    DeleteBet(driver)
    return True
