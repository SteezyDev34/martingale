import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.Function_GetSetActuel import GetSetActuel
from Functions.GetIfMatchPage import GetIfMatchPage


# from ChromeDriver.SetDriver1 import driver


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    tentative = 0
    while not get_score:
        try:
            score_teams = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  'scoreboard-scores__item'))
            )
            score_teams = driver.find_elements(By.CLASS_NAME, 'scoreboard-scores__item')
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            tentative = tentative + 1
            time.sleep(1)
            if tentative == 5:
                config.error = True
        else:
            try:
                config.score_actuel = score_teams[0].text + ':' + score_teams[1].text
            except Exception as e:
                continue
            else:
                get_score = True
                if config.saved_score != config.score_actuel:
                    record_scores(driver)
                config.saved_score = config.score_actuel
    return True


def record_scores(driver):
    saved_jeu_actuel = config.jeu_actuel
    GetSetActuel(driver)
    GetJeuActuel(driver)
    if saved_jeu_actuel != config.jeu_actuel:
        time.sleep(1)
        '''# Pour éviter de recupérer des faux scores dû au chargement js ex: 
            {'set': '1', 'jeu': 9, 'score': '30:40'}
            {'set': '1', 'jeu': 10, 'score': '30:0'}
            {'set': '1', 'jeu': 10, 'score': '0:0'}'''
        return
    nouveau_score = {'set': config.set_actuel, 'jeu': config.jeu_actuel, 'score': config.score_actuel}
    config.log(nouveau_score, '', False, 2)
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    GetScoreActuel(driver)
