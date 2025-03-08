from selenium.webdriver.common.by import By

from Functions.GetIfMatchPage import GetIfMatchPage
import config
#from ChromeDriver.SetDriver1 import driver


def GetScoreActuel(driver):
    config.score_actuel = False
    get_score = False
    while not get_score and not config.error:
        try:
            score_teams = driver.find_elements(By.CLASS_NAME,'scoreboard-scores__item')
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            GetIfMatchPage(driver)
            config.error = True
        else:
            config.score_actuel =score_teams[0].text+':'+score_teams[1].text
            get_score = True
            if config.saved_score != config.score_actuel:
                print("Score actuel = "+str(config.score_actuel))
                #print("saved actuel = " + str(config.saved_score))
            config.saved_score = config.score_actuel
    return True
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])
    GetScoreActuel(driver)
