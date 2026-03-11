# Function_VerificationMatchTrouve
# VERRIFICATION DU MATCH TROUVÉ

from urllib.parse import urlparse

from selenium.webdriver.common.by import By

import config
from Functions import GetMatchDone
from Functions.GetJsonData import getIfGlobalPerte


def extract_match_slug_from_url(match_url):
    path = urlparse(match_url).path.strip('/')
    if not path:
        return ''

    last_segment = path.split('/')[-1]
    if not last_segment:
        return ''

    parts = [part for part in last_segment.split('-') if part]
    if len(parts) >= 2 and parts[0].isdigit():
        return '-'.join(parts[1:])
    return '-'.join(parts)


def main(driver, bet_item, matchlist_file_name):
    try:
        config.log('Vérification si match déjà parié', 'info', True, 4)
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'dashboard-game-block__link')[
            0].get_attribute(
            "href")
        config.newmatch = extract_match_slug_from_url(newmatchtxt)
        print(config.newmatch)
    except Exception as e:
        config.log('Impossible de lire le lien du match!', 'warning', False, 4)
        config.log_clear_line()
        return [False, config.newmatch]
    else:
        match_list = GetMatchDone.main(config.matchlist_file_name)
        if config.in_stat and any(config.newmatch in x for x in match_list):
            config.log('Le match autorisé!', 'success', False, 4)
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        elif config.in_stat and not any(config.newmatch in x for x in match_list):
            print('vérif si perte')
            p = config.perte
            if not p or p == 0:
                p = getIfGlobalPerte()
            if not p or p == 0:
                config.log('Le match  n\'est pas autorisé! pas de perte', 'warning', True, 4, False)
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
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4)
            return [False, config.newmatch]


def getstats(driver, bet_item, matchlist_file_name):
    try:
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'dashboard-game-block__link')[
            0].get_attribute(
            "href")
        config.newmatch = extract_match_slug_from_url(newmatchtxt)
    except Exception as e:
        print(f"#E0007\nUne erreur est survenue : {e}")
        print('Impossible de lire le lien du match!')
        return [False, config.newmatch]
    else:
        print('newmatch : ' + config.newmatch)
        match_list = GetMatchDone.main(config.matchlisttodo_file_name)
        config.log(match_list, 'info', False, 4)
        if any(config.newmatch in x for x in match_list):
            txtlog = "          Le match n\'a pas encore été parié! 111"
            config.log(txtlog, config.newmatch)
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        else:
            txtlog = '          Le match a déjà été parié! 111'
            config.log(txtlog, config.newmatch)
            return [False, config.newmatch]


# VERRIFICATION DU MATCH TROUVÉ PAR URL
def fromUrl(driver, matchlist_file_name):
    try:
        config.log('            Vérification si match déjà parié', 'info', True)
        newmatchtxt = driver.current_url
        config.newmatch = extract_match_slug_from_url(newmatchtxt)
    except Exception as e:
        config.log('            Impossible de lire le lien du match!', 'warning', False)
        return [False, config.newmatch]
    else:
        match_list = GetMatchDone.main(config.matchlist_file_name)
        if config.in_stat and any(config.newmatch in x for x in match_list):
            config.log('Le match autorisé!', 'success', False, 4)
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        elif not config.in_stat and not any(config.newmatch in x for x in match_list):
            config.log('Le match autorisé!', 'success', False, 4)
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        else:
            config.log('Le match  n\'est pas autorisé!', 'warning', True, 4)
            return [False, config.newmatch]


# VERRIFICATION DU MATCH TROUVÉ PAR URL
def newmatchFromUrl(driver):
    try:
        newmatchtxt = driver.current_url
        config.newmatch = extract_match_slug_from_url(newmatchtxt)
    except Exception as e:
        config.log('        Impossible de lire le lien du match!', 'warning', False)
        config.log_clear_line()
        return [False, config.newmatch]
