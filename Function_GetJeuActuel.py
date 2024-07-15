from selenium.webdriver.common.by import By

import Function_GetSetActuel
from Function_GetSetActuel import GetSetActuel
import config
def GetJeuActuel(driver):
    config.jeu_actuel = 0
    try:
        config.jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        config.saveLog(f"#E0009\nUne erreur est survenue : {e}")
        config.saveLog("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            GetSetActuel(driver)
            if config.set_actuel == '1':
                jeu_actuel_player1 = config.jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                jeu_actuel_player2 = config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '2':
                jeu_actuel_player1 = config.jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                jeu_actuel_player2 = config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif config.set_actuel == '3':
                jeu_actuel_player1 = config.jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                jeu_actuel_player2 = config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                return False
        except Exception as e:
            config.saveLog(f"#JEU0010\nUne erreur est survenue : {e}")
            config.saveLog("erreur : numjeu")
            return False
        else:
            config.saveLog('Récupération du jeu actuel : ' + str(config.jeu_actuel))
            return True
