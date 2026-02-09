import inspect
import json
import os
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from Functions import GetMatchScore, GetLigueName, Functions_stats
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.DeleteBet import DeleteBet
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetJsonData import getCompet, DispatchPerte, set1DispatchPerte
from Functions.Managers.MatchManager import match_manager
from Functions.Managers.ScriptManager import script_manager
from Functions.UpdateMatchDone import todo
from Functions.VerificationListeMatchLive import VerificationListeMatchLive
from Functions.WaitWhileTimeAppear import WaitWhileTimeAppear
from Functions._to_remove import AddRunning
from config import site_url


def charger_matchlist_depuis_json():
    """
    Fonction pour charger la liste des matchs depuis le fichier JSON le plus récent
    
    Returns:
        list: Liste des matchs si un fichier JSON valide existe, None sinon
    """
    try:
        datafiles_path = os.path.join(config.projectPath, "DataFiles")
        if not os.path.exists(datafiles_path):
            return None

        # Rechercher tous les fichiers matchlist_*.json
        json_files = [f for f in os.listdir(datafiles_path) if f.startswith('matchlist_') and f.endswith('.json')]

        if not json_files:
            config.log("Aucun fichier JSON de matchlist trouvé", 'info', True)
            return None

        use = input('Voulez vous utiliser le json récupéré? (Y/N): ')
        config.log_clear_line()
        if use.upper() not in ['Y', 'y', 'O', 'o']:
            config.log("Utilisation de la matchlist récupérée", 'info', True)
            return None

        # Trier par date de modification (le plus récent en premier)
        json_files.sort(key=lambda x: os.path.getmtime(os.path.join(datafiles_path, x)), reverse=True)
        latest_file = os.path.join(datafiles_path, json_files[0])

        # Charger le fichier JSON
        with open(latest_file, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        matchlist = data.get('matches', [])

        if matchlist and len(matchlist) > 0:
            config.log(f"Matchlist chargée depuis {latest_file} - {len(matchlist)} matchs trouvés", 'info', True)
            return matchlist
        else:
            config.log(f"Fichier JSON {latest_file} existe mais est vide", 'info', True)
            return None

    except Exception as e:
        config.log(f"Erreur lors du chargement du fichier JSON: {str(e)}", 'error', True)
        return None


def traiter_matchlist(matchlist):
    goodmatch = []
    for matchItem in matchlist:
        players_name = matchItem[0]
        ligue_name = matchItem[1]
        # Vérifier si c'est un match WTA
        if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
            config.proba40A = Functions_stats.get_wta_proba_40A_sofascore(players_name[0], players_name[1])
        else:
            config.proba40A = Functions_stats.get_wta_proba_40A_sofascore(players_name[0], players_name[1])
        if float(config.proba40A) >= float(config.probamini):
            matchItem.append(config.proba40A)
            goodmatch.append(matchItem)
    return goodmatch


def sauvegarder_matchlist_json(matchlist):
    try:
        # Créer un nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"matchlist_{timestamp}.json"
        json_filepath = os.path.join(config.projectPath, "DataFiles", json_filename)

        # Créer le dossier DataFiles s'il n'existe pas
        os.makedirs(os.path.dirname(json_filepath), exist_ok=True)

        # Préparer les données à enregistrer
        data_to_save = {
            "timestamp": datetime.now().isoformat(),
            "total_matches": len(matchlist),
            "matches": matchlist
        }

        # Enregistrer dans le fichier JSON
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data_to_save, json_file, ensure_ascii=False, indent=2)

        config.log(f"Matchlist enregistrée dans: {json_filepath}", 'info', True)

    except Exception as e:
        config.log(f"Erreur lors de l'enregistrement de matchlist: {str(e)}", 'error', True)


def rechercheDeMatch(driver):
    config.error = False
    config.log("-" * 60, "title", False, False, False)
    config.log(' RECHERCHE DE MATCH', 'title', False, False, False)
    config.log("-" * 60, "title", False, False, False)
    config.match_found = False
    while not config.match_found and not config.error:
        if config.in_stat and (
                not config.last_classement or config.last_classement != datetime.now().strftime("%Y-%m-%d")):
            config.log("Classement différent du dernier run, recherche de nouveaux matchs", 'info', True)
            classementeDeMatch(driver, False)

        logline = 0
        print('test error', config.error)
        config.match_found = GetIfMatchPage(driver)
        page_de_match = config.match_found
        if not config.match_found and float(config.perte) > 0:
            if config.scriptType == '1SET':
                set1DispatchPerte()
            else:
                DispatchPerte()
        # SCRIPT RECHERCHE DE MATCH
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        script_manager.check_previous_scripts(config.script_num)
        # VERIFICATION SI PAGE DE LIST LIVE"""
        """if not VerificationListeMatchLive(driver):
            config.log("PAGE VIDE", 'error', True)
            driver.get(config.site_url)
            return False"""
        if config.site_type == 'mobile_site':
            config.site_type = 'new_site'
            DeleteBet(driver)
            config.site_type = 'mobile_site'
        try:
            # RECUPERATION DES LIGUES EN COURS
            config.log('Récupération des ligues', 'info', False, 1, show_script_type=False)
            logline += 1
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  config.classes['dashboard_champ'][config.site_type])

        except:
            config.log('ligues introuvables!', 'warning', True, 2, False)
            logline += 3
            config.log_clear_line(logline)
            return False
        else:
            print('#3TFRTYH2', config.error)
            config.log('ligues trouvées!', 'success', True, 2, False)
            # POUR CHAQUE LIGUE RÉCUPÉRÉE
            for bet_ligue in bet_list_ligue:
                logligueline = 0
                # ON RÉCUPÈRE LE NOM DE LA LIGUE
                config.ligue_name = GetLigueName.main(bet_ligue)
                # EN CAS D'ERREUR
                if not config.ligue_name:
                    config.log('nom ligues introuvalbe!', 'warning', True, 2, False)
                    config.error = False
                    config.log_clear_line(logligueline)
                    continue
                # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                config.log(config.ligue_name, 'info', False, 2, False)
                logligueline += 1

                if getCompet():
                    # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                    try:
                        config.log('Récupération des matchs', 'info', False, 3, False)
                        logligueline += 1

                        bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                            config.classes['dashboard_champ_matchlist'][
                                                                config.site_type])
                    except:
                        config.log('Listes des matchs introuvables!', 'warning', True, 3, False)
                        config.log_clear_line(logligueline)
                        # s'il y une erreur on passe au suivant
                        continue
                    else:
                        if len(bet_items) <= 0:
                            config.log('Listes des matchs introuvables!', 'warning', True, 3, False)
                            config.log_clear_line(logligueline)
                            continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                        for bet_item in bet_items:
                            try:
                                config.log('On récupère le nom des joueurs', 'info', False, 3, False)
                                logligueline += 1

                                div_bet_player = bet_item.find_element(By.CLASS_NAME, config.classes[
                                    'dashboard_champ_match_teams_name'][
                                    config.site_type])
                            except:
                                config.log('Impossible de récpérer les joueurs!', 'warning', True, 3, False)
                                continue
                            else:
                                if div_bet_player:
                                    div_bet_player = div_bet_player.text.split('\n')
                                    config.log(str(div_bet_player), 'info', False, 3, False)
                                    logligueline += 1

                                try:
                                    # on récupère le score
                                    div_bet_score = bet_item.find_elements(By.CLASS_NAME, config.classes[
                                        'dashboard_champ_match_teams_score'][
                                        config.site_type])
                                except:

                                    config.log('Impossible de récupérer le score!', 'warning', True, 4)
                                    continue
                                else:
                                    # si le score est récupéré
                                    if len(div_bet_score) <= 0:
                                        config.log('Pas de score!', 'warning', True, 4, False)
                                        continue
                                    # on le vérifie
                                    config.log('Vérification du score!', 'info', False, 4, False)
                                    logligueline += 1

                                    bet_score = GetMatchScore.main(div_bet_score[0],
                                                                   config.score_to_start)
                                    if bet_score:  # SI LE MATCH EST PRET
                                        config.log('Score OK', 'info', False, 4, False)
                                        logligueline += 1

                                        # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                        config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                                       config.matchlist_file_name)
                                        if config.site_type == 'mobile_site':
                                            config.site_type = 'new_site'
                                            DeleteBet(driver)
                                            config.site_type = 'mobile_site'
                                        if config.newmatch[0]:
                                            print('#3TFYH', config.error)
                                            if OuverturePageMatch.main(bet_item, config.script_num,
                                                                       config.newmatch[1],
                                                                       config.running_file_name,
                                                                       config.matchlist_file_name):
                                                config.newmatch = config.newmatch[1]
                                                config.match_found = True
                                                config.log_clear_line(logligueline)
                                                break
                                            else:
                                                continue
                                    else:
                                        config.log('Score NOT OK', 'warning', False, 4, False)
                                        logligueline += 1

                if config.match_found:
                    AddRunning.main(config.script_num, config.running_file_name)
                    break
                config.log_clear_line(logligueline)

        if not config.match_found:
            config.log_clear_line(logline)
            config.log('PAS DE MATCH TROUVE!', 'warning', False, 2, False)
            driver.get(config.site_url)
            time.sleep(5)
            config.log_clear_line()
        else:
            print('get mobile url')
            get_url = driver.current_url
            get_url = get_url.replace('?platform_type=mobile', '')
            get_url += '?platform_type=mobile'
            driver.get(get_url)
            print(get_url)
            print('MATCH TROUVE!')
            logline += 3
            config.log_clear_line(logline)
            time.sleep(3)
        # FIN# VERIFICATION SI PAGE DE MATCH LIVE

    return config.match_found


def rechercheDeMatch1set(driver):
    config.error = False
    # config.log(' RECHERCHE DE MATCH', 'title', False)
    config.match_found = False
    # config.init_variable()
    config.match_found = GetIfMatchPage(driver)
    if not config.match_found and float(config.perte) > 0:
        if config.scriptType == '1SET':
            set1DispatchPerte()
        else:
            DispatchPerte()
    # config.match_found = False
    # SCRIPT RECHERCHE DE MATCH
    # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
    script_manager.check_previous_scripts(config.script_num)
    # VERIFICATION SI PAGE DE LIST LIVE"""
    """if not VerificationListeMatchLive(driver):
        config.log("PAGE VIDE", 'error', True)
        driver.get(config.site_url)
        return False"""
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
            config.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                config.log('nom ligues introuvalbe!', 'warning', False, 2)
                # config.log_clear_line()
                config.error = False
                continue
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            config.log(' ' + config.ligue_name, 'info', False, 2)
            # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
            if getCompet():
                try:
                    config.log('Récupération des matchs', 'info', False, 3)
                    # config.log_clear_line()
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
                        # config.log_clear_line(2)
                        continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            config.log('On récupère le nom des joueurs', 'info', False, 3)
                            # config.log_clear_line()
                            div_bet_player = bet_item.find_element(By.CLASS_NAME, 'ui-team-scores__teams')
                        except:
                            config.log('Impossible de récpérer les joueurs!', 'warning', False, 3)
                            # config.log_clear_line()
                            continue
                        else:
                            if div_bet_player:
                                div_bet_player = div_bet_player.text.split('\n')
                                config.log(str(div_bet_player), 'info', False, 3)
                                # config.log_clear_line()
                            try:
                                # on récupère le score
                                div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                       'ui-game-scores')
                            except:

                                config.log('Impossible de récupérer le score!', 'warning', False, 4)
                                time.sleep(2)
                                # config.log_clear_line()
                                continue
                            else:
                                # si le score est récupéré
                                if len(div_bet_score) <= 0:
                                    config.log('Pas de score!', 'warning', False, 4)
                                    time.sleep(2)
                                    # config.log_clear_line()
                                    continue
                                # on le vérifie
                                config.log('Vérification du score!', 'info', False, 4)
                                # config.log_clear_line()
                                bet_score = GetMatchScore.set1main(div_bet_score[0],
                                                                   config.score_to_start)

                                try:
                                    div_bet_cote = bet_item.find_element(By.CLASS_NAME,
                                                                         'dashboard-markets__group')
                                    btn_cote = div_bet_cote.find_elements(By.CLASS_NAME, 'dashboard-markets__market')
                                    cotev1 = float(btn_cote[0].text)
                                    print('cote v1', cotev1)
                                    cotev2 = float(btn_cote[2].text)
                                    print('cote v2', cotev2)
                                except Exception as e:
                                    print(f'erreur de cote {e}')
                                    continue
                                else:
                                    if cotev1 > 1.1 and cotev1 < 1.4:
                                        config.win_type = 'V1'
                                        config.cote_base = 1.3
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev1 > 1.4 and cotev1 < 1.7:
                                        config.win_type = 'V1'
                                        config.cote_base = 1.5
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev1 > 1.7 and cotev1 < 1.9:
                                        config.win_type = 'V1'
                                        config.cote_base = 1.8
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev2 > 1.1 and cotev2 < 1.4:
                                        config.cote_base = 1.3
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                    elif cotev2 > 1.4 and cotev2 < 1.7:
                                        config.cote_base = 1.5
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                    elif cotev2 > 1.7 and cotev2 < 1.9:
                                        config.cote_base = 1.8
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                    else:
                                        continue
                                if bet_score:  # SI LE MATCH EST PRET

                                    config.log('Score ok', 'info', False, 4)
                                    # config.log_clear_line()
                                    # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                    if config.site_type == 'mobile_site':
                                        config.site_type = 'new_site'
                                        DeleteBet(driver)
                                        config.site_type = 'mobile_site'

                                    config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                                   config.matchlist_file_name)
                                    if config.newmatch[0]:
                                        if OuverturePageMatch.main(bet_item, config.script_num,
                                                                   config.newmatch[1],
                                                                   config.running_file_name,
                                                                   config.matchlist_file_name):
                                            config.newmatch = config.newmatch[1]
                                            config.log(config.newmatch, 'info', False, 4)
                                            config.match_found = True
                                            break
                                        else:
                                            continue
                                else:
                                    config.log('Score NOT ok', 'warning', False, 4)
                                    config.log_clear_line()
            config.log_clear_line()
            if config.match_found:
                AddRunning.main(config.script_num, config.running_file_name)
                break

    if not config.match_found:
        config.log('PAS DE MATCH TROUVE!', 'warning', True, 2)
        # config.log_clear_line(3)
        driver.get(config.site_url)
        time.sleep(5)
    else:
        get_url = driver.current_url
        get_url = get_url.replace('?platform_type=mobile', '')
        get_url += '?platform_type=mobile'
        driver.get(get_url)
        config.log('MATCH TROUVE!', 'success', False, 2)
        time.sleep(5)
    # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCHs
    return config.match_found


def rechercheDeMatchNBA(driver):
    config.error = False
    print('RECHERCHE DE MATCH NBA')
    config.match_found = False
    while not config.match_found and not config.error:
        config.init_variable()
        """On vérifie si c'est la page d'un match """
        config.match_found = GetIfMatchPage(driver)
        # SCRIPT RECHERCHE DE MATCH
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        script_manager.check_previous_scripts(config.script_num)
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            current_frame = inspect.currentframe()
            if current_frame:
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
            else:
                config.log('Error in VerificationListeMatchLive', 'error', True)
            print("PAGE VIDE")
            driver.get('https://1xbet.com/fr/live/basketball/')
            return False
        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config.ligue_name = GetLigueName.main(bet_ligue)
            print(config.ligue_name)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                config.error = False
                break
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            x = True
            if x:
                print('get comp')
                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'c-events-scoreboard__item')
                except:
                    print(' c-events-scoreboard__item')
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            # on récupère le score
                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                   'c-events-scoreboard__lines_tennis')
                        except:
                            txtlog = "Impossible de récupérer le score"
                            config.log(txtlog, 'warning', True)
                            print(txtlog)
                            continue
                        else:
                            # si le score est récupéré
                            if len(div_bet_score) <= 0:
                                print("pas de sc")
                                continue
                            # on le vérifie
                            bet_score = GetMatchScore.main(div_bet_score[0],
                                                           config.score_to_start)
                            if bet_score:  # SI LE MATCH EST PRET
                                # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                print(' # ON VERIFIE QU IL N A PAS DÉJA ÉTÉ PARIÉ')
                                config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                               config.matchlist_file_name)
                                print('config.newmatch[0]', config.newmatch[0])
                                if config.newmatch[0]:
                                    if OuverturePageMatch.main(bet_item, config.script_num,
                                                               config.newmatch[1],
                                                               config.running_file_name,
                                                               config.matchlist_file_name):
                                        config.newmatch = config.newmatch[1]
                                        config.match_found = True
                                        break
                                    else:
                                        continue
            else:
                print('pas de get compet')
            if config.match_found:
                AddRunning.main(config.script_num, config.running_file_name)
                break

        if not config.match_found:
            config.log('PAS DE MATCH TROUVE', 'info', True)
            driver.get('https://1xbet.com/fr/live/basketball/')

        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH
    return config.match_found


def classementeDeMatch(driver, use_json_cache=True):
    driver.get(config.site_line_url)
    config.error = False
    config.match_found = False
    save_site_type = config.site_type
    config.site_type = 'new_site'
    while not config.match_found and not config.error:
        line = 0
        config.init_variable()
        matchlist_from_json = None
        if use_json_cache:
            matchlist_from_json = charger_matchlist_depuis_json()

        if matchlist_from_json is not None:
            # Utiliser la matchlist du fichier JSON
            matchlist = matchlist_from_json
            config.log(f"Matchlist chargée depuis JSON - {len(matchlist)} matchs", 'info', True)
        else:
            """On vérifie si c'est la page d'un match """
            config.match_found = GetIfMatchPage(driver)
            # SCRIPT RECHERCHE DE MATCH
            # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
            # script_manager.check_previous_scripts(config.script_num)
            # VERIFICATION SI PAGE DE LIST LIVE"""
            if not VerificationListeMatchLive(driver):
                config.error = True
                driver.get(config.site_line_url)
                return False
            # RECUPERATION DES LIGUES EN COURS
            bet_list_ligue = driver.find_elements(By.CLASS_NAME, config.classes['dashboard_champ'][config.site_type])
            matchlist = []
            liguelist = []
            for bet_ligue in bet_list_ligue:
                # ON RÉCUPÈRE LE NOM DE LA LIGUE
                config.ligue_name = GetLigueName.main(bet_ligue)
                # EN CAS D'ERREUR
                if not config.ligue_name:
                    config.error = False
                    break
                liguelist.append([bet_ligue.find_elements(By.CLASS_NAME,
                                                          config.classes['dashboard_champ_name'][config.site_type])[
                    0].get_attribute(
                    "href"), config.ligue_name])

            for link in liguelist:
                if link[0]:
                    config.ligue_name = link[1]
                    if not getCompet():
                        config.log('Compétition non autorisé', 'warning', True)
                        continue
                    config.log(f'Accès à : {link[0]}', 'info', True)
                    driver.get(link[0])
                else:
                    continue

                if not WaitWhileTimeAppear(driver):
                    config.log('Wait time appear', 'warning', True)
                    continue

                bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                      config.classes['dashboard_champ_body_games'][config.site_type])
                # POUR CHAQUE LIGUE RÉCUPÉRÉE
                for bet_ligue in bet_list_ligue:

                    # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                    line += 1
                    # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                    try:
                        bet_items = driver.find_elements(By.CLASS_NAME,
                                                         config.classes['dashboard_game_block_row'][
                                                             config.site_type])
                    except:
                        # s'il y une erreur on passe au suivant
                        continue
                    else:
                        if len(bet_items) <= 0:
                            config.log('AUCUN MATCHS RÉCUPÉ', 'warning', True)
                            continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                        i = 0
                        for bet_item in bet_items:
                            # Initialiser les variables de date pour éviter des références non définies
                            day_month = None
                            hour = None
                            current_year = None
                            try:
                                # Attendre jusqu'à 10 secondes que l'élément s'affiche dans bet_item
                                time_element = WebDriverWait(bet_item, 10).until(EC.visibility_of_element_located(
                                    (By.CLASS_NAME, config.classes['events_time'][config.site_type])))

                                if config.site_type == 'old_site':
                                    start_time_text = bet_item.find_element(By.CLASS_NAME,
                                                                            config.classes['events_time'][
                                                                                config.site_type]).text
                                elif config.site_type == 'new_site':
                                    start_date_text = time_element.find_element(By.CLASS_NAME,
                                                                                'dashboard-game-info__date').text
                                    start_time_text = time_element.find_element(By.CLASS_NAME,
                                                                                'dashboard-game-info__time').text
                                    start_time_text = start_date_text + ' ' + start_time_text
                            except Exception as e:
                                events_time_selector = config.classes['events_time'][config.site_type]
                                config.log(
                                    f'heure de debut non trouvé {events_time_selector} {e} ',
                                    'warning', True)
                            else:
                                try:
                                    parts = start_time_text.split()
                                    if len(parts) >= 2:
                                        day_month = parts[0]  # '09/09'
                                        hour = parts[1].split()[0]
                                        # Ajouter l'année actuelle
                                        current_year = datetime.now().year
                                        match_date_only = datetime.strptime(f"{day_month}/{current_year}",
                                                                            "%d/%m/%Y").date()

                                        # Date actuelle sans l'heure
                                        today = datetime.now().date()

                                        if match_date_only > today:
                                            config.log('Match date later', 'warning', True)
                                            # Match prévu dans le futur, on passe
                                            continue
                                        else:
                                            config.log(match_date_only, 'info', True)
                                except ValueError:
                                    config.log("Erreur de parsing de la date", 'warning', True)

                            try:
                                teams_name = bet_item.find_element(By.CLASS_NAME,
                                                                   config.classes['team_wrap'][config.site_type])
                                players = teams_name.find_elements(By.CLASS_NAME,
                                                                   config.classes['team_name'][config.site_type])
                                players_name = []
                                match = []
                                if len(players) <= 1:
                                    continue
                                for player in players:
                                    player = player.text.split('(')[0]
                                    player = player.strip()
                                    config.log(player, config.newmatch)
                                    players_name.append(player)
                                match.append(players_name)
                                match.append(config.ligue_name)
                                newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                                     config.classes['match_link'][
                                                                         config.site_type])[
                                    0].get_attribute(
                                    "href")
                                newmatch = newmatchtxt.split(
                                    '-')
                                config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                                match.append(config.newmatch)
                                # N'ajouter la date que si toutes les composantes sont définies
                                if day_month and current_year and hour:
                                    match_date = datetime.strptime(
                                        f"{day_month}/{current_year} {hour}:00",
                                        "%d/%m/%Y %H:%M:%S"
                                    ).strftime("%Y-%m-%d %H:%M:%S")
                                    match.append(match_date)
                                else:
                                    # Si l'heure ou la date n'est pas disponible, ignorer ce match
                                    continue
                                matchlist.append(match)

                            except Exception as e:
                                continue
                    config.log_clear_line(line)
                    line = 0

        # Sauvegarder la matchlist dans un fichier JSON avant traitement
        sauvegarder_matchlist_json(matchlist)

        # Traiter les matchs pour obtenir les probabilités
        goodmatch = traiter_matchlist(matchlist)

        # Tri en fonction de la dernière valeur (indice -1) en ordre décroissant
        tableau_trie = sorted(goodmatch, key=lambda x: x[-1], reverse=True)

        # Fonction de priorisation des matchs par ligue
        def prioritize_matches_by_league(matches, max_matches=30):
            """
            Priorise les matchs selon la hiérarchie des ligues :
            1. ATP sans "qualification"
            2. Challenger sans "qualification"  
            3. WTA sans "qualification"
            4. ATP avec "qualification"
            5. Challenger avec "qualification"
            6. WTA avec "qualification"
            7. ITF sans "qualification"
            8. ITF avec "qualification"
            """
            # Catégoriser les matchs par priorité
            priority_groups = {
                1: [],  # ATP sans qualification
                2: [],  # Challenger sans qualification
                3: [],  # WTA sans qualification
                4: [],  # ATP avec qualification
                5: [],  # Challenger avec qualification
                6: [],  # WTA avec qualification
                7: [],  # ITF sans qualification
                8: []   # ITF avec qualification
            }
            
            for match in matches:
                ligue_name = match[1].lower()
                has_qualification = 'qualification' in ligue_name
                
                # Déterminer la priorité basée sur le nom de la ligue
                if 'atp' in ligue_name:
                    priority = 4 if has_qualification else 1
                elif 'challenger' in ligue_name:
                    priority = 5 if has_qualification else 2
                elif any(wta_term in ligue_name for wta_term in ['wta', 'féminin', 'femmes', 'women']):
                    priority = 6 if has_qualification else 3
                elif 'itf' in ligue_name:
                    priority = 8 if has_qualification else 7
                else:
                    # Autres ligues, priorité basse
                    priority = 8
                
                priority_groups[priority].append(match)
            
            # Construire la liste finale en respectant les priorités
            final_matches = []
            for priority in sorted(priority_groups.keys()):
                group = priority_groups[priority]
                # Trier chaque groupe par probabilité décroissante
                group_sorted = sorted(group, key=lambda x: x[-1], reverse=True)
                
                # Ajouter les matchs jusqu'à atteindre la limite
                remaining_slots = max_matches - len(final_matches)
                if remaining_slots <= 0:
                    break
                    
                final_matches.extend(group_sorted[:remaining_slots])
            
            return final_matches

        # Appliquer la priorisation pour retenir les 30 meilleurs matchs
        top_matches = prioritize_matches_by_league(tableau_trie, 30)

        for match in top_matches:
            try:
                # Assurer un format propre pour les joueurs: "Joueur A - Joueur B"
                players = match[0]
                if isinstance(players, (list, tuple)):
                    players_str = " - ".join(str(p).strip().strip("[]'\"") for p in players)
                else:
                    # Nettoyer les éventuels crochets/quotes provenant d'une conversion liste->str
                    players_str = str(players).strip().strip("[]'\"")

                # Recomposer la ligne au format attendu
                league = match[1]
                match_id = match[2]
                date_str = match[3]
                prob = match[4]
                match_info = "|".join([
                    players_str,
                    str(league),
                    str(match_id),
                    str(date_str),
                    str(prob)
                ])

                success = match_manager.add_match_todo(match_info)
                if success:
                    config.log(f"Match ajouté à la liste: {match[0]} vs {match[1]}", 'success', True)
                else:
                    config.log(f"Match déjà dans la liste: {match[0]} vs {match[1]}", 'warning', True)
            except Exception as e:
                config.log(f"Erreur lors de l'ajout du match: {str(e)}", 'error', True)

        # Sauvegarde de la date dans un fichier
        last_classement_file = os.path.join(config.projectPath, "DataFiles", "last_classement.txt")
        try:
            with open(last_classement_file, 'w') as f:
                f.write(datetime.now().strftime("%Y-%m-%d"))
                config.last_classement = datetime.now().strftime("%Y-%m-%d")
                config.log(f"Date du dernier classement sauvegardée: {datetime.now().strftime('%Y-%m-%d')}", 'info',
                           True)
        except Exception as e:
            config.log(f"Erreur lors de la sauvegarde de la date: {str(e)}", 'error', True)
        # Créer le dossier DataFiles/done s'il n'existe pas
        done_dir = os.path.join(config.projectPath, "DataFiles", "done")
        os.makedirs(done_dir, exist_ok=True)

        # Déplacer les anciens fichiers matchlist_*.json dans le dossier done
        datafiles_path = os.path.join(config.projectPath, "DataFiles")
        for filename in os.listdir(datafiles_path):
            if filename.startswith('matchlist_') and filename.endswith('.json'):
                src_path = os.path.join(datafiles_path, filename)
                dst_path = os.path.join(done_dir, filename)
                try:
                    os.rename(src_path, dst_path)
                except Exception as e:
                    config.log(f"Erreur lors du déplacement de {filename} vers done: {str(e)}", 'warning', True)
        config.log_clear_line(line)
        break
    config.site_type = save_site_type


# Fonction déplacée dans MatchManager


def newclassementeDeMatch(driver):
    driver.get(site_url)
    config.error = False
    print('RECHERCHE DE MATCH')
    config.match_found = False
    while not config.match_found and not config.error:
        config.init_variable()
        """On vérifie si c'est la page d'un match """
        config.match_found = GetIfMatchPage(driver)
        # SCRIPT RECHERCHE DE MATCH
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        script_manager.check_previous_scripts(config.script_num)
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            config.error = True
            print("PAGE VIDE")
            driver.get(config.site_url)
            return False
        # VÉRIFICATION S'IL EXISTE UN FICHIER JSON DE MATCHLIST
        matchlist_from_json = charger_matchlist_depuis_json()

        if matchlist_from_json is not None:
            # Utiliser la matchlist du fichier JSON
            matchlist = matchlist_from_json
            config.log(f"Matchlist chargée depuis JSON - {len(matchlist)} matchs", 'info', True)
        else:
            # Procéder au scraping normal
            config.log("Aucun fichier JSON valide trouvé, procédure de scraping normale", 'info', True)

            # RECUPERATION DES LIGUES EN COURS
            tennis_menu = driver.find_elements(By.CLASS_NAME,
                                               'sports-menu-app-sport')

            for menu in tennis_menu:
                sport_link = menu.find_element(By.CLASS_NAME, 'sports-menu-app-sport__link')
                sport = sport_link.find_element(By.CLASS_NAME, 'ui-nav-link-caption__label').text
                if 'tennis de table' in sport.lower():
                    continue
                elif 'tennis' not in sport.lower():
                    continue
                else:
                    # print('tennis trouvé')
                    # print('click ok')
                    break
            country = driver.find_element(By.CLASS_NAME, 'sports-menu-group-by-country')
            # print('find countries')
            countrybutton = country.find_elements(By.CLASS_NAME, 'sports-menu-group-by-champ')
            links = []
            for cntrybtn in countrybutton:
                # print('country', cntrybtn.text.lower())
                if ('double' in cntrybtn.text.lower()
                        or 'spéciaux' in cntrybtn.text.lower()
                        or 'special' in cntrybtn.text.lower()
                        or 'mixte' in cntrybtn.text.lower()
                        or 'gagnant' in cntrybtn.text.lower()
                        or 'itf' in cntrybtn.text.lower()
                        or 'winner' in cntrybtn.text.lower()
                        or 'utr' in cntrybtn.text.lower()):
                    continue
                classes = cntrybtn.get_attribute("class")  # récupère toutes les classes dans une string
                linkcontent = cntrybtn.find_element(By.CLASS_NAME, 'ui-nav-link__content')
                link = linkcontent.get_attribute(
                    "href")
                # Vérifier si 'nav_link' est absent
                if "sports-menu-app-champ-with-sub-champs-group__item" not in classes.split() and link:
                    print('link', link)
                    links.append(link)
                    continue
                elif linkcontent:
                    linkcontent.click()
                    print('click country', linkcontent.text)
                else:
                    continue

                liguebtn = driver.find_elements(By.CLASS_NAME, 'sports-menu-app-champ-with-sub-champs-group__item')
                for lbtn in liguebtn:
                    link = lbtn.find_element(By.CLASS_NAME, 'ui-nav-link__content').get_attribute(
                        "href")
                    if ('double' in link.lower()
                            or 'spéciaux' in link.lower()
                            or 'mixte' in link.lower()
                            or 'gagnant' in link.lower()
                            or 'winner' in link.lower()
                            or 'utr' in link.lower()
                            or 'double' in link.lower()):
                        continue
                    print('link', link)
                    links.append(link)
                linkcontent.click()
                time.sleep(2)
                print('fermeture')
            matchlist = []
            liguelist = []
            for link in links:
                driver.get(link)
                time.sleep(5)
                bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                      'dashboard-champ')
                print('bet_list_ligue', bet_list_ligue)

                for bet_ligue in bet_list_ligue:
                    # ON RÉCUPÈRE LE NOM DE LA LIGUE
                    config.ligue_name = GetLigueName.main(bet_ligue)
                    print('config.ligue_nam', config.ligue_name)
                    # EN CAS D'ERREUR
                    if not config.ligue_name:
                        config.error = False
                        continue
                    liguelist.append([bet_ligue.find_elements(By.CLASS_NAME,
                                                              'dashboard-champ__more')[
                        0].get_attribute(
                        "href"), config.ligue_name])
                bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                      'dashboard-champ-body__games')
                # POUR CHAQUE LIGUE RÉCUPÉRÉE
                for bet_ligue in bet_list_ligue:
                    # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                    if getCompet():
                        # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                        try:
                            bet_items = driver.find_elements(By.CLASS_NAME,
                                                             'dashboard-game-block__row')
                        except:
                            print(' c-events-scoreboard__item')
                            # s'il y une erreur on passe au suivant
                            continue
                        else:
                            if len(bet_items) <= 0:
                                continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                        i = 0
                        for bet_item in bet_items:
                            try:
                                teams_name = bet_item.find_element(By.CLASS_NAME,
                                                                   'dashboard-game-block__teams')
                                players = teams_name.find_elements(By.CLASS_NAME, 'dashboard-game-team-info')
                                players_name = []
                                match = []
                                if len(players) <= 1:
                                    continue
                                for player in players:
                                    player = player.text.split('(')[0]
                                    player = player.strip()
                                    config.log(player, config.newmatch)
                                    players_name.append(player)
                                match.append(players_name)
                                match.append(config.ligue_name)
                                newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                                     'dashboard-game-block-link')[
                                    0].get_attribute(
                                    "href")
                                newmatch = newmatchtxt.split(
                                    '-')
                                config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                                match.append(config.newmatch)
                                matchlist.append(match)

                            except Exception as e:
                                continue
                            else:
                                print('ok')
                else:
                    print('not comp')

        print(len(matchlist))
        print('matchlist', matchlist)

        # Enregistrement de matchlist dans un fichier JSON
        try:
            # Créer un nom de fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"matchlist_{timestamp}.json"
            json_filepath = os.path.join(config.projectPath, "DataFiles", json_filename)

            # Créer le dossier DataFiles s'il n'existe pas
            os.makedirs(os.path.dirname(json_filepath), exist_ok=True)

            # Préparer les données à enregistrer
            data_to_save = {
                "timestamp": datetime.now().isoformat(),
                "total_matches": len(matchlist),
                "matches": matchlist
            }

            # Enregistrer dans le fichier JSON
            with open(json_filepath, 'w', encoding='utf-8') as json_file:
                json.dump(data_to_save, json_file, ensure_ascii=False, indent=2)

            config.log(f"Matchlist enregistrée dans: {json_filepath}", 'info', True)
            print(f"Matchlist enregistrée dans: {json_filepath}")

        except Exception as e:
            config.log(f"Erreur lors de l'enregistrement de matchlist: {str(e)}", 'error', True)
            print(f"Erreur lors de l'enregistrement de matchlist: {str(e)}")
        goodmatch = []
        for matchItem in matchlist:
            players_name = matchItem[0]
            ligue_name = matchItem[1]
            print('matchitem', matchItem)
            # goodmatch.append(matchItem)#ajout dasn tou sles cas pour faire tous ls match
            if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
                print('wta get proba')
                config.proba40A = Functions_stats.get_wta_proba_40A(players_name[0], players_name[1])
                print('tentative proba 1 : ', config.proba40A)
                # config.proba40A = 0.5
                time.sleep(1)
                if config.proba40A == 0:
                    config.proba40A = Functions_stats.get_wta_proba_40A_other(players_name[0], players_name[1], driver)
                    print('tentative proba 2 : ', config.proba40A)
            else:
                config.proba40A = Functions_stats.get_proba_40A(players_name[0], players_name[1])
                # config.proba40A = 0.5
                time.sleep(1)
                if config.proba40A == 0:
                    config.proba40A = Functions_stats.get_proba_40A_other(players_name[0], players_name[1], driver)
            print('proba ' + str(config.proba40A))
            if float(config.proba40A) >= float(config.probamini):
                matchItem.append(config.proba40A)
                print(matchItem)
                goodmatch.append(matchItem)

        # Tri en fonction de la dernière valeur (indice -1) en ordre décroissant
        tableau_trie = sorted(goodmatch, key=lambda x: x[-1], reverse=True)

        # Fonction de priorisation des matchs par ligue (même logique que classementeDeMatch)
        def prioritize_matches_by_league_new(matches, max_matches=30):
            """
            Priorise les matchs selon la hiérarchie des ligues :
            1. ATP sans "qualification"
            2. Challenger sans "qualification"  
            3. WTA sans "qualification"
            4. ATP avec "qualification"
            5. Challenger avec "qualification"
            6. WTA avec "qualification"
            7. ITF sans "qualification"
            8. ITF avec "qualification"
            """
            # Catégoriser les matchs par priorité
            priority_groups = {
                1: [],  # ATP sans qualification
                2: [],  # Challenger sans qualification
                3: [],  # WTA sans qualification
                4: [],  # ATP avec qualification
                5: [],  # Challenger avec qualification
                6: [],  # WTA avec qualification
                7: [],  # ITF sans qualification
                8: []   # ITF avec qualification
            }
            
            for match in matches:
                ligue_name = match[1].lower()
                has_qualification = 'qualification' in ligue_name
                
                # Déterminer la priorité basée sur le nom de la ligue
                if 'atp' in ligue_name:
                    priority = 4 if has_qualification else 1
                elif 'challenger' in ligue_name:
                    priority = 5 if has_qualification else 2
                elif any(wta_term in ligue_name for wta_term in ['wta', 'féminin', 'femmes', 'women']):
                    priority = 6 if has_qualification else 3
                elif 'itf' in ligue_name:
                    priority = 8 if has_qualification else 7
                else:
                    # Autres ligues, priorité moyenne
                    priority = 4 if has_qualification else 2
                
                priority_groups[priority].append(match)
            
            # Construire la liste finale en respectant les priorités
            final_matches = []
            for priority in sorted(priority_groups.keys()):
                group = priority_groups[priority]
                # Trier chaque groupe par probabilité décroissante
                group_sorted = sorted(group, key=lambda x: x[-1], reverse=True)
                
                # Ajouter les matchs jusqu'à atteindre la limite
                remaining_slots = max_matches - len(final_matches)
                if remaining_slots <= 0:
                    break
                    
                final_matches.extend(group_sorted[:remaining_slots])
            
            return final_matches

        # Appliquer la priorisation pour retenir les 30 meilleurs matchs (ou 10 si souhaité)
        top_matches = prioritize_matches_by_league_new(tableau_trie, 30)
        for m in top_matches:
            # Join array elements with pipe separator before adding to todo
            try:
                todo("add", "|".join(str(x) for x in m), config.matchlisttodo_file_name)
            except:
                pass
        break


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    import sys

    GetIfNewSite(driver)
    # Récupérer le chemin absolu du fichier actuel
    current_file_path = os.path.abspath(__file__)

    # Récupérer le dossier parent du fichier actuel
    parent_directory = os.path.dirname(current_file_path)
    # ajouter un autre niveau parent si nécessaire
    project_directory = os.path.dirname(parent_directory)
    sys.path.append(project_directory)
    classementeDeMatch(driver)
