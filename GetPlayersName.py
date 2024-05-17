from selenium.webdriver.common.by import By


def GetPlayersName(driver):
    print('c-scoreboard-team')

    players = driver.find_elements(By.CLASS_NAME,'c-scoreboard-team')
    print(str(len(players)))
    players_name=[]
    for player in players:
        name = player.find_element(By.CLASS_NAME, 'c-tablo-container__text').text
        print('getname : '+name)
        name = name.split('(')[0]
        name = name.strip()
        print(name)
        players_name.append(name)
    return players_name
