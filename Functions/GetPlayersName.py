from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def GetPlayersName(driver):
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME,
                                            'scoreboard-intro__team'))
        )
    except:
        players_name = []
    else:
        players = driver.find_elements(By.CLASS_NAME, 'scoreboard-intro__team')
        players_name = []
        for player in players:
            name = player.find_element(By.CLASS_NAME, 'scoreboard-team-name__text').text
            name = name.split('(')[0]
            name = name.strip()
            players_name.append(name)
    return players_name


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    GetPlayersName(driver)
