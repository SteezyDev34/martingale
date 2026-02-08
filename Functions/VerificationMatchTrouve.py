# Function_VerificationMatchTrouve
# VERRIFICATION DU MATCH TROUVÉ

from selenium.webdriver.common.by import By

import config
from Functions.GetJsonData import getIfGlobalPerte, getIf1setGlobalPerte
from Functions.Managers.MatchManager import MatchManager

# Initialiser l'instance du gestionnaire de matchs
match_manager = MatchManager.get_instance()


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
            driver.get(newmatchtxt)
            config.log_clear_line()
            return [True, config.newmatch]
        elif config.in_stat and match_is_todo and not match_is_done:
            config.log('Le match autorisé!', 'success', False, 4, False)
            if config.site_type == 'mobile_site':
                newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
                newmatchtxt = f'{newmatchtxt}?platform_type=mobile'
            driver.get(newmatchtxt)
            config.log_clear_line()
            return [True, config.newmatch]
        elif not config.in_stat and not match_is_todo and not match_is_done:
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4, False)
            # blocage des autres match en atente d'un plus gros BK
            return [False, config.newmatch]
            p = config.perte
            if not p or p == 0:
                p = getIfGlobalPerte()
            if not p or p == 0:
                p = getIf1setGlobalPerte()
            if not p or p == 0:
                config.log('Le match  n\'est pas autorisé!', 'warning', True, 4, False)
                return [False, config.newmatch]
            else:
                config.log('Le match  non autorisé mais perte en cours', 'success', False, 4, False)
                if config.site_type == 'mobile_site':
                    newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
                    newmatchtxt = f'{newmatchtxt}?platform_type=mobile'
                driver.get(newmatchtxt)
                config.log_clear_line()
                return [True, config.newmatch]
        else:
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4, False)
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
        newmatchtxt = driver.current_url

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
def newmatchFromUrl(driver):
    try:
        newmatchtxt = driver.current_url
        newmatchtxt = newmatchtxt.replace('?platform_type=desktop', '')
        newmatchtxt = newmatchtxt.replace('?platform_type=mobile', '')
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        config.log('        Impossible de lire le lien du match!', 'warning', False)
        config.log_clear_line()
        return [False, config.newmatch]
