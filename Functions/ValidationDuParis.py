import json
import os
import sys
import time
from datetime import datetime

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions.GetMise import GetMise
import config
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise
from Functions.GetCouponInfo import GetCouponInfo

try:
    from Functions import RedisIPC
except Exception:
    RedisIPC = None


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
    url = "http://bettracker.sc2vagr6376.universe.wf/backend/api.php?action=add"

    # Récupérer les données du pari validé si disponibles
    vb = getattr(config, 'validated_bet', None)

    # Préparer le payload conforme au format demandé
    # date doit être au format YYYY-MM-DD
    if vb and vb.get('timestamp'):
        date_val = vb.get('timestamp')[:10]
    else:
        date_val = datetime.now().strftime('%Y-%m-%d')

    stake_val = None
    try:
        stake_val = float(vb.get('montant')) if vb and vb.get('montant') is not None else float(
            getattr(config, 'mise', 0))
    except Exception:
        stake_val = float(getattr(config, 'mise', 0))

    odds_val = None
    try:
        odds_val = float(vb.get('cote')) if vb and vb.get('cote') is not None else float(getattr(config, 'cote', 0))
    except Exception:
        odds_val = float(getattr(config, 'cote', 0))

    match_val = ''
    if vb:
        match_val = vb.get('match') or (vb.get('equipe_1', '') + ' - ' + vb.get('equipe_2', '')).strip(' -')
    # Preferer la sélection (`bet`) extraite du coupon pour `bet_event`, sinon fallback sur le match
    bet_event_val = ''
    if vb and vb.get('bet'):
        bet_event_val = vb.get('bet')
    else:
        bet_event_val = match_val

    payload = {
        'date': date_val,
        'bookmaker': vb.get('bookmaker') if vb and vb.get('bookmaker') else '1xbet',
        'stake': stake_val,
        'odds': odds_val,
        'result': vb.get('result') if vb and vb.get('result') else 'en cours',
        'tipster': vb.get('tipster') if vb and vb.get('tipster') else getattr(config, 'tipster', 'ADR'),
        'bet_event': bet_event_val,
        'bet_to_recover_id': vb.get('bet_to_recover_id', '') if vb else '',
        'coupon': vb.get('coupon') if vb and vb.get('coupon') else '',
        'type_de_pari': vb.get('type_de_pari') if vb and vb.get('type_de_pari') else '',
        'equipe_1': vb.get('equipe_1') if vb and vb.get('equipe_1') else '',
        'equipe_2': vb.get('equipe_2') if vb and vb.get('equipe_2') else '',
        'match': match_val,
    }

    # Ajouter des champs utiles (coupon, raw match) si présents
    if vb:
        if vb.get('coupon'):
            payload['coupon'] = vb.get('coupon')
        payload['raw'] = vb

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict) and result.get('success') == True:
            print(f"✅ Paris enregistré avec succès (ID: {result.get('id')})")
            return True
        else:
            print(f"❌ Erreur lors de l'enregistrement : {result}")
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
    attempt = 3
    if config.scriptType in ['15V1', '15V2']:
       attempt = 2
    #return True # Temporary bypass for testing purposes, remove this line to enable full validation logic
    while not validation and tentative < attempt:
        config.log('Vérification des paris validés')
        config.log('Tentative', str(tentative))

        # Vérification que le jeu actuel et le set actuel n'ont pas déjà été pariés
        if hasattr(config, 'validated_bet') and config.validated_bet is not None:
            current_set = getattr(config, 'set_actuel', None)

            if (config.looking_game is not None and current_set is not None and
                    config.validated_bet.get('jeu') == config.looking_game and
                    config.validated_bet.get('set') == current_set and config.validated_bet.get(
                        'url') == config.ligue_name):
                if config.scriptType in ['15V1', '15V2']:
                    if config.validated_bet.get('numero_point') == config.looking_point:
                        config.log(f"1 Ce point ({config.looking_point}) et ce jeu ({config.looking_game}) ont déjà été pariés. Annulation.",
                                'warning', False)
                        validation = True
                        print(config.validated_bet)
                        already = True
                        break  # Sortir de la boucle si le jeu et le set ont déjà été pariés
                else:
                    config.log(f"2 Ce jeu ({config.looking_game}) et ce set ({current_set}) ont déjà été pariés. Annulation.",
                            'warning', False)
                    validation = True
                    print(config.validated_bet)
                    already = True
                    break
        config.log('Aucun pari validé ne correspond au jeu actuel, on continue la validation', 'info', False)
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
            try:
                if config.scriptType == 'LIVE' and config.site_type == 'mobile_site':
                    info = GetCouponInfo(driver)
            except Exception as e:
                config.log(f"Erreur GetCouponInfo: {e}", 'error', False)
                info = {}

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
                        cpn_setting = \
                            driver.find_elements(By.CLASS_NAME, config.classes['cpn_amount_input'][config.site_type])[0]
                        l = cpn_setting.get_attribute(
                            "value")
                        config.log("2 mise insérrer : " + str(l))
                        GetMise(driver)
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
                                print('click sur placer le paris')
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
                                try:
                                    if config.scriptType == 'LIVE' and config.site_type == 'mobile_site':
                                        close = False
                                    else:
                                        #info = GetCouponInfo(driver)
                                        close = True
                                    if ModalHandler(driver, close):
                                        validation = True
                                except Exception as e:
                                    config.log(f"Erreur lors de la validation du pari : {e}", 'error', False)
                                    validation = False
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

        if config.scriptType != 'LIVE':
            config.validated_bet = {
                'montant': config.mise,
                'cote': config.cote,
                'jeu': config.looking_game,
                'set': config.set_actuel if hasattr(config, 'set_actuel') else None,
                'numero_point': config.looking_point if hasattr(config, 'looking_point') else None,
                'winscore': config.win_type,
                'timestamp': current_timestamp,
                'url': url_to_store
            }
        else:
            # Récupérer les informations depuis la modal via GetCouponInfo
            # Fusionner les valeurs essentielles
            if info:
                validated = {
                    'montant': info.get('montant', config.mise),
                    'cote': info.get('cote', config.cote),
                    'match': info.get('match'),
                    'equipe_1': info.get('equipe_1'),
                    'equipe_2': info.get('equipe_2'),
                    'type_de_pari': info.get('type_de_pari'),
                    'bet': info.get('bet'),
                    'coupon': info.get('coupon'),
                    'timestamp': info.get('timestamp'),
                    'tipster': info.get('tipster'),
                    'bet_to_recover_id': config.bet_to_recover_id if hasattr(config, 'bet_to_recover_id') else '',
                }
                config.validated_bet = validated
            # Envoyer les données au service distant
            try:
                SendBetData()
            except Exception as e:
                config.log(f"Erreur lors de l'envoi des données du pari : {e}", 'error', False)

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

        config.perte = RedisIPC.get_loss(config.scriptType)  # Just to log the current loss before updating it

        config.perte = float(config.perte) + float(config.mise)

        # Enregistrer la perte via RedisIPC si disponible, sinon fallback vers l'API distante
        if RedisIPC:
            RedisIPC.set_loss(getattr(config, 'scriptType', 'UNKNOWN'), float(config.perte), publish=True)

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
    config.site_type = 'mobile_site'
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'new_site'
    config.scriptType = 'LIVE'
    config.tipster = 'ADR'
    config.mise = 0.2
    ValidationDuParis(driver)
