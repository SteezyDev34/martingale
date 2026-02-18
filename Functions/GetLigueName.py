# get_ligue_name
from selenium.webdriver.common.by import By

import config


def main(bet_ligue):
    config.ligue_name = False
    try:
        div_ligue_name = bet_ligue.find_element(By.TAG_NAME, 'div')
    except Exception as e:
        config.log('Lecture nom ligue impossible!', 'warning', False, 2)
        config.ligue_name = False
        config.log_clear_line()
    else:
        try:
            config.ligue_name = div_ligue_name.find_element(By.CLASS_NAME,
                                                            'dashboard-champ-name__caption')
            config.ligue_name = config.ligue_name.text.lower()
            config.ligue_name = config.ligue_name.replace('.', '')
        except Exception as e:
            config.log(f'#E0005 Une erreur est survenue : {e}', 'warning', False, 2)
            config.ligue_name = False
            config.log_clear_line()
    return config.ligue_name


# GetLigueNameFromUrl
def fromUrl(driver):
    get_url = driver.current_url
    print(" url = " + get_url)
    get_url = get_url.split('basketball/')
    get_url = get_url[1].split('/')
    get_url = get_url[0]
    get_url = get_url.split('-')
    del get_url[0]
    get_url = (' ').join(get_url)
    config.ligue_name = get_url
    return [config.ligue_name, driver.current_url]


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    print(fromUrl(driver))
