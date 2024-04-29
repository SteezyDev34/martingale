# get_ligue_name
from selenium.webdriver.common.by import By


def main(bet_ligue):
    ligue_name = False
    try:
        div_ligue_name = bet_ligue.find_element(By.TAG_NAME, 'div')
    except Exception as e:
        #print (f"#E0004\nUne erreur est survenue : {e}")
        print('Lecture nom ligue impossible!')
        ligue_name = False
    else:
        try:
            ligue_name = div_ligue_name.find_element(By.CLASS_NAME,
                                                     'c-events__name')
            ligue_name = ligue_name.text.lower()
            ligue_name = ligue_name.replace('.', '')
        except Exception as e:
            print(f"#E0005\nUne erreur est survenue : {e}")
            ligue_name = False
        #else:
            #print('a Nom de la ligue :'+ligue_name)
    return ligue_name
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
    ligue_name = get_url
    '''if len(re.findall("wta",get_url.lower())) >0:
        ligue_name ='wta'
    elif len(re.findall("atp",get_url.lower())) >0:
        ligue_name = 'atp'
    elif len(re.findall("itf", get_url.lower())) > 0:
        ligue_name = 'itf'
    else:
        ligue_name = '''''
    return [ligue_name,driver.current_url]