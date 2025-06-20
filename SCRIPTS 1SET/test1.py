import time

from selenium.webdriver.common.by import By

import config
from Functions import GetMatchScore, GetLigueName, AddRunning
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfScriptsRunning import GetIfScriptsRunning
from Functions.GetJsonData import getCompet, DispatchPerte


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
