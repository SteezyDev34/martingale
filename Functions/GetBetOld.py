import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetScoreActuel import GetScoreActuel


def GetBetOld(driver, nextBet=False, selection=''):
    config.log("RECHERCHE DES PARIS " + config.scriptType + "....", 'info', True, 2)
    if config.scriptType != 'LIVE':
        GetScoreActuel(driver)
    DeleteBet(driver)
    if nextBet:
        jeu = int(config.jeu_actuel) + 1
    else:
        jeu = config.jeu_actuel
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    sType = selection
    if config.scriptType == "40A":
        sType = ": 40-40"
        config.win_type = '40:40'

    elif config.scriptType == "30A":
        sType = " 30-30"
        config.win_type = '30:30'
    elif config.scriptType == "15A":
        sType = " 15-15"
        config.win_type = '15:15'

    if config.scriptType == '6P':
        sType = ", 6"
        config.win_type = ['40:30', '30:40']  # inversé
    if config.scriptType == '5P':
        sType = ", 5"
        config.win_type = ['40:15', '15:40']  # inversé
    if config.scriptType == '4P':
        sType = ", 4"
        config.win_type = ['40:0', '0:40']  # inversé

    # print('i '+str(i))
    while not clic and tentative_clic < 5:
        if config.scriptType != 'LIVE':
            scoreboard_player = driver.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score')
            scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__row')[0]
            first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'c-scoreboard-player-score__ball')
            if first_player:
                print('PLAYER 1')
            else:
                print('PLAYER 2')
            if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 1
                    if config.scriptType == '4030':
                        config.win_type = '40:30'
                        win_texte = '40+:30'
                        sType = "Game " + str(config.looking_game) + " 40+:30, Player " + str(first_player)
                    elif config.scriptType == '4015':
                        config.win_type = '40:15'  # inversé
                        win_texte = '40+:15'
                        sType = "Game " + str(config.looking_game) + " 40+:15, Player " + str(first_player)
                    elif config.scriptType == '400':
                        config.win_type = '40:0'  # inversé
                        win_texte = '40+:0'
                        sType = "Game " + str(config.looking_game) + " 40+:0, Player " + str(first_player)
                else:
                    first_player = 2
                    if config.scriptType == '4030':
                        config.win_type = '30:40'  # inversé
                        win_texte = '30:40+'
                        sType = "Game " + str(config.looking_game) + " 30:40+, Player " + str(first_player)
                    elif config.scriptType == '4015':
                        config.win_type = '15:40'  # inversé
                        win_texte = '15:40+'
                        sType = "Game " + str(config.looking_game) + " 15:40+, Player " + str(first_player)
                    elif config.scriptType == '400':
                        win_texte = '0:40+'
                        config.win_type = '0:40'  # inversé
                        sType = "Game " + str(config.looking_game) + " 0:40+, Player " + str(first_player)
            if config.scriptType == '030':
                sType = "Receveur Va Mener 30-0"
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet) or (
                        len(first_player) > 0 and int(config.jeu_actuel) == int(config.looking_game)):
                    first_player = 1

                    if config.scriptType == '030':
                        config.win_type = '0:30'  # inversé
                else:
                    first_player = 2
                    if config.scriptType == '030':
                        config.win_type = '30:0'  # inversé
                print('first_player :', first_player)
            if config.scriptType == '300':
                sType = "Serveur va mener 30-0"
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 1
                    config.win_type = '30:0'  # inversé
                else:
                    first_player = 2
                    config.win_type = '0:30'  # inversé
                print('first_player :', first_player)
            if config.scriptType == 'BREAK':
                sType = "gne dans le jeu"
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 1
                    config.win_type = ['0:40', '15:40', '30:40', '40:A']
                else:
                    first_player = 2
                    config.win_type = ['40:0', '40:15', '40:30', 'A:40']
                print('first_player :', first_player)
            print('config.win_type', config.win_type)
            if config.scriptType == '15A' or config.scriptType == '30A' or config.scriptType == '40A' or config.scriptType == '030' or config.scriptType == '300':
                x_path = (
                        '//div[contains(@class, "bet_group_col")]'
                        '//div[not(contains(@style, "display: none;"))]'
                        '//div[contains(@class, "bet-inner") and not(contains(@class, "blockSob"))]'
                        '//span[contains(text(), "Jeu ' + str(jeu) + '") '
                                                                     'and contains(text(),"' + sType + ' - Oui")]'
                )
        else:
            x_path = (
                    '//div[contains(@class, "bet_group_col")]'
                    '//div[not(contains(@style, "display: none;"))]'
                    '//div[contains(@class, "bet-inner") and not(contains(@class, "blockSob"))]'
                    '//span[contains(text(), "' + str(sType) + '")]'
            )
            print(x_path)
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, x_path))
            )
        except Exception as e:
            tentative_clic += 1
            config.log(f'error recup lin #ERR345 jeu : {jeu}, stype : {sType} e : {e}', 'error', True, 2)
        else:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                x_path)))
                list_of_bet_type = driver.find_elements(By.XPATH, x_path)
            except Exception as e:
                config.log(f"#E0015\ btn 40A not reachable : {e}", 'error', True, 2)
            else:
                if len(list_of_bet_type) > 0:
                    config.log('JEU TROUVÉ! : ' + list_of_bet_type[0].text, 'success', True, 2)
                    tentative = 0
                    while not clic and tentative < 5:
                        try:
                            list_of_bet_type[0].click()
                            element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'cpn-bet-market__label'))
                            )
                        except Exception as e:
                            config.log('Pas de paris affiché!', 'error', True, 2)
                            tentative += 1
                        else:
                            time.sleep(1)
                            cpn_bet_market_label = driver.find_element(By.CLASS_NAME, 'cpn-bet-market__label').text
                            if config.scriptType == '15A' or config.scriptType == '30A' or config.scriptType == '40A' or config.scriptType == '030' or config.scriptType == '300':
                                if 'Jeu ' + str(
                                        jeu) in cpn_bet_market_label and sType + ' - Oui' in cpn_bet_market_label:
                                    clic = True
                                    return clic
                                else:
                                    tentative += 1
                                    DeleteBet(driver)
                            elif config.scriptType == 'LIVE':
                                if sType in cpn_bet_market_label:
                                    clic = True
                                    return clic
                                else:
                                    tentative += 1
                                    DeleteBet(driver)

                else:
                    config.log("pas de btn 40 recuperé")
                    return clic
    return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '40A'
    GetIfNewSite(driver)
    print(config.site_type)
    print(GetBetOld(driver))
