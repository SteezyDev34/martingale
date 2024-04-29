#Function_GetIfMatchPage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#VÉRIFIERR SI PAGE DE MATCH
def main(driver):
    #driver.switch_to.window(driver.window_handles[0])
    print("verfication si page match...")
    try:
        #on cherche le ttableau des score
        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'c-scoreboard-score__heading'))
        )
    except:
        print('Tableau des scores introuvable!')
        try:
            #on vérifie que le match ne soit pas terminé
            element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'after-game-info__text'))
            )
        except:
            print("vérificattion page de match impossible!")
            driver.get('https://1xbet.com/fr/live/tennis')
            return False
        else:
            print("MATCH TERMINÉ!")
            driver.get('https://1xbet.com/fr/live/tennis')
            return False
    else:
        print('PAGE MATCH OK!')
        return True
