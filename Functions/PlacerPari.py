import json
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from Functions.AfficherParis import AfficherParis
from Functions.GetBetOld import GetBetOld


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
        donnees_test = codeList
        print(codeList)
        print("=== DONNÉES ===")
        print(f"Match: {donnees_test['equipe_1']} vs {donnees_test['equipe_2']}")
        print(f"Date: {donnees_test['date']}")
        print(f"Catégorie de pari: {donnees_test['categorie']}")
        print(f"Type de pari: {donnees_test['type_de_pari']}")
        print(f"Sélection: {donnees_test['selection']}")
        print(f"Cote: {donnees_test['odds']}")
        print("=" * 50)

        equipe1 = donnees_test['equipe_1']
        equipe2 = donnees_test['equipe_2']
        categorie = donnees_test['categorie']
        type_de_pari = donnees_test['type_de_pari']
        selection = donnees_test['selection']  # "Plus De 20.5"
        mise = 0.2,  # Mise de test
        cote_min = float(donnees_test['odds'])  # Cote minimum basée sur l'exemple

        driver.get('https://1xbet.com/fr')
        # BOUTON DE RECHERCHE
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, 'b-searchBut-live')))
        except Exception as e:
            print(f'Erreur lors de la recherche du bouton de recherche: {str(e)}')
            exit()
        else:
            search_button = driver.find_element(By.ID, 'b-searchBut-live')
            search_button.click()
        # POPUP DE RECHERCHE
        try:
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, 'search-in-popup')))
        except Exception as e:
            print(f'Erreur lors de la recherche du champ de recherche: {str(e)}')
        else:
            search_input = driver.find_element(By.ID, 'search-in-popup')
            search_input.send_keys(f"{equipe1} - {equipe2}")
            search_popup_button = driver.find_element(By.CLASS_NAME, 'search-popup__button')
            search_popup_button.click()
        # RECHERCHE DU MATCH DANS LA LIST ET OUVERTURE DU MATCH
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'search-popup-events__item')))
        except Exception as e:
            print(f'Erreur lors de la recherche du match: {equipe1} vs {equipe2} : {str(e)}')
        else:
            try:
                matches = driver.find_elements(By.CLASS_NAME, 'search-popup-events__item')
                team1 = ''
                team2 = ''
                for match in matches:
                    teams = match.find_element(By.CLASS_NAME, 'search-popup-event__teams').text
                    if ' - ' in teams:
                        team1, team2 = teams.split(' - ')
                    if (equipe1 in team1 or team1 in equipe1) and (equipe2 in team2 or team2 in equipe2):
                        print('Match found')
                        link = match.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        driver.get(link)
                        break
            except Exception as e:
                print(f'Erreur lors de la selection du match: {equipe1} vs {equipe2} : {str(e)}')
                exit()
        # Afficher la categorie de paris
        AfficherParis(driver, categorie, type_de_pari)
        GetBetOld(driver, selection=selection)

        try:
            # Rechercher le match
            resultat_recherche = rechercher_match(driver, equipe1, equipe2)
            if not resultat_recherche['success']:
                return resultat_recherche

            # Sélectionner le pari
            resultat_selection = selectionner_pari(driver, type_de_pari, cote_min)
            if not resultat_selection['success']:
                return resultat_selection

            # Placer la mise
            resultat_mise = placer_mise(driver, mise)
            if not resultat_mise['success']:
                return resultat_mise

            # Valider le pari
            resultat_validation = valider_pari(driver)

            return {
                'success': True,
                'message': 'Pari placé avec succès',
                'details': {
                    'equipes': f"{equipe1} vs {equipe2}",
                    'type_de_pari': type_de_pari,
                    'mise': mise,
                    'cote': resultat_selection.get('cote'),
                    'coupon': resultat_validation.get('coupon_number')
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors du placement du pari: {str(e)}',
                'error': str(e)
            }


def rechercher_match(driver, equipe1, equipe2):
    """
    Recherche un match spécifique sur 1xBet
    
    :param driver: Instance du driver Selenium
    :param equipe1: Nom de la première équipe
    :param equipe2: Nom de la deuxième équipe
    :return: Dictionnaire avec le résultat de la recherche
    """

    try:
        # Construire la requête de recherche
        recherche_text = f"{equipe1} - {equipe2}"

        # Localiser la barre de recherche
        barre_recherche = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'games-search-app__search'))
        )

        # Effacer et saisir le texte de recherche
        barre_recherche.clear()
        time.sleep(0.5)
        barre_recherche.send_keys(recherche_text)
        time.sleep(1)

        # Vérifier que le texte a été saisi correctement
        valeur_saisie = barre_recherche.get_attribute("value")
        if valeur_saisie != recherche_text:
            return {
                'success': False,
                'message': 'Erreur lors de la saisie dans la barre de recherche'
            }

        # Attendre que les résultats apparaissent
        time.sleep(2)

        # Vérifier qu'il y a des résultats
        try:
            resultats = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'c-events__item'))
            )

            if len(resultats) == 0:
                return {
                    'success': False,
                    'message': 'Aucun match trouvé pour cette recherche'
                }

        except TimeoutException:
            return {
                'success': False,
                'message': 'Timeout lors de la recherche du match'
            }

        return {
            'success': True,
            'message': 'Match trouvé avec succès',
            'resultats_count': len(resultats)
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}'
        }


def selectionner_pari(driver, type_de_pari, cote_min=None):
    """
    Sélectionne un type de pari spécifique
    
    :param driver: Instance du driver Selenium
    :param type_de_pari: Type de pari à sélectionner
    :param cote_min: Cote minimum acceptée
    :return: Dictionnaire avec le résultat de la sélection
    """

    try:
        # Attendre que les cotes soient chargées
        time.sleep(2)

        # Localiser les éléments de pari selon le type
        if type_de_pari in ['1', 'X', '2']:  # Paris simples 1X2
            selecteur = f"[data-bet-type='{type_de_pari}']"
        else:  # Autres types de paris
            selecteur = f"[title*='{type_de_pari}'], [data-title*='{type_de_pari}']"

        try:
            element_pari = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selecteur))
            )
        except TimeoutException:
            return {
                'success': False,
                'message': f'Pari "{type_de_pari}" non trouvé ou non disponible'
            }

        # Récupérer la cote
        try:
            cote_element = element_pari.find_element(By.CLASS_NAME, 'c-bets__bet-odds')
            cote = float(cote_element.text.replace(',', '.'))
        except:
            cote = None

        # Vérifier la cote minimum si spécifiée
        if cote_min and cote and cote < cote_min:
            return {
                'success': False,
                'message': f'Cote trop faible: {cote} < {cote_min}'
            }

        # Cliquer sur le pari
        driver.execute_script("arguments[0].click();", element_pari)
        time.sleep(1)

        return {
            'success': True,
            'message': 'Pari sélectionné avec succès',
            'cote': cote
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de la sélection du pari: {str(e)}'
        }


def placer_mise(driver, mise):
    """
    Place la mise dans le coupon de pari
    
    :param driver: Instance du driver Selenium
    :param mise: Montant de la mise
    :return: Dictionnaire avec le résultat
    """

    try:
        # Attendre que le coupon soit ouvert
        time.sleep(2)

        # Localiser le champ de mise
        try:
            champ_mise = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-test-id="betslip-stake-input"]'))
            )
        except TimeoutException:
            # Essayer un autre sélecteur
            try:
                champ_mise = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'coupon-bet-sum__input'))
                )
            except TimeoutException:
                return {
                    'success': False,
                    'message': 'Champ de mise non trouvé'
                }

        # Effacer et saisir la mise
        champ_mise.clear()
        time.sleep(0.5)
        champ_mise.send_keys(str(mise))
        time.sleep(0.5)

        # Vérifier que la mise a été saisie
        valeur_mise = champ_mise.get_attribute('value')
        if valeur_mise != str(mise):
            return {
                'success': False,
                'message': 'Erreur lors de la saisie de la mise'
            }

        return {
            'success': True,
            'message': 'Mise placée avec succès'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors du placement de la mise: {str(e)}'
        }


def valider_pari(driver):
    """
    Valide le pari en cliquant sur le bouton de validation
    
    :param driver: Instance du driver Selenium
    :return: Dictionnaire avec le résultat de la validation
    """

    try:
        # Localiser le bouton de validation
        try:
            bouton_validation = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'coupon-buttons'))
            )
        except TimeoutException:
            return {
                'success': False,
                'message': 'Bouton de validation non trouvé'
            }

        # Cliquer sur le bouton
        bouton_validation.click()
        time.sleep(2)

        # Attendre la fin du traitement
        try:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, 'ui-preloader-default'))
            )
        except TimeoutException:
            pass  # Le preloader peut ne pas apparaître

        # Vérifier le résultat de la validation
        try:
            # Rechercher un modal de succès
            modal_succes = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'coupon-success-modal'))
            )

            # Récupérer le numéro de coupon si disponible
            try:
                numero_coupon = modal_succes.find_element(By.CLASS_NAME, 'coupon-number').text
            except:
                numero_coupon = None

            return {
                'success': True,
                'message': 'Pari validé avec succès',
                'coupon_number': numero_coupon
            }

        except TimeoutException:
            # Vérifier s'il y a un message d'erreur
            try:
                erreur = driver.find_element(By.CLASS_NAME, 'notification-alert__text')
                return {
                    'success': False,
                    'message': f'Erreur de validation: {erreur.text}'
                }
            except:
                return {
                    'success': False,
                    'message': 'Validation échouée - statut inconnu'
                }

    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        }


def placer_pari_simple(driver, recherche_match, type_de_pari, mise):
    """
    Version simplifiée pour placer un pari rapidement
    
    :param driver: Instance du driver Selenium
    :param recherche_match: Texte de recherche pour le match
    :param type_de_pari: Type de pari ('1', 'X', '2', etc.)
    :param mise: Montant de la mise
    :return: Résultat de l'opération
    """

    print(f"Placement du pari: {recherche_match} - {type_de_pari} - {mise}€")

    # Recherche du match
    print("Recherche du match...")
    barre_recherche = driver.find_element(By.CLASS_NAME, 'games-search-app__search')
    barre_recherche.clear()
    barre_recherche.send_keys(recherche_match)
    time.sleep(2)

    # Sélection du pari
    print(f"Sélection du pari {type_de_pari}...")
    element_pari = driver.find_element(By.CSS_SELECTOR, f"[data-bet-type='{type_de_pari}']")
    element_pari.click()
    time.sleep(1)

    # Placement de la mise
    print(f"Placement de la mise: {mise}€...")
    champ_mise = driver.find_element(By.CLASS_NAME, 'coupon-bet-sum__input')
    champ_mise.clear()
    champ_mise.send_keys(str(mise))
    time.sleep(1)

    # Validation
    print("Validation du pari...")
    bouton_validation = driver.find_element(By.CLASS_NAME, 'coupon-buttons')
    bouton_validation.click()
    time.sleep(3)

    print("Pari placé avec succès !")
    return True


def tester_avec_donnees_exemple():
    """
    Fonction de test utilisant les données d'exemple fournies
    """

    # Données d'exemple pour les tests
    donnees_test = {
        "date": "05/09/2025",
        "equipe_1": "Club Canoneros Marina",
        "equipe_2": "Jaguares de Chiapas",
        "categorie": "Temps réglementaire",
        "type_de_pari": "Handicap asiatique",
        "selection": "Handiсap 2 (+0.75)",
        "odds": "1.1"
    }

    try:
        from ChromeDriver.SetDriver1 import driver

        # Test avec les données d'exemple
        resultat = placer_pari(
            driver, donnees_test
        )

        print("RÉSULTAT DU TEST:")
        print(json.dumps(resultat, indent=2, ensure_ascii=False))

        return resultat

    except ImportError:
        print("Erreur: Impossible d'importer le driver Chrome")
        return None
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        return None


if __name__ == "__main__":
    # Test avec les données d'exemple
    print("Lancement du test avec les données d'exemple...")
    tester_avec_donnees_exemple()
