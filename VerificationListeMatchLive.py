# verification_liste_match_live
from selenium.webdriver.common.by import By


def main(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'game_content_line')

    except:
        print("Liste match live non visible!")
        return False
    else:
        return True
