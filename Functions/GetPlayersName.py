from selenium.webdriver.common.by import By

import config


def GetPlayersName(driver):
    if "ca.1xbet.com" in config.current_url:
        players = driver.find_elements(By.CLASS_NAME,'scoreboard-team-name')
    else:
        players = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-team')

    players_name=[]
    for player in players:
        if "ca.1xbet.com" in config.current_url:
            name = player.find_element(By.CLASS_NAME, 'scoreboard-team-name__text').text
        else:
            name = player.find_element(By.CLASS_NAME, 'c-tablo-container__text').text
        name = name.split('(')[0]
        name = name.strip()
        config.saveLog(name, config.newmatch)
        players_name.append(name)
    return players_name
