import time

from selenium.webdriver.common.by import By
import config

from Functions import GetMatchScore, GetLigueName, AddRunning, Functions_stats, Functions_stats1
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.VerificationListeMatchLive import VerificationListeMatchLive
from Functions.GetJsonData import getCompet
from Functions.UpdateMatchDone import todo

def rechercheDeMatch(driver):
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
            driver.get('https://1xbet.com/fr/live/Tennis/')
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
                except :
                    print(' c-events-scoreboard__item')
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
                            config.saveLog(txtlog,0, config.newmatch)
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
                                print('config.newmatch[0]',config.newmatch[0])
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
            config.saveLog('PAS DE MATCH TROUVE',1)
            driver.get('https://1xbet.com/fr/live/Tennis/')


        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH
    return config.match_found
def classementeDeMatch(driver):
    driver.get('https://1xbet.com/fr/line/tennis')
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
            driver.get('https://1xbet.com/fr/line/tennis')
            return False
        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        matchlist =[]
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
                except :
                    print(' c-events-scoreboard__item')
                    # s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue# SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    i = 0
                    for bet_item in bet_items:
                        try:
                            teams_name = bet_item.find_element(By.CLASS_NAME, 'c-events__teams')
                            teams_name = teams_name.get_attribute('title')
                            players = teams_name.split(' — ')
                            players_name = []
                            match = []
                            for player in players:
                                player = player.split('(')[0]
                                player = player.strip()
                                config.saveLog(player, config.newmatch)
                                print(player)
                                players_name.append(player)
                            match.append(players_name)
                            match.append(config.ligue_name)
                            newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                                                 'c-events__name')[
                                0].get_attribute(
                                "href")
                            newmatch = newmatchtxt.split(
                                '-')
                            config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
                            match.append(config.newmatch)
                            matchlist.append(match)

                        except:
                            txtlog = "Impossible de récupérer le score"
                            config.saveLog(txtlog,0, config.newmatch)
                            print(txtlog)
                            continue

        print(matchlist)
        goodmatch =[]
        for matchItem in matchlist:
            players_name = matchItem[0]
            ligue_name = matchItem[1]
            print(matchItem)
            if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
                config.proba40A = Functions_stats.get_wta_proba_40A(players_name[0], players_name[1])
                # config.proba40A = 0.5
                if config.proba40A == 0:
                    config.proba40A = Functions_stats1.get_wta_proba_40A_other(players_name[0], players_name[1],driver)
            else:
                config.proba40A = Functions_stats1.get_proba_40A(players_name[0], players_name[1])
                # config.proba40A = 0.5
                if config.proba40A == 0:
                    config.proba40A = Functions_stats1.get_proba_40A_other(players_name[0], players_name[1],
                                                                           driver)
            print('proba '+str(config.proba40A))
            if float(config.proba40A) >= float(config.probamini):
                matchItem.append(config.proba40A)
                print(matchItem)
                goodmatch.append(matchItem)

        # Tri en fonction de la dernière valeur (indice -1) en ordre décroissant
        tableau_trie = sorted(goodmatch, key=lambda x: x[-1], reverse=True)

        # Retenir les 10 premières lignes
        top_10 = tableau_trie[:10]
        for m in top_10:
            todo("add", m[2], config.matchlisttodo_file_name)