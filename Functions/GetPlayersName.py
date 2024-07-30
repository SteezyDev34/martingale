from selenium.webdriver.common.by import By

import config


def GetPlayersName(driver):
    players = driver.find_elements(By.CLASS_NAME,'c-scoreboard-team')
    players_name=[]
    for player in players:
        name = player.find_element(By.CLASS_NAME, 'c-tablo-container__text').text
        name = name.split('(')[0]
        name = name.strip()
        config.saveLog(name, config.newmatch)
        print(name)
        players_name.append(name)
    return players_name
