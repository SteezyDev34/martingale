# Function_VerificationMatchTrouve
#VERRIFICATION DU MATCH TROUVÉ
from selenium.webdriver.common.by import By
import config
import GetMatchDone
def main(driver,bet_item,matchlist_file_name):
    try:
        newmatchtxt = bet_item.find_elements(By.CLASS_NAME,
                                             'c-events__name')[
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
        print('newmatch : '+config.newmatch)
        match_list = GetMatchDone.main(matchlist_file_name)
        config.saveLog(match_list, config.newmatch)
        if not any( config.newmatch in x for x in match_list):
            txtlog = "Le match n\'a pas encore été parié!"
            config.saveLog(txtlog, config.newmatch)
            driver.get(newmatchtxt)
            return [True,config.newmatch]
        else:
            txtlog = 'Le match a déjà été parié!'
            config.saveLog(txtlog, config.newmatch)
            return [False, config.newmatch]

#VERRIFICATION DU MATCH TROUVÉ PAR URL
def fromUrl(driver,matchlist_file_name):
    try:
        newmatchtxt = driver.current_url
        newmatch = newmatchtxt.split(
            '-')
        config.newmatch = newmatch[-3] + '-' + newmatch[-2] + '-' + newmatch[-1]
    except Exception as e:
        print(f"#E0007\nUne erreur est survenue : {e}")
        print('Impossible de lire le lien du match!')
        return [False, config.newmatch]
    else:
        #print('newmatch : '+newmatch)
        match_list = GetMatchDone.main(matchlist_file_name)
        if not any( config.newmatch in x for x in match_list):
            #print('Le match n\'a pas encore été parié!')
            return [True,config.newmatch]
        else:
            txtlog = 'Le match a déjà été parié!'
            config.saveLog(txtlog, config.newmatch)
            return [False, config.newmatch]