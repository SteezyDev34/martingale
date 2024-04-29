from selenium.webdriver.common.by import By

import GetIfMatchPage


def main(driver,saved_score):
    #driver.switch_to.window(driver.window_handles[0])
    score_actuel = False
    get_score = 0
    error = 0
    saved = ''
    while get_score == 0 and error == 0:
        try:
            score_actuel = driver.find_element(By.CLASS_NAME,'c-scoreboard-score__content').text
        except Exception as e:
            print(f"#E0020\nUne erreur est survenue : {e}")
            GetIfMatchPage.main(driver)
            error = 1
        else:
            get_score = 1
            score_actuel = score_actuel.replace("\n", "")
            if saved_score != score_actuel:
                print("Score actuel = "+score_actuel)
                print("saved actuel = " + saved_score)
            saved_score = score_actuel
    return score_actuel
