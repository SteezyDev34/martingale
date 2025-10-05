import json
import os
import re
import time
from datetime import date, datetime

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode

# Fichier de cache partagé pour toutes les stats tennis
CACHE_FILE = "tennis_stats_cache.json"
# Fichier de log pour les joueurs non trouvés
PLAYERS_NOT_FOUND_LOG = "players_not_found.log"


def log_player_not_found(player_name, function_name=""):
    """
    Enregistre dans un fichier de log les joueurs qui ne sont pas trouvés.
    
    Args:
        player_name (str): Nom du joueur non trouvé
        function_name (str): Nom de la fonction qui a appelé le log (optionnel)
    """
    # Créer le répertoire Logs s'il n'existe pas
    os.makedirs("Logs", exist_ok=True)

    # Préparer le message de log avec timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] Joueur non trouvé: {player_name}"
    if function_name:
        log_message += f" (fonction: {function_name})"
    log_message += "\n"

    # Écrire dans le fichier de log
    try:
        with open(PLAYERS_NOT_FOUND_LOG, "a", encoding="utf-8") as f:
            print(f"{log_message}")
            f.write(log_message)
    except Exception as e:
        print(f"Erreur lors de l'écriture du log: {e}")


def load_cache():
    """
    Charge le cache JSON depuis CACHE_FILE.
    - Si le fichier n'existe pas ou est vide, renvoie {}.
    - Si le JSON est invalide, renvoie {} sans lever d'erreur.
    """
    # 1. Fichier absent ou vide → cache vide
    if not os.path.isfile(CACHE_FILE) or os.path.getsize(CACHE_FILE) == 0:
        return {}

    # 2. Lecture protégée
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # print("Cache chargé :", data)  # print facultatif pour debug
            return data
    except json.JSONDecodeError:
        # JSON corrompu ou vide → retour d'un cache vide
        print("Attention : cache JSON invalide, on repart avec {}")
        return {}
    except Exception as e:
        # Autre erreur d'I/O (permissions, etc.)
        print(f"Erreur lecture cache ({e}), retour de {{}}")
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# Initialise cache en mémoire
cache = load_cache()

global headers
headers = {
    'X-RapidAPI-Key': 'ef2b13642dmshf1d9ccde3c85691p1e0f03jsn54d169ef64f5',
    'X-RapidAPI-Host': 'ultimate-tennis1.p.rapidapi.com'
}

today = date.today().isoformat()

# Mises à jour quotidiennes ATP et WTA rankings
if cache.get('atp_ranking_date') != today:
    try:
        resp = requests.get("https://ultimate-tennis1.p.rapidapi.com/live_leaderboard/450", headers=headers)
        data = resp.json().get('data', [])
        cache['atp_ids'] = [f"{p['Name'].split('.')[-1].strip()}|{p['id']}" for p in data]
        cache['atp_ranking_date'] = today
        save_cache(cache)
    except:
        pass

if cache.get('wta_ranking_date') != today:
    try:
        resp = requests.get("https://ultimate-tennis1.p.rapidapi.com/rankings/wta/singles/1000/current",
                            headers=headers)
        data = resp.json().get('data', [])
        cache['wta_ids'] = [f"{p['name'].strip()}|{p['ID']}" for p in data]
        cache['wta_ranking_date'] = today
        save_cache(cache)
    except:
        pass


# Utilitaires pour récupérer les ID depuis le cache

def getPlayerApiId(playerName):
    name = unidecode(playerName).strip().lower()
    for entry in cache.get('atp_ids', []):
        n, pid = entry.lower().split('|')
        if n in name:
            return pid
    return None


def getPlayerWtaApiId(playerName):
    lastname = unidecode(playerName).split()[-1].lower()
    for entry in cache.get('wta_ids', []):
        n, pid = entry.lower().split('|')
        if n.split()[-1] == lastname:
            return pid
    return None


# Probabilité 40-40 via API Ultimate Tennis

def get_proba_40A(playerName1, playerName2, cat='atp', surface='hard'):
    # Initialise cache en mémoire
    cache = load_cache()
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    print(p1_key)
    print(p2_key)
    if p1_key in cache and p2_key in cache:
        print('proba found in cache')
        return cache[p1_key] + cache[p2_key]
    id1 = getPlayerApiId(playerName1)
    id2 = getPlayerApiId(playerName2)
    if not id1 or not id2:
        return 0.0
    url1 = f"https://ultimate-tennis1.p.rapidapi.com/player_stats/{cat}/{id1}/2024/{surface}"
    url2 = f"https://ultimate-tennis1.p.rapidapi.com/player_stats/{cat}/{id2}/2024/{surface}"
    try:
        d1 = requests.get(url1, headers=headers).json()
        time.sleep(1)
        d2 = requests.get(url2, headers=headers).json()
        time.sleep(1)
        svc1 = d1['ServiceRecordStats']['ServicePointsWonPercentage'] / 100
        ret1 = d1['ReturnRecordStats']['ReturnPointsWonPercentage'] / 100
        svc2 = d2['ServiceRecordStats']['ServicePointsWonPercentage'] / 100
        ret2 = d2['ReturnRecordStats']['ReturnPointsWonPercentage'] / 100
        prob1 = svc1 * ret1
        prob2 = svc2 * ret2
        cache[f"player_{playerName1.lower()}_40-40"] = prob1
        cache[f"player_{playerName2.lower()}_40-40"] = prob2
        save_cache(cache)
        return prob1 + prob2
    except:
        return 0.0


# Probabilité 40-40 via API WTA

def get_wta_proba_40A(playerName1, playerName2):
    # Initialise cache en mémoire
    cache = load_cache()
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    print(p1_key)
    print(p2_key)
    if p1_key in cache and p2_key in cache:
        print('proba found in cache')
        return cache[p1_key] + cache[p2_key]
    pid1 = getPlayerWtaApiId(playerName1)
    pid2 = getPlayerWtaApiId(playerName2)
    if not pid1 or not pid2:
        return 0.0
    url1 = f"https://ultimate-tennis1.p.rapidapi.com/player_stats/wta/{pid1}/2024"
    url2 = f"https://ultimate-tennis1.p.rapidapi.com/player_stats/wta/{pid2}/2024"
    try:
        d1 = requests.get(url1, headers=headers).json()
        time.sleep(1)
        d2 = requests.get(url2, headers=headers).json()
        time.sleep(1)
        svc1 = d1['player_data'][0]['service_points_won_percent'] / 100
        ret1 = d1['player_data'][0]['return_points_won_percent'] / 100
        svc2 = d2['player_data'][0]['service_points_won_percent'] / 100
        ret2 = d2['player_data'][0]['return_points_won_percent'] / 100
        prob1 = svc1 * ret1
        prob2 = svc2 * ret2
        cache[f"player_{playerName1.lower()}_40-40"] = prob1
        cache[f"player_{playerName2.lower()}_40-40"] = prob2
        save_cache(cache)
        return prob1 + prob2
    except:
        return 0.0


# Désactiver les avertissements liés à la désactivation de la vérification SSL
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)


def get_wta_proba_40A_sofascore(playerName1, playerName2):
    # Initialise cache en mémoire
    print("\n===== DÉBUT FONCTION get_wta_proba_40A_sofascore =====")
    print(f"Joueurs: {playerName1} vs {playerName2}")
    cache = load_cache()
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    print(f"Clés de cache: {p1_key}, {p2_key}")
    if p1_key in cache and p2_key in cache:
        print('Probabilités trouvées dans le cache')
        result = cache[p1_key] + cache[p2_key]
        print(f"Résultat depuis cache: {result}")
        # return result

    print("Recherche des IDs des joueurs via API...")
    url1 = f"http://datas.sc2vagr6376.universe.wf/api/sports/2/teams/search?search={playerName1.replace(' ', '+')}"
    url2 = f"http://datas.sc2vagr6376.universe.wf/api/sports/2/teams/search?search={playerName2.replace(' ', '+')}"
    try:
        print(f"Requête API pour {playerName1}: {url1}")
        # Désactiver la vérification SSL pour les certificats auto-signés
        d1 = requests.get(url1, headers=headers, verify=False).json()
        print(f"Réponse API pour {playerName1}: {d1}")
        time.sleep(1)
        print(f"Requête API pour {playerName2}: {url2}")
        d2 = requests.get(url2, headers=headers, verify=False).json()
        print(f"Réponse API pour {playerName2}: {d2}")
        time.sleep(1)

        # Vérifier si des résultats ont été trouvés
        if not d1.get('data') or len(d1['data']) == 0:
            print(f"Aucun résultat trouvé pour {playerName1}")
            log_player_not_found(playerName1, "get_wta_proba_40A_sofascore")
        if not d2.get('data') or len(d2['data']) == 0:
            print(f"Aucun résultat trouvé pour {playerName2}")
            log_player_not_found(playerName2, "get_wta_proba_40A_sofascore")

        # Afficher les résultats trouvés pour aider au débogage
        print(f"Résultats pour {playerName1}:")
        for i, player in enumerate(d1['data']):
            print(
                f"  {i + 1}. {player.get('name')} (ID: {player.get('sofascore_id')}, Ligue: {player.get('league', {}).get('name', 'Inconnue')})")

        print(f"Résultats pour {playerName2}:")
        for i, player in enumerate(d2['data']):
            print(
                f"  {i + 1}. {player.get('name')} (ID: {player.get('sofascore_id')}, Ligue: {player.get('league', {}).get('name', 'Inconnue')})")

        # Sélectionner le joueur individuel (non double) si possible
        pid1 = None
        for player in d1['data']:
            # Éviter les équipes de double (contiennent souvent '/')
            if '/' not in player.get('name', ''):
                # pid1 = player.get('sofascore_id')
                pid1 = player.get('id')
                print(f"Sélectionné pour {playerName1}: {player.get('name')} (ID: {pid1})")
                break

        pid2 = None
        for player in d2['data']:
            if '/' not in player.get('name', ''):
                # pid2 = player.get('sofascore_id')
                pid2 = player.get('id')
                print(f"Sélectionné pour {playerName2}: {player.get('name')} (ID: {pid2})")
                break

        # Si aucun joueur individuel n'a été trouvé, utiliser le premier résultat
        if pid1 is None and d1['data']:
            # pid1 = d1['data'][0]['sofascore_id']
            pid1 = d1['data'][0]['id']
            print(f"Aucun joueur individuel trouvé pour {playerName1}, utilisation du premier résultat (ID: {pid1})")

        if pid2 is None and d2['data']:
            # pid2 = d2['data'][0]['sofascore_id']
            pid2 = d2['data'][0]['id']
            print(f"Aucun joueur individuel trouvé pour {playerName2}, utilisation du premier résultat (ID: {pid2})")

        if not pid1 and not pid2:
            print("Impossible de récupérer les IDs des joueurs")
            return 0.0

        print(f"IDs récupérés: {pid1} pour {playerName1}, {pid2} pour {playerName2}")
    except Exception as e:
        print(f"Erreur lors de la récupération des IDs: {e}")
        # Ajouter un avertissement sur la désactivation de la vérification SSL
        print("Note: Si l'erreur persiste, vérifiez la configuration SSL ou le certificat du serveur.")
        return 0.0
    else:
        # url1 = f"https://www.sofascore.com/api/v1/team/{pid1}/year-statistics/2025"
        # url2 = f"https://www.sofascore.com/api/v1/team/{pid2}/year-statistics/2025"
        url1 = f"http://datas.sc2vagr6376.universe.wf/api/stats/tennis/player/{pid1}"
        url2 = f"http://datas.sc2vagr6376.universe.wf/api/stats/tennis/player/{pid2}"
        print(f"URLs des statistiques: \n{url1}\n{url2}")
        try:
            print(f"Récupération des statistiques pour {playerName1}...")
            json_data = requests.get(url1, headers=headers, verify=False).json()
            d1 = json_data.get('data', {})  # ou {} ou [] selon ce que tu attends
            time.sleep(1)
            print(f"Récupération des statistiques pour {playerName2}...")
            json_data = requests.get(url2, headers=headers, verify=False).json()
            d2 = json_data.get('data', {})  # ou {} ou [] selon ce que tu attends
            time.sleep(1)
            print("Statistiques récupérées avec succès")

            # Calcul des statistiques globales pour le joueur 1
            total_first_serve_points_scored1 = 0
            total_first_serve_points_total1 = 0
            total_second_serve_points_scored1 = 0
            total_second_serve_points_total1 = 0
            total_break_points_scored1 = 0
            total_break_points_total1 = 0

            # Parcourir toutes les surfaces pour le joueur 1
            print(f"Structure des données pour {playerName1}: {list(d1.keys())}")
            print(f"Nombre de statistiques pour {playerName1}: {len(d1.get('statistics', []))}")
            for i, stat in enumerate(d1.get('statistics', [])):
                print(f"Surface {i + 1} pour {playerName1}: {stat.get('groundType', 'Inconnue')}")
                total_first_serve_points_scored1 += stat.get('firstServePointsScored', 0)
                total_first_serve_points_total1 += stat.get('firstServePointsTotal', 0)
                total_second_serve_points_scored1 += stat.get('secondServePointsScored', 0)
                total_second_serve_points_total1 += stat.get('secondServePointsTotal', 0)
                total_break_points_scored1 += stat.get('breakPointsScored', 0)
                total_break_points_total1 += stat.get('breakPointsTotal', 0)

            # Calcul des statistiques globales pour le joueur 2
            total_first_serve_points_scored2 = 0
            total_first_serve_points_total2 = 0
            total_second_serve_points_scored2 = 0
            total_second_serve_points_total2 = 0
            total_break_points_scored2 = 0
            total_break_points_total2 = 0

            # Parcourir toutes les surfaces pour le joueur 2
            print(f"Structure des données pour {playerName2}: {list(d2.keys())}")
            print(f"Nombre de statistiques pour {playerName2}: {len(d2.get('statistics', []))}")
            for i, stat in enumerate(d2.get('statistics', [])):
                print(f"Surface {i + 1} pour {playerName2}: {stat.get('groundType', 'Inconnue')}")
                total_first_serve_points_scored2 += stat.get('firstServePointsScored', 0)
                total_first_serve_points_total2 += stat.get('firstServePointsTotal', 0)
                total_second_serve_points_scored2 += stat.get('secondServePointsScored', 0)
                total_second_serve_points_total2 += stat.get('secondServePointsTotal', 0)
                total_break_points_scored2 += stat.get('breakPointsScored', 0)
                total_break_points_total2 += stat.get('breakPointsTotal', 0)

            print(f"\nTotaux pour {playerName1}:")
            print(f"Points gagnés sur 1ère balle: {total_first_serve_points_scored1}/{total_first_serve_points_total1}")
            print(
                f"Points gagnés sur 2ème balle: {total_second_serve_points_scored1}/{total_second_serve_points_total1}")
            print(f"Balles de break converties: {total_break_points_scored1}/{total_break_points_total1}")

            print(f"\nTotaux pour {playerName2}:")
            print(f"Points gagnés sur 1ère balle: {total_first_serve_points_scored2}/{total_first_serve_points_total2}")
            print(
                f"Points gagnés sur 2ème balle: {total_second_serve_points_scored2}/{total_second_serve_points_total2}")
            print(f"Balles de break converties: {total_break_points_scored2}/{total_break_points_total2}")

            # Calcul des pourcentages de service et retour
            svc1 = float(total_first_serve_points_scored1) / float(
                total_first_serve_points_total1) if total_first_serve_points_total1 > 0 else 0.0
            ret1 = float(total_break_points_scored1) / float(
                total_break_points_total1) if total_break_points_total1 > 0 else 0.0
            svc2 = float(total_first_serve_points_scored2) / float(
                total_first_serve_points_total2) if total_first_serve_points_total2 > 0 else 0.0
            ret2 = float(total_break_points_scored2) / float(
                total_break_points_total2) if total_break_points_total2 > 0 else 0.0

            print(f"\nPourcentages pour {playerName1}:")
            print(f"Service: {svc1:.4f} ({total_first_serve_points_scored1}/{total_first_serve_points_total1})")
            print(f"Retour: {ret1:.4f} ({total_break_points_scored1}/{total_break_points_total1})")

            print(f"\nPourcentages pour {playerName2}:")
            print(f"Service: {svc2:.4f} ({total_first_serve_points_scored2}/{total_first_serve_points_total2})")
            print(f"Retour: {ret2:.4f} ({total_break_points_scored2}/{total_break_points_total2})")

            # Calcul des probabilités
            prob1 = float(svc1) * float(ret1)
            prob2 = float(svc2) * float(ret2)

            print(f"\nProbabilités calculées:")
            print(f"{playerName1}: {prob1:.4f} (svc {svc1:.4f} * ret {ret1:.4f})")
            print(f"{playerName2}: {prob2:.4f} (svc {svc2:.4f} * ret {ret2:.4f})")

            # Mise en cache des résultats
            cache[f"player_{playerName1.lower()}_40-40"] = prob1
            cache[f"player_{playerName2.lower()}_40-40"] = prob2
            save_cache(cache)

            result = float(prob1) + float(prob2)
            print(f"Résultat final: {result:.4f}")
            print("===== FIN FONCTION get_wta_proba_40A_sofascore =====\n")
            return result
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            print("Traceback:")
            import traceback
            traceback.print_exc()
            print("===== FIN FONCTION get_wta_proba_40A_sofascore (avec erreur) =====\n")
            return 0.0


# Probabilité 40-40 via scraping head-to-head UltimateStatistics

def get_proba_40A_other(playerName1, playerName2, driver1, link=False):
    # Initialise cache en mémoire
    cache = load_cache()
    # Vérifier cache pour chaque joueur
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    print(p1_key)
    print(p2_key)
    if p1_key in cache and p2_key in cache:
        print('proba found in cache')
        # return cache[p1_key] + cache[p2_key]
    prob_service_joueur1 = 0.0
    prob_service_joueur2 = 0.0
    prob_retour_joueur1 = 0.0
    prob_retour_joueur2 = 0.0
    p1 = unidecode(playerName1).replace('-', ' ').strip()
    p2 = unidecode(playerName2).replace('-', ' ').strip()
    attempt = 0
    total_prob = 0.0

    while attempt < 2:

        print('attempt', attempt)
        try:
            driver1.get('https://www.ultimatetennisstatistics.com/headToHead?tab=statistics')
            WebDriverWait(driver1, 5).until(
                EC.presence_of_element_located((By.ID, 'player1'))
            )
            # Input and player selection with nickname fallback
            fld1 = driver1.find_element(By.ID, 'player1')
            found = False

            # Try with original name first
            fld1.send_keys(playerName1)
            time.sleep(1)
            WebDriverWait(driver1, 5).until(
                EC.visibility_of_element_located((By.ID, 'ui-id-1'))
            )
            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                if p1.lower() in item.text.lower():
                    item.click()
                    found = True
                    break

            # If not found, try with nicknames
            if not found:
                nicknames = get_player_nickname(playerName1)
                if nicknames:
                    for nickname in nicknames:
                        fld1 = WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'player1'))
                        )
                        fld1.clear()
                        fld1.send_keys(nickname)
                        time.sleep(1)
                        WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-1'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
                                print('item.text.lower', item.text.lower)
                                item.click()
                                found = True
                                break
                        if found:
                            break
                        else:
                            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                                item.click()
                                p1_key = 'player1'
                                break
            time.sleep(1)
            fld2 = WebDriverWait(driver1, 5).until(
                EC.visibility_of_element_located((By.ID, 'player2'))
            )
            found = False

            # Try with original name first
            fld2.send_keys(playerName2)
            time.sleep(1)
            WebDriverWait(driver1, 5).until(
                EC.visibility_of_element_located((By.ID, 'ui-id-2'))
            )
            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                if p2.lower() in item.text.lower():
                    print('found', item.text.lower())
                    item.click()
                    found = True
                    break

            # If not found, try with nicknames
            if not found:
                nicknames = get_player_nickname(playerName2)
                if nicknames:
                    for nickname in nicknames:
                        fld2 = WebDriverWait(driver1, 5).until(
                            EC.visibility_of_element_located((By.ID, 'player2'))
                        )
                        print('nickname', nickname)
                        fld2.clear()
                        fld2.send_keys(nickname)
                        WebDriverWait(driver1, 5).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-2'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
                                print('item.text.lower', item.text.lower())
                                item.click()
                                found = True
                                break
                if found:
                    print('found, ', p2_key)
                else:
                    for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                        item.click()
                        print('not found, ', p2_key)
                        p2_key = 'player2'
            # Rechargement avec IDs
            m = re.search(r'playerId1=(\d+)&playerId2=(\d+)', driver1.current_url)
            if m:
                driver1.get(
                    f"https://www.ultimatetennisstatistics.com/headToHead?tab=statistics&playerId1={m.group(1)}&playerId2={m.group(2)}"
                )
            WebDriverWait(driver1, 5).until(
                EC.visibility_of_element_located((By.ID, 'statisticsOverview'))
            )
            rows = driver1.find_element(By.ID, 'statisticsOverview').find_elements(By.TAG_NAME, 'tr')
            for tr in rows:
                txt = tr.text.lower()
                if 'service points won %' in txt:
                    a, b = tr.text.split('Service Points Won %')
                    prob_service_joueur1 = float(a.replace('%', '').strip()) / 100 if a else 0.0
                    prob_service_joueur2 = float(b.replace('%', '').strip()) / 100 if b else 0.0
                if 'return points won %' in txt:
                    a, b = tr.text.split('Return Points Won %')
                    prob_retour_joueur1 = float(a.replace('%', '').strip()) / 100 if a else 0.0
                    prob_retour_joueur2 = float(b.replace('%', '').strip()) / 100 if b else 0.0
                    break
            # Calcul et cache individuel
            p1_c = prob_service_joueur1 * prob_retour_joueur1
            p2_c = prob_service_joueur2 * prob_retour_joueur2
            print('p1_key', p1_key)
            print('p2_key', p2_key)
            cache[p1_key] = p1_c
            cache[p2_key] = p2_c
            save_cache(cache)
            total_prob = p1_c + p2_c
            print('Proba 40-40 h2h =', total_prob)
            return total_prob
        except Exception as e:
            print('Erreur get_proba_40A_other :', e)
            attempt += 1
            time.sleep(1)
    if link:
        try:
            driver1.get(link)
        except:
            pass
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    cache[p1_key] = 0
    cache[p2_key] = 0
    save_cache(cache)
    return total_prob


# Probabilité 40-40 via scraping head-to-head Sofascore

def get_proba_40A_other_sofascore_tofinishdev(playerName1, playerName2, driver1, link=False):
    # Initialise cache en mémoire
    cache = load_cache()
    # Vérifier cache pour chaque joueur
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    print(p1_key)
    print(p2_key)
    if p1_key in cache and p2_key in cache:
        print('proba found in cache')
        return cache[p1_key] + cache[p2_key]
    prob_service_joueur1 = 0.0
    prob_service_joueur2 = 0.0
    prob_retour_joueur1 = 0.0
    prob_retour_joueur2 = 0.0
    p1 = unidecode(playerName1).replace('-', ' ').strip()
    p2 = unidecode(playerName2).replace('-', ' ').strip()
    attempt = 0
    total_prob = 0.0

    while attempt < 2:

        print('attempt', attempt)
        try:
            driver1.get('https://www.sofascore.com/fr/tennis/team/compare')
            WebDriverWait(driver1, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="__next"]/main/div/div/div/div[1]/div[3]/div/div[2]'))
            )
            h2h_block = driver1.find_element(By.XPATH, '//*[@id="__next"]/main/div/div/div/div[1]/div[3]/div/div[2]')
            # Input and player selection with nickname fallback
            flds = h2h_block.find_elements(By.TAG_NAME, 'input')
            fld1 = flds[0]
            found = False

            # Try with original name first
            fld1.send_keys(playerName1)
            time.sleep(2)
            WebDriverWait(driver1, 20).until(
                EC.visibility_of_element_located((By.ID, 'ui-id-1'))
            )
            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                if p1.lower() in item.text.lower():
                    item.click()
                    found = True
                    break

            # If not found, try with nicknames
            if not found:
                nicknames = get_player_nickname(playerName1)
                if nicknames:
                    for nickname in nicknames:
                        fld1 = WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'player1'))
                        )
                        fld1.clear()
                        fld1.send_keys(nickname)
                        time.sleep(1)
                        WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-1'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
                                print('item.text.lower', item.text.lower)
                                item.click()
                                found = True
                                break
                        if found:
                            break
                        else:
                            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                                item.click()
                                p1_key = 'player1'
                                break
            time.sleep(1)
            fld2 = WebDriverWait(driver1, 20).until(
                EC.visibility_of_element_located((By.ID, 'player2'))
            )
            found = False

            # Try with original name first
            fld2.send_keys(playerName2)
            time.sleep(1)
            WebDriverWait(driver1, 20).until(
                EC.visibility_of_element_located((By.ID, 'ui-id-2'))
            )
            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                if p2.lower() in item.text.lower():
                    print('found', item.text.lower())
                    item.click()
                    found = True
                    break

            # If not found, try with nicknames
            if not found:
                nicknames = get_player_nickname(playerName2)
                if nicknames:
                    for nickname in nicknames:
                        fld2 = WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'player2'))
                        )
                        print('nickname', nickname)
                        fld2.clear()
                        fld2.send_keys(nickname)
                        WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-2'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
                                print('item.text.lower', item.text.lower())
                                item.click()
                                found = True
                                break
                if found:
                    print('found, ', p2_key)
                else:
                    for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                        item.click()
                        print('not found, ', p2_key)
                        p2_key = 'player2'
            # Rechargement avec IDs
            m = re.search(r'playerId1=(\d+)&playerId2=(\d+)', driver1.current_url)
            if m:
                driver1.get(
                    f"https://www.ultimatetennisstatistics.com/headToHead?tab=statistics&playerId1={m.group(1)}&playerId2={m.group(2)}"
                )
            WebDriverWait(driver1, 20).until(
                EC.visibility_of_element_located((By.ID, 'statisticsOverview'))
            )
            rows = driver1.find_element(By.ID, 'statisticsOverview').find_elements(By.TAG_NAME, 'tr')
            for tr in rows:
                txt = tr.text.lower()
                if 'service points won %' in txt:
                    a, b = tr.text.split('Service Points Won %')
                    prob_service_joueur1 = float(a.replace('%', '').strip()) / 100 if a else 0.0
                    prob_service_joueur2 = float(b.replace('%', '').strip()) / 100 if b else 0.0
                if 'return points won %' in txt:
                    a, b = tr.text.split('Return Points Won %')
                    prob_retour_joueur1 = float(a.replace('%', '').strip()) / 100 if a else 0.0
                    prob_retour_joueur2 = float(b.replace('%', '').strip()) / 100 if b else 0.0
                    break
            # Calcul et cache individuel
            p1_c = prob_service_joueur1 * prob_retour_joueur1
            p2_c = prob_service_joueur2 * prob_retour_joueur2
            print('p1_key', p1_key)
            print('p2_key', p2_key)
            cache[p1_key] = p1_c
            cache[p2_key] = p2_c
            save_cache(cache)
            total_prob = p1_c + p2_c
            print('Proba 40-40 h2h =', total_prob)
            return total_prob
        except Exception as e:
            print('Erreur get_proba_40A_other :', e)
            attempt += 1
            time.sleep(1)
    if link:
        try:
            driver1.get(link)
        except:
            pass
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"
    cache[p1_key] = 0
    cache[p2_key] = 0
    save_cache(cache)
    return total_prob


# Probabilité 40-40 via scraping WTA Rankings

def get_wta_proba_40A_other(playerName1, playerName2, driver1, link=False):
    # Initialise cache en mémoire
    cache = load_cache()
    """
    Calcule la probabilité d'aller en 40-40 pour deux joueuses WTA via scraping WTA Rankings,
    avec système de cache et gestion des surnoms.
    """
    # Clés de cache individuelles
    p1_key = f"player_{unidecode(playerName1).strip().lower().replace('-', ' ')}_40-40"
    p2_key = f"player_{unidecode(playerName2).strip().lower().replace('-', ' ')}_40-40"

    # Si déjà en cache, on retourne la somme
    if p1_key in cache and p2_key in cache:
        print('Probabilités trouvées en cache')
        return cache[p1_key] + cache[p2_key]

    # Normalisation des noms
    playerName1 = unidecode(playerName1).replace('-', ' ').strip()
    playerName2 = unidecode(playerName2).replace('-', ' ').strip()
    players = [playerName1, playerName2]
    print('get proba other')
    prob_service_joueur1 = 0
    prob_service_joueur2 = 0
    prob_retour_joueur1 = 0
    prob_retour_joueur2 = 0
    prob_40_40_joueur1 = 0
    prob_40_40_joueur2 = 0
    playerName1 = unidecode(playerName1)
    playerName2 = unidecode(playerName2)
    playerName1 = playerName1.replace('-', ' ')
    playerName2 = playerName2.replace('-', ' ')
    tentative = 0
    prob = 0
    ok = 0
    playersName = [playerName1, playerName2]
    while ok == 0 and tentative < 2:
        from ChromeDriver.SetDriver import driver
        i = 1
        try:
            print(playersName)
            for playerName in playersName:
                print(playerName)
                print('try driver get')
                try:
                    driver.switch_to.window(driver.window_handles[0])
                    driver.get('https://www.wtatennis.com/rankings/singles')
                except:
                    print('te')
                print('drvier get done')
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'rankings__list'))
                )

                fieldplayer1 = driver.find_elements(By.CLASS_NAME, 'js-player-search-button')[0]
                fieldplayer1.click()
                time.sleep(2)
                fieldplayer1 = driver.find_elements(By.CLASS_NAME, 'js-player-search-input')[0]
                fieldplayer1.send_keys(playerName)
                element = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, 'js-rankings-body'))
                )
                time.sleep(5)
                player_block = driver.find_elements(By.CLASS_NAME, 'js-rankings-body')[0]
                player_list = player_block.find_elements(By.CLASS_NAME, 'player-row')
                print('player list length:', len(player_list))

                # If no players found, try with nicknames
                if len(player_list) == 0:
                    nicknames = get_player_nickname(playerName)
                    if nicknames:
                        for nickname in nicknames:
                            fieldplayer1.clear()
                            fieldplayer1.send_keys(nickname)
                            time.sleep(5)
                            player_block = driver.find_elements(By.CLASS_NAME, 'js-rankings-body')[0]
                            player_list = player_block.find_elements(By.CLASS_NAME, 'player-row')
                            if len(player_list) > 0:
                                print('Found player with nickname:', nickname)
                                break

                print('Final player list length:', len(player_list))
                for player in player_list:
                    print('eaach player')
                    player_name = player.find_elements(By.CLASS_NAME, 'player-cell__name-wrap')[0].text.strip().replace(
                        '\n', ' ')
                    print(player_name.lower())
                    if re.search(playerName.lower(), player_name.lower()):
                        print('find')
                        player.click()
                        drawer_links = driver.find_elements(By.CLASS_NAME, 'player-row-drawer__link')
                        for link in drawer_links:
                            if link.is_displayed():
                                print("Lien visible trouvé, on clique.")
                                link.click()

                    else:
                        print('not found')
                    try:
                        time.sleep(2)
                        curretn = driver.current_url + '/stats'
                        print('driver get stats', curretn)
                        driver.switch_to.window(driver.window_handles[0])
                        try:
                            driver.get(curretn)
                        except:
                            print('te')
                        print('driver ok')
                        # Attendre que le conteneur des stats soit chargé
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "player-stats__secondary-stats"))
                        )
                        print('player-stats__secondary-stats')
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "tournament-year-dropdown"))
                        )
                        print('tournament-year-dropdown')
                        # Cliquer sur le bouton du menu déroulant
                        dropdown_button = driver.find_element(By.CLASS_NAME, "tournament-year-dropdown__clickzone")
                        dropdown_button.click()

                        # Attendre que les options soient visibles
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "tournament-year-dropdown__option"))
                        )
                        print('tournament-year-dropdown__option')

                        time.sleep(3)

                        # Sélectionner l'option "2024"
                        option_2025 = driver.find_element(By.XPATH, "//div[@data-value='2025']")
                        option_2025.click()
                        time.sleep(3)
                        # Localiser les stats
                        stats = driver.find_elements(By.CLASS_NAME, "player-stats__secondary")

                        # Parcourir les stats pour récupérer les labels et valeurs
                        print('len stats')
                        print(len(stats))
                        for stat in stats:
                            label = stat.find_element(By.CLASS_NAME, "player-stats__secondary-label").text
                            print('label', label)
                            value = stat.find_element(By.CLASS_NAME, "player-stats__secondary-value").text
                            if label in ["Service Points Won %"]:

                                if i == 2:
                                    prob_service_joueur2 = value.replace('%', '')
                                    print('proba', prob_service_joueur2)

                                    if prob_service_joueur2 == '':
                                        prob_service_joueur2 = 0
                                    else:
                                        prob_service_joueur2 = float(prob_service_joueur2) / 100
                                        print('prob_service_joueur2 : ' + str(prob_service_joueur2))
                                else:
                                    prob_service_joueur1 = value.replace('%', '')
                                    print('proba', prob_service_joueur1)
                                    if prob_service_joueur1 == '':
                                        prob_service_joueur1 = 0
                                    else:
                                        prob_service_joueur1 = float(prob_service_joueur1) / 100
                                        print('prob_service_joueur1 : ' + str(prob_service_joueur1))
                            if label in ["Return Points Won"]:
                                if i == 2:
                                    prob_retour_joueur2 = value.replace('%', '')
                                    if prob_retour_joueur2 == '':
                                        prob_retour_joueur2 = 0
                                    else:
                                        prob_retour_joueur2 = float(prob_retour_joueur2) / 100
                                        print('prob_retour_joueur1 : ' + str(prob_retour_joueur2))
                                else:
                                    prob_retour_joueur1 = value.replace('%', '')
                                    if prob_retour_joueur1 == '':
                                        prob_retour_joueur1 = 0
                                    else:
                                        prob_retour_joueur1 = float(prob_retour_joueur1) / 100
                                        print('prob_retour_joueur1 : ' + str(prob_retour_joueur1))
                        if i == 2:
                            print('break')
                            break
                        else:
                            i = i + 1
                        print('end')
                    except Exception as e:
                        print('no stats found')
                        print(e)
                        if i == 2:
                            print('break')
                            break
                        else:
                            i = i + 1

            # Calculate probabilities for each player
            # Conversion explicite en float pour éviter les erreurs de type
            prob_service_joueur1 = float(prob_service_joueur1) if isinstance(prob_service_joueur1,
                                                                             (int, float)) else 0.0
            prob_retour_joueur1 = float(prob_retour_joueur1) if isinstance(prob_retour_joueur1, (int, float)) else 0.0
            prob_service_joueur2 = float(prob_service_joueur2) if isinstance(prob_service_joueur2,
                                                                             (int, float)) else 0.0
            prob_retour_joueur2 = float(prob_retour_joueur2) if isinstance(prob_retour_joueur2, (int, float)) else 0.0

            prob_40_40_joueur1 = float(prob_service_joueur1) * float(prob_retour_joueur1)
            prob_40_40_joueur2 = float(prob_service_joueur2) * float(prob_retour_joueur2)
            print('Proba j1 40 A = ' + str(prob_40_40_joueur1))
            print('Proba j2 40 A = ' + str(prob_40_40_joueur2))

            # Save individual probabilities to cache
            cache[f"player_{playerName1.lower()}_40-40"] = prob_40_40_joueur1
            cache[f"player_{playerName2.lower()}_40-40"] = prob_40_40_joueur2
            save_cache(cache)

            # Calcul de la probabilité totale
            prob_40_40_totale = float(prob_40_40_joueur1) + float(prob_40_40_joueur2)
            prob = float(prob_40_40_totale)
            print('Proba 40 A = ' + str(prob))
            return prob
        except Exception as e:
            # Initialisation des variables en cas d'erreur
            prob_40_40_joueur1 = 0.0
            prob_40_40_joueur2 = 0.0
            # Save individual probabilities to cache
            cache[f"player_{playerName1.lower()}_40-40"] = prob_40_40_joueur1
            cache[f"player_{playerName2.lower()}_40-40"] = prob_40_40_joueur2
            save_cache(cache)
            print('une erreur est survenue lors de la proba')
            print(e)
            tentative = tentative + 1
            continue
    # Initialisation de la variable prob si elle n'est pas définie
    if 'prob' not in locals():
        prob = 0.0
    # Initialisation de driver s'il n'est pas défini
    if 'driver' not in locals() or driver is None:
        # Importer driver uniquement si nécessaire
        try:
            from ChromeDriver.SetDriver import driver as chrome_driver
            driver = chrome_driver
        except Exception as e:
            print(f"Erreur lors de l'initialisation du driver: {e}")
            driver = None

    # Initialisation de link s'il n'est pas défini
    if 'link' not in locals():
        link = None

    # Vérification que driver et link sont définis avant utilisation
    if link is not None and driver is not None:
        try:
            # Vérifier que driver a les méthodes nécessaires avant de les utiliser
            if hasattr(driver, 'switch_to') and hasattr(driver, 'window_handles') and hasattr(driver, 'get'):
                driver.switch_to.window(driver.window_handles[0])
                driver.get(str(link))
            else:
                print('Driver non initialisé correctement, impossible de naviguer')
        except Exception as e:
            print('Erreur lors de la navigation:', e)
    return prob


def get_player_nickname(name, nickname_file="nicknames.json"):
    """
    Vérifie dans un fichier JSON les surnoms d'un joueur.
    Si `name` est un nom officiel, retourne [nom_officiel] + liste de surnoms.
    Si `name` est un surnom, retourne [nom_officiel] + liste de surnoms.
    Sinon, retourne None.
    """
    try:
        with open(nickname_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception:
        return None
    lower_name = name.strip().lower()
    # Vérifier si c'est un nom officiel
    for real, nicks in mapping.items():
        if real.strip().lower() == lower_name:
            return [real] + nicks
    # Vérifier si c'est un surnom
    for real, nicks in mapping.items():
        for nick in nicks:
            if nick.strip().lower() == lower_name:
                return [real] + nicks
    return None
