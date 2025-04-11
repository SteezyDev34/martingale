import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfMatchPage import GetIfMatchPage


# from ChromeDriver.SetDriver1 import driver


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    tentative = 0
    while not get_score and not config.error:
        try:
            score_teams = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  'scoreboard-scores__item'))
            )
            score_teams = driver.find_elements(By.CLASS_NAME, 'scoreboard-scores__item')
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            GetIfMatchPage(driver)
            tentative = tentative + 1
            time.sleep(1)
            if tentative == 5:
                config.error = True
        else:
            config.score_actuel = score_teams[0].text + ':' + score_teams[1].text
            get_score = True
            if config.saved_score != config.score_actuel:
                config.log('Score actuel : ' + str(config.score_actuel), '', False, 2)
                record_scores()
            config.saved_score = config.score_actuel
    return True


def record_scores():
    nouveau_score = {'set': config.set_actuel, 'jeu': config.jeu_actuel, 'score': config.score_actuel}
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})
    print(config.all_scores)


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    GetScoreActuel(driver)
