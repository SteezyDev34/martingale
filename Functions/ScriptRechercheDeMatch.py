import inspect
import json
import time
from datetime import datetime

from selenium.webdriver.common.by import By

import config
from Functions import GetMatchScore, GetLigueName, AddRunning, Functions_stats
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.GetJsonData import getCompet, DispatchPerte, set1DispatchPerte
from Functions.UpdateMatchDone import todo
from Functions.VerificationListeMatchLive import VerificationListeMatchLive


def charger_matchlist_depuis_json():
    import os

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

        # Trier par date de modification (le plus récent en premier)
        json_files.sort(key=lambda x: os.path.getmtime(os.path.join(datafiles_path, x)), reverse=True)
        latest_file = os.path.join(datafiles_path, json_files[0])

        # Charger le fichier JSON
        with open(latest_file, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        matchlist = data.get('matches', [])

        if matchlist and len(matchlist) > 0:
            config.log(f"Matchlist chargée depuis {latest_file} - {len(matchlist)} matchs trouvés", 'info', True)
            print(f"Matchlist chargée depuis {latest_file} - {len(matchlist)} matchs trouvés")
            return matchlist
        else:
            config.log(f"Fichier JSON {latest_file} existe mais est vide", 'info', True)
            return None

    except Exception as e:
        config.log(f"Erreur lors du chargement du fichier JSON: {str(e)}", 'error', True)
        return None


def rechercheDeMatch(driver):
    config.error = False
    config.log(' RECHERCHE DE MATCH', 'title', False)
    config.match_found = False
    while not config.match_found and not config.error:
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
        GetIfScriptsRunning()
        # VERIFICATION SI PAGE DE LIST LIVE"""
        """if not VerificationListeMatchLive(driver):
            config.log("PAGE VIDE", 'error', True)
            driver.get(config.site_url)
            return False"""
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
                if getCompet():
                    # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                    try:
                        config.log('Récupération des matchs', 'info', False, 3)
                        config.log_clear_line()
                        bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                            'dashboard-game-block')
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
                            try:
                                config.log('On récupère le nom des joueurs', 'info', False, 3)
                                config.log_clear_line()
                                div_bet_player = bet_item.find_element(By.CLASS_NAME, 'ui-team-scores__teams')
                            except:
                                config.log('Impossible de récpérer les joueurs!', 'warning', False, 3)
                                config.log_clear_line()
                                continue
                            else:
                                if div_bet_player:
                                    div_bet_player = div_bet_player.text.split('\n')
                                    config.log(str(div_bet_player), 'info', False, 3)
                                    config.log_clear_line()
                                try:
                                    # on récupère le score
                                    div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                           'ui-game-scores')
                                except:

                                    config.log('Impossible de récupérer le score!', 'warning', False, 4)
                                    time.sleep(2)
                                    config.log_clear_line()
                                    continue
                                else:
                                    # si le score est récupéré
                                    if len(div_bet_score) <= 0:
                                        config.log('Pas de score!', 'warning', False, 4)
                                        time.sleep(2)
                                        config.log_clear_line()
                                        continue
                                    # on le vérifie
                                    config.log('Vérification du score!', 'info', False, 4)
                                    config.log_clear_line()
                                    bet_score = GetMatchScore.main(div_bet_score[0],
                                                                   config.score_to_start)
                                    if bet_score:  # SI LE MATCH EST PRET
                                        config.log('Score ok', 'info', False, 4)
                                        config.log_clear_line()
                                        # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                        config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                                       config.matchlist_file_name)
                                        print(config.newmatch[0])
                                        if config.newmatch[0]:
                                            if OuverturePageMatch.main(bet_item, config.script_num,
                                                                       config.newmatch[1],
                                                                       config.running_file_name,
                                                                       config.matchlist_file_name):
                                                config.newmatch = config.newmatch[1]
                                                config.log(config.newmatch, 'info', False, 4)
                                                print('MATCH OK')
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
            config.log_clear_line(3)
            driver.get(config.site_url)
            time.sleep(5)
        else:

            config.log('MATCH TROUVE!', 'success', False, 2)
            config.match_end = False
            time.sleep(3)
        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH
    return config.match_found


def rechercheDeMatch1set(driver):
    config.error = False
    config.log(' RECHERCHE DE MATCH', 'title', False)
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
    GetIfScriptsRunning()
    # VERIFICATION SI PAGE DE LIST LIVE"""
    """if not VerificationListeMatchLive(driver):
        config.log("PAGE VIDE", 'error', True)
        driver.get(config.site_url)
        return False"""
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
            if getCompet():
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
                        try:
                            config.log('On récupère le nom des joueurs', 'info', False, 3)
                            config.log_clear_line()
                            div_bet_player = bet_item.find_element(By.CLASS_NAME, 'ui-team-scores__teams')
                        except:
                            config.log('Impossible de récpérer les joueurs!', 'warning', False, 3)
                            config.log_clear_line()
                            continue
                        else:
                            if div_bet_player:
                                div_bet_player = div_bet_player.text.split('\n')
                                config.log(str(div_bet_player), 'info', False, 3)
                                config.log_clear_line()
                            try:
                                # on récupère le score
                                div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                       'ui-game-scores')
                            except:

                                config.log('Impossible de récupérer le score!', 'warning', False, 4)
                                time.sleep(2)
                                config.log_clear_line()
                                continue
                            else:
                                # si le score est récupéré
                                if len(div_bet_score) <= 0:
                                    config.log('Pas de score!', 'warning', False, 4)
                                    time.sleep(2)
                                    config.log_clear_line()
                                    continue
                                # on le vérifie
                                config.log('Vérification du score!', 'info', False, 4)
                                config.log_clear_line()
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
                                    if cotev1 > 1.2 and cotev1 < 1.9:
                                        config.win_type = 'V1'
                                        if 'wta' in config.ligue_name or 'women' in config.ligue_name or 'femmes' in config.ligue_name:
                                            config.win_type = 'V2'
                                        print('1SET')
                                    elif cotev2 > 1.2 and cotev2 < 1.9:
                                        config.win_type = 'V2'
                                        if 'wta' in config.ligue_name or 'women' in config.ligue_name or 'femmes' in config.ligue_name:
                                            config.win_type = 'V1'
                                        print('1SETV2')
                                    else:
                                        continue
                                if bet_score:  # SI LE MATCH EST PRET

                                    config.log('Score ok', 'info', False, 4)
                                    config.log_clear_line()
                                    # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
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
        config.log_clear_line(3)
        driver.get(config.site_url)
        time.sleep(5)
    else:

        config.log('MATCH TROUVE!', 'success', False, 2)
        time.sleep(5)
    # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH
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
        GetIfScriptsRunning()
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            current_frame = inspect.currentframe()
            config.log(
                f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                'error', True)
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
                            config.log(txtlog, 0, config.newmatch)
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
            config.log('PAS DE MATCH TROUVE', 1)
            driver.get('https://1xbet.com/fr/live/basketball/')

        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH
    return config.match_found


def classementeDeMatch(driver):
    driver.get('https://ca.1xbet.com/fr/line/tennis')
    config.error = False
    print('RECHERCHE DE MATCH')
    config.match_found = False
    while not config.match_found and not config.error:
        config.init_variable()
        """On vérifie si c'est la page d'un match """
        config.match_found = GetIfMatchPage(driver)
        # SCRIPT RECHERCHE DE MATCH
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning()
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            config.error = True
            print("PAGE VIDE")
            driver.get('https://ca.1xbet.com/fr/line/tennis')
            return False
        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard__champ')
        matchlist = []
        liguelist = []
        print(str(len(bet_list_ligue)))
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                config.error = False
                break
            liguelist.append([bet_ligue.find_elements(By.CLASS_NAME,
                                                      'dashboard-champ-name__label')[
                0].get_attribute(
                "href"), config.ligue_name])

        for link in liguelist:
            driver.get(link[0])
            config.ligue_name = link[1]
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  'dashboard-champ-body__games')
            # POUR CHAQUE LIGUE RÉCUPÉRÉE
            for bet_ligue in bet_list_ligue:

                # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                if getCompet():
                    print(config.ligue_name)
                    print('get comp')
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
                                                                     'dashboard-game-block__link')[
                                    0].get_attribute(
                                    "href")
                                newmatch = newmatchtxt.split(
                                    '-')
                                config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                                match.append(config.newmatch)
                                matchlist.append(match)

                            except Exception as e:
                                print(e)
                                txtlog = "Impossible de récupérer le score"
                                config.log(txtlog, 0, config.newmatch)
                                print(txtlog)
                                continue
                            else:
                                print('ok')
                else:
                    print('not comp')

        print(len(matchlist))
        goodmatch = []
        for matchItem in matchlist:
            players_name = matchItem[0]
            ligue_name = matchItem[1]
            print(matchItem)
            # goodmatch.append(matchItem)#ajout dasn tou sles cas pour faire tous ls match
            if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
                config.proba40A = Functions_stats.get_wta_proba_40A(players_name[0], players_name[1])
                # config.proba40A = 0.5
                time.sleep(1)
                if config.proba40A == 0:
                    config.proba40A = Functions_stats.get_wta_proba_40A_other(players_name[0], players_name[1], driver)
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

        # Retenir les 10 premières lignes
        top_10 = tableau_trie[:50]
        for m in top_10:
            # Join array elements with pipe separator before adding to todo
            try:
                todo("add", "|".join(str(x) for x in m), config.matchlisttodo_file_name)
            except:
                pass
        break


def newclassementeDeMatch(driver):
    import os
    driver.get('https://ca.1xbet.com/fr/line/tennis')
    config.error = False
    print('RECHERCHE DE MATCH')
    config.match_found = False
    while not config.match_found and not config.error:
        config.init_variable()
        """On vérifie si c'est la page d'un match """
        config.match_found = GetIfMatchPage(driver)
        # SCRIPT RECHERCHE DE MATCH
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning()
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            config.error = True
            print("PAGE VIDE")
            driver.get('https://ca.1xbet.com/fr/line/tennis')
            return False
        # VÉRIFICATION S'IL EXISTE UN FICHIER JSON DE MATCHLIST
        matchlist_from_json = charger_matchlist_depuis_json()

        if matchlist_from_json is not None:
            # Utiliser la matchlist du fichier JSON
            matchlist = matchlist_from_json
            print(f"Utilisation de la matchlist depuis le fichier JSON - {len(matchlist)} matchs")
            config.log(f"Matchlist chargée depuis JSON - {len(matchlist)} matchs", 'info', True)
        else:
            # Procéder au scraping normal
            print("Aucun fichier JSON valide trouvé, procédure de scraping normale")
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

        # Retenir les 10 premières lignes
        top_10 = tableau_trie[:100]
        for m in top_10:
            # Join array elements with pipe separator before adding to todo
            try:
                todo("add", "|".join(str(x) for x in m), config.matchlisttodo_file_name)
            except:
                pass
        break


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    import sys
    import os

    # Récupérer le chemin absolu du fichier actuel
    current_file_path = os.path.abspath(__file__)

    # Récupérer le dossier parent du fichier actuel
    parent_directory = os.path.dirname(current_file_path)
    # ajouter un autre niveau parent si nécessaire
    project_directory = os.path.dirname(parent_directory)
    sys.path.append(project_directory)
    rechercheDeMatch(driver)
