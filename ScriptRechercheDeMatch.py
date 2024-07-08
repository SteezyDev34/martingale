import time

from selenium.webdriver.common.by import By
import config
#import config_30A
import config4030

import Functions_stats
import Functions_stats1
import GetInfosDeMise
import GetLigueName
import GetMatchScore
from Function_GetSetActuel import GetSetActuel
import OuverturePageMatch
import VerificationMatchTrouve
from GetCompetOk import GetCompetOk, GetCompetOk30
from GetIfMatchPage import GetIfMatchPage
from GetIfScriptsRunning import GetIfScriptsRunning
from GetPlayersName import GetPlayersName
from VerificationListeMatchLive import VerificationListeMatchLive


def rechercheDeMatch(driver):
    config.error = False

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk()
    compet_ok_list = get_compet['compet_ok_list']
    config.saveLog('compet_ok_list : '+str(compet_ok_list))

    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet['compet_not_ok_list']
    config.saveLog('compet_not_ok_list : '+str(compet_not_ok_list))

    """On vérifie si c'est la page d'un match live"""
    match_found = GetIfMatchPage(driver)
    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not config.error:
        config.saveLog('Recherche de match')

        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning(config.running_file_name)

        # VERIFICATION SI PAGE DE MATCH LIVE"""
        if not VerificationListeMatchLive(driver):
            config.error = True
            return False

        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        if config.devMode:
            config.saveLog('nb ligue found : '+str(len(bet_list_ligue)))
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                if config.devMode:
                    print('error #23231#')
                config.error = False
                break
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            if any(compet_ok in config.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config.ligue_name for
                compet_not_ok in compet_not_ok_list):

                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'c-events-scoreboard__item')
                except :
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue# SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            # on récupère le score
                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                   'c-events-scoreboard__lines_tennis')
                        except:
                            config.saveLog("Impossible de récupérer le score")
                            continue
                        else:
                            # si le score est récupéré
                            if len(div_bet_score) <= 0:
                                continue
                            # on le vérifie
                            bet_score = GetMatchScore.main(div_bet_score[0],
                                                                        config.score_to_start)
                            if bet_score:  # SI LE MATCH EST PRET
                                # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                config.newmatch = VerificationMatchTrouve.main(driver,bet_item,
                                                                                     config.matchlist_file_name)
                                if config.newmatch[0]:
                                    if OuverturePageMatch.main(bet_item, config.script_num,
                                                                            config.newmatch[1],
                                                                            config.running_file_name,
                                                                            config.matchlist_file_name):
                                        config.newmatch = config.newmatch[1]
                                        match_found = True
                                        break
                                    else:
                                        continue
            else:
                config.saveLog('Mauvaise ligue')
            # si un match est trouvé on arrete la recherche
            if match_found:
                break

        if not match_found:
            config.saveLog('Pas de bonne ligue trouvé, attente 30 sec')
            time.sleep(30)


        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH

    if match_found and not config.error:
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        config.newmatch = VerificationMatchTrouve.fromUrl(driver, config.matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = GetPlayersName(driver)
        if 'wta' in config.ligue_name.lower() or 'féminin' in config.ligue_name.lower() or 'femmes' in config.ligue_name.lower() or 'women' in config.ligue_name.lower():
            config.proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
            #config.proba40A = 0.5
        else:
            config.proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            #config.proba40A = 0.5
            if config.proba40A ==  0:
                config.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1],driver,config.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(config.ligue_name, config.rattrape_perte, config.perte, config.wantwin, config.mise, config.increment,
                                                            config.proba40A)
        config.perte = float(infos_de_mise[0])
        config.wantwin = float(infos_de_mise[1])
        config.mise = float(infos_de_mise[2])
        config.increment = float(infos_de_mise[3])
        config.rattrape_perte = infos_de_mise[4]
        print("#RRRRR Rattrap = "+str(config.rattrape_perte))
        # END RECHERCHE INFOS DE MISE
        config.saved_set = ""
        config.set_actuel = GetSetActuel(driver)
        config.saved_set = config.set_actuel

        if not config.set_actuel:

            config.error = True
        print('err ' + str(config.error))
    else:
        time.sleep(30)
    return match_found

def rechercheDeMatch30(driver):
    config_30A.error = False

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk30()
    compet_ok_list = get_compet['compet_ok_list']
    config_30A.saveLog('compet_ok_list : '+str(compet_ok_list))

    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet['compet_not_ok_list']
    config_30A.saveLog('compet_not_ok_list : '+str(compet_not_ok_list))

    """On vérifie si c'est la page d'un match live"""
    match_found = GetIfMatchPage(driver)
    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not config_30A.error:
        config_30A.saveLog('Recherche de match')

        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning(config_30A.running_file_name)

        # VERIFICATION SI PAGE DE MATCH LIVE"""
        if not VerificationListeMatchLive(driver):
            config_30A.error = True
            return False

        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        if config_30A.devMode:
            config_30A.saveLog('nb ligue found : '+str(len(bet_list_ligue)))
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config_30A.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config_30A.ligue_name:
                if config_30A.devMode:
                    print('error #23231#')
                config_30A.error = False
                break
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            if any(compet_ok in config_30A.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config_30A.ligue_name for
                compet_not_ok in compet_not_ok_list):

                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'c-events-scoreboard__item')
                except :
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue# SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            # on récupère le score
                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                   'c-events-scoreboard__lines_tennis')
                        except:
                            config_30A.saveLog("Impossible de récupérer le score")
                            continue
                        else:
                            # si le score est récupéré
                            if len(div_bet_score) <= 0:
                                continue
                            # on le vérifie
                            bet_score = GetMatchScore.main(div_bet_score[0],
                                                                        config_30A.score_to_start)
                            if bet_score:  # SI LE MATCH EST PRET
                                # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                config_30A.newmatch = VerificationMatchTrouve.main(driver,bet_item,
                                                                                     config_30A.matchlist_file_name)
                                if config_30A.newmatch[0]:
                                    if OuverturePageMatch.main(bet_item, config_30A.script_num,
                                                                            config_30A.newmatch[1],
                                                                            config_30A.running_file_name,
                                                                            config_30A.matchlist_file_name):
                                        config_30A.newmatch = config_30A.newmatch[1]
                                        match_found = True
                                        break
                                    else:
                                        continue
            else:
                config_30A.saveLog('Mauvaise ligue')
            # si un match est trouvé on arrete la recherche
            if match_found:
                break

        if not match_found:
            config_30A.saveLog('Pas de bonne ligue trouvé, attente 30 sec')
            time.sleep(30)


        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH

    if match_found and not config_30A.error:
        config_30A.ligue_name = GetLigueName.fromUrl(driver)[0]
        config_30A.match_Url = GetLigueName.fromUrl(driver)[1]
        config_30A.newmatch = VerificationMatchTrouve.fromUrl(driver, config_30A.matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = GetPlayersName(driver)
        if 'wta' in config_30A.ligue_name.lower() or 'féminin' in config_30A.ligue_name.lower() or 'femmes' in config_30A.ligue_name.lower() or 'women' in config_30A.ligue_name.lower():
            config_30A.proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
            #config_30A.proba40A = 0.5
        else:
            config_30A.proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            #config_30A.proba40A = 0.5
            if config_30A.proba40A ==  0:
                config_30A.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1],driver,config_30A.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(config_30A.ligue_name, config_30A.rattrape_perte, config_30A.perte, config_30A.wantwin, config_30A.mise, config_30A.increment,
                                                            config_30A.proba40A)
        config_30A.perte = float(infos_de_mise[0])
        config_30A.wantwin = float(infos_de_mise[1])
        config_30A.mise = float(infos_de_mise[2])
        config_30A.increment = float(infos_de_mise[3])
        config_30A.rattrape_perte = infos_de_mise[4]
        print("#RRRRR Rattrap = "+str(config_30A.rattrape_perte))
        # END RECHERCHE INFOS DE MISE
        config_30A.saved_set = ""
        config_30A.set_actuel = GetSetActuel(driver)
        config_30A.saved_set = config_30A.set_actuel

        if not config_30A.set_actuel:

            config_30A.error = True
        print('err ' + str(config_30A.error))
    else:
        time.sleep(30)
    return match_found

def rechercheDeMatch4030(driver):
    config4030.error = False

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk30()
    compet_ok_list = get_compet['compet_ok_list']
    config4030.saveLog('compet_ok_list : '+str(compet_ok_list))

    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet['compet_not_ok_list']
    config4030.saveLog('compet_not_ok_list : '+str(compet_not_ok_list))

    """On vérifie si c'est la page d'un match live"""
    match_found = GetIfMatchPage(driver)
    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not config4030.error:
        config4030.saveLog('Recherche de match')

        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning(config4030.running_file_name)

        # VERIFICATION SI PAGE DE MATCH LIVE"""
        if not VerificationListeMatchLive(driver):
            config4030.error = True
            return False

        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        if config4030.devMode:
            config4030.saveLog('nb ligue found : '+str(len(bet_list_ligue)))
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config4030.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config4030.ligue_name:
                if config4030.devMode:
                    print('error #23231#')
                config4030.error = False
                break
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            if any(compet_ok in config4030.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config4030.ligue_name for
                compet_not_ok in compet_not_ok_list):

                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'c-events-scoreboard__item')
                except :
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue# SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            # on récupère le score
                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                   'c-events-scoreboard__lines_tennis')
                        except:
                            config4030.saveLog("Impossible de récupérer le score")
                            continue
                        else:
                            # si le score est récupéré
                            if len(div_bet_score) <= 0:
                                continue
                            # on le vérifie
                            bet_score = GetMatchScore.main(div_bet_score[0],
                                                                        config4030.score_to_start)
                            if bet_score:  # SI LE MATCH EST PRET
                                # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                config4030.newmatch = VerificationMatchTrouve.main(driver,bet_item,
                                                                                     config4030.matchlist_file_name)
                                if config4030.newmatch[0]:
                                    if OuverturePageMatch.main(bet_item, config4030.script_num,
                                                                            config4030.newmatch[1],
                                                                            config4030.running_file_name,
                                                                            config4030.matchlist_file_name):
                                        config4030.newmatch = config4030.newmatch[1]
                                        match_found = True
                                        break
                                    else:
                                        continue
            else:
                config4030.saveLog('Mauvaise ligue')
            # si un match est trouvé on arrete la recherche
            if match_found:
                break

        if not match_found:
            config4030.saveLog('Pas de bonne ligue trouvé, attente 30 sec')
            time.sleep(30)


        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH

    if match_found and not config4030.error:
        config4030.ligue_name = GetLigueName.fromUrl(driver)[0]
        config4030.match_Url = GetLigueName.fromUrl(driver)[1]
        config4030.newmatch = VerificationMatchTrouve.fromUrl(driver, config4030.matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = GetPlayersName(driver)
        if 'wta' in config4030.ligue_name.lower() or 'féminin' in config4030.ligue_name.lower() or 'femmes' in config4030.ligue_name.lower() or 'women' in config4030.ligue_name.lower():
            config4030.proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
            #config4030.proba40A = 0.5
        else:
            config4030.proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            #config4030.proba40A = 0.5
            if config4030.proba40A ==  0:
                config4030.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1],driver,config4030.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(config4030.ligue_name, config4030.rattrape_perte, config4030.perte, config4030.wantwin, config4030.mise, config4030.increment,
                                                            config4030.proba40A)
        config4030.perte = float(infos_de_mise[0])
        config4030.wantwin = float(infos_de_mise[1])
        config4030.mise = float(infos_de_mise[2])
        config4030.increment = float(infos_de_mise[3])
        config4030.rattrape_perte = infos_de_mise[4]
        print("#RRRRR Rattrap = "+str(config4030.rattrape_perte))
        # END RECHERCHE INFOS DE MISE
        config4030.saved_set = ""
        config4030.set_actuel = GetSetActuel(driver)
        config4030.saved_set = config4030.set_actuel

        if not config4030.set_actuel:

            config4030.error = True
        print('err ' + str(config4030.error))
    else:
        time.sleep(30)
    return match_found