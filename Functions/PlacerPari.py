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


def placer_pari(driver, codeList):
    """
    Fonction pour placer un pari sur 1xBet
    
    :param driver: Instance du driver Selenium
    :param equipe1: Nom de la première équipe
    :param equipe2: Nom de la deuxième équipe
    :param categorie: Nom de la categorie
    :param selection: Nom de la selection
    :param type_de_pari: Type de pari (ex: '1', 'X', '2', 'Over 2.5', etc.)
    :param mise: Montant de la mise
    :param cote_min: Cote minimum acceptée (optionnel)
    :return: Dictionnaire avec le résultat de l'opération
    """
    donnees_test = []
    config.site_type = 'mobile_site'
    tentative = 0
    while codeList != [] and tentative < 3:
        print('ok')
        # Récupérer le premier élément de la liste (dictionnaire de pari)
        donnees_test = codeList[0]
        print("=== DONNÉES ===")
        print(f"Match: {donnees_test['equipe_1']} vs {donnees_test['equipe_2']}")
        print(f"Date: {donnees_test['date']}")
        print(f"Catégorie de pari: {donnees_test['categorie']}")
        print(f"Type de pari: {donnees_test['type_de_pari']}")
        print(f"Sélection: {donnees_test['selection']}")
        print(f"sport: {donnees_test.get('sport', None)}")
        print(f"Tipster: {donnees_test['tipster']}")
        print("=" * 50)
        print('etst')
        equipe1 = donnees_test['equipe_1']
        equipe2 = donnees_test['equipe_2']
        categorie = donnees_test['categorie']
        type_de_pari = donnees_test['type_de_pari']
        selection = donnees_test['selection']  # "Plus De 20.5"
        sport_id = donnees_test.get('sport', None)  # Valeur par défaut si 'sport' n'est pas présent
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
                            new_pari = donnees_test.copy()
                            if isinstance(item, dict):
                                new_pari['categorie'] = item.get('categorie', new_pari.get('categorie'))
                                new_pari['type_de_pari'] = item.get('type_de_pari', new_pari.get('type_de_pari'))
                                new_pari['selection'] = item.get('selection', new_pari.get('selection'))
                                new_pari['odds'] = item.get('odds', new_pari.get('odds'))
                            combined_paris.append(new_pari)
                else:
                    new_pari = donnees_test.copy()
                    new_pari['categorie'] = donnees_test.get('categorie', new_pari.get('categorie'))
                    new_pari['type_de_pari'] = donnees_test.get('type_de_pari', new_pari.get('type_de_pari'))
                    new_pari['selection'] = donnees_test.get('selection', new_pari.get('selection'))
                    new_pari['odds'] = donnees_test.get('odds', new_pari.get('odds'))
                    combined_paris.append(new_pari)
        except Exception as e:
            print(f"Erreur lors du parsing/normalisation de 'selection': {e}")
            
        config.tipster = donnees_test['tipster']
        config.match_name = equipe1 + ' - ' + equipe2
        find_match = False
        driver.get('https://ca.1xbet.com/fr?platform_type=mobile')
        # BOUTON DE RECHERCHE
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'home-navigation__link--search')))
        except Exception as e:
            print(f'Erreur lors de la recherche du bouton de recherche: {str(e)}')
            tentative = tentative + 1
            continue
        else:
            search_button = driver.find_element(By.CLASS_NAME, 'home-navigation__link--search')
            search_button.click()
        # POPUP DE RECHERCHE
        # Attendre que la page soit complètement chargée (document.readyState == 'complete')
        try:
            time.sleep(2)
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == 'complete'
            )
        except Exception:
            # fallback court si l'attente échoue
            time.sleep(3)
        try:
            time.sleep(5)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'search-app__content')))
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'ui-search-default')))
            modal__content = driver.find_element(By.CLASS_NAME, 'search-app__content')
        except Exception as e:
            print(f'Erreur lors de la recherche du champ de recherche: {str(e)}')
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
                print('Champ de recherche introuvable avec les sélecteurs habituels')
            else:
                # Remplissage robuste : scroll, ajouter id/name, injecter valeur via JS + dispatch d'événements
                try:
                    search_term = f"{equipe1} - {equipe2}"
                    search_input.send_keys(search_term)

                except Exception as e:
                    # Dernier recours : send_keys simple
                    time.sleep(2)
                    try:
                        print(e)
                        search_input.send_keys(f"{equipe1} - {equipe2}")
                    except Exception as e2:
                        print(f"Impossible d'envoyer le texte dans le champ de recherche: {e2} | original: {e}")
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

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'ui-game-card__content')))
            time.sleep(3)
        except Exception as e:
            print(f'Erreur lors de la recherche du match: {equipe1} vs {equipe2} : {str(e)}')
            tentative = tentative + 1
            continue

        else:
            print('ui-game-cards found')
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

                        print(f"🏆 Équipes trouvées: '{team1}' vs '{team2}'")
                        print(f"🔍 Recherche: '{equipe1}' vs '{equipe2}'")

                        # Comparaison flexible des noms d'équipes
                        if (equipe1.lower() in team1.lower() or team1.lower() in equipe1.lower()) and \
                                (equipe2.lower() in team2.lower() or team2.lower() in equipe2.lower()):
                            print('✅ Match found!')
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
                                print('✅ Match found (fallback method)')
                                link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                driver.get(link)
                                find_match = True
                                break

                except Exception as e:
                    print(f"⚠️ Erreur lors de l'extraction des équipes: {e}")
                    tentative = tentative + 1
                    continue
            if not find_match:
                for match in matches:
                    # Nouvelle structure HTML - récupérer les noms d'équipes depuis les spans
                    team_names = match.find_elements(By.CLASS_NAME, 'ui-game-card-scoreboard__name')

                    if len(team_names) >= 2:
                        team1 = team_names[0].text.strip()
                        team2 = team_names[1].text.strip()
                    print('try to compare', f"{team1} - {team2}", f'{equipe1} vs {equipe2}')
                    try:
                        if compare_match_name(f"{team1} - {team2}", f'{equipe1} vs {equipe2}', sport_id):
                            print('Match found')
                            link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                            driver.get(link)
                            find_match = True
                            break
                    except Exception as e:
                        print(f'Une erreur de comparaison {e}')

            # except Exception as e:
            # print(f'Erreur lors de la selection du match: {equipe1} vs {equipe2} : {str(e)}')
            # exit()
        if not find_match:
            send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
            # Retirer l'élément de la liste avant de retourner
            if codeList:
                del codeList[0]
            return False
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
            else:
                constructor_bet = driver.find_element(By.CLASS_NAME, 'ico--constructor-bet')
                constructor_bet.click()
                time.sleep(2)
        for pari in combined_paris:
            print(pari)
            while not AfficherParis(driver, pari['categorie'], pari['type_de_pari']):
                tentative += 1
                if tentative > 3:
                    send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                    # Retirer l'élément de la liste avant de retourner
                    if codeList:
                        del codeList[0]
                    return False

            tentative = 0
            time.sleep(2)
            while not GetBetOld(driver, selection=pari['selection']):
                tentative += 1
                if tentative > 3:
                    send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                    # Retirer l'élément de la liste avant de retourner
                    if codeList:
                        del codeList[0]
                    return False
        if len(combined_paris)>1:
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'quick-coupon-header__redirect')))
            except Exception as e:
                print(f'Erreur lors de la recherche du bouton de validation des paris combinés: {str(e)}')
            else:
                combobet_footer = driver.find_element(By.CLASS_NAME, 'quick-coupon-header__redirect')
                combobet_footer.click()
                time.sleep(2)

        while not PlacerMise(driver, constructor=(len(combined_paris)>1)):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
                return False
        validation = False
        while not validation:
            validation = ValidationDuParis(driver)
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
                return False
        if not validation:
            return False
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
