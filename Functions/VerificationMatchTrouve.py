# Function_VerificationMatchTrouve
# VERRIFICATION DU MATCH TROUVÉ

from selenium.webdriver.common.by import By

import config
from Functions.GetJsonData import getIfGlobalPerte, getIf1setGlobalPerte
from Functions.Managers.MatchManager import MatchManager

# Initialiser l'instance du gestionnaire de matchs
match_manager = MatchManager.get_instance()


def _navigate(driver, url):
    """Navigate via bridge si actif, sinon Selenium."""
    try:
        from Functions.BridgeAdapter import bridge_active
        if bridge_active():
            from websocket_server import bridge as _bridge
            _bridge.navigate(url)
            return
    except Exception:
        pass
    if driver:
        driver.get(url)


def main(driver, bet_item, matchlist_file_name):
    try:
        # config.log('Vérification si match déjà parié', 'info', True, 4)
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             config.classes['match_link'][config.site_type])[
            0].get_attribute(
            "href")
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        config.log('Impossible de lire le lien du match!', 'warning', False, 4)
        config.log_clear_line()
        return [False, config.newmatch]
    else:
        # Vérification si le match est déjà traité ou en attente
        match_is_done = match_manager.match_exists(config.newmatch)
        match_is_todo = match_manager.is_match_todo(config.newmatch)
        print('match_is_done', match_is_done)
        print('match_is_todo', match_is_todo)
        print('config.site_type ', config.site_type)
        if config.scriptType == '1SET' and not match_is_done:
            config.log('Le match autorisé!', 'success', False, 4, False)
            if config.site_type == 'mobile_site':
                newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
                newmatchtxt = f'{newmatchtxt}?platform_type=mobile'
            _navigate(driver, newmatchtxt)
            config.log_clear_line()
            return [True, config.newmatch]
        elif config.in_stat and match_is_todo and not match_is_done:
            config.log('Le match autorisé!', 'success', False, 4, False)
            if config.site_type == 'mobile_site':
                newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
                newmatchtxt = f'{newmatchtxt}?platform_type=mobile'
            _navigate(driver, newmatchtxt)
            config.log_clear_line()
            return [True, config.newmatch]
        elif config.in_stat and not match_is_todo and not match_is_done:
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4, False)
            config.log_clear_line()
            _navigate(driver, newmatchtxt)
            return [True, config.newmatch]
        else:
            
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4, False)
            config.log_clear_line()
            return [False, config.newmatch]


def getstats(driver, bet_item, matchlist_file_name):
    try:
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'dashboard-game-block__link')[
            0].get_attribute(
            "href")
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        print(f"#E0007\nUne erreur est survenue : {e}")
        print('Impossible de lire le lien du match!')
        return [False, config.newmatch]
    else:
        print('newmatch : ' + config.newmatch)
        match_is_todo = match_manager.is_match_todo(config.newmatch)

        if match_is_todo:
            txtlog = "          Le match n'a pas encore été parié!"
            config.log(txtlog, config.newmatch)
            if config.site_type == 'mobile_site':
                newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
                newmatchtxt = f'{newmatchtxt}?platform_type=mobile'
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        else:
            txtlog = '          Le match a déjà été parié!'
            config.log(txtlog, config.newmatch)
            return [False, config.newmatch]


# VERRIFICATION DU MATCH TROUVÉ PAR URL
def fromUrl(driver, matchlist_file_name):
    try:
        config.log('            Vérification si match déjà parié', 'info', True)
        newmatchtxt = _get_current_url(driver)

        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        config.log('            Impossible de lire le lien du match!', 'warning', False)
        return [False, config.newmatch]
    else:
        match_is_todo = match_manager.is_match_todo(config.newmatch)

        if match_is_todo:
            config.log('        Le match autorisé!', 'warning', True)
            return [True, config.newmatch]
        else:
            config.log('            Le match n\'est pas autorisé!', 'warning', True)
            return [False, config.newmatch]


# VERRIFICATION DU MATCH TROUVÉ PAR URL
def _get_current_url(driver):
    """Retourne l'URL courante via bridge ou Selenium."""
    try:
        from Functions.BridgeAdapter import bridge_active
        if bridge_active():
            from websocket_server import bridge
            state = bridge.get_state()
            return (state or {}).get('url', '') or ''
    except Exception:
        pass
    return driver.current_url if driver else ''


def newmatchFromUrl(driver):
    try:
        newmatchtxt = _get_current_url(driver)
        newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
        newmatchtxt = newmatchtxt.replace('?platform_type=mobile', '')
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        config.log('        Impossible de lire le lien du match!', 'warning', False)
        config.log_clear_line()
        return [False, config.newmatch]
    else:
        return [True, config.newmatch]
