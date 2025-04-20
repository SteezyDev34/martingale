# Function_VerificationMatchTrouve
# VERRIFICATION DU MATCH TROUVÉ

from selenium.webdriver.common.by import By

import config
from Functions import GetMatchDone


def main(driver, bet_item, matchlist_file_name):
    try:
        config.log('Vérification si match déjà parié', 'info', False, 4)
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'dashboard-game-block__link')[
            0].get_attribute(
            "href")
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
        print(config.newmatch)
    except Exception as e:
        config.log('Impossible de lire le lien du match!', 'warning', False, 4)
        config.log_clear_line()
        return [False, config.newmatch]
    else:
        match_list = GetMatchDone.main(config.matchlisttodo_file_name)
        if any(config.newmatch in x for x in match_list):
            config.log('Le match autorisé!', 'success', False, 4)
            driver.get(newmatchtxt)
            return [True, config.newmatch]
        else:
            config.log('Le match  n\'est pas autorisé!', 'warning', False, 4)
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
        match_list = GetMatchDone.main(matchlist_file_name)
        config.log(match_list, config.newmatch)
        if any(config.newmatch in x for x in match_list):
            txtlog = "          Le match n\'a pas encore été parié!"
            config.log(txtlog, config.newmatch)
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
        match_list = GetMatchDone.main(matchlist_file_name)
        if any(config.newmatch in x for x in match_list):
            config.log('        Le match autorisé!', 'warning', True)
            return [True, config.newmatch]
        else:
            config.log('            Le match  n\'est pas autorisé!', 'warning', True)
            return [False, config.newmatch]


# VERRIFICATION DU MATCH TROUVÉ PAR URL
def newmatchFromUrl(driver):
    try:
        newmatchtxt = driver.current_url
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        config.log('        Impossible de lire le lien du match!', 'warning', False)
        config.log_clear_line()
        return [False, config.newmatch]
