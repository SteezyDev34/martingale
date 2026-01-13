import os
import sys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetSetActuel import GetSetActuel


# from ChromeDriver.SetDriver1 import driver


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    tentative = 0
    first = True
    while not get_score:
        try:
            score_teams = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  config.classes['score_container'][config.site_type]))
            )
            score_teams = driver.find_elements(By.CLASS_NAME, config.classes['score_container'][config.site_type])
        except Exception as e:
            score_container_selector = config.classes['score_container'][config.site_type]
            print(f"#E0020\nUne erreur est survenue : {score_container_selector}")
            config.log_clear_line()
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            tentative = tentative + 1
            time.sleep(1)
            if tentative == 5:
                config.error = True
                return False
        else:
            try:
                if config.site_type == 'mobile_site':
                    block_score_teams = score_teams[0]
                    team1_elements = block_score_teams.find_elements(By.CLASS_NAME, 'scoreboard-scores__item--team-1')
                    team2_elements = block_score_teams.find_elements(By.CLASS_NAME, 'scoreboard-scores__item--team-2')
                    if team1_elements and team2_elements:
                        config.score_actuel = team1_elements[0].text + ':' + team2_elements[0].text
                    else:
                        raise Exception("Impossible de trouver les scores des équipes en mode mobile_site")
                else:
                    config.score_actuel = score_teams[0].text + ':' + score_teams[1].text
            except Exception as e:
                print(f"#E0021\nUne erreur est survenue lors de la récupération du score : {e}")
                continue
            else:
                if config.saved_score != config.score_actuel:
                    if not first:
                        first = False
                        record_scores(driver)
                    else:
                        first = False
                        time.sleep(2)
                        continue
                else:
                    get_score = True
                config.saved_score = config.score_actuel
    return True


def record_scores(driver):
    GetSetActuel(driver)
    GetJeuActuel(driver)
    nouveau_score = {'set': config.set_actuel, 'jeu': config.jeu_actuel, 'score': config.score_actuel}
    config.log(nouveau_score, clear=False, indent=2)
    config.log_clear_line()
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})


def GetQTScoreActuel(driver):
    config.score_actuel = []
    tentative = 0
    while not config.score_actuel:
        try:
            config.score_actuel = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-table__col')
        except Exception as e:
            config.log(f"#E0009\nUne erreur est survenue : {e}")
            config.log("erreur : c-scorebdfdfvdoard-player-score__row")
            tentative = tentative + 1
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            else:
                tentative = tentative + 1
                if tentative == 5:
                    config.error = True
                    return False
        else:
            try:
                if config.qt_actuel == 1:
                    score_actuel_player1 = \
                        config.score_actuel[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 2:
                    score_actuel_player1 = \
                        config.score_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 3:
                    score_actuel_player1 = \
                        config.score_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                elif config.qt_actuel == 4:
                    score_actuel_player1 = \
                        config.score_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    score_actuel_player2 = \
                        config.score_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.score_actuel = [int(score_actuel_player1.text), int(score_actuel_player2.text)]
                else:
                    return False
            except Exception as e:
                continue
            else:
                get_score = True
                if config.saved_score != config.score_actuel:
                    record_scores()
                config.saved_score = config.score_actuel
    return True


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    print("Démarrage de la récupération du score actuel...")
    GetScoreActuel(driver)
