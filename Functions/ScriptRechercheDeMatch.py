import time

from selenium.webdriver.common.by import By
import config

from Functions import GetMatchScore, Functions_stats1, GetInfosDeMise, Functions_stats, GetLigueName
from Functions.Function_GetSetActuel import GetSetActuel
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetCompetOk import GetCompetOk, GetCompetOk30
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.GetPlayersName import GetPlayersName
from Functions.VerificationListeMatchLive import VerificationListeMatchLive
from Functions.GetJsonData import getCompet


def rechercheDeMatch(driver):
    config.error = False
    print('RECHERCHE DE MATCH')
    match_found = False
    while not match_found and not config.error:
        config.init_variable()
        """On vérifie si c'est la page d'un match """
        match_found = GetIfMatchPage(driver)
        # SCRIPT RECHERCHE DE MATCH
        config.saveLog('Recherche de match', config.newmatch)
        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        GetIfScriptsRunning()
        # VERIFICATION SI PAGE DE LIST LIVE"""
        if not VerificationListeMatchLive(driver):
            config.error = True
            print("PAGE VIDE")
            return False
        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        config.saveLog('nb ligue found : '+str(len(bet_list_ligue)),config.newmatch)
        # POUR CHAQUE LIGUE RÉCUPÉRÉE
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            config.ligue_name = GetLigueName.main(bet_ligue)
            # EN CAS D'ERREUR
            if not config.ligue_name:
                config.error = False
                break
            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            if getCompet():
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
                            txtlog = "Impossible de récupérer le score"
                            config.saveLog(txtlog, config.newmatch)
                            print(txtlog)
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
                                config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
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
                config.saveLog('Mauvaise ligue :'+config.ligue_name)
            # si un match est trouvé on arrete la recherche
            if match_found:
                break

        if not match_found:
            driver.get('https://1xbet.com/fr/live/Tennis/')
            config.saveLog('Pas de bonne ligue trouvé, attente 30 sec', config.newmatch)
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
                config.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1], driver, config.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(config.ligue_name, config.rattrape_perte, config.perte, config.wantwin, config.mise, config.increment,
                                            config.proba40A, '40')
        config.perte = float(infos_de_mise[0])
        config.wantwin = float(infos_de_mise[1])
        config.mise = float(infos_de_mise[2])
        config.increment = float(infos_de_mise[3])
        config.rattrape_perte = infos_de_mise[4]
        # END RECHERCHE INFOS DE MISE
        config.saved_set = ""
        config.set_actuel = GetSetActuel(driver)
        config.saved_set = config.set_actuel

        if not config.set_actuel:

            config.error = True
    else:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    return match_found

def rechercheDeMatch30(driver):
    config.error = False

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk30()
    compet_ok_list = get_compet['compet_ok_list']
    config.saveLog('compet_ok_list : '+str(compet_ok_list), config.newmatch)

    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet['compet_not_ok_list']
    config.saveLog('compet_not_ok_list : '+str(compet_not_ok_list), config.newmatch)

    """On vérifie si c'est la page d'un match live"""
    match_found = GetIfMatchPage(driver)
    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not config.error:
        config.saveLog('Recherche de match', config.newmatch)

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
            config.saveLog('nb ligue found : '+str(len(bet_list_ligue)), config.newmatch)
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
                            config.saveLog("Impossible de récupérer le score", config.newmatch)
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
                                config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
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
                config.saveLog('Mauvaise ligue', config.newmatch)
            # si un match est trouvé on arrete la recherche
            if match_found:
                break

        if not match_found:
            config.saveLog('Pas de bonne ligue trouvé, attente 30 sec', config.newmatch)
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
                config.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1], driver, config.match_Url)

        infos_de_mise = GetInfosDeMise.main(config.ligue_name, config.rattrape_perte, config.perte, config.wantwin, config.mise, config.increment,
                                            config.proba40A)
        config.perte = float(infos_de_mise[0])
        config.wantwin = float(infos_de_mise[1])
        config.mise = float(infos_de_mise[2])
        config.increment = float(infos_de_mise[3])
        config.rattrape_perte = infos_de_mise[4]
        # END RECHERCHE INFOS DE MISE
        config.saved_set = ""
        config.set_actuel = GetSetActuel(driver)
        config.saved_set = config.set_actuel

        if not config.set_actuel:

            config.error = True
    else:
        time.sleep(30)
    return match_found

def rechercheDeMatch4030(driver):
    config.error = False

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk30()
    compet_ok_list = get_compet['compet_ok_list']
    config.saveLog('compet_ok_list : '+str(compet_ok_list), config.newmatch)

    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet['compet_not_ok_list']
    config.saveLog('compet_not_ok_list : '+str(compet_not_ok_list), config.newmatch)

    """On vérifie si c'est la page d'un match live"""
    match_found = False
    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not config.error:
        config.init_variable()
        config.saveLog('Recherche de match', config.newmatch)

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
            config.saveLog('nb ligue found : '+str(len(bet_list_ligue)), config.newmatch)
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
                            config.saveLog("Impossible de récupérer le score", config.newmatch)
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
                                config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
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
                config.saveLog('Mauvaise ligue', config.newmatch)
            # si un match est trouvé on arrete la recherche
            if match_found:
                break


        if not match_found:
            if GetIfMatchPage(driver):
                match_found = True
            else:
                config.saveLog('Pas de bonne ligue trouvé, attente 30 sec', config.newmatch)
                time.sleep(30)
                break


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
                config.proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1], driver, config.match_Url)

        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(config.ligue_name, config.rattrape_perte, config.perte, config.wantwin, config.mise, config.increment,
                                            config.proba40A,'30')
        config.perte = float(infos_de_mise[0])
        config.wantwin = float(infos_de_mise[1])
        config.mise = float(infos_de_mise[2])
        config.increment = float(infos_de_mise[3])
        config.rattrape_perte = infos_de_mise[4]
        # END RECHERCHE INFOS DE MISE
        config.saved_set = ""
        config.set_actuel = GetSetActuel(driver)
        config.saved_set = config.set_actuel

        if not config.set_actuel:

            config.error = True
        print('err ' + str(config.error))
    else:
        driver.get('https://1xbet.com/fr/live/Tennis/')
    return match_found