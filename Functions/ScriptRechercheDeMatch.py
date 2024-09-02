import time

from selenium.webdriver.common.by import By
import config

from Functions import GetMatchScore, GetLigueName, AddRunning
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.VerificationListeMatchLive import VerificationListeMatchLive
from Functions.GetJsonData import getCompet


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
                                config.newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                               config.matchlist_file_name)
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

