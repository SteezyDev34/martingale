import json
import os
import time
import sys
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfNewSite import GetIfNewSite
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise


def SendBetData():
    """
    Envoie les données du pari à l'API.
    
    Args:
        coupon_number (str): Numéro du coupon
        cote_globale (str): Cote globale du pari
        type_pari (str): Type de pari
        mise (float): Montant de la mise
        gains_potentiels (float): Gains potentiels
        match_details (dict): Détails du match (équipes, ligue)
        cote (str): Cote du pari
        statut (str): Statut du pari
        script (str): Type de script
        
    Returns:
        bool: True si l'envoi a réussi, False sinon
    """

    # Construction de l'URL de l'API
    url = "https://p-com.studio/api/insert_paris.php"

    try:
        # Préparation des données à envoyer en POST
        data = {
            'coupon_number': '0',
            'type_pari': config.win_type,
            'mise': config.mise,
            'gains_potentiels': config.netprofit,
            'match_details': json.dumps({'teams': config.teams, 'league': config.ligue_name}),
            'cote': config.cote,
            'script': config.scriptType
        }

        # Envoi de la requête POST avec les données
        response = requests.post(url, data=data)

        # Vérifier que la requête a réussi
        response.raise_for_status()

        # Parser le JSON depuis la réponse
        result = response.json()

        if result['status'] == "success":
            print(f"✅ Paris enregistré avec succès (ID: {result['id']})")
            return True
        else:
            print(f"❌ Erreur lors de l'enregistrement : {result['message']}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête HTTP : {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Erreur lors du parsing du JSON : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return False


def ValidationDuParis(driver, nexbet=False):
    validation = False
    tentative = 0
    already = False
    while not validation and tentative < 3:
        config.log('Vérification des paris validés')
        config.log('Tentative', str(tentative))

        # Vérification que le jeu actuel et le set actuel n'ont pas déjà été pariés
        if hasattr(config, 'validated_bet') and config.validated_bet is not None:
            current_set = getattr(config, 'set_actuel', None)

            if (config.looking_game is not None and current_set is not None and
                    config.validated_bet.get('jeu') == config.looking_game and
                    config.validated_bet.get('set') == current_set and config.validated_bet.get(
                        'url') == config.ligue_name):
                config.log(f"Ce jeu ({config.looking_game}) et ce set ({current_set}) ont déjà été pariés. Annulation.",
                           'warning', False)
                validation = True
                print(config.validated_bet)
                already = True
                break  # Sortir de la boucle si le jeu et le set ont déjà été pariés
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, config.classes['cpn_amount_input'][config.site_type])[0]
            l = cpn_setting.get_attribute("value")
            config.log("mise insérée : " + str(l), 'info', indent=2)
        except Exception as e:
            tentative += 1
            config.log('erreur verification mise')
            if tentative > 2:
                break
        else:
            if str(l) == str(config.mise):
                sending_mise = 1
                config.log('RECHERCHE DU BOUTON PLACER UN PARIS', 'info', False, 2)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        config.classes['coupon_buttons'][config.site_type]))
                    )
                except Exception as e:
                    config.log('zone de bouton non trouvé!', 'error', False)
                    tentative = tentative + 1
                    validation = ModalHandler(driver)
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = \
                            driver.find_elements(By.CLASS_NAME, config.classes['cpn_amount_input'][config.site_type])[0]
                        l = cpn_setting.get_attribute(
                            "value")
                        config.log("mise insérrer : " + str(l))
                    except Exception as e:
                        config.log(f"#E005689\nUne erreur est survenue : {e}")
                        tentative = tentative + 1
                        if ModalHandler(driver):
                            validation = True
                    else:
                        if str(l) == str(config.mise):
                            getbtn = driver.find_element(By.CLASS_NAME,
                                                         config.classes['coupon_buttons'][config.site_type])
                            try:
                                getbtn.click()
                            except:
                                tentative = tentative + 1
                                if ModalHandler(driver):
                                    validation = True
                            else:
                                tentative = tentative + 1
                                preloader = 1
                                printtext = 0
                                line = 0
                                while preloader == 1:

                                    try:
                                        if printtext == 0:
                                            waiting_time = 5
                                        else:
                                            waiting_time = 1
                                        WebDriverWait(driver, waiting_time).until(EC.visibility_of_element_located(
                                            (By.CLASS_NAME, config.classes['preloader'][config.site_type])))
                                    except:
                                        config.log('pas de loader', 'infos', False, indent=3)
                                        line += 1
                                        preloader = 0
                                    else:
                                        if printtext == 0:
                                            config.log('loading...', 'infos', False, indent=3)
                                            line += 1
                                            printtext = 1
                                config.log_clear_line(line)
                                if ModalHandler(driver):
                                    validation = True
                        else:
                            PlacerMise(driver)
                            tentative = tentative + 1
            else:
                PlacerMise(driver)
                tentative = tentative + 1
    if validation and not already:
        # Store bet information in validated_bet variable
        from datetime import datetime
        # SendBetData()
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Create validated bet data
        # Déterminer l'URL à stocker : pour le script 1SET on veut l'URL courante du driver
        try:
            if getattr(config, 'scriptType', None) == '1SET':
                url_to_store = driver.current_url
            else:
                url_to_store = config.ligue_name
        except Exception:
            # En cas de problème d'accès au driver, revenir à la valeur par défaut
            url_to_store = getattr(config, 'ligue_name', None)

        config.validated_bet = {
            'montant': config.mise,
            'cote': config.cote,
            'jeu': config.looking_game,
            'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
            'winscore': config.win_type,
            'timestamp': current_timestamp,
            'url': url_to_store
        }

        # Save validated bet to JSON file named after script type
        json_filename = f"{config.scriptType}_validated_bets.json"
        try:
            # Chargement des paris existants avec gestion de corruption JSON
            try:
                with open(json_filename, 'r') as f:
                    existing_bets = json.load(f)
            except FileNotFoundError:
                existing_bets = []
            except json.JSONDecodeError as e:
                # Sauvegarde du fichier corrompu
                backup_name = json_filename.replace('.json', f'_corrupted_{int(time.time())}.json')
                os.rename(json_filename, backup_name)
                config.log(f"Fichier JSON corrompu détecté, backup créé : {backup_name}", 'error', False)
                existing_bets = []

            # Ajout du nouveau pari
            existing_bets.append(config.validated_bet)

            # Sauvegarde des paris mis à jour
            with open(json_filename, 'w') as f:
                json.dump(existing_bets, f, indent=4)
        except Exception as e:
            config.log(f"Erreur lors de la sauvegarde du pari validé dans le JSON : {e}", 'error', False)
        config.placed_game = config.looking_game
        config.log(f'{config.validated_bet}', 'info', False, indent=3)
        config.perte = float(config.perte) + float(config.mise)
        config.wantwin = float(config.wantwin) + float(config.increment)
        # Calculate net profit based on stake, odds and losses
        config.log('Perte ' + str(config.perte))
        config.netprofit = round(
            (float(config.mise) * float(config.cote)) - float(config.perte), 2)
        config.log(f'Potential Net profit: {config.netprofit}', 'title', clear=False, indent=3)
    return validation


if __name__ == "__main__":
    # driver.switch_to.window(driver.window_handles[0])
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '40A'
    config.mise = 0.2
    ValidationDuParis(driver)
