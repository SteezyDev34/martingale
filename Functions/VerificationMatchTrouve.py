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


def _has_scripttype_for_bot_family(match_id):
    """
    Vérifie que le match a au moins un scriptType compatible avec le bot_family en
    cours (1530A ou 456P), pour ne pas ouvrir un match dont les scriptTypes calculés
    au classement (cf. traiter_matchlist) ne concernent que l'autre famille de bots.
    """
    bot_family = getattr(config, 'bot_family', None)
    if bot_family not in ('1530A', '456P'):
        return True
    script_cfg = match_manager.get_match_script_config(match_id)
    script_types = script_cfg.get('script_types', []) if script_cfg else []
    if not script_types:
        return True  # laisse la vérification distante/legacy décider
    valid = config.VALID_SCRIPTTYPES_1530A if bot_family == '1530A' else config.VALID_SCRIPTTYPES_456P
    return any(st in valid for st in script_types)


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
        match_is_todo_raw = match_manager.is_match_todo(config.newmatch)
        # Si le match est dans matches_todo mais qu'aucun de ses scriptTypes calculés au
        # classement ne concerne le bot_family en cours (1530A vs 456P), il ne faut pas
        # l'accepter — sinon on retombe dans la branche "match inconnu" ci-dessous qui
        # accepte quand même (elle est faite pour les VRAIS matchs jamais classés).
        match_has_valid_scripttype = _has_scripttype_for_bot_family(config.newmatch) if match_is_todo_raw else True
        match_is_todo = match_is_todo_raw and match_has_valid_scripttype
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
        elif config.in_stat and match_is_todo_raw and not match_has_valid_scripttype and not match_is_done:
            # Match connu (classé) mais aucun scriptType compatible avec ce bot_family
            # (ex: match calculé pour 456P uniquement, scanné par un bot 1530A) → rejeté
            # explicitement, sans navigation (contrairement au cas "match inconnu" ci-dessous).
            config.log('Le match n\'est pas autorisé (scriptType non compatible avec ce bot)!', 'warning', True, 4, False)
            config.log_clear_line()
            return [False, config.newmatch]
        elif config.in_stat and not match_is_todo_raw and not match_is_done:
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
