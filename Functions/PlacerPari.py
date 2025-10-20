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
    while codeList != []:
        print('ok')
        # Récupérer le premier élément de la liste (dictionnaire de pari)
        print(codeList)
        donnees_test = codeList[0]
        print(codeList)
        print("=== DONNÉES ===")
        print(f"Match: {donnees_test['equipe_1']} vs {donnees_test['equipe_2']}")
        print(f"Date: {donnees_test['date']}")
        print(f"Catégorie de pari: {donnees_test['categorie']}")
        print(f"Type de pari: {donnees_test['type_de_pari']}")
        print(f"Sélection: {donnees_test['selection']}")
        print(f"Tipster: {donnees_test['tipster']}")
        print("=" * 50)
        print('etst')
        equipe1 = donnees_test['equipe_1']
        equipe2 = donnees_test['equipe_2']
        categorie = donnees_test['categorie']
        type_de_pari = donnees_test['type_de_pari']
        selection = donnees_test['selection']  # "Plus De 20.5"
        config.tipster = donnees_test['tipster']
        config.match_name = equipe1 + ' - ' + equipe2
        find_match = False
        driver.get('https://1xbet.com/fr')
        # BOUTON DE RECHERCHE
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'games-search-app-search__button')))
        except Exception as e:
            print(f'Erreur lors de la recherche du bouton de recherche: {str(e)}')
            exit()
        else:
            search_button = driver.find_element(By.CLASS_NAME, 'games-search-app-search__button')
            search_button.click()
        # POPUP DE RECHERCHE
        try:

            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'games-search-modal__input')))
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'modal__content')))
            modal__content = driver.find_element(By.CLASS_NAME, 'modal__content')
        except Exception as e:
            print(f'Erreur lors de la recherche du champ de recherche: {str(e)}')
        else:
            search_input = modal__content.find_element(By.CSS_SELECTOR, 'input.games-search-modal__input')
            search_input.send_keys(f"{equipe1} - {equipe2}")
            search_popup_button = modal__content.find_element(By.CLASS_NAME, 'ico--search')
            search_popup_button.click()
        # RECHERCHE DU MATCH DANS LA LIST ET OUVERTURE DU MATCH
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'games-search-modal-results-list__item')))
        except Exception as e:
            print(f'Erreur lors de la recherche du match: {equipe1} vs {equipe2} : {str(e)}')
        else:
            # try:
            matches = driver.find_elements(By.CLASS_NAME, 'games-search-modal-results-list__item')
            team1 = ''
            team2 = ''

            for match in matches:
                teams = match.find_element(By.CLASS_NAME, 'games-search-modal-card-info__main').text
                if ' - ' in teams:
                    team1, team2 = teams.split(' - ')
                if (equipe1 in team1 or team1 in equipe1) and (equipe2 in team2 or team2 in equipe2):
                    print('Match found')
                    link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    driver.get(link)
                    find_match = True
                    break
            if not find_match:
                for match in matches:
                    teams = match.find_element(By.CLASS_NAME, 'games-search-modal-card-info__main').text
                    if compare_match_name(teams, f'{equipe1} vs {equipe2}'):
                        print('Match found')
                        link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        driver.get(link)
                        find_match = True
                        break

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
        while not AfficherParis(driver, categorie, type_de_pari):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
                return False

        tentative = 0
        while not GetBetOld(driver, selection=selection):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
                return False

        while not PlacerMise(driver):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
                return False
        while not ValidationDuParis(driver):
            tentative += 1
            if tentative > 3:
                send_telegram(Functions.Functions_telegram.alertGroup, f"Une erreur est survenue : {codeList}")
                # Retirer l'élément de la liste avant de retourner
                if codeList:
                    del codeList[0]
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
