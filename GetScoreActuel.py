from selenium.webdriver.common.by import By

from GetIfMatchPage import GetIfMatchPage
import config


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    while not get_score and not config.error:
        try:
            config.score_actuel = driver.find_element(By.CLASS_NAME,'c-scoreboard-score__content').text
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            GetIfMatchPage(driver)
            config.error = True
        else:
            get_score = True
            config.score_actuel = config.score_actuel.replace("\n", "")
            if config.saved_score != config.score_actuel:
                print("Score actuel = "+str(config.score_actuel))
                print("saved actuel = " + str(config.saved_score))
            config.saved_score = config.score_actuel
    return True
