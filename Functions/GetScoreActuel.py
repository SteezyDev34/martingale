from selenium.webdriver.common.by import By

import config
from Functions.GetIfMatchPage import GetIfMatchPage


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


def record_scores():
    nouveau_score = {'qt': config.qt_actuel, 'score': config.score_actuel}
    config.log(nouveau_score, '', False, 2)
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.qt_actuel = 1
    GetQTScoreActuel(driver)
    print(config.score_actuel)
