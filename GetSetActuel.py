# GetSetActuel.py
#OBTENIR LE SET ACTUEL
from selenium.webdriver.common.by import By


def main(driver, error,saved_set):
    #driver.switch_to.window(driver.window_handles[0])
    if error == 0:
        try:
            set_actuel = driver.find_elements(By.CLASS_NAME,'c-scoreboard-score__heading')[0].text
        except Exception as e:
            print(f"#E0009\nUne erreur est survenue : {e}")
            print("erreur : c-scoreboard-score__heading")
            return False
        else:
            try:
                numset = int(set_actuel.split(' ')[0])
            except Exception as e:
                print(f"#E0010\nUne erreur est survenue : {e}")
                print("erreur : numset")
                return False
            else:
                set = str(numset) + " Set"
                set_actuel = set
                if saved_set != set_actuel:
                    print('Récupération du set actuel : ' + set_actuel)
                return set_actuel
    else:
        print("erreur_get_set_actuel : " + str(error))
        return False