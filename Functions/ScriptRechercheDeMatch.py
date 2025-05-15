import inspect
import time

from selenium.webdriver.common.by import By

import config
from Functions import GetMatchScore, GetLigueName, AddRunning, Functions_stats, Functions_stats1
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.GetJsonData import getCompet, DispatchPerte
from Functions.UpdateMatchDone import todo
from Functions.VerificationListeMatchLive import VerificationListeMatchLive


def rechercheDeMatch(driver):
    config.error = False
    config.log(' RECHERCHE DE MATCH', 'title', False)
    config.match_found = False
    while not config.match_found and not config.error:
        # config.init_variable()
        config.match_found = GetIfMatchPage(driver)
        if not config.match_found and float(config.perte) > 0:
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
            config.match_end = False
            time.sleep(3)
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
            if getCompet():
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
                print('tennis trouvé')
                print('click ok')
                break
        country = driver.find_element(By.CLASS_NAME, 'sports-menu-group-by-country')
        print('find countries')
        countrybutton = country.find_elements(By.CLASS_NAME, 'sports-menu-group-by-champ')
        for cntrybtn in countrybutton:
            print('contry')
            cntrybtn.click()
            print('click cntry')
            if 'itf' in cntrybtn.text.lower():
                break

        liguebtn = driver.find_elements(By.CLASS_NAME, 'sports-menu-app-champ-with-sub-champs-group__item')
        links = []
        for lbtn in liguebtn:
            link = lbtn.find_element(By.CLASS_NAME, 'ui-nav-link__content').get_attribute(
                "href")
            links.append(link)
        print(links)
        matchlist = []
        liguelist = []
        for link in links:
            driver.get(link)
            time.sleep(5)
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  'dashboard-champ')

            for bet_ligue in bet_list_ligue:
                # ON RÉCUPÈRE LE NOM DE LA LIGUE
                config.ligue_name = GetLigueName.main(bet_ligue)
                # EN CAS D'ERREUR
                if not config.ligue_name:
                    config.error = False
                    break
                liguelist.append([bet_ligue.find_elements(By.CLASS_NAME,
                                                          'ui-dashboard-champ-name__link')[
                    0].get_attribute(
                    "href"), config.ligue_name])

        for link in liguelist:
            driver.get(link[0])
            config.ligue_name = link[1]
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  'ui-dashboard-champ__games')
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
                    config.proba40A = Functions_stats1.get_wta_proba_40A_other(players_name[0], players_name[1], driver)
            else:
                config.proba40A = Functions_stats1.get_proba_40A(players_name[0], players_name[1])
                # config.proba40A = 0.5
                time.sleep(1)
                if config.proba40A == 0:
                    config.proba40A = Functions_stats1.get_proba_40A_other(players_name[0], players_name[1], driver)
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
            todo("add", "|".join(str(x) for x in m), config.matchlisttodo_file_name)
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
