import json
import os
import time
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions import Functions_1XBET
from Functions import GetLigueName, AddRunning
from Functions.DeleteBet import DeleteBet
from Functions.FisrtQTBet import FirstQTBet
from Functions.Function_GetSetActuel import GetQTActuel
from Functions.Function_scriptDelRunning import scriptDelRunning
from Functions.Functions_1XBET import remove_match_from_json_file
from Functions.GetJsonData import QTDispatchPerte, getGlobalPerte, SendGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.VerificationMatchTrouve import extract_match_slug_from_url
from Functions.VerificationMatchTrouve import newmatchFromUrl


def _get_qt_validated_bets_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'QT_validated_bets.json')


def all_script(driver):
    # driver.switch_to.window(driver.window_handles[0])
    result = False
    # Mise à jour du fichier txt des script en cours
    scriptDelRunning()
    # --------
    # SCRIPT RECHERCHE DE MATCH
    #
    #
    #
    config.match_found = False
    rechercheDeMatch(driver)
    # --------
    if config.match_found:
        if config.match_found and not config.error:
            AddRunning.main(config.script_num, config.running_file_name)
            config.ligue_name = GetLigueName.fromUrl(driver)[0]
            config.match_Url = GetLigueName.fromUrl(driver)[1]
            config.teams = GetPlayersName(driver)
            newmatchFromUrl(driver)

        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
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
            print('wintwin', config.wantwin)
            GetQTActuel(driver)
            ##PREPARATTION PREMIER PARIS
            FirstQTBet(driver)
            config.perte = 0

        config.lose = False
        config.perte = 0
    # VÉRIFICATION DES MATCH
    print('START CHEKING LIST')
    time.sleep(5)
    matches_ok = True
    while matches_ok:
        driver.get(config.site_url)
        matches_ok = False
        try:
            # RECUPERATION DES LIGUES EN COURS
            # config.log(' Récupération des ligues', 'info', True, 1)
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  'dashboard-champ')
        except:
            config.log('ligues introuvables!', 'warning', True, 2)
            return False
        else:
            config.log('ligues trouvées!', 'success', True, 2)
            # POUR CHAQUE LIGUE RÉCUPÉRÉE
            for bet_ligue in bet_list_ligue:
                if matches_ok:
                    break
                # ON RÉCUPÈRE LE NOM DE LA LIGUE
                config.ligue_name = GetLigueName.main(bet_ligue)
                # EN CAS D'ERREUR
                if not config.ligue_name:
                    # config.log('nom ligues introuvalbe!', 'warning', False, 2)
                    config.log_clear_line()
                    config.error = False
                    continue
                # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                # config.log(' ' + config.ligue_name, 'info', False, 2)
                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    config.log('Récupération des matchs', 'info', False, 3)
                    config.log_clear_line()
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'dashboard-champ__game')
                except:
                    # config.log('Listes des matchs introuvables!', 'warning', False, 3)
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        # config.log('Listes des matchs introuvables!', 'warning', False, 3)
                        # s'il y une erreur on passe au suivant
                        config.log_clear_line(2)
                        continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        if matches_ok:
                            break
                        # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                             'dashboard-game-block__link')[
                            0].get_attribute(
                            "href")
                        config.newmatch = extract_match_slug_from_url(newmatchtxt)
                        # config.log(config.newmatch, 'info', False, 4)
                        # Check if newmatch exists in JSON file
                        try:
                            print('ok')
                        except:
                            print('tet')
                        else:
                            json_file = _get_qt_validated_bets_path()
                            try:
                                with open(json_file, 'r') as f:
                                    match_data = json.load(f)
                            except FileNotFoundError:
                                match_data = []
                            # Vérifie si config.newmatch est présent dans l'URL du fichier JSON
                            original_tab = driver.current_window_handle  # Mémorise l'onglet actuel
                            for match in match_data:
                                if matches_ok:
                                    break
                                if 'timestamp' in match:
                                    match_time = datetime.strptime(match['timestamp'], "%Y-%m-%d %H:%M:%S")
                                    if match_time < datetime.now() - timedelta(days=2):
                                        print('match abandonné')
                                        config.perte = float(match['montant']) * float(match['cote'])
                                        QTDispatchPerte()
                                        print('insertion')
                                        remove_match_from_json_file(json_file, match['url'],
                                                                    match['scripttype'], match['timestamp'])
                                        print('remove')
                                        config.error = 'LOSE'
                                        continue
                                for scriptType in config.scriptTypeList:
                                    config.switchScript(scriptType)
                                    print('scriptType : ' + scriptType)

                                    if 'url' in match and config.newmatch in match[
                                        'url'] and config.scriptType.lower() == \
                                            match['scripttype'].lower():
                                        print(config.newmatch, match['url'], match['scripttype'], config.scriptType)

                                        div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                               'ui-game-scores')
                                        qt_section = div_bet_score[0].find_elements(By.CLASS_NAME,
                                                                                    'ui-game-scores__item')
                                        qt_actuel = len(qt_section) - 1
                                        try:
                                            element = WebDriverWait(bet_item, 10).until(
                                                EC.presence_of_element_located(
                                                    (By.CLASS_NAME, 'dashboard-game-info__period'))
                                            )
                                        except:
                                            matches_ok = True
                                            break
                                        div_period = bet_item.find_elements(By.CLASS_NAME,
                                                                            'dashboard-game-info__period')
                                        period = div_period[0].text
                                        period = period.replace(
                                            '\n', '')
                                        if period != "Mi-temps":
                                            period = period.split(' ')[0]
                                            period = int(''.join(char for char in period if char.isdigit()))
                                        print('period', period, 'qt_actuel', qt_actuel)
                                        if (period == "Mi-temps" and int(qt_actuel) == int(match['qt']) and
                                            qt_section[-1].text.strip().replace('\n', '') != "00") or (
                                                period == "Mi-temps" and int(qt_actuel) > int(match['qt']) and
                                                qt_section[-1].text.strip().replace('\n', '') == "00") or (
                                                period != "Mi-temps" and int(period) != int(match['qt'])):
                                            # print('MATCH NON TERMINÉ SELON SCORE')
                                            print('MATCH TROUVÉ')
                                        else:
                                            continue
                                        # ✅ Ouvre un nouvel onglet via JavaScript
                                        newurl = bet_item.find_elements(By.CLASS_NAME, 'dashboard-game-block__link')[
                                            0].get_attribute(
                                            "href")
                                        driver.get(newurl)
                                        time.sleep(5)
                                        config.validated_bet = {
                                            'montant': match['montant'],
                                            'scripttype': match['scripttype'],
                                            'qt': match['qt'],
                                            'win': match['win'],
                                            'timestamp': match['timestamp'],
                                            'url': match['url']
                                        }
                                        config.mise = match['montant']
                                        config.cote = match['cote']
                                        config.perte = float(match['montant']) * float(match['cote'])
                                        config.qt_actuel = match['qt']
                                        config.win_type = match['win']
                                        GetLigueName.fromUrl(driver)
                                        txtlog = "QT TERMINÉ ON PREPARE LE PROCHAIN BET"
                                        config.log(txtlog, config.newmatch)
                                        result = GetResult(driver)
                                        GetQTActuel(driver)
                                        if result == 'LOSE':
                                            if config.qt_actuel > 6:
                                                QTDispatchPerte()
                                            else:
                                                if FirstQTBet(driver):
                                                    print('BET VALIDE')
                                                    remove_match_from_json_file(json_file, match['url'],
                                                                                match['scripttype'], match['timestamp'])
                                            config.perte = 0
                                        elif result == 'WIN':
                                            config.perte = 0
                                            config.init_variable()
                                            DeleteBet(driver)
                                            remove_match_from_json_file(json_file, match['url'],
                                                                        match['scripttype'], match['timestamp'])
                                            Functions_1XBET.update_match_done("del", config.newmatch,
                                                                              config.matchlist_file_name)

                                        matches_ok = True
                                        driver.get(config.site_url)
                                        break
                                        ##PREPARATTION PREMIER PARIS

                                    # RETOUR SUR LA SECTION TPS REGLEMENTAIRE

                                    # RetourTpsReg(driver)

                        # except Exception as e:
                        # print('ERR', e)
            return True
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
