from selenium.webdriver.common.by import By

import GetSetActuel


def main(driver):
    #driver.switch_to.window(driver.window_handles[0])
    error = 0
    try:
        jeu_actuel = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')
    except Exception as e:
        print(f"#E0009\nUne erreur est survenue : {e}")
        print("erreur : c-scoreboard-player-score__row")
        return False
    else:
        try:
            set_actuel = GetSetActuel.main(driver, error, '')
            if set_actuel == '1 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[1]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '2 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[2]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            elif set_actuel == '3 Set':
                jeu_actuel_player1 = jeu_actuel[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                jeu_actuel_player2 = jeu_actuel[1].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__cell')[3]
                numjeu = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
            else:
                numjeu = False
        except Exception as e:
            print(f"#JEU0010\nUne erreur est survenue : {e}")
            print("erreur : numjeu")
            return False
        else:
            jeu = "Jeu " + str(numjeu)
            print('Récupération du jeu actuel : ' + jeu)
            return numjeu
