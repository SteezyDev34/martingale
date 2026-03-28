# -*- coding: utf-8 -*-
import json
import os
import sys
import time

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import Functions.Functions_telegram
import config
from Functions.AfficherParis import AfficherParis
from Functions.Functions_telegram import send_telegram
from Functions.GetBetOld import GetBetOld
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis
from Functions.getTextFromImageGPT import compare_match_name


def log_message(message, level="INFO", flush_output=True):
    """
    Fonction utilitaire pour l'affichage des messages avec flush automatique
    pour éviter les freezes du terminal
    """
    timestamp = time.strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {level}: {message}"
    print(formatted_message, flush=flush_output)
    return formatted_message


def optimized_wait(driver, condition, timeout=10, poll_frequency=0.5):
    """
    Attente optimisée avec des messages de progression pour éviter l'impression de freeze
    """
    start_time = time.time()
    elapsed_dots = 0
    
    while time.time() - start_time < timeout:
        try:
            if condition(driver):
                return True
            
            # Afficher des points de progression toutes les 2 secondes
            if int(time.time() - start_time) > elapsed_dots * 2:
                log_message(".", level="", flush_output=True)
                elapsed_dots += 1
                
        except Exception:
            pass
        
        time.sleep(poll_frequency)
    
    return False


def placer_pari(driver, codeList):
    """
    Fonction pour placer un pari sur 1xBet
    
    :param driver: Instance du driver Selenium
    :param codeList: Données du pari au format {'matches': [...], 'tipster': '...'}
    :return: Dictionnaire avec le résultat de l'opération
    """
    config.site_type = 'mobile_site'
    tentative = 0
    
    # Nouveau format : {'matches': [...], 'tipster': '...'}
    matches_list = codeList['matches']
    global_tipster = codeList.get('tipster', '')
    
    while tentative < 3:
        log_message('Début de tentative de placement de pari')
        success = True
        # Traiter chaque match de la liste
        for match in matches_list:
            log_message("=== DONNÉES ===")
            log_message(f"Match: {match['equipe_1']} vs {match['equipe_2']}")
            log_message(f"Date: {match['date']}")
            log_message(f"Catégorie de pari: {match['categorie']}")
            log_message(f"Type de pari: {match['type_de_pari']}")
            log_message(f"Sélection: {match['selection']}")
            log_message(f"Sport: {match.get('sport', None)}")
            log_message(f"Tipster: {global_tipster or match.get('tipster', '')}")
            log_message("=" * 50)
            log_message('Traitement du match en cours...')

            equipe1 = match['equipe_1']
            equipe2 = match['equipe_2']
            categorie = match['categorie']
            type_de_pari = match['type_de_pari']
            selection = match['selection']  # "Plus De 20.5"
            sport_id = match.get('sport', None)  # Valeur par défaut si 'sport' n'est pas présent
            # Normaliser et gérer différents formats de `selection`:
            # - Si c'est une chaîne JSON sérialisée représentant une liste -> convertir en tableau de paris
            # - Si c'est déjà une liste Python -> l'utiliser comme tableau
            # - Sinon -> retourner un tableau contenant l'élément d'origine (marqué comme 'Combiné')
            combined_paris = None
            try:
                if isinstance(selection, str):
                    s = selection.strip()
                    combined_paris = []
                    if s.startswith('[') and s.endswith(']'):
                        parsed = json.loads(selection)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            for item in parsed:
                                new_pari = match.copy()
                                if isinstance(item, dict):
                                    new_pari['categorie'] = item.get('categorie', new_pari.get('categorie'))
                                    new_pari['type_de_pari'] = item.get('type_de_pari', new_pari.get('type_de_pari'))
                                    new_pari['selection'] = item.get('selection', new_pari.get('selection'))
                                    new_pari['odds'] = item.get('odds', new_pari.get('odds'))
                                combined_paris.append(new_pari)
                    else:
                        new_pari = match.copy()
                        new_pari['categorie'] = match.get('categorie', new_pari.get('categorie'))
                        new_pari['type_de_pari'] = match.get('type_de_pari', new_pari.get('type_de_pari'))
                        new_pari['selection'] = match.get('selection', new_pari.get('selection'))
                        new_pari['odds'] = match.get('odds', new_pari.get('odds'))
                        combined_paris.append(new_pari)
            except Exception as e:
                print(f"Erreur lors du parsing/normalisation de 'selection': {e}", flush=True)
            else:
                # Construction de la liste des sélections
                selections_list = "\n".join([f"  - {pari['selection']}" for pari in combined_paris])
                
                formatted_telegram_msg = f"📊 Nouveau pari à placer:\n" \
                                    f"Match: {equipe1} vs {equipe2}\n" \
                                    f"Date: {match['date']}\n" \
                                    f"Catégorie de pari: {categorie}\n" \
                                    f"Type de pari: {type_de_pari}\n" \
                                    f"Sélection:\n{selections_list}\n" \
                                    f"Sport: {sport_id}\n" \
                                    f"Tipster: {global_tipster}"
                
            config.tipster = global_tipster
            config.match_name = equipe1 + ' - ' + equipe2
            find_match = False
            log_message(f"🌐 Accès à 1xBet pour {equipe1} vs {equipe2}...")
            driver.get('https://ca.1xbet.com/fr?platform_type=mobile')
            # BOUTON DE RECHERCHE
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'home-navigation__link--search')))
            except Exception as e:
                log_message(f'❌ Erreur lors de la recherche du bouton de recherche: {str(e)}', "ERROR")
                tentative = tentative + 1
                continue
            else:
                log_message("🔍 Bouton de recherche trouvé, clic en cours...")
                search_button = driver.find_element(By.CLASS_NAME, 'home-navigation__link--search')
                search_button.click()
            # POPUP DE RECHERCHE
            # Attendre que la page soit complètement chargée (document.readyState == 'complete')
            try:
                log_message("⏳ Attente du chargement de la page...")
                time.sleep(2)
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == 'complete'
                )
                log_message("✅ Page chargée")
            except Exception:
                log_message("⚠️ Timeout du chargement, poursuite...", "WARNING")
                time.sleep(2)
            try:
                time.sleep(3)
                log_message("🔍 Recherche du champ de saisie...")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'search-app__content')))
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'ui-search-default')))
                modal__content = driver.find_element(By.CLASS_NAME, 'search-app__content')
            except Exception as e:
                log_message(f'❌ Erreur lors de la recherche du champ de recherche: {str(e)}', "ERROR")
                tentative = tentative + 1
                continue
            else:
                # Chercher l'input de recherche avec plusieurs sélecteurs possibles
                search_input = None
                selectors = ['input.ui-field__input', 'input.ui-search-default', 'input.search-app-head__search',
                            'input.ui-field__input.search-app-head__search']
                for sel in selectors:
                    try:
                        search_input = modal__content.find_element(By.CSS_SELECTOR, sel)
                        break
                    except Exception:
                        continue

                if not search_input:
                    log_message('❌ Champ de recherche introuvable avec les sélecteurs habituels', "ERROR")
                else:
                    # Remplissage robuste : scroll, ajouter id/name, injecter valeur via JS + dispatch d'événements
                    try:
                        search_term = f"{equipe1} - {equipe2}"
                        log_message(f"⌨️ Saisie du terme de recherche: {search_term}")
                        search_input.send_keys(search_term)

                    except Exception as e:
                        # Dernier recours : send_keys simple
                        time.sleep(2)
                        try:
                            print(e)
                            search_input.send_keys(f"{equipe1} - {equipe2}")
                        except Exception as e2:
                            log_message(f"❌ Impossible d'envoyer le texte dans le champ de recherche: {e2} | original: {e}", "ERROR")
            try:
                # Rechercher et cliquer sur le span "Avant-match"
                """try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[contains(@class, 'ui-caption') and text()='Avant-match']"))
                    )
                    avant_match_span = driver.find_element(By.XPATH,
                                                        "//span[contains(@class, 'ui-caption') and text()='Avant-match']")
                    avant_match_span.click()
                    print("✅ Cliqué sur 'Avant-match'")
                except Exception as e:
                    print(f"⚠️ Impossible de cliquer sur 'Avant-match': {e}")"""

                log_message("🔍 Lancement de la recherche du match...")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'ui-game-card__content')))
                time.sleep(2)
            except Exception as e:
                log_message(f'❌ Erreur lors de la recherche du match: {equipe1} vs {equipe2} : {str(e)}', "ERROR")
                tentative = tentative + 1
                continue

            else:
                print('✅ Cartes de matches trouvées, recherche en cours...', flush=True)
                # try:
                matches = driver.find_elements(By.CLASS_NAME, 'search-game-card')
                team1 = ''
                team2 = ''

                for match in matches:
                    try:
                        # Nouvelle structure HTML - récupérer les noms d'équipes depuis les spans
                        team_names = match.find_elements(By.CLASS_NAME, 'ui-game-card-scoreboard-teams-name__caption')

                        if len(team_names) >= 2:
                            team1 = team_names[0].text.strip()
                            team2 = team_names[1].text.strip()

                            log_message(f"🏆 Équipes trouvées: '{team1}' vs '{team2}'")
                            log_message(f"🔍 Comparaison avec: '{equipe1}' vs '{equipe2}'")

                            # Comparaison flexible des noms d'équipes
                            if (equipe1.lower() in team1.lower() or team1.lower() in equipe1.lower()) and \
                                    (equipe2.lower() in team2.lower() or team2.lower() in equipe2.lower()):
                                print('✅ Match trouvé! Accès à la page du match...', flush=True)
                                link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                driver.get(link)
                                find_match = True
                                break
                        else:
                            # Fallback vers l'ancienne méthode si la nouvelle structure n'est pas trouvée
                            scoreboard = match.find_element(By.CLASS_NAME, 'ui-game-card-scoreboard')
                            teams_text = scoreboard.text
                            if ' - ' in teams_text:
                                team1, team2 = teams_text.split(' - ')
                                if (equipe1 in team1 or team1 in equipe1) and (equipe2 in team2 or team2 in equipe2):
                                    print('✅ Match trouvé (méthode alternative)!', flush=True)
                                    link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                    driver.get(link)
                                    find_match = True
                                    break

                    except Exception as e:
                        log_message(f"⚠️ Erreur lors de l'extraction des équipes: {e}", "WARNING")
                        continue
                if not find_match:
                    for match in matches:
                        # Nouvelle structure HTML - récupérer les noms d'équipes depuis les spans
                        team_names = match.find_elements(By.CLASS_NAME, 'ui-game-card-scoreboard__name')

                        if len(team_names) >= 2:
                            team1 = team_names[0].text.strip()
                            team2 = team_names[1].text.strip()
                        log_message(f'Tentative de comparaison: {team1} - {team2} avec {equipe1} vs {equipe2}')
                        try:
                            if (equipe1 in team1 or team1 in equipe1) and (equipe2 in team2 or team2 in equipe2):
                                log_message('✅ Match trouvé (méthode alternative 2)!')
                                link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                driver.get(link)
                                find_match = True
                                break
                            if compare_match_name(f"{team1} - {team2}", f'{equipe1} vs {equipe2}', sport_id):
                                log_message('✅ Match trouvé via comparaison IA!')
                                link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                driver.get(link)
                                find_match = True
                                break
                        except Exception as e:
                            log_message(f'Erreur lors de la comparaison: {e}', "WARNING")

                # except Exception as e:
                # print(f'Erreur lors de la selection du match: {equipe1} vs {equipe2} : {str(e)}')
                # exit()
            if not find_match:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la recherche du match : {formatted_telegram_msg}")
                success = False
                break
            # Afficher la categorie de paris
            tentative = 0
            try:
                time.sleep(2)
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == 'complete'
                )
            except Exception:
                # fallback court si l'attente échoue
                time.sleep(3)
            if len(combined_paris)>1:
                print(combined_paris)
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'ico--constructor-bet')))
                except Exception as e:
                    print(f'Erreur lors de la recherche de la section de paris combinés: {str(e)}')
                    send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la recherche de la section de paris combinés : {formatted_telegram_msg}")
                    return False
                else:
                    constructor_bet = driver.find_element(By.CLASS_NAME, 'ico--constructor-bet')
                    constructor_bet.click()
                    time.sleep(2)
            for pari in combined_paris:
                print(pari)
                while not AfficherParis(driver, pari['categorie'], pari['type_de_pari']):
                    tentative += 1
                    if tentative > 3:
                        send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de l'affichage du pari : {formatted_telegram_msg}")
                        return False

                tentative = 0
                time.sleep(2)
                while not GetBetOld(driver, selection=pari['selection']):
                    tentative += 1
                    if tentative > 3:
                        send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la récupération du pari : {formatted_telegram_msg}")
                        return False
            if len(combined_paris)>1:
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'quick-coupon-header__redirect')))
                except Exception as e:
                    print(f'Erreur lors de la recherche du bouton de validation des paris combinés: {str(e)}')
                    send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la recherche du bouton de validation des paris combinés : {formatted_telegram_msg}")
                    return False
                else:
                    combobet_footer = driver.find_element(By.CLASS_NAME, 'quick-coupon-header__redirect')
                    combobet_footer.click()
                    time.sleep(2)

        while not PlacerMise(driver, constructor=(len(combined_paris)>1)):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la mise du pari : {formatted_telegram_msg}")
                return False
        validation = False
        while not validation:
            validation = ValidationDuParis(driver)
            tentative += 1
            if tentative > 3:
                return False
        if not validation:
            send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la validation du pari : {formatted_telegram_msg}")
            return False
        try:
            # Formatage des événements selon le nouveau format API
            formatted_events = []
            for pari in combined_paris:
                event_data = {
                    "team1": equipe1,
                    "team2": equipe2,
                    "league": pari.get('league', 'Ligue Inconnue'),  # À ajuster selon vos données
                    "description": pari['selection'],
                    "odds": float(pari.get('odds', config.cote)),
                    "sport_id": sport_id or 1  # Valeur par défaut si sport_id est None
                }
                formatted_events.append(event_data)
            
            # Structure des données selon le nouveau format API
            bet_data = {
                "bet_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "global_odds": float(config.cote),
                "bet_code": f"auxobot-{config.tipster.lower()}" if config.tipster else "auxobot-multi",
                "stake": float(config.mise),
                "stake_type": "currency",
                "events": formatted_events
            }

            # Configuration de la nouvelle API
            api_url = getattr(config, 'AUXOTRACK_API_URL', "https://api.auxotracker.lan/api/auxobot/bets")
            
            # Récupération du token depuis les variables d'environnement
            auxobot_token = getattr(config, 'AUXOBOT_TOKEN')
            
            if not auxobot_token:
                raise Exception("AUXOBOT_TOKEN non configuré dans le fichier .env")
            
            headers = {
                'Authorization': f'Bearer {auxobot_token}',
                'Content-Type': 'application/json'
            }

            print(f"Envoi des données à l'API: {api_url}")
            print(f"Données envoyées: {json.dumps(bet_data, indent=2, ensure_ascii=False)}")

            response = requests.post(
                api_url,
                headers=headers,
                json=bet_data,
                timeout=30,
                verify=False  # Pour éviter les erreurs SSL avec -k comme dans curl
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
            # Pari traité avec le nouveau format
            print(f"Pari traité avec succès")

        # Si on arrive ici sans exception, le traitement a réussi pour ce match
        
        # Fin de la boucle for (tous les matches traités)
        # Si tous les matches ont été traités avec succès
        if success:
            return {
                'success': True,
                'message': 'Tous les paris ont été traités',
                'processed_count': len(matches_list)
            }
        
        # Si il y a eu un échec, incrémenter tentative et recommencer
        tentative += 1
        print(f"Tentative {tentative} échouée, nouvelle tentative...")

    # Si on sort de la boucle while, toutes les tentatives ont échoué
    return {
        'success': False,
        'message': 'Échec après 3 tentatives',
        'processed_count': 0
    }


def avec_donnees_exemple():
    """
    Fonction de test utilisant les données d'exemple fournies
    """
    from ChromeDriver.SetDriver1 import driver

    # Données d'exemple pour les tests
    donnees_test = {
        "date": "05/09/2025",
        "equipe_1": "Earthquakes",
        "equipe_2": "Austin",
        "categorie": "Temps réglementaire",
        "type_de_pari": "Handicap",
        "selection": "Handicap 1 (-1)",
        "odds": "1.1",
        "tipster": 'TEST'
    }

    # try:
    # Test en mode simulation sans driver réel
    print("=== MODE TEST SANS DRIVER ===")
    print("Test des données d'exemple uniquement...")

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
