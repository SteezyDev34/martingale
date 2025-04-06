from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import Functions.Function_GetSetActuel
from Functions.Function_GetSetActuel import GetSetActuel
import config
from selenium.webdriver.support import expected_conditions as EC


def GetJeuActuel(driver):
    config.jeu_actuel = 0
    try:
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'scoreboard-periods-table__col'))
        )
        config.jeu_actuel = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-table__col')
    except Exception as e:
        config.log(f"#E0009\nUne erreur est survenue : {e}")
        config.log("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            # print('get set')
            GetSetActuel(driver)
            if config.set_actuel == '1':
                jeu_actuel_player1 = \
                config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                jeu_actuel_player2 = \
                config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '2':
                jeu_actuel_player1 = \
                config.jeu_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                jeu_actuel_player2 = \
                config.jeu_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '3':
                jeu_actuel_player1 = \
                config.jeu_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                jeu_actuel_player2 = \
                config.jeu_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '4':
                jeu_actuel_player1 = \
                config.jeu_actuel[4].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                jeu_actuel_player2 = \
                config.jeu_actuel[4].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '5':
                jeu_actuel_player1 = \
                config.jeu_actuel[5].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                jeu_actuel_player2 = \
                config.jeu_actuel[5].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                return False
        except Exception as e:
            config.log(f"#JEU0010\nUne erreur est survenue : {e}")
            config.log("erreur : numjeu")
            return False
        else:
            # config.log('Récupération du jeu actuel : ' + str(config.jeu_actuel))
            return True


if __name__ == "__main__":
    from ChromeDriver.SetDriver4 import driver

    GetJeuActuel(driver)
