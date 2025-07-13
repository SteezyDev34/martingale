import json
import os
import re
import time
from datetime import date

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode

# Fichier de cache partagé pour toutes les stats tennis
CACHE_FILE = "tennis_stats_cache.json"


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
    print(cache)
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
    print(cache)
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
        try:
            driver1.get('https://www.ultimatetennisstatistics.com/headToHead?tab=statistics')
            WebDriverWait(driver1, 20).until(
                EC.presence_of_element_located((By.ID, 'player1'))
            )
            # Input and player selection with nickname fallback
            fld1 = driver1.find_element(By.ID, 'player1')
            found = False

            # Try with original name first
            fld1.send_keys(playerName1)
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
                        fld1.clear()
                        fld1.send_keys(nickname)
                        WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-1'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-1 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
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
            fld2 = driver1.find_element(By.ID, 'player2')
            found = False

            # Try with original name first
            fld2.send_keys(playerName2)
            WebDriverWait(driver1, 20).until(
                EC.visibility_of_element_located((By.ID, 'ui-id-2'))
            )
            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                if p2.lower() in item.text.lower():
                    item.click()
                    found = True
                    break

            # If not found, try with nicknames
            if not found:
                nicknames = get_player_nickname(playerName2)
                if nicknames:
                    for nickname in nicknames:
                        fld2.clear()
                        fld2.send_keys(nickname)
                        WebDriverWait(driver1, 20).until(
                            EC.visibility_of_element_located((By.ID, 'ui-id-2'))
                        )
                        for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                            if nickname.lower() in item.text.lower():
                                item.click()
                                found = True
                                break
                        if found:
                            break
                        else:
                            for item in driver1.find_elements(By.CSS_SELECTOR, '#ui-id-2 .ui-menu-item'):
                                item.click()
                                p2_key = 'player2'
                                break
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
                        WebDriverWait(driver, 10).until(
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
            prob_40_40_joueur1 = prob_service_joueur1 * prob_retour_joueur1
            prob_40_40_joueur2 = prob_service_joueur2 * prob_retour_joueur2
            print('Proba j1 40 A = ' + str(prob_40_40_joueur1))
            print('Proba j2 40 A = ' + str(prob_40_40_joueur2))

            # Save individual probabilities to cache
            cache[f"player_{playerName1.lower()}_40-40"] = prob_40_40_joueur1
            cache[f"player_{playerName2.lower()}_40-40"] = prob_40_40_joueur2
            save_cache(cache)

            # Calcul de la probabilité totale
            prob_40_40_totale = prob_40_40_joueur1 + prob_40_40_joueur2
            prob = prob_40_40_totale
            print('Proba 40 A = ' + str(prob))
            return prob
        except Exception as e:
            # Save individual probabilities to cache
            cache[f"player_{playerName1.lower()}_40-40"] = prob_40_40_joueur1
            cache[f"player_{playerName2.lower()}_40-40"] = prob_40_40_joueur2
            save_cache(cache)
            print('une erreur est survenue lors de la proba')
            print(e)
            tentative = tentative + 1
            continue
    if link:
        driver.switch_to.window(driver.window_handles[0])
        try:
            driver.get(link)
        except:
            print('te')
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
