# get_ligue_name
from selenium.webdriver.common.by import By
import config

def main(bet_ligue):
    config.ligue_name = False
    try:
        div_ligue_name = bet_ligue.find_element(By.TAG_NAME, 'div')
    except Exception as e:
        txtlog = "Lecture nom ligue impossible!"
        config.saveLog(txtlog, config.newmatch)
        config.ligue_name = False
    else:
        try:
            config.ligue_name = div_ligue_name.find_element(By.CLASS_NAME,
                                                     'c-events__name')
            config.ligue_name = config.ligue_name.text.lower()
            config.ligue_name = config.ligue_name.replace('.', '')
        except Exception as e:
            config.saveLog(f"#E0005\nUne erreur est survenue : {e}")
            config.ligue_name = False
    return config.ligue_name
# GetLigueNameFromUrl
def fromUrl(driver):
    get_url = driver.current_url
    #print(" url = "+get_url)
    get_url = get_url.split('tennis/')
    get_url = get_url[1].split('/')
    get_url = get_url[0]
    get_url = get_url.split('-')
    del get_url[0]
    get_url = (' ').join(get_url)
    config.ligue_name = get_url
    '''if len(re.findall("wta",get_url.lower())) >0:
        ligue_name ='wta'
    elif len(re.findall("atp",get_url.lower())) >0:
        ligue_name = 'atp'
    elif len(re.findall("itf", get_url.lower())) > 0:
        ligue_name = 'itf'
    else:
        ligue_name = '''''
    return [config.ligue_name,driver.current_url]