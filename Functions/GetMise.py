# GetMise
import os
import sys

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions import RedisIPC
import config


def GetMise(driver):
    logline = 0
    if config.rattrape_perte == 3:
        config.log('Bonne proba, cote : 3', 'info', False)
        logline += 1
        config.cote = config.cotebase
    else:
        # Si la cote a déjà été stockée dans validated_bet (même jeu/pari),
        # la réutiliser directement — elle ne change pas entre le pré-chargement
        # et le placement. Seule la perte varie (deduct_largest inter-scripts).
        # Cela évite un aller-retour DOM inutile de ~200ms.
        cote_vb = None
        try:
            vb = getattr(config, 'validated_bet', None)
            if vb and vb.get('cote'):
                _c = str(vb['cote']).replace(',', '.')
                if float(_c) > 1.0:
                    cote_vb = _c
        except Exception:
            pass
        if cote_vb:
            config.cote = cote_vb
            config.log(f'cote recupéré (validated_bet) {str(config.cote)}', 'info', False)
            logline += 1
        else:
            config.log("Rattrapage, recuperation de la cote", 'info', False)
            logline += 1
            from Functions.BridgeAdapter import bridge_active
            if bridge_active():
                # Cote déjà lue lors de la sélection du marché (bridge.select_market_by_text),
                # évite un aller-retour DOM supplémentaire — même sémantique que le fallback
                # `config.cotebase` ci-dessous si elle n'est pas disponible.
                bridge_cote = getattr(config, '_bridge_last_cote', None)
                if bridge_cote:
                    config.cote = bridge_cote
                    config.log(f'cote recupéré (bridge) {str(config.cote)}', 'info', False)
                else:
                    config.cote = config.cotebase
                logline += 1
            else:
                try:
                    config.log(f"tentative de recup cote avec class {config.classes['coef_value'][config.site_type]}", 'info', False)
                    config.cote = ''.join(filter(lambda x: x.isdigit() or x in ',.',
                                                driver.find_elements(By.CLASS_NAME,
                                                                    config.classes['coef_value'][config.site_type])[0].text))
                except Exception as e:
                    try:
                        if config.scriptType == 'LIVE' and config.site_type == 'mobile_site':
                            config.cote = ''.join(filter(lambda x: x.isdigit() or x in ',.',
                                                            driver.find_elements(By.CLASS_NAME,
                                                                                config.classes['coef_value'][config.site_type])[0].text))
                        else:
                            config.log(f"tentative de recup cote avec class {config.classes['cpn_action_coef'][config.site_type]}", 'info', False)

                    except Exception as e:
                        print(e)
                        config.log('erreur recup cote', 'info', False)
                        logline += 1
                        config.cote = config.cotebase
                else:
                    config.log(f'cote recupéré {str(config.cote)}', 'info', False)
                    logline += 1
                    if config.cote == '' or str(config.cote) == '0' or str(config.cote) == '1' or config.cote == 0:
                        config.cote = config.cotebase
    if config.scriptType == 'LIVE':
        try:
            resp_json = get_recommended_stake()
            config.mise = round(float(resp_json.get('recommended_stake', 0)), 2)
            # Si 'last_lost_bet_id' existe, le récupérer sinon mettre une chaîne vide
            config.bet_to_recover_id = resp_json.get('last_lost_bet_id') or ''
        except Exception as e:
            config.log(f"Impossible de récupérer la mise recommandée: {e}", 'warning', False)
            config.mise = round(float(getattr(config, 'mise', 0)), 2)
            config.bet_to_recover_id = ''
        config.log_clear_line(logline)
        if config.mise < 0.2:
            config.mise = 0.2
        return True
    else:
        if RedisIPC.get_loss(config.scriptType, config.perte) is not None:
            config.perte = RedisIPC.get_loss(config.scriptType, config.perte)
        config.mise = (float(config.wantwin) + float(config.perte)) / (float(config.cote) - 1)
    config.mise = round(config.mise, 2)
    if config.mise < 0.2:
        config.mise = 0.2
    txtlog = "cote : " + str(config.cote) + " | perte : " + str(
        config.perte) + " | wantwin : " + str(
        config.wantwin) + " | mise : " + str(config.mise)
    config.log(txtlog, 'info', False, indent=3)
    logline += 1
    getmisemax = True
    tentative = 0
    while not getmisemax:
        try:
            btn_extra = driver.find_elements(By.CLASS_NAME,
                                             'cpn-extra__btn')[
                0]
        except:
            tentative += 1
            if tentative > 5:
                getmisemax = True
                config.misemax = 0
        else:
            btn_extra.click()
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'cpn-dropdown--is-active'))
                )
                btn_extra = driver.find_elements(By.CLASS_NAME,
                                                 'cpn-dropdown--is-active')[
                    0]
            except:
                tentative += 1
                if tentative > 5:
                    getmisemax = True
                    config.misemax = 0
            else:
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                                    'cpn-dropdown__content')[
                    0]
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                                    'cpn-extra-settings__item')[
                    0]
                btn_extra = btn_extra.find_elements(By.CLASS_NAME,
                                                    'cpn-extra-settings__btn')[
                    0].text
                try:
                    config.misemax = float(btn_extra.split(' EUR')[0].replace(' ', ''))
                except:
                    getmisemax = True
                    config.misemax = 0
                else:
                    getmisemax = True
    config.log_clear_line(logline)
    return True

def get_recommended_stake(cote=None, tipster=None, bankroll_id=2, target_percentage=1, recover_losses=1):
    """
    Récupère la mise recommandée depuis l'API AuxoTracker via la route bot (/auxobot/recommended-stake).
    Authentification par AUXOBOT_TOKEN (middleware auxobot), pas Sanctum.
    Lève une exception en cas d'erreur. Le caller doit gérer l'exception.
    """
    cote = cote or config.cote
    tipster = tipster or config.tipster

    base = getattr(config, 'AUXOTRACK_API_URL', 'https://api.auxotracker.p-com.studio')
    url = f"{base.rstrip('/')}/api/auxobot/recommended-stake"

    headers = {'Accept': 'application/json'}
    token = getattr(config, 'AUXOBOT_TOKEN', None)
    if token:
        headers['Authorization'] = f'Bearer {token}'

    params = {
        'user_id': getattr(config, 'AUXOBOT_USER_ID', 3),
        'tipster': tipster,
        'target_percentage': target_percentage,
        'recover_losses': recover_losses,
        'odds': cote,
    }
    if bankroll_id is not None:
        params['bankroll_id'] = bankroll_id

    config.log("-" * 50, "info", False)
    config.log("Récupération de la mise recommandée depuis l'API", "info", False)
    try:
        req = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
        req.raise_for_status()
        data = req.json()
        config.log(f"Requête envoyée à l'API: {req.url}", "info", False)
        config.log(f"Réponse de l'API: {data}", "info", False)
        return data
    except requests.RequestException as e:
        config.log(f"Erreur API recommended-stake: {e}", 'error', False)
        raise


if __name__ == "__main__":
    from websocket_server import start_bridge
    from Functions.GetSetActuel import GetSetActuel
    from Functions.GetJeuActuel import GetJeuActuel
    from Functions.GetScoreActuel import GetScoreActuel
    from Functions.AfficherParis import AfficherParis
    from Functions.GetBetOld import GetBetOld

    start_bridge(wait_timeout=15)
    config.site_type = 'mobile_site'
    config.scriptType = '30A'
    config.perte = 2

    GetSetActuel(None)
    GetScoreActuel(None)
    GetJeuActuel(None)
    config.looking_game = int(config.jeu_actuel)
    print("AfficherParis:", AfficherParis(None))
    print("GetBetOld:", GetBetOld(None))
    print("cote captée:", getattr(config, '_bridge_last_cote', None))

    print("GetMise:", GetMise(None))
    print("config.mise:", config.mise, "config.cote:", config.cote)

