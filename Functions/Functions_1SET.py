import json
import time
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By

import Functions.GetJsonData
import config
from Functions import GetLigueName, RedisIPC
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.Functions_1XBET import remove_match_from_json_file
from Functions.GetJsonData import getPerte, set1DispatchPerte, get1setGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.Managers.MatchManager import match_manager
from Functions.Managers.ScriptManager import script_manager
from Functions.ScriptRechercheDeMatch import rechercheDeMatch1set
from Functions.VerificationMatchTrouve import newmatchFromUrl


def all_script(driver):
    # Nettoyer le script inactif
    script_manager.stop_script(config.scriptType, config.script_num)

    config.all_scores = {}

    # --------
    # SCRIPT RECHERCHE DE MATCH
    config.match_found = rechercheDeMatch1set(driver)
    # --------
    # Si un match est trouvé et qu'il n'y a pas d'erreur
    if config.match_found and not config.error:
        # Démarre le script avec le type et numéro spécifiés
        script_manager.start_script(config.scriptType, config.script_num)

        # Get league name and match URL
        ligue_info = GetLigueName.fromUrl(driver)
        print(ligue_info)
        config.ligue_name = ligue_info[0] + ' ' + str(config.cote_base)
        config.match_Url = ligue_info[1]
        print('LIGUE NAME:', config.ligue_name)
        # Récupère les noms des joueurs/équipes
        config.teams = GetPlayersName(driver)

        # Vérifie si c'est un nouveau match depuis l'URL
        newmatchFromUrl(driver)
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)

            if not config.win_type:
                config.win_type = input("Quel est le win type V1/V2")

            config.log('RECHERCHE INFOS DE MISE', 'title', False)
            infosperte = getPerte()
            print(infosperte)
            print(config.perte)
            if infosperte and config.perte == 0:
                config.perte = float(infosperte['perte'])
                print('PERTE RECUPERÉE DANS JSON :', config.perte)
                Functions.GetJsonData.delPerte(infosperte['id'])
            if not config.perte or config.perte == 0:
                infosperte = get1setGlobalPerte()
                config.perte = float(infosperte['perte'])
                print('PERTE RECUPERÉE DANS GLOBAL :', config.perte)
                
            config.rattrape_perte = 1
        # END RECHERCHE INFOS DE MISE
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            print('wintwin', config.wantwin)
            GetSetActuel(driver)
            ##PREPARATTION PREMIER PARIS
            FirstGameBet(driver)
            config.perte = 0
            RedisIPC.set_loss(config.scriptType, 0)  # Met à jour le statut du match dans le gestionnaire de matchs
            match_manager.add_match(config.newmatch)
    print('START CHEKING LIST')
    time.sleep(5)

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
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            ligue = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR: GetLigueName.main peut renvoyer False
            if not ligue:
                config.log_clear_line()
                config.error = False
                continue
            config.ligue_name = ligue + ' ' + str(config.cote_base)
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

                    # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                    newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                         'dashboard-game-block__link')[
                        0].get_attribute(
                        "href")
                    newmatch = newmatchtxt.split(
                        '-')
                    config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                    config.log(config.newmatch, 'info', False, 4)
                    # Check if newmatch exists in JSON file
                    try:
                        with open('1SET_validated_bets.json', 'r') as f:
                            match_data = json.load(f)
                            # Vérifie si config.newmatch est présent dans l'URL du fichier JSON
                            original_tab = driver.current_window_handle  # Mémorise l'onglet actuel
                            for match in match_data:
                                if 'timestamp' in match:
                                    match_time = datetime.strptime(match['timestamp'], "%Y-%m-%d %H:%M:%S")
                                    if match_time < datetime.now() - timedelta(days=2):
                                        print('match abandonné')
                                        config.perte = float(match['montant']) * float(match['cote'])
                                        set1DispatchPerte()
                                        remove_match_from_json_file('1SET_validated_bets.json', match['url'])
                                        config.error = 'LOSE'
                                        match_manager.remove_match(config.newmatch)
                                        continue
                                if 'url' in match and config.newmatch in match['url']:
                                    div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                           'ui-game-scores')
                                    text = div_bet_score[0].text
                                    text = text.replace(
                                        '\n', '')

                                    print('score : ', text)
                                    if '6' not in text and '7' not in text:
                                        # print('MATCH NON TERMINÉ SELON SCORE')
                                        continue
                                    elif '0066' in text or '0065' in text or '0056' in text:
                                        # print('TIE BREAK MATCH NON TERMINÉ SELON SCORE')
                                        continue
                                    else:
                                        print('MATCH TROUVÉ')
                                    # ✅ Ouvre un nouvel onglet via JavaScript
                                    newurl = bet_item.find_elements(By.CLASS_NAME, 'dashboard-game-block__link')[
                                        0].get_attribute(
                                        "href")
                                    print('# ✅ Ouvre un nouvel onglet via JavaScript')
                                    if config.site_type == 'mobile_site':
                                        newurl = newurl.replace('?platform_type=desktop', '')
                                        newurl = f'{newurl}?platform_type=mobile'
                                    driver.get(newurl)
                                    time.sleep(5)
                                    config.switchScript(config.scriptType)
                                    GetSetActuel(driver)
                                    config.validated_bet = match
                                    print(config.set_actuel)
                                    print(config.validated_bet['set'])
                                    if float(config.validated_bet['cote']) > 1.1 and float(config.validated_bet['cote']) < 1.4:
                                        config.cote_base = 1.3
                                    elif float(config.validated_bet['cote']) > 1.4 and float(config.validated_bet['cote']) < 1.7:
                                        config.cote_base = 1.5
                                    elif float(config.validated_bet['cote']) > 1.7 and float(config.validated_bet['cote']) < 1.9:
                                        config.cote_base = 1.8
                                    config.ligue_name = GetLigueName.fromUrl(driver)[0] + ' ' + str(config.cote_base)
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
                                        match_manager.remove_match(config.newmatch)
                                    elif config.result == 'WIN':
                                        # Load and process validated bets from JSON file
                                        remove_match_from_json_file('1SET_validated_bets.json', config.newmatch)
                                        config.perte = 0
                                        config.error = 'WIN'
                                        match_manager.remove_match(config.newmatch)
                                    return


                    except Exception as e:
                        print(e)

    DeleteBet(driver)
    return True
