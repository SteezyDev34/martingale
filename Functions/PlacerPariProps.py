# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import re
import unicodedata
from difflib import SequenceMatcher

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

import config
from Functions.getTextFromImageGPT import compare_match_name, compare_player_name, compare_prop_name
from Functions.Logs.Logger import log
from Functions.GetMise import GetMise
if os.getenv('PYCHARM_HOSTED') != '1':  # Si exécuté dans PyCharm
    # Simple écriture de lignes vides pour PyCharm

    # Vérification de l'environnement
    import VenvDependencyManager

    VenvDependencyManager.main()

# La fonction locale `get_mise` a été supprimée.
# Utiliser `GetMise(driver)` depuis `Functions/GetMise.py` qui met à jour `config.mise`.


def clear_betslip_if_present(driver, wait=5):
    """
    Si un betslip est présent, cliquer sur la croix (premier bouton) pour le fermer.
    Retourne True si une action de fermeture a été tentée, False sinon.
    """
    log("[PlacerPariProps] clear_betslip_if_present start", "debug")
    try:
        betlist_el = WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'betlist'))
        )
    except Exception:
        print("ℹ️ Aucun betslip détecté.")
        return False

    try:
        bet_item = betlist_el.find_element(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')
    except Exception:
        print("ℹ️ Aucun élément de pari détecté dans le betslip.")
        return False
 
    try:
        btns = bet_item.find_elements(By.TAG_NAME, 'button')
        if not btns:
            return False
        close_btn = btns[0]
        try:
            close_btn.click()
        except Exception:
            try:
                driver.execute_script('arguments[0].click();', close_btn)
            except Exception:
                return False

        # attendre la disparition de l'élément betslip (si possible)
        try:
            WebDriverWait(driver, wait).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')) == 0
            )
        except Exception:
            pass
        return True
    except Exception:
        return False


def click_clear_if_in_sidebar(driver):
    """Vérifie la présence du bouton 'Tout effacer' dans `right-sidebar` et clique dessus.
    Retourne True si le clic a été effectué, False sinon.
    """
    log("[PlacerPariProps] click_clear_if_in_sidebar start", "debug")
    try:
        sidebar = driver.find_element(By.ID, 'right-sidebar')
    except Exception:
        return False

    try:
        clear_btn = sidebar.find_element(By.XPATH, ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tout effacer')]")
    except Exception:
        return False

    try:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clear_btn)
        except Exception:
            log("[PlacerPariProps] click_clear_if_in_sidebar: scrollIntoView failed", "debug")
            pass
        try:
            clear_btn.click()
            log("[PlacerPariProps] click_clear_if_in_sidebar: clicked clear_btn", "debug")
        except Exception:
            try:
                driver.execute_script('arguments[0].click();', clear_btn)
                log("[PlacerPariProps] click_clear_if_in_sidebar: clicked clear_btn via JS", "debug")
            except Exception:
                log("[PlacerPariProps] click_clear_if_in_sidebar: failed to click clear_btn", "error")
                return False
        time.sleep(0.3)
        return True
    except Exception as e:
        log(f"[PlacerPariProps] click_clear_if_in_sidebar error: {e}", "error")
        return False


def placer_pari(driver, codeList):
    """
    Fonction pour placer un pari sur 1xBet
        :param mise: Montant de la mise
    :param c ote_min: Cote minimum acceptée (optionnel)
    :return: Dictionnaire avec le résultat de l'opération
    """
    donnees_test = []
    log(f"[PlacerPariProps] placer_pari start codeList_type={type(codeList)} len={len(codeList) if hasattr(codeList,'__len__') else 'n/a'}", "debug")
    while codeList != []:
        # Récupérer le premier élément de la liste (dictionnaire de pari)
        matches_list = codeList['matches']
        donnees_test = matches_list[0] if matches_list else {}
        log(f"[PlacerPariProps] matches_list type={type(matches_list)} length={len(matches_list) if hasattr(matches_list,'__len__') else 'n/a'}", "debug")
        log(f"[PlacerPariProps] donnees_test keys={list(donnees_test.keys()) if isinstance(donnees_test, dict) else type(donnees_test)}", "debug")
        print("=== DONNÉES ===")
        # Support du format classique et du format NBA player-props
        # Format attendu NBA (exemple):
        # {
        #   "date": "25/09/2025",
        #   "player_name": "LeBron James",
        #   "prop_type": "Points",
        #   "line": 27.5,
        #   "over_under": "Over",
        # }
        if 'player_name' in donnees_test:
            print(f"Player: {donnees_test.get('player_name')}")
            print(f"Teams: {donnees_test.get('equipe_1')} - {donnees_test.get('equipe_2')}")
            print(f"Prop type: {donnees_test.get('prop_type')}")
            print(f"Line: {donnees_test.get('line')}")
            print(f"Over/Under: {donnees_test.get('over_under')}")
            print("=" * 50)

            # Construire des valeurs compatibles avec le reste du flux
            player_name = donnees_test.get('player_name')
            teams = donnees_test.get('equipe_1', '') + ' - ' + donnees_test.get('equipe_2', '')
            # teams attendu au format 'TeamA - TeamB'
            if ' - ' in teams:
                equipe1, equipe2 = [t.strip() for t in teams.split(' - ', 1)]
            else:
                equipe1 = teams
                equipe2 = ''

            categorie = 'Player Props'
            type_de_pari = donnees_test.get('prop_type')
            # selection exemple: 'LeBron James - Points Over 27.5'
            line_val = donnees_test.get('line')
            over_under = donnees_test.get('over_under')
            selection = f"{player_name} - {type_de_pari} {over_under} {line_val}"
            config.tipster = donnees_test.get('tipster', '')
            config.match_name = teams
            # Mettre la cote dans config.cote si nécessaire
            try:
                config.cote = float(donnees_test.get('odds'))
            except Exception:
                config.cote = donnees_test.get('odds')

        else:
            print(f"Match: {donnees_test.get('equipe_1')} vs {donnees_test.get('equipe_2')}")
            print(f"Date: {donnees_test.get('date')}")
            print(f"Catégorie de pari: {donnees_test.get('categorie')}")
            print(f"Type de pari: {donnees_test.get('type_de_pari')}")
            print(f"Sélection: {donnees_test.get('selection')}")
            print(f"Tipster: {donnees_test.get('tipster')}")
            print("=" * 50)
            equipe1 = donnees_test.get('equipe_1')
            equipe2 = donnees_test.get('equipe_2')
            categorie = donnees_test.get('categorie')
            type_de_pari = donnees_test.get('type_de_pari')
            selection = donnees_test.get('selection')  # "Plus De 20.5"
            config.tipster = donnees_test.get('tipster')
            config.match_name = f"{equipe1} - {equipe2}"
        find_match = False
        url_nba = 'https://stake.bet/fr/sports/basketball/usa/nba'
        log(f"[PlacerPariProps] Navigating to {url_nba}", "debug")
        driver.get(url_nba)
        # ZONE LIST DE MATCH
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'fixture-wrapper')))
        except Exception as e:
            print(f'Erreur lors de la recherche du bouton de recherche: {str(e)}')
            exit()
        else:

            # Attendre jusqu'à 5s l'apparition d'un bouton optionnel et cliquer si présent,
            # sinon continuer normalement.
            try:
                opt_btn_xpath = '//*[@id="svelte"]/div[1]/div[2]/div/div/button'
                log(f"[PlacerPariProps] waiting up to 5s for optional button {opt_btn_xpath}", "debug")
                opt_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, opt_btn_xpath))
                )
                if opt_btn:
                    try:
                        opt_btn.click()
                        log("[PlacerPariProps] optional button clicked", "debug")
                        time.sleep(0.3)
                    except Exception as e_click:
                        try:
                            driver.execute_script('arguments[0].click();', opt_btn)
                            log("[PlacerPariProps] optional button clicked via JS", "debug")
                        except Exception as e_js:
                            log(f"[PlacerPariProps] failed to click optional button: {e_click} / {e_js}", "error")
            except TimeoutException:
                log("[PlacerPariProps] optional button not present after 5s (Timeout)", "debug")
            except Exception as e:
                log(f"[PlacerPariProps] optional button wait error: {e}", "error")

            print("✅ Bloc des matchs chargé")
            log("[PlacerPariProps] fixture-wrapper presence confirmed", "debug")
            match_block = driver.find_element(By.CLASS_NAME, 'fixture-wrapper')
            
        # List des match
        try:
            match_list = match_block.find_elements(By.CLASS_NAME, 'fixture-preview')
        except Exception as e:
            print(f'Erreur lors de la recherche des matchs: {str(e)}')
        else:
            print(f"Nombre de matchs trouvés: {len(match_list)}")
            log(f"[PlacerPariProps] Nombre de matchs trouvés: {len(match_list)}", "debug")
            def _normalize_text(s):
                if not s:
                    return ''
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()

            # Première passe : comparaison locale (texte sans accents, insensible à la casse)
            for match in match_list:
                try:
                    teams_block = match.find_element(By.CLASS_NAME, 'teams')
                    teams = teams_block.find_elements(By.TAG_NAME, 'a')
                    home = f"{teams[0].text} vs {teams[1].text}"
                    target = f"{equipe1} vs {equipe2}"
                    print(f"Comparaison locale des matchs: '{home}' vs '{target}'")
                    log(f"[PlacerPariProps] local compare home_norm='{_normalize_text(home)}' target_norm='{_normalize_text(target)}'", "debug")
                    try:
                        if _normalize_text(home) == _normalize_text(target):
                            print(f"✅ Match trouvé (texte): {home}")
                            log(f"[PlacerPariProps] Match trouvé local: {home}", "info")
                            link = teams[0].get_attribute('href')
                            driver.get(link)
                            find_match = True
                            time.sleep(1)
                            # Attendre jusqu'à 5s l'apparition d'un bouton optionnel et cliquer si présent,
                            # sinon continuer normalement.
                            try:
                                opt_btn_xpath = '//*[@id="svelte"]/div[1]/div[2]/div/div/button'
                                log(f"[PlacerPariProps] waiting up to 5s for optional button {opt_btn_xpath}", "debug")
                                opt_btn = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, opt_btn_xpath))
                                )
                                if opt_btn:
                                    try:
                                        opt_btn.click()
                                        log("[PlacerPariProps] optional button clicked", "debug")
                                        time.sleep(0.3)
                                    except Exception as e_click:
                                        try:
                                            driver.execute_script('arguments[0].click();', opt_btn)
                                            log("[PlacerPariProps] optional button clicked via JS", "debug")
                                        except Exception as e_js:
                                            log(f"[PlacerPariProps] failed to click optional button: {e_click} / {e_js}", "error")
                            except TimeoutException:
                                log("[PlacerPariProps] optional button not present after 5s (Timeout)", "debug")
                            except Exception as e:
                                log(f"[PlacerPariProps] optional button wait error: {e}", "error")
                            break
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la comparaison locale: {e}")
                        continue
                except Exception:
                    continue

            # Si pas trouvé localement, faire une seconde passe en utilisant l'IA
            if not find_match:
                print("ℹ️ Aucun match trouvé localement — tentative avec l'IA...")
                for match in match_list:
                    try:
                        teams_block = match.find_element(By.CLASS_NAME, 'teams')
                        teams = teams_block.find_elements(By.TAG_NAME, 'a')
                        home = f"{teams[0].text} vs {teams[1].text}"
                        target = f"{equipe1} vs {equipe2}"
                        print(f"Comparaison IA des matchs: '{home}' vs '{target}'")
                        try:
                            log(f"[PlacerPariProps] compare_match_name call for '{home}' vs '{target}'", "debug")
                            if compare_match_name(home, target):
                                print(f"✅ Match trouvé (IA): {home}")
                                log(f"[PlacerPariProps] Match trouvé via IA: {home}", "info")
                                link = teams[0].get_attribute('href')
                                driver.get(link)
                                find_match = True
                                time.sleep(1)
                                # Attendre jusqu'à 5s l'apparition d'un bouton optionnel et cliquer si présent,
                                # sinon continuer normalement.
                                try:
                                    opt_btn_xpath = '//*[@id="svelte"]/div[1]/div[2]/div/div/button'
                                    log(f"[PlacerPariProps] waiting up to 5s for optional button {opt_btn_xpath}", "debug")
                                    opt_btn = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, opt_btn_xpath))
                                    )
                                    if opt_btn:
                                        try:
                                            opt_btn.click()
                                            log("[PlacerPariProps] optional button clicked", "debug")
                                            time.sleep(0.3)
                                        except Exception as e_click:
                                            try:
                                                driver.execute_script('arguments[0].click();', opt_btn)
                                                log("[PlacerPariProps] optional button clicked via JS", "debug")
                                            except Exception as e_js:
                                                log(f"[PlacerPariProps] failed to click optional button: {e_click} / {e_js}", "error")
                                except TimeoutException:
                                    log("[PlacerPariProps] optional button not present after 5s (Timeout)", "debug")
                                except Exception as e:
                                    log(f"[PlacerPariProps] optional button wait error: {e}", "error")      
                                break
                        except Exception as e:
                            print(f"⚠️ Erreur lors de l'appel IA compare_match_name: {e}")
                            continue
                    except Exception:
                        continue
    
        if find_match:
            # Attendre et cliquer sur le bouton "Props du Joueur" s'il existe
            try:
                xpath_expr = "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'props du joueur')]"
                WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_expr))
                )
                try:
                    props_btn = driver.find_element(By.XPATH, xpath_expr)
                    log("[PlacerPariProps] Props button is clickable", "debug")
                    props_btn.click()
                    log("[PlacerPariProps] Props button clicked", "debug")
                    time.sleep(1)
                except Exception as click_err:
                        print(f"⚠️ Bouton 'Props du Joueur' trouvé mais non cliquable: {click_err}")
                        log(f"[PlacerPariProps] Props button click error: {click_err}", "error")
                else:
                    clear_betslip_if_present(driver)
                    log("[PlacerPariProps] after clear_betslip_if_present", "debug")
                    try:
                        log("[PlacerPariProps] waiting for page-content containing team names", "debug")
                        WebDriverWait(driver, 8).until(
                            lambda d: any(
                                ((equipe1 and equipe1 in el.text) or (equipe2 and equipe2 in el.text))
                                for el in d.find_elements(By.CLASS_NAME, 'main-content')
                            )
                        )

                        # Conteneur principal des joueurs (varie selon le site)
                        log("[PlacerPariProps] locating players blocks (class 'players')", "debug")
                        players_blocks = driver.find_elements(By.CLASS_NAME, 'players')
                        log(f"[PlacerPariProps] players_blocks found: {len(players_blocks)}", "debug")
                        players = []
                        for idx_block, players_block in enumerate(players_blocks):
                            log(f"[PlacerPariProps] processing players_block #{idx_block}", "debug")
                            # Récupérer uniquement les divs enfants de premier niveau
                            player_divs = players_block.find_elements(By.XPATH, './div')
                            log(f"[PlacerPariProps] player_divs found in block #{idx_block}: {len(player_divs)}", "debug")
                            for idx_pd, pd in enumerate(player_divs):
                                try:
                                    log(f"[PlacerPariProps] processing player div #{idx_pd} in block #{idx_block}", "debug")
                                    text = pd.text.strip()
                                    log(f"[PlacerPariProps] pd.text (first100): {repr(text)[:100]}", "debug")
                                    if not text:
                                        log(f"[PlacerPariProps] pd.text empty, skipping div #{idx_pd}", "debug")
                                        continue

                                    # Tenter d'extraire le nom du joueur depuis un lien ou un élément dédié
                                    try:
                                        name_el = pd.find_element(By.CLASS_NAME, "header")
                                        player_name = name_el.text.strip()
                                        log(f"[PlacerPariProps] name_el found for div #{idx_pd}: {player_name}", "debug")
                                    except Exception as e_name:
                                        # Fallback : première ligne de texte
                                        player_name = text.splitlines()[0]
                                        log(f"[PlacerPariProps] name_el not found for div #{idx_pd}, fallback name='{player_name}' (error: {e_name})", "debug")

                                    players.append({
                                        'element': pd,
                                        'name': player_name,
                                        'raw_text': text
                                    })
                                    log(f"[PlacerPariProps] appended player #{idx_pd}: {player_name}", "debug")
                                except Exception as e_pd:
                                    log(f"[PlacerPariProps] exception processing player div #{idx_pd} in block #{idx_block}: {e_pd}", "error")
                                    continue

                    except Exception as e:
                        print(f"⚠️ Impossible d'extraire la liste des joueurs: {e}")
                    log(f"[PlacerPariProps] players collected: {len(players) if 'players' in locals() else 0}", "debug")
                    # Si nous avons un player_name cible, comparer avec GPT pour trouver le bon joueur
                    try:
                        if 'player_name' in donnees_test and players:
                            target = donnees_test.get('player_name')
                            found_player = None

                            def _normalize_name(s):
                                if not s:
                                    return ''
                                s = unicodedata.normalize('NFD', s)
                                s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
                                s = re.sub(r'[^A-Za-z0-9 ]+', ' ', s).lower()
                                s = re.sub(r'\s+', ' ', s).strip()
                                return s

                            # Première passe : comparaison locale (égalité normalisée puis fuzzy)
                            n_target = _normalize_name(target)
                            for p in players:
                                try:
                                    n_p = _normalize_name(p['name'])
                                    if n_target and n_p:
                                        if n_target == n_p:
                                            found_player = p
                                            print(f"✅ Joueur trouvé (texte exact): {p['name']} pour cible '{target}'")
                                            log(f"[PlacerPariProps] Joueur trouvé exact: {p['name']} pour target '{target}'", "info")
                                            break
                                        score = SequenceMatcher(None, n_target, n_p).ratio()
                                        if score >= 0.85:
                                            found_player = p
                                            print(f"✅ Joueur trouvé (fuzzy {score:.2f}): {p['name']} pour cible '{target}'")
                                            log(f"[PlacerPariProps] Joueur trouvé fuzzy ({score:.2f}): {p['name']} pour target '{target}'", "info")
                                            break
                                except Exception:
                                    continue

                            # Si pas trouvé localement, deuxième passe : fallback IA
                            if not found_player:
                                print("ℹ️ Aucun joueur trouvé localement — tentative avec l'IA...")
                                for p in players:
                                    try:
                                        match = False
                                        try:
                                            match = compare_player_name(target, p['name'])
                                        except Exception as e:
                                            print(f"⚠️ Erreur lors de la comparaison IA des noms: {e}")
                                            match = False
                                        if match:
                                            found_player = p
                                            print(f"✅ Joueur trouvé (IA): {p['name']} pour cible '{target}'")
                                            log(f"[PlacerPariProps] Joueur trouvé IA: {p['name']} pour target '{target}'", "info")
                                            break
                                    except Exception:
                                        continue

                            if found_player:
                                try:
                                    el = found_player['element']
                                    # Scroll element into view and click
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                                    time.sleep(0.5)
                                    el.click()
                                    log(f"[PlacerPariProps] clicked on found player element: {found_player.get('name', 'unknown')}", "debug")
                                    
                                except Exception as e:
                                    print(f"⚠️ Impossible de cliquer sur le joueur trouvé: {e}")
                                    log(f"[PlacerPariProps] Error clicking found player: {e}", "error")
                            else:
                                print(f"ℹ️ Aucun joueur correspondant trouvé pour '{target}'")
                            # Après avoir cliqué sur le joueur, attendre le panneau des props ouvert
                            try:
                                # Attendre un container avec classes 'content' et 'is-open' DANS l'élément cliqué `el`
                                WebDriverWait(driver, 8).until(
                                    lambda d: len(el.find_elements(By.CSS_SELECTOR, 'div.content.is-open')) > 0
                                )
                                content_containers = el.find_elements(By.CSS_SELECTOR, 'div.content.is-open')

                                log(f"[PlacerPariProps] content_containers found: {len(content_containers)}", "debug")

                                selected_div = None
                                found_number = None
                                for cc in content_containers:
                                    # Chercher récursivement les divs avec une classe contenant 'flex'
                                    all_flex = cc.find_elements(By.XPATH, './/div[contains(@class, "flex")]')
                                    # Fallback: recherche via CSS si XPath ne trouve rien
                                    if not all_flex:
                                        all_flex = cc.find_elements(By.CSS_SELECTOR, 'div.flex')

                                    # Calculer la profondeur relative à `cc` pour chaque flex
                                    depths = []
                                    for fd in all_flex:
                                        try:
                                            depth = driver.execute_script(
                                                "var start=arguments[0], root=arguments[1]; var d=0; var el=start; while(el && el!==root){el=el.parentElement; d++;} return d;",
                                                fd, cc
                                            )
                                        except Exception:
                                            depth = 9999
                                        depths.append((fd, depth))

                                    if depths:
                                        min_depth = min(d for (_f, d) in depths)
                                        flex_divs = [f for (f, d) in depths if d == min_depth]
                                    else:
                                        flex_divs = []

                                    for idx, fd in enumerate(flex_divs):
                                        try:
                                            fd_text = fd.text.strip()
                                            if not fd_text:
                                                continue
                                            # Normalisation simple pour comparaison locale
                                            def _normalize_prop(s):
                                                if not s:
                                                    return ''
                                                s = unicodedata.normalize('NFD', s)
                                                s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
                                                s = re.sub(r'[^A-Za-z0-9 ]+', ' ', s).lower()
                                                s = re.sub(r'\s+', ' ', s).strip()
                                                return s

                                            n_target_prop = _normalize_prop(type_de_pari or '')
                                            # prendre la première ligne du bloc comme libellé principal
                                            first_line = fd_text.splitlines()[0] if fd_text else ''
                                            n_fd = _normalize_prop(first_line)

                                            # Première passe : comparaison locale stricte (égalité normalisée)
                                            match_prop = False
                                            if n_target_prop and n_fd and n_target_prop == n_fd:
                                                match_prop = True
                                                print(f"✅ Prop match local: '{first_line}' == '{type_de_pari}'")

                                            # Si pas trouvé localement, on laissera l'IA décider dans une seconde passe
                                            if match_prop:
                                                selected_div = fd
                                                log(f"[PlacerPariProps] Prop match local selected: {first_line}", "debug")
                                                break
                                        except Exception:
                                            continue
                                        # Si aucun selected_div trouvé avec la passe locale, faire une passe IA
                                    if not selected_div:
                                        for fd in flex_divs:
                                            try:
                                                fd_text = fd.text.strip()
                                                if not fd_text:
                                                    continue
                                                try:
                                                    match_prop = compare_prop_name(type_de_pari or '', fd_text)
                                                except Exception as e:
                                                    print(f"⚠️ Erreur compare_prop_name: {e}")
                                                    match_prop = False

                                                if match_prop:
                                                    selected_div = fd
                                                    log(f"[PlacerPariProps] Prop match IA selected: {fd_text.splitlines()[0] if fd_text else ''}", "debug")
                                                    break
                                            except Exception:
                                                continue
                                            
                                    if selected_div:
                                        log(f"[PlacerPariProps] entered selected_div block for type_de_pari='{type_de_pari}' line_val={line_val}", "debug")
                                        log(f"[PlacerPariProps] selected_div text (first200): {repr(selected_div.text)[:200]}", "debug")

                                        # Mettre la div sélectionnée au centre de l'écran, puis extraire la valeur NUMÉRIQUE
                                        try:
                                            log("[PlacerPariProps] scrolling selected_div into view", "debug")
                                            try:
                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selected_div)
                                            except Exception as e_scroll:
                                                log(f"[PlacerPariProps] scrollIntoView failed: {e_scroll}", "debug")
                                            fd_text_local = selected_div.text.strip()
                                            log(f"[PlacerPariProps] fd_text_local (first200): {repr(fd_text_local)[:200]}", "debug")
                                            m = re.search(r"(\d+[.,]?\d*)", fd_text_local)
                                            if m:
                                                found_number = m.group(1).replace(',', '.')
                                                print(f"✅ Nombre trouvé dans la div matching: {found_number}")
                                                log(f"[PlacerPariProps] found_number in selected_div: {found_number}", "debug")
                                            else:
                                                print(f"⚠️ Aucun nombre trouvé dans la div matching pour '{type_de_pari}' (texte: {fd_text_local.splitlines()[0] if fd_text_local else 'n/a'})")
                                                log("[PlacerPariProps] no numeric match in selected_div text", "debug")
                                        except Exception as e:
                                            print(f"⚠️ Erreur lors de l'extraction du nombre dans la div matching: {e}")
                                            log(f"[PlacerPariProps] exception extracting number from selected_div: {e}", "error")

                                        # Si une ligne cible est fournie, on compare et on ajuste en cliquant sur les boutons
                                        try:
                                            desired_line = None
                                            try:
                                                desired_line = float(line_val)
                                            except Exception:
                                                pass
                                            log(f"[PlacerPariProps] parsed desired_line={desired_line}", "debug")

                                            if desired_line is not None and found_number is not None:
                                                # Nouvel UI: bouton affichant la valeur + dropdown d'options.
                                                found = False
                                                cur_val = None
                                                try:
                                                    log("[PlacerPariProps] searching for numeric display button inside selected_div", "debug")
                                                    # Chercher un bouton descendant qui affiche une valeur numérique
                                                    num_btn = None
                                                    num_btn_val = None
                                                    try:
                                                        possible_btns = selected_div.find_elements(By.TAG_NAME, 'button')
                                                    except Exception as e_pos:
                                                        possible_btns = []
                                                        log(f"[PlacerPariProps] error finding possible_btns: {e_pos}", "debug")

                                                    log(f"[PlacerPariProps] possible_btns count: {len(possible_btns)}", "debug")
                                                    for idx_bbtn, bbtn in enumerate(possible_btns):
                                                        try:
                                                            btxt = bbtn.text.strip()
                                                            log(f"[PlacerPariProps] possible_btn #{idx_bbtn} text (first50): {repr(btxt)[:50]}", "debug")
                                                            mbtn = re.search(r"(\d+[.,]?\d*)", btxt)
                                                            if mbtn:
                                                                num_btn = bbtn
                                                                num_btn_val = float(mbtn.group(1).replace(',', '.'))
                                                                log(f"[PlacerPariProps] numeric button candidate #{idx_bbtn} val={num_btn_val}", "debug")
                                                                break
                                                        except Exception as e_bbtn:
                                                            log(f"[PlacerPariProps] error inspecting possible_btn #{idx_bbtn}: {e_bbtn}", "debug")
                                                            continue

                                                    if num_btn:
                                                        log(f"[PlacerPariProps] numeric display button found value={num_btn_val}", "debug")
                                                        cur_val = num_btn_val
                                                        # Si la valeur affichée correspond déjà à la ligne désirée
                                                        if abs(cur_val - desired_line) < 1e-6:
                                                            log("[PlacerPariProps] numeric display already matches desired_line", "debug")
                                                            found = True
                                                        else:
                                                            # Ouvrir le dropdown et tenter de cliquer sur l'option exacte
                                                            try:
                                                                log("[PlacerPariProps] attempting to open numeric dropdown", "debug")
                                                                try:
                                                                    num_btn.click()
                                                                except Exception:
                                                                    driver.execute_script('arguments[0].click();', num_btn)
                                                                log("[PlacerPariProps] numeric display button clicked to open dropdown", "debug")
                                                                # Attendre l'apparition des options dans le dropdown
                                                                WebDriverWait(driver, 3).until(
                                                                    lambda d: len(d.find_elements(By.CSS_SELECTOR, '.dropdown-scroll-content button')) > 0
                                                                )
                                                                options = driver.find_elements(By.CSS_SELECTOR, '.dropdown-scroll-content button')
                                                                log(f"[PlacerPariProps] dropdown options count: {len(options)}", "debug")
                                                                match_opt = None
                                                                for idx_opt, opt in enumerate(options):
                                                                    try:
                                                                        try:
                                                                            span = opt.find_element(By.CSS_SELECTOR, 'span.ds-body-md-strong')
                                                                            opt_text = span.text.strip()
                                                                        except Exception:
                                                                            opt_text = opt.text.strip()
                                                                        log(f"[PlacerPariProps] option #{idx_opt} text (first50): {repr(opt_text)[:50]}", "debug")
                                                                        mopt = re.search(r"(\d+[.,]?\d*)", opt_text)
                                                                        if mopt:
                                                                            opt_val = float(mopt.group(1).replace(',', '.'))
                                                                            log(f"[PlacerPariProps] option #{idx_opt} numeric={opt_val}", "debug")
                                                                            if abs(opt_val - desired_line) < 1e-6:
                                                                                match_opt = opt
                                                                                log(f"[PlacerPariProps] found matching option #{idx_opt} -> {opt_val}", "debug")
                                                                                break
                                                                    except Exception as e_opt:
                                                                        log(f"[PlacerPariProps] error reading option #{idx_opt}: {e_opt}", "debug")
                                                                        continue

                                                                if match_opt:
                                                                    try:
                                                                        match_opt.click()
                                                                    except Exception:
                                                                        try:
                                                                            driver.execute_script('arguments[0].click();', match_opt)
                                                                        except Exception as e_clickopt:
                                                                            log(f"[PlacerPariProps] failed to click dropdown option: {e_clickopt}", "error")
                                                                    # petit délai pour que le DOM se réinitialise après la sélection
                                                                    time.sleep(0.3)
                                                                    # Instrumentation post-selection : snapshot du DOM et recherche immédiate des boutons outcome
                                                                    try:
                                                                        time.sleep(0.5)
                                                                    except Exception:
                                                                        pass
                                                                    try:
                                                                        try:
                                                                            oh = selected_div.get_attribute('outerHTML') or ''
                                                                            log(f"[PlacerPariProps] selected_div outerHTML (first2000): {oh[:2000]}", "debug")
                                                                        except Exception as e_oh:
                                                                            log(f"[PlacerPariProps] error getting selected_div outerHTML: {e_oh}", "debug")

                                                                        try:
                                                                            post_local = selected_div.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                            log(f"[PlacerPariProps] post-dropdown local outcome count: {len(post_local)}", "debug")
                                                                            for idx_p, pb in enumerate(post_local[:8]):
                                                                                try:
                                                                                    aria_pb = (pb.get_attribute('aria-label') or '')[:200]
                                                                                    txt_pb = (pb.text or '')[:200]
                                                                                    log(f"[PlacerPariProps] post-dropdown local outcome #{idx_p} aria='{aria_pb}' text='{txt_pb}'", "debug")
                                                                                except Exception as e_pb:
                                                                                    log(f"[PlacerPariProps] error reading post-local outcome #{idx_p}: {e_pb}", "debug")
                                                                        except Exception as e_postloc:
                                                                            log(f"[PlacerPariProps] error finding post-dropdown local outcomes: {e_postloc}", "debug")

                                                                        try:
                                                                            post_global = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                            log(f"[PlacerPariProps] post-dropdown global outcome count: {len(post_global)}", "debug")
                                                                        except Exception as e_postg:
                                                                            log(f"[PlacerPariProps] error finding post-dropdown global outcomes: {e_postg}", "debug")
                                                                    except Exception as e_postin:
                                                                        log(f"[PlacerPariProps] unexpected error in post-dropdown instrumentation: {e_postin}", "debug")

                                                                    log(f"[PlacerPariProps] selected dropdown option {desired_line}", "debug")
                                                                    found = True
                                                                    cur_val = desired_line

                                                                    # Si l'option a été sélectionnée via le dropdown, tenter aussi
                                                                    # immédiatement la sélection Over/Under (prise en charge du cas manquant)
                                                                    try:
                                                                        over_under_choice = (over_under or '')
                                                                        ou = str(over_under_choice).strip().lower()
                                                                        log(f"[PlacerPariProps] post-dropdown Over/Under attempt (ou={ou})", "debug")

                                                                        over_btn = None
                                                                        under_btn = None

                                                                        # Chercher localement les boutons outcome
                                                                        try:
                                                                            outcome_btns = selected_div.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                            log(f"[PlacerPariProps] post-dropdown local outcome count: {len(outcome_btns)}", "debug")
                                                                        except Exception as e_locp:
                                                                            outcome_btns = []
                                                                            log(f"[PlacerPariProps] error finding post-dropdown local outcome btns: {e_locp}", "debug")

                                                                        for b in outcome_btns:
                                                                            try:
                                                                                aria = (b.get_attribute('aria-label') or '').lower()
                                                                                try:
                                                                                    name_el = b.find_element(By.CSS_SELECTOR, '[data-testid="outcome-button-name"], span')
                                                                                    txt = name_el.text.strip().lower()
                                                                                except Exception:
                                                                                    txt = (b.text or '').strip().lower()
                                                                                if 'plus' in aria or 'over' in aria or 'plus' in txt or 'over' in txt:
                                                                                    over_btn = b
                                                                                if 'moins' in aria or 'under' in aria or 'moins' in txt or 'under' in txt:
                                                                                    under_btn = b
                                                                            except Exception as e_b:
                                                                                log(f"[PlacerPariProps] error inspecting post-dropdown outcome btn: {e_b}", "debug")

                                                                        # Fallback global si nécessaire
                                                                        if not over_btn or not under_btn:
                                                                            try:
                                                                                global_btns = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                            except Exception as e_globp:
                                                                                global_btns = []
                                                                                log(f"[PlacerPariProps] error finding post-dropdown global outcome btns: {e_globp}", "debug")
                                                                            for gb in global_btns:
                                                                                try:
                                                                                    aria = (gb.get_attribute('aria-label') or '').lower()
                                                                                    txt = (gb.text or '').strip().lower()
                                                                                    if not over_btn and ('plus' in aria or 'plus' in txt or 'over' in aria or 'over' in txt):
                                                                                        over_btn = gb
                                                                                    if not under_btn and ('moins' in aria or 'moins' in txt or 'under' in aria or 'under' in txt):
                                                                                        under_btn = gb
                                                                                except Exception:
                                                                                    continue

                                                                        # Click selon le choix
                                                                        try:
                                                                            if ou.startswith('over') and over_btn:
                                                                                try:
                                                                                    over_btn.click()
                                                                                except Exception:
                                                                                    try:
                                                                                        driver.execute_script('arguments[0].click();', over_btn)
                                                                                    except Exception as e_click1:
                                                                                        log(f"[PlacerPariProps] failed click post-dropdown over_btn: {e_click1}", "debug")
                                                                                log("[PlacerPariProps] post-dropdown clicked Over attempt", "debug")
                                                                            elif ou.startswith('under') and under_btn:
                                                                                try:
                                                                                    under_btn.click()
                                                                                except Exception:
                                                                                    try:
                                                                                        driver.execute_script('arguments[0].click();', under_btn)
                                                                                    except Exception as e_click2:
                                                                                        log(f"[PlacerPariProps] failed click post-dropdown under_btn: {e_click2}", "debug")
                                                                                log("[PlacerPariProps] post-dropdown clicked Under attempt", "debug")
                                                                            else:
                                                                                log(f"[PlacerPariProps] post-dropdown no Over/Under buttons found for ou={ou}", "debug")
                                                                        except Exception as e_postclick:
                                                                            log(f"[PlacerPariProps] error during post-dropdown Over/Under click: {e_postclick}", "error")

                                                                        # Attendre le betslip si la sélection a déclenché son affichage
                                                                        try:
                                                                            betlist_el = WebDriverWait(driver, 5).until(
                                                                                EC.presence_of_element_located((By.CLASS_NAME, 'betlist'))
                                                                            )
                                                                            try:
                                                                                WebDriverWait(driver, 5).until(
                                                                                    lambda d: len(betlist_el.find_elements(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')) > 0
                                                                                )
                                                                                log("[PlacerPariProps] betslip detected after post-dropdown click", "debug")
                                                                            except Exception as e_btw:
                                                                                log(f"[PlacerPariProps] betlist present but no items after post-dropdown: {e_btw}", "debug")
                                                                        except Exception as e_nobetp:
                                                                            log(f"[PlacerPariProps] no betlist detected after post-dropdown: {e_nobetp}", "debug")
                                                                    except Exception as e_post_over:
                                                                        log(f"[PlacerPariProps] unexpected error in post-dropdown Over/Under flow: {e_post_over}", "error")
                                                                else:
                                                                    log(f"[PlacerPariProps] desired value {desired_line} not found in dropdown options", "debug")
                                                            except Exception as e_dd:
                                                                log(f"[PlacerPariProps] error handling numeric dropdown: {e_dd}", "error")
                                                    else:
                                                        log("[PlacerPariProps] no numeric display button found in selected_div", "debug")
                                                except Exception as e_num:
                                                    log(f"[PlacerPariProps] numeric dropdown detection error: {e_num}", "error")

                                                # Si on n'a pas pu sélectionner via dropdown, retomber sur la lecture texte existante
                                                if not found:
                                                    try:
                                                        current = float(found_number)
                                                    except Exception:
                                                        current = None

                                                    log(f"[PlacerPariProps] desired_line={desired_line} found_number={found_number} current={current}", "debug")

                                                    if current is not None and abs(current - desired_line) < 1e-6:
                                                        print(f"ℹ️ La ligne actuelle {current} correspond à la ligne souhaitée {desired_line}.")
                                                    else:
                                                        # Rechercher boutons à l'intérieur de la div sélectionnée
                                                        try:
                                                            btns = selected_div.find_elements(By.TAG_NAME, 'button')
                                                        except Exception:
                                                            btns = []

                                                        dec_btn = btns[0] if len(btns) >= 1 else None
                                                        inc_btn = btns[1] if len(btns) >= 2 else None

                                                        def _read_current_number():
                                                            try:
                                                                txt = selected_div.text
                                                                mm = re.search(r"(\d+[.,]?\d*)", txt)
                                                                return float(mm.group(1).replace(',', '.')) if mm else None
                                                            except Exception:
                                                                return None

                                                        found = False
                                                        max_clicks = 8

                                                        # Choisir le sens d'ajustement selon la valeur actuelle
                                                        try:
                                                            cur_val = _read_current_number()
                                                        except Exception:
                                                            cur_val = None

                                                        # Si current non lisible, tenter de lire depuis found_number
                                                        if cur_val is None:
                                                            try:
                                                                cur_val = float(found_number)
                                                            except Exception:
                                                                cur_val = None

                                                    if cur_val is None:
                                                        print("⚠️ Impossible de lire la valeur actuelle pour décider du bouton à cliquer.")
                                                    else:
                                                        # Si la valeur actuelle est plus grande, il faut diminuer
                                                        if cur_val > desired_line:
                                                            primary_btn, secondary_btn = dec_btn, inc_btn
                                                            primary_name, secondary_name = 'diminuer', 'augmenter'
                                                        else:
                                                            primary_btn, secondary_btn = inc_btn, dec_btn
                                                            primary_name, secondary_name = 'augmenter', 'diminuer'

                                                        # Essayer d'abord le bouton principal
                                                        if primary_btn:
                                                            log(f"[PlacerPariProps] attempting primary_btn clicks ({primary_name}) up to {max_clicks}", "debug")
                                                            for i in range(max_clicks):
                                                                try:
                                                                    primary_btn.click()
                                                                except Exception:
                                                                    try:
                                                                        driver.execute_script('arguments[0].click();', primary_btn)
                                                                    except Exception:
                                                                        pass
                                                                log(f"[PlacerPariProps] primary_btn click attempt {i+1} ({primary_name})", "debug")
                                                                time.sleep(0.4)
                                                                cur = _read_current_number()
                                                                log(f"[PlacerPariProps] after click, current={cur}", "debug")
                                                                if cur is not None and abs(cur - desired_line) < 1e-6:
                                                                    print(f"✅ Ligne atteinte après {i+1} clics sur {primary_name}: {cur}")
                                                                    log(f"[PlacerPariProps] Ligne atteinte after {i+1} clicks ({primary_name}): {cur}", "info")
                                                                    found = True
                                                                    break

                                                        # Si pas trouvé, tenter le bouton secondaire
                                                        if not found and secondary_btn:
                                                            for i in range(max_clicks):
                                                                try:
                                                                    secondary_btn.click()
                                                                except Exception:
                                                                    try:
                                                                        driver.execute_script('arguments[0].click();', secondary_btn)
                                                                    except Exception:
                                                                        pass
                                                                time.sleep(0.4)
                                                                cur = _read_current_number()
                                                                if cur is not None and abs(cur - desired_line) < 1e-6:
                                                                    print(f"✅ Ligne atteinte après {i+1} clics sur {secondary_name}: {cur}")
                                                                    found = True
                                                                    break

                                                        if not found:
                                                            print(f"⚠️ Impossible d'atteindre la ligne souhaitée {desired_line} (valeur actuelle approximative: {cur_val}) après essais.")
                                                        else:
                                                            # Si la ligne désirée a été atteinte, cliquer sur le bouton Over/Under
                                                            try:
                                                                over_under_choice = (over_under or '')
                                                                # Normaliser
                                                                ou = str(over_under_choice).strip().lower()
                                                                log(f"[PlacerPariProps] entering Over/Under selection (ou={ou} desired_line={desired_line} cur_val={cur_val})", "debug")

                                                                # 1) Rechercher localement des boutons outcome (data-testid)
                                                                over_btn = None
                                                                under_btn = None
                                                                try:
                                                                    outcome_btns = selected_div.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                    log(f"[PlacerPariProps] outcome_btns count: {len(outcome_btns)}", "debug")
                                                                except Exception as e_out:
                                                                    outcome_btns = []
                                                                    log(f"[PlacerPariProps] error finding outcome_btns: {e_out}", "debug")

                                                                for idx_b, b in enumerate(outcome_btns):
                                                                    try:
                                                                        aria = (b.get_attribute('aria-label') or '').lower()
                                                                        txt = ''
                                                                        try:
                                                                            name_el = b.find_element(By.CSS_SELECTOR, '[data-testid="outcome-button-name"], span')
                                                                            txt = name_el.text.strip().lower()
                                                                        except Exception:
                                                                            try:
                                                                                txt = b.text.strip().lower()
                                                                            except Exception:
                                                                                txt = ''
                                                                        log(f"[PlacerPariProps] outcome_btn #{idx_b} aria='{aria}' text='{txt[:100]}'", "debug")
                                                                        if 'plus' in aria or 'over' in aria or 'plus' in txt or 'over' in txt:
                                                                            over_btn = b
                                                                        if 'moins' in aria or 'under' in aria or 'moins' in txt or 'under' in txt:
                                                                            under_btn = b
                                                                    except Exception as e_binfo:
                                                                        log(f"[PlacerPariProps] error inspecting outcome_btn #{idx_b}: {e_binfo}", "debug")
                                                                        continue

                                                                log(f"[PlacerPariProps] after outcome scan over_btn={'yes' if over_btn else 'no'} under_btn={'yes' if under_btn else 'no'}", "debug")

                                                                # 2) Fallback local: tous les boutons dans selected_div
                                                                if not over_btn or not under_btn:
                                                                    try:
                                                                        all_btns = selected_div.find_elements(By.TAG_NAME, 'button')
                                                                        log(f"[PlacerPariProps] all_btns count in selected_div: {len(all_btns)}", "debug")
                                                                    except Exception as e_all:
                                                                        all_btns = []
                                                                        log(f"[PlacerPariProps] error finding all_btns: {e_all}", "debug")
                                                                    for idx_b, b in enumerate(all_btns):
                                                                        try:
                                                                            aria = (b.get_attribute('aria-label') or '').lower()
                                                                            txt = b.text.strip().lower()
                                                                            log(f"[PlacerPariProps] all_btn #{idx_b} aria='{aria}' text='{txt[:100]}'", "debug")
                                                                            if not over_btn and ('plus' in aria or 'plus' in txt or 'over' in aria or 'over' in txt):
                                                                                over_btn = b
                                                                            if not under_btn and ('moins' in aria or 'moins' in txt or 'under' in aria or 'under' in txt):
                                                                                under_btn = b
                                                                        except Exception as e_ab:
                                                                            log(f"[PlacerPariProps] error inspecting all_btn #{idx_b}: {e_ab}", "debug")
                                                                            continue

                                                                log(f"[PlacerPariProps] after local fallback over_btn={'yes' if over_btn else 'no'} under_btn={'yes' if under_btn else 'no'}", "debug")

                                                                # 3) Dernier fallback global: rechercher dans la page entière
                                                                if not over_btn or not under_btn:
                                                                    try:
                                                                        global_btns = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="fixture-outcome"]')
                                                                        log(f"[PlacerPariProps] global_btns count: {len(global_btns)}", "debug")
                                                                    except Exception as e_gl:
                                                                        global_btns = []
                                                                        log(f"[PlacerPariProps] error finding global_btns: {e_gl}", "debug")
                                                                    for idx_b, b in enumerate(global_btns):
                                                                        try:
                                                                            aria = (b.get_attribute('aria-label') or '').lower()
                                                                            txt = b.text.strip().lower()
                                                                            log(f"[PlacerPariProps] global_btn #{idx_b} aria='{aria}' text='{txt[:100]}'", "debug")
                                                                            if not over_btn and ('plus' in aria or 'plus' in txt or 'over' in aria or 'over' in txt):
                                                                                over_btn = b
                                                                            if not under_btn and ('moins' in aria or 'moins' in txt or 'under' in aria or 'under' in txt):
                                                                                under_btn = b
                                                                        except Exception as e_gb:
                                                                            log(f"[PlacerPariProps] error inspecting global_btn #{idx_b}: {e_gb}", "debug")
                                                                            continue

                                                            except Exception as e_select:
                                                                over_btn = None
                                                                under_btn = None
                                                                log(f"[PlacerPariProps] error finding Over/Under buttons: {e_select}", "error")

                                                            # Click selon le choix Over/Under
                                                            try:
                                                                log(f"[PlacerPariProps] will click ou='{ou}' over_btn={'yes' if over_btn else 'no'} under_btn={'yes' if under_btn else 'no'}", "debug")
                                                                if ou.startswith('over') and over_btn:
                                                                    try:
                                                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", over_btn)
                                                                    except Exception as e_sc:
                                                                        log(f"[PlacerPariProps] scrollIntoView over_btn failed: {e_sc}", "debug")
                                                                    try:
                                                                        over_btn.click()
                                                                        log("[PlacerPariProps] over_btn.click() called", "debug")
                                                                        print("✅ Clic sur Over effectué")
                                                                    except Exception:
                                                                        try:
                                                                            driver.execute_script('arguments[0].click();', over_btn)
                                                                            log("[PlacerPariProps] over_btn clicked via JS", "debug")
                                                                            print("✅ Clic sur Over effectué (via JS)")
                                                                        except Exception as e:
                                                                            log(f"[PlacerPariProps] Impossible de cliquer sur le bouton Over: {e}", "error")
                                                                elif ou.startswith('under') and under_btn:
                                                                    try:
                                                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", under_btn)
                                                                    except Exception as e_sc2:
                                                                        log(f"[PlacerPariProps] scrollIntoView under_btn failed: {e_sc2}", "debug")
                                                                    try:
                                                                        under_btn.click()
                                                                        log("[PlacerPariProps] under_btn.click() called", "debug")
                                                                        print("✅ Clic sur Under effectué")
                                                                    except Exception:
                                                                        try:
                                                                            driver.execute_script('arguments[0].click();', under_btn)
                                                                            log("[PlacerPariProps] under_btn clicked via JS", "debug")
                                                                            print("✅ Clic sur Under effectué (via JS)")
                                                                        except Exception as e:
                                                                            log(f"[PlacerPariProps] Impossible de cliquer sur le bouton Under: {e}", "error")
                                                                else:
                                                                    log(f"[PlacerPariProps] Aucun bouton Over/Under trouvé pour ou='{ou}'", "debug")
                                                            except Exception as e_click_ou:
                                                                log(f"[PlacerPariProps] error clicking Over/Under button: {e_click_ou}", "error")

                                                                # Vérifier que le betslip est affiché : attendre d'abord le container .betlist,
                                                                # puis la présence d'un enfant [data-testid="betslip-bet"] à l'intérieur.
                                                                try:
                                                                    betlist_el = WebDriverWait(driver, 8).until(
                                                                        EC.presence_of_element_located((By.CLASS_NAME, 'betlist'))
                                                                    )
                                                                    try:
                                                                        WebDriverWait(driver, 8).until(
                                                                            lambda d: len(betlist_el.find_elements(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')) > 0
                                                                        )
                                                                        # Récupérer le (unique) élément du betslip et afficher son contenu
                                                                        try:
                                                                            bet_item = betlist_el.find_element(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')
                                                                            time.sleep(1)
                                                                            try:
                                                                                items_texts = [bet_item.text.strip()]
                                                                            except Exception:
                                                                                items_texts = ['']
                                                                        except Exception:
                                                                            items_texts = []

                                                                        print('✅ Betslip détecté (element data-testid="betslip-bet") dans .betlist')
                                                                        # --- Calculer et remplir la mise dans le betslip ---
                                                                        time.sleep(2)
                                                                        try:
                                                                            # Récupérer la mise recommandée via Functions.GetMise.GetMise
                                                                            try:
                                                                                GetMise(driver)
                                                                                print(f"ℹ️ GetMise exécuté; config.mise={getattr(config, 'mise', None)}")
                                                                            except Exception as e:
                                                                                print(f"⚠️ GetMise erreur: {e}")
                                                                            # Pour compatibilité du flux existant, target_win reste None
                                                                            target_win = None
                                                                            # Récupérer la cote/payout depuis l'élément (si présent)
                                                                            odds_val = None
                                                                            try:
                                                                                odds_el = betlist_el.find_element(By.CSS_SELECTOR, '[data-testid="betslip-odds-payout"]')
                                                                                od_text = odds_el.text if odds_el else ''
                                                                                print(f"ℹ️ Texte des cotes/payout dans le betslip: '{od_text}'")
                                                                                m_od = re.search(r"(\d+[.,]?\d*)", od_text)
                                                                                if m_od:
                                                                                    odds_val = float(m_od.group(1).replace(',', '.'))
                                                                            except Exception as e:
                                                                                print(f"⚠️ Impossible d'extraire la cote/payout du betslip: {e}")
                                                                                odds_val = None

                                                                            # Si on a une cible de gain et une cote, calculer la stake
                                                                            stake = None
                                                                            if target_win is not None and odds_val:
                                                                                try:
                                                                                    stake = float(target_win) / float(odds_val) if float(odds_val) != 0 else None
                                                                                except Exception:
                                                                                    stake = None

                                                                            # Fallback: si pas de target_win, utiliser config.mise si fourni
                                                                            if stake is None and getattr(config, 'mise', None) is not None:
                                                                                try:
                                                                                    stake = float(config.mise)
                                                                                except Exception:
                                                                                    stake = None

                                                                            if stake is not None:
                                                                                # formater la stake raisonnablement (2 décimales)
                                                                                stake_str = f"{stake:.2f}"
                                                                                print(f"ℹ️ Mise calculée: {stake_str} (target_win={target_win}, odds={odds_val})")
                                                                                # trouver un champ input dans le bet_item
                                                                                try:
                                                                                    input_el = betlist_el.find_element(By.TAG_NAME, 'input')
                                                                                except Exception as e:
                                                                                    print(f"⚠️ Impossible de trouver le champ input pour la mise: {e}")
                                                                                    input_el = None

                                                                                if input_el:
                                                                                    try:
                                                                                        input_el.clear()
                                                                                    except Exception:
                                                                                        pass
                                                                                    try:
                                                                                        input_el.send_keys(stake_str)
                                                                                        print('✅ Champ mise rempli via send_keys')
                                                                                    except Exception:
                                                                                        # fallback JS set value + dispatch input event
                                                                                        try:
                                                                                            driver.execute_script(
                                                                                                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));",
                                                                                                input_el, stake_str
                                                                                            )
                                                                                            print('✅ Champ mise rempli via JS')
                                                                                        except Exception as e:
                                                                                            print('⚠️ Impossible de remplir le champ mise:', e)

                                                                                    # Après insertion de la mise, vérifier que le champ contient la valeur
                                                                                    try:
                                                                                        # Chercher un input plus spécifique si possible
                                                                                        try:
                                                                                            try:
                                                                                                input_el = betlist_el.find_element(By.CSS_SELECTOR, 'input[data-testid="input-bet-amount"]')
                                                                                            except Exception:
                                                                                                input_el = bet_item.find_element(By.CSS_SELECTOR, 'input[data-testid="input-bet-amount"]')
                                                                                        except Exception:
                                                                                            # fallback: garder l'input précédemment trouvé (variable input_el)
                                                                                            pass

                                                                                        def _get_input_val(el):
                                                                                            try:
                                                                                                return (el.get_attribute('value') or '').strip()
                                                                                            except Exception:
                                                                                                try:
                                                                                                    return (el.text or '').strip()
                                                                                                except Exception:
                                                                                                    return ''

                                                                                        success_input = False
                                                                                        last_read = None
                                                                                        # attendre un court instant que la valeur remonte dans l'UI
                                                                                        for _ in range(6):
                                                                                            try:
                                                                                                last_read = _get_input_val(input_el) if input_el else ''
                                                                                            except Exception:
                                                                                                last_read = ''
                                                                                            # vérifier aussi le montant estimé affiché
                                                                                            try:
                                                                                                est_el = betlist_el.find_element(By.CSS_SELECTOR, '[data-testid="single-bet-estimated-amount"]')
                                                                                                est_text = est_el.text.strip() if est_el else ''
                                                                                            except Exception:
                                                                                                est_text = ''
                                                                                            if last_read:
                                                                                                if last_read.replace(',', '.') == stake_str or last_read == stake_str:
                                                                                                    success_input = True
                                                                                                    break
                                                                                            if est_text and est_text not in ('€0.00', '0.00', '€0'):
                                                                                                success_input = True
                                                                                                break
                                                                                            time.sleep(0.3)

                                                                                        # Si pas encore ok, forcer via JS et redétecter
                                                                                        if not success_input and input_el:
                                                                                            try:
                                                                                                driver.execute_script(
                                                                                                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                                                                                                    input_el, stake_str
                                                                                                )
                                                                                                time.sleep(0.4)
                                                                                                try:
                                                                                                    last_read = _get_input_val(input_el)
                                                                                                except Exception:
                                                                                                    last_read = ''
                                                                                                if last_read and (last_read.replace(',', '.') == stake_str or last_read == stake_str):
                                                                                                    success_input = True
                                                                                            except Exception:
                                                                                                pass

                                                                                        if not success_input:
                                                                                            print(f"⚠️ La mise n'a pas été insérée correctement (valeur lue: {last_read})")
                                                                                        else:
                                                                                            print('✅ Mise présente dans le champ, tentative de validation')

                                                                                            # Rechercher un bouton de validation dans la sidebar (heuristiques)
                                                                                            clicked_confirm = False
                                                                                            candidate_btn = None
                                                                                            try:
                                                                                                sidebar = driver.find_element(By.ID, 'right-sidebar')
                                                                                            except Exception:
                                                                                                sidebar = None

                                                                                            words = ('valider', 'parier', 'payer', 'confirmer', 'place bet', 'placer', 'submit', 'bet')

                                                                                            if sidebar:
                                                                                                try:
                                                                                                    btns = sidebar.find_elements(By.TAG_NAME, 'button')
                                                                                                except Exception:
                                                                                                    btns = []
                                                                                                for b in btns:
                                                                                                    try:
                                                                                                        txt = (b.text or '').strip().lower()
                                                                                                        aria = (b.get_attribute('aria-label') or '').strip().lower()
                                                                                                        if any(w in txt or w in aria for w in words):
                                                                                                            candidate_btn = b
                                                                                                            break
                                                                                                    except Exception:
                                                                                                        continue
                                                                                                # fallback: dernier bouton
                                                                                                if not candidate_btn and btns:
                                                                                                    candidate_btn = btns[-1]

                                                                                            # fallback global si rien trouvé dans la sidebar
                                                                                            if not candidate_btn:
                                                                                                try:
                                                                                                    all_btns = driver.find_elements(By.TAG_NAME, 'button')
                                                                                                    for b in all_btns:
                                                                                                        try:
                                                                                                            txt = (b.text or '').strip().lower()
                                                                                                            aria = (b.get_attribute('aria-label') or '').strip().lower()
                                                                                                            if any(w in txt or w in aria for w in words):
                                                                                                                candidate_btn = b
                                                                                                                break
                                                                                                        except Exception:
                                                                                                            continue
                                                                                                except Exception:
                                                                                                    pass

                                                                                            if candidate_btn:
                                                                                                try:
                                                                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", candidate_btn)
                                                                                                except Exception:
                                                                                                    pass
                                                                                                try:
                                                                                                    candidate_btn.click()
                                                                                                except Exception:
                                                                                                    try:
                                                                                                        driver.execute_script('arguments[0].click();', candidate_btn)
                                                                                                    except Exception as e:
                                                                                                        print('⚠️ Impossible de cliquer sur le bouton de validation:', e)
                                                                                                else:
                                                                                                    # attendre notification ou vidage du betslip
                                                                                                    time.sleep(0.5)
                                                                                                    try:
                                                                                                        WebDriverWait(driver, 8).until(
                                                                                                            lambda d: len(d.find_elements(By.CSS_SELECTOR, '.notification-list .snack-notification')) > 0
                                                                                                        )
                                                                                                        print('✅ Notification de confirmation détectée (snack-notification)')
                                                                                                        clicked_confirm = True
                                                                                                    except Exception:
                                                                                                        # peut-être que le betslip a été vidé
                                                                                                        try:
                                                                                                            if len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="betslip-bet"]')) == 0:
                                                                                                                clicked_confirm = True
                                                                                                                print('✅ Betslip vidé après validation')
                                                                                                        except Exception:
                                                                                                            pass

                                                                                            if clicked_confirm:
                                                                                                # essayer de cliquer sur "Tout effacer" si présent
                                                                                                try:
                                                                                                    clicked = click_clear_if_in_sidebar(driver)
                                                                                                    if clicked:
                                                                                                        print("✅ Clic sur 'Tout effacer' effectué dans right-sidebar")
                                                                                                except Exception:
                                                                                                    pass
                                                                                            else:
                                                                                                print('⚠️ Aucun signe de validation après le clic (ni notification ni vidage du betslip)')
                                                                                    except Exception as e:
                                                                                        print('⚠️ Erreur lors de l\'insertion/validation de la mise:', e)
                                                                            else:
                                                                                print('⚠️ Impossible de déterminer la mise à placer (pas de cible ou cote)')
                                                                        except Exception as e:
                                                                            print('⚠️ Erreur lors du calcul/placement de la mise:', e)
                                                                    except Exception:
                                                                        print('⚠️ Betslip non détecté dans le conteneur .betlist (vérifier sélecteur ou rendu)')
                                                                except Exception:
                                                                    print('⚠️ Conteneur .betlist non trouvé (vérifier présence du betslip sur la page)')
                                                            except Exception as e:
                                                                print(f"⚠️ Erreur lors du clic Over/Under: {e}")
                                        except Exception as e:
                                            print(f"⚠️ Erreur lors de l'ajustement de la ligne: {e}")

                            except Exception as e:
                                print(f"⚠️ Erreur lors de la recherche du conteneur 'content is-open': {e}")
                    except Exception:
                        pass
            except Exception:
                print("ℹ️ Aucun bouton 'Props du Joueur' trouvé pour ce match")

        try:
            bet_data = {
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'bookmaker': '1xbet',
                'stake': config.mise,
                'odds': config.cote,
                'result': '',  # Sera mis à jour plus tard
                'tipster': config.tipster.upper(),
                'bet_event': f"{equipe1} vs {equipe2} - {selection}",
                'bet_to_recover_id': None
            }

            # Appel à l'API pour ajouter le pari
            api_url = "http://bettracker.sc2vagr6376.universe.wf/backend/api.php"  # URL de l'API
            full_url = f"{api_url}?action=add"
            print(f"Envoi des données à l'API: {full_url}")
            print(f"Données envoyées: {json.dumps(bet_data, indent=2)}")

            response = requests.post(
                full_url,
                headers={'Content-Type': 'application/json'},
                json=bet_data,
                timeout=30
            )

            print(f"Code de statut de la réponse: {response.status_code}")
            print(f"En-têtes de la réponse: {dict(response.headers)}")
            print(f"Contenu brut de la réponse: '{response.text}'")

            # Vérification de la réponse
            if not response.ok:
                raise Exception(f"Erreur HTTP: {response.status_code} - {response.text}")

            # Traitement de la réponse - gestion des réponses vides
            response_data = {}
            if response.content and response.content.strip():
                try:
                    response_data = response.json()
                except json.JSONDecodeError as json_error:
                    print(f"Erreur de décodage JSON: {json_error}")
                    print(f"Contenu de la réponse: {response.text}")
                    response_data = {'raw_response': response.text}
            else:
                print("Réponse vide de l'API - considérée comme succès")

            return {
                'success': True,
                'message': 'Pari ajouté avec succès à l\'API',
                'details': {
                    'equipes': f"{equipe1} vs {equipe2}",
                    'type_de_pari': type_de_pari,
                    'mise': config.mise,
                    'cote': config.cote,
                    'api_response': response_data
                }
            }

        except requests.exceptions.RequestException as e:
            print(f'Erreur lors de l\'appel à l\'API: {str(e)}')
            return {
                'success': False,
                'message': f'Erreur lors de l\'appel à l\'API: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            print(f'Erreur lors de l\'ajout du pari: {str(e)}')
            return {
                'success': False,
                'message': f'Impossible d\'ajouter le pari. Veuillez réessayer plus tard.',
                'error': str(e)
            }
        finally:
            # Retirer l'élément traité de la liste pour éviter une boucle infinie
            if codeList:
                del codeList[0]
                print(f"Pari traité et retiré de la liste. Éléments restants: {len(codeList)}")

    # Retour par défaut si la boucle se termine sans traitement
    return {
        'success': True,
        'message': 'Tous les paris ont été traités',
        'processed_count': len(donnees_test) if isinstance(donnees_test, list) else 1
    }


def avec_donnees_exemple():
    """
    Fonction de test utilisant les données d'exemple fournies
    """
    from ChromeDriver.SetDriver1 import driver

    # Données d'exemple pour les tests
    donnees_test = {
  "matches": [
    {
      "date": "11/05/2026",
      "equipe_1": "Los Angeles Lakers",
      "equipe_2": "Oklahoma City Thunder",
      "categorie": "Player Props (FR)",
      "type_de_pari": "Points",
      "player_name": "Deandre Ayton",
      "prop_type": "Points",
      "line": 12.5,
      "over_under": "Under",
      "selection": "Deandre Ayton Moins de 12.5 Points",
      "odds": 1.35,
      "sport": "4",
      "intitule": "Deandre Ayton moins de 12.5 points"
    }
  ]
}


    # Test avec les données d'exemple
    resultat = placer_pari(
        driver, [donnees_test]
    )

    print("RÉSULTAT DU TEST:")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))

    return resultat

    # except ImportError:
    # print("Erreur: Impossible d'importer le driver Chrome")
    # return None
    # except Exception as e:
    # print(f"Erreur lors du test: {str(e)}")
    # return None


if __name__ == "__main__":
    config.site_type = 'new_site'
    # Test avec les données d'exemple
    print("Lancement du test avec les données d'exemple...")
    config.scriptType = 'LIVE'
    avec_donnees_exemple()
