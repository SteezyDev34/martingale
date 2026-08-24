import inspect
import json
import os
import time
from datetime import datetime


# ---------------------------------------------------------------------------
# Seuils de sélection des scriptTypes (tunable)
# svc = % 1er service gagné  |  ret = % balles de break converties
# proba40A = svc1*ret1 + svc2*ret2
# ---------------------------------------------------------------------------
_THRESHOLDS = {
    # Base — activés si stats OK
    '300':   lambda s: s['svc_avg'] >= 0.58,
    '15A':   lambda s: s['svc_avg'] >= 0.62,
    '30A':   lambda s: s['svc_avg'] >= 0.60,
    'BREAK': lambda s: s['ret_avg'] >= 0.38,
    '40A':   lambda s: s['proba40A'] >= 0.04,
    # Risqués — seuils plus exigeants
    '150':   lambda s: s['svc_avg'] >= 0.68,
    '015':   lambda s: s['ret_avg'] >= 0.42,
    '030':   lambda s: s['ret_avg'] >= 0.42,
    '6P':    lambda s: s['proba40A'] <= 0.10 and s['svc_avg'] >= 0.58,
    '4P':    lambda s: s['proba40A'] <= 0.05 and s['svc_avg'] >= 0.60,
    '5P':    lambda s: s['proba40A'] <= 0.05 and s['svc_avg'] >= 0.60,
    'HOLD':  lambda s: s['svc_avg'] >= 0.65,
}

_BASE_SCRIPTS  = ['300', '15A', '30A', 'BREAK', '40A']
_RISKY_SCRIPTS = ['150', '015', '030', '6P', '4P', '5P', 'HOLD']


def compute_script_types(stats):
    """
    Retourne (scriptTypeList, total_gain_wanted) selon les stats du match.
    stats = dict avec proba40A, svc1, ret1, svc2, ret2.
    """
    svc_avg = (stats.get('svc1', 0) + stats.get('svc2', 0)) / 2
    ret_avg = (stats.get('ret1', 0) + stats.get('ret2', 0)) / 2
    s = {
        'proba40A': stats.get('proba40A', 0),
        'svc_avg': svc_avg,
        'ret_avg': ret_avg,
        'svc1': stats.get('svc1', 0),
        'svc2': stats.get('svc2', 0),
        'ret1': stats.get('ret1', 0),
        'ret2': stats.get('ret2', 0),
    }
    script_types = []
    for st in _BASE_SCRIPTS + _RISKY_SCRIPTS:
        if _THRESHOLDS[st](s):
            script_types.append(st)
    total_gain_wanted = len(script_types) * 3.0
    config.log(
        f"ScriptTypes sélectionnés ({len(script_types)}): {script_types} → objectif {total_gain_wanted}€ "
        f"[svc={svc_avg:.2f} ret={ret_avg:.2f} p40A={s['proba40A']:.4f}]",
        'info', True
    )
    return script_types, total_gain_wanted

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from urllib.parse import quote_plus
import requests

import config
from Functions import GetMatchScore, GetLigueName, Functions_stats
from Functions import OuverturePageMatch
from Functions import VerificationMatchTrouve
from Functions.DeleteBet import DeleteBet
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetJsonData import getCompet, DispatchPerte, set1DispatchPerte
#from Functions.GetResult import GetMatchResultFromDashboard
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
        # Récupération des stats étendues (svc, ret, proba40A)
        stats = Functions_stats.get_match_stats_extended(players_name[0], players_name[1])
        config.proba40A = stats['proba40A']
        # Sélection des scriptTypes selon les stats
        script_types, total_gain_wanted = compute_script_types(stats)
        # On n'inclut le match que si au moins un scriptType est activé
        if not script_types:
            config.log(f"Aucun scriptType activé pour {players_name[0]} vs {players_name[1]}, match ignoré", 'warning', True)
            continue
        if float(config.proba40A) >= float(config.probamini):
            try:
                # Construire l'URL de l'API auxotracker avec encodage des noms et date du jour
                date_str = datetime.now().strftime("%Y-%m-%d")
                player1 = players_name[0]
                player2 = players_name[1]
                p1_enc = quote_plus(player1)
                p2_enc = quote_plus(player2)
                base_api = "https://api.auxotracker.p-com.studio/api/matches/tennis/link"
                api_url = f"{base_api}?team1={p1_enc}&team2={p2_enc}&date={date_str}"

                # Appel de l'API
                sofascore_link = None
                try:
                    resp = requests.get(api_url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('success'):
                            sofascore_link = data.get('sofascore_link')
                        else:
                            config.log(f"API retourné success=false pour {api_url}", 'warning', True)
                    else:
                        config.log(f"Requête API échouée {resp.status_code} pour {api_url}", 'warning', True)
                except Exception as e:
                    config.log(f"Erreur lors de l'appel API auxotracker: {e}", 'warning', True)

                # Ajouter les informations au matchItem
                matchItem.append(config.proba40A)
                matchItem.append(sofascore_link)
                matchItem.append(script_types)
                matchItem.append(total_gain_wanted)
                goodmatch.append(matchItem)
            except Exception as e:
                config.log(f"Erreur lors de la récupération du lien Sofascore: {e}", 'warning', True)
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


def _bridge_recherche_match():
    """Version bridge de rechercheDeMatch — pas de Selenium."""
    from websocket_server import bridge
    from Functions.Managers.MatchManager import match_manager
    from Functions._to_remove import AddRunning

    bridge.navigate(config.site_url)
    leagues = bridge.get_match_list()  # service worker attend que la page soit chargée
    if not leagues:
        config.log('ligues introuvables!', 'warning', True, 2, False)
        return False

    config.log(f'ligues trouvées! ({len(leagues)})', 'success', True, 2, False)

    for league in leagues:
        ligue_name = league.get('leagueName', '')
        config.ligue_name = ligue_name
        if not ligue_name:
            continue
        config.log(ligue_name, 'info', False, 2, False)

        if not getCompet():
            continue

        for match in league.get('matches', []):
            url = match.get('url', '')
            score = (match.get('score') or '').replace('\n', '').strip()
            has_ball = match.get('hasBall', False)
            p1 = match.get('p1') or ''
            p2 = match.get('p2') or ''

            config.log(f'{p1} vs {p2} — {score}', 'info', False, 3, False)

            # Vérifier que le score correspond et qu'il y a un service en cours
            score_ok = any(s == score for s in config.score_to_start) and has_ball
            if not score_ok:
                config.log('Score NOT OK', 'warning', False, 4, False)
                continue

            # Extraire l'ID du match depuis l'URL
            try:
                url_clean = url.replace('?platform_type=desktop', '').replace('?platform_type=mobile', '')
                parts = url_clean.split('-')
                newmatch_id = parts[-3] + '-' + parts[-2] + '-' + parts[-1]
            except Exception:
                config.log('Impossible de lire ID match!', 'warning', False, 4)
                continue

            if match_manager.match_exists(newmatch_id):
                config.log('Match déjà parié!', 'warning', False, 4, False)
                continue

            config.log('Match OK — navigation', 'success', False, 4, False)
            config.newmatch = newmatch_id
            bridge.navigate(url)
            _t.sleep(1)
            try:
                AddRunning.main(config.script_num, config.running_file_name)
            except Exception:
                pass
            config.match_found = True
            return True

    config.log('PAS DE MATCH TROUVE!', 'warning', False, 2, False)
    return False


def rechercheDeMatch(driver):
    config.error = False
    config.log("-" * 60, "title", False, False, False)
    config.log(' RECHERCHE DE MATCH', 'title', False, False, False)
    config.log("-" * 60, "title", False, False, False)
    config.match_found = False

    from Functions.BridgeAdapter import bridge_active
    if bridge_active():
        while not config.match_found and not config.error:
            if config.in_stat and (
                    not config.last_classement or config.last_classement != datetime.now().strftime("%Y-%m-%d")):
                classementeDeMatch(driver, False)
            script_manager.check_previous_scripts(config.script_num)
            # Déjà sur une page de match ? (match ouvert avant le démarrage du script)
            if GetIfMatchPage(driver):
                result = VerificationMatchTrouve.newmatchFromUrl(driver)
                if result[0]:
                    config.newmatch = result[1]
                    config.match_found = True
                    try:
                        from Functions._to_remove import AddRunning
                        AddRunning.main(config.script_num, config.running_file_name)
                    except Exception:
                        pass
                    return
            DeleteBet(driver)
            if not _bridge_recherche_match():
                import time as _t; _t.sleep(5)
        return

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
                                        #config.log('WIN MATCH', GetMatchResultFromDashboard(
                                        div_bet_score[0].get_attribute('innerHTML')
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
            # Charger les scriptTypes calculés au classement pour ce match
            _script_cfg = match_manager.get_match_script_config(config.newmatch)
            if _script_cfg and _script_cfg.get('script_types'):
                config.scriptTypeList = _script_cfg['script_types']
                config.total_gain_wanted = _script_cfg['total_gain_wanted']
                config.log(
                    f"ScriptTypes chargés pour {config.newmatch}: {config.scriptTypeList} "
                    f"→ objectif {config.total_gain_wanted}€",
                    'success', True
                )
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
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V2'
                                        config.cote_base = 1.3
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev1 > 1.4 and cotev1 < 1.7:
                                        config.win_type = 'V1'
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V2'
                                        config.cote_base = 1.5
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev1 > 1.7 and cotev1 < 1.9:
                                        config.win_type = 'V1'
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V2'
                                        config.cote_base = 1.8
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                    elif cotev2 > 1.1 and cotev2 < 1.4:
                                        config.cote_base = 1.3
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V1'
                                    elif cotev2 > 1.4 and cotev2 < 1.7:
                                        config.cote_base = 1.5
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V1'
                                    elif cotev2 > 1.7 and cotev2 < 1.9:
                                        config.cote_base = 1.8
                                        config.ligue_name = config.ligue_name + ' ' + str(config.cote_base)
                                        config.win_type = 'V2'
                                        if 'femmes' in config.ligue_name:
                                            config.win_type = 'V1'      

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
        print('test error innit ')
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
                                    (By.CLASS_NAME, 'dashboard-game-info__date')))
                                
                                time_element = bet_item.find_element(By.CLASS_NAME,
                                                                            config.classes['events_time'][
                                                                                config.site_type])

                                if config.site_type == 'old_site':
                                    start_time_text = bet_item.find_element(By.CLASS_NAME,
                                                                            config.classes['events_time'][
                                                                                config.site_type]).text
                                elif config.site_type == 'new_site':
                                    start_date_text = time_element.find_element(By.CLASS_NAME,
                                                                                'dashboard-game-info__date').text
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
        tableau_trie = sorted(goodmatch, key=lambda x: x[-2], reverse=True)

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
                8: []  # ITF avec qualification
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
                group_sorted = sorted(group, key=lambda x: x[-2], reverse=True)

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
                link = match[5]
                script_types_json = json.dumps(match[6]) if len(match) > 6 else json.dumps([])
                total_gain = str(match[7]) if len(match) > 7 else '0'
                match_info = "|".join([
                    players_str,
                    str(league),
                    str(match_id),
                    str(date_str),
                    str(prob),
                    str(link),
                    script_types_json,
                    total_gain
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
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    driver.get(config.site_line_url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'sports-menu-app-sport'))
    )
    config.error = False
    print('RECHERCHE DE MATCH')
    config.match_found = False
    save_site_type = config.site_type
    config.site_type = 'new_site'
    while not config.match_found and not config.error:
        line = 0
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
            driver.get(config.site_line_url)
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

            country = driver.find_element(By.CLASS_NAME, 'sports-menu-group-by-country')
            # print('find countries')
            countrybutton = country.find_elements(By.CLASS_NAME, 'sports-menu-group-by-champ')
            links = []
            liguelist = []

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
                ligue_name = linkcontent.get_attribute("title")
                print('ligue_name1', ligue_name)
                # Vérifier si 'nav_link' est absent
                if "sports-menu-app-champ-with-sub-champs-group__item" not in classes.split() and link:
                    print('link', link)
                    links.append(link)
                    liguelist.append([link, ligue_name])
                    continue
                elif linkcontent:
                    linkcontent.click()
                    print('click country', linkcontent.text)
                else:
                    continue

                liguebtn = driver.find_elements(By.CLASS_NAME, 'sports-menu-app-champ-with-sub-champs-group__item')
                for lbtn in liguebtn:
                    # ON RÉCUPÈRE LE NOM DE LA LIGUE (plus robuste : fallback sur .text / aria-label)
                    try:
                        ligue_elem = lbtn.find_element(By.CLASS_NAME, 'ui-nav-link__content')
                        ligue_name = ligue_elem.get_attribute("title") or ligue_elem.text or ligue_elem.get_attribute("aria-label") or ""
                        ligue_name = ligue_name.strip()
                        ligue_name = ligue_name.replace('.', '')  # Nettoyage de caractères indésirables
                        link = ligue_elem.get_attribute("href") or ""
                        print('ligue_name2', ligue_name)
                    except Exception as e:
                        config.log(f"Erreur récupération ligue: {e}", 'warning', True)
                        continue
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
                    liguelist.append([link, ligue_name])

                linkcontent.click()
                time.sleep(2)
                print('fermeture')
            matchlist = []
            print('liguelist', liguelist)
            for link in liguelist:
                if link[0]:
                    config.ligue_name = link[1]
                    print('ligue_name', config.ligue_name)
                    if not getCompet():
                        config.log('Compétition non autorisé', 'warning', True)
                        continue
                    if config.site_type == 'new_site':
                        link[0] = link[0].replace('?platform_type=mobile', '')
                        link[0] = f'{link[0]}?platform_type=desktop'
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
                                print('try time')
                                # Attendre jusqu'à 10 secondes que l'élément s'affiche dans bet_item
                                time_element = WebDriverWait(bet_item, 10).until(EC.visibility_of_element_located(
                                    (By.CLASS_NAME, 'dashboard-game-info__date')))
                                
                                time_element = bet_item.find_element(By.CLASS_NAME,
                                                                            config.classes['events_time'][
                                                                                config.site_type])

                                if config.site_type == 'old_site':
                                    print('old site time')
                                    start_time_text = bet_item.find_element(By.CLASS_NAME,
                                                                            config.classes['events_time'][
                                                                                config.site_type]).text
                                elif config.site_type == 'new_site':
                                    print('new site time')
                                    start_date_text = time_element.find_element(By.CLASS_NAME,
                                                                                'dashboard-game-info__date').text
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

        print(len(matchlist))
        print('matchlist', matchlist)

             # Sauvegarder la matchlist dans un fichier JSON avant traitement
        sauvegarder_matchlist_json(matchlist)

        # Traiter les matchs pour obtenir les probabilités
        goodmatch = traiter_matchlist(matchlist)

        # Tri en fonction de la dernière valeur (indice -1) en ordre décroissant
        tableau_trie = sorted(goodmatch, key=lambda x: x[-2], reverse=True)

        # Fonction de priorisation des matchs par ligue
        def prioritize_matches_by_league(matches, max_matches=100):
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
                8: []  # ITF avec qualification
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
                group_sorted = sorted(group, key=lambda x: x[-2], reverse=True)

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
                link = match[5]
                script_types_json = json.dumps(match[6]) if len(match) > 6 else json.dumps([])
                total_gain = str(match[7]) if len(match) > 7 else '0'
                match_info = "|".join([
                    players_str,
                    str(league),
                    str(match_id),
                    str(date_str),
                    str(prob),
                    str(link),
                    script_types_json,
                    total_gain
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
    rechercheDeMatch(driver)
