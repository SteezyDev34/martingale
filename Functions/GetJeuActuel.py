from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetSetActuel import GetSetActuel


def GetJeuActuel(driver):
    savedjeu = config.jeu_actuel
    config.jeu_actuel = False
    tentative = 0
    while not config.jeu_actuel:
        # driver.switch_to.window(driver.window_handles[0])
        try:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  config.classes['jeu_container'][config.site_type]))
            )
            config.jeu_actuel = driver.find_elements(By.CLASS_NAME, config.classes['jeu_container'][config.site_type])
        except Exception as e:
            config.log(f"#E0009\nUne erreur est survenue : {e}")
            config.log("erreur : c-scoreboard-player-score__row")
            tentative = tentative + 1
            if not GetIfMatchPage(driver):
                config.error = True
                config.jeu_actuel = savedjeu
                return False
            else:
                tentative = tentative + 1
                if tentative == 5:
                    config.jeu_actuel = savedjeu
                    config.error = True
                    return False
        else:
            try:
                # print('get set')
                GetSetActuel(driver)
                if config.site_type == 'old_site':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[0].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            -1]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[1].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            -1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                elif config.set_actuel == '1':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[1].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[1].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                elif config.set_actuel == '2':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[2].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[2].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                elif config.set_actuel == '3':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[3].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[3].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                elif config.set_actuel == '4':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[4].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[4].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                elif config.set_actuel == '5':
                    jeu_actuel_player1 = \
                        config.jeu_actuel[5].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[5].find_elements(By.CLASS_NAME, config.classes['jeu_cell'][config.site_type])[
                            1]
                    config.jeu_actuel = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                else:
                    config.jeu_actuel = savedjeu
                    return False
            except Exception as e:
                config.log(f"#JEU0010\nUne erreur est survenue : {e}")
                config.log("erreur : numjeu")
                config.jeu_actuel = savedjeu
                if not GetIfMatchPage(driver):
                    config.error = True
                    return False
                else:
                    tentative = tentative + 1
                    if tentative == 5:
                        config.error = True
                        return False
            else:
                # Vérification que config.jeu_actuel est un entier valide
                if isinstance(config.jeu_actuel, int):
                    # config.log('Récupération du jeu actuel : ' + str(config.jeu_actuel), 'info')
                    # config.log_clear_line()
                    return True
                else:
                    config.log(f"#JEUERR\nLe jeu actuel n'est pas un entier valide: {type(config.jeu_actuel)}")
                    config.error = True
                    config.jeu_actuel = savedjeu
                    return False

    return False


def GetSetScoreActuel(driver):
    savedjeu = config.jeu_actuel
    config.jeu_actuel = False
    tentative = 0
    while not config.jeu_actuel:
        # driver.switch_to.window(driver.window_handles[0])
        try:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  'scoreboard-periods-table__col'))
            )
            config.jeu_actuel = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-table__col')
        except Exception as e:
            config.log(f"#E0009\nUne erreur est survenue : {e}")
            config.log("erreur : c-scoreboard-player-score__row")
            tentative = tentative + 1
            if not GetIfMatchPage(driver):
                config.error = True
                config.jeu_actuel = savedjeu
                return False
            else:
                tentative = tentative + 1
                if tentative == 5:
                    config.jeu_actuel = savedjeu
                    config.error = True
                    return False
        else:
            try:
                print('get set ', config.set_actuel)
                if int(config.set_actuel) == 1:
                    jeu_actuel_player1 = \
                        config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[1].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.jeu_actuel = [int(jeu_actuel_player1.text), int(jeu_actuel_player2.text)]
                elif int(config.set_actuel) == 2:
                    jeu_actuel_player1 = \
                        config.jeu_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[2].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.jeu_actuel = [int(jeu_actuel_player1.text), int(jeu_actuel_player2.text)]
                elif int(config.set_actuel) == 3:
                    jeu_actuel_player1 = \
                        config.jeu_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[3].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.jeu_actuel = [int(jeu_actuel_player1.text), int(jeu_actuel_player2.text)]
                elif int(config.set_actuel) == 4:
                    jeu_actuel_player1 = \
                        config.jeu_actuel[4].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[4].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.jeu_actuel = [int(jeu_actuel_player1.text), int(jeu_actuel_player2.text)]
                elif int(config.set_actuel) == 5:
                    jeu_actuel_player1 = \
                        config.jeu_actuel[5].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[0]
                    jeu_actuel_player2 = \
                        config.jeu_actuel[5].find_elements(By.CLASS_NAME, 'scoreboard-periods-table-cell--td')[1]
                    config.jeu_actuel = [int(jeu_actuel_player1.text), int(jeu_actuel_player2.text)]
                else:
                    print('no score')
                    config.jeu_actuel = savedjeu
                    return False
            except Exception as e:
                config.log(f"#JEU0010\nUne erreur est survenue : {e}")
                config.log("erreur : numjeu")
                config.jeu_actuel = savedjeu
                if not GetIfMatchPage(driver):
                    config.error = True
                    return False
                else:
                    tentative = tentative + 1
                    if tentative == 5:
                        config.error = True
                        return False
            else:
                return True

    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.site_type = 'new_site'
    GetJeuActuel(driver)
