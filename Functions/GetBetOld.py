import time
import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetScoreActuel import GetScoreActuel
from Functions.getTextFromImageGPT import compare_selection


def GetBetOld(driver, nextBet=False, selection='', mobile=False):
    config.log("RECHERCHE DES PARIS " + config.scriptType + "....", 'info', False, 2)
    if config.scriptType in config.allScriptType:
        GetScoreActuel(driver)
    DeleteBet(driver)
    if nextBet:
        jeu = int(config.jeu_actuel) + 1
        print('jeu next bet ', jeu)
    else:
        jeu = config.jeu_actuel
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    sType = selection
    

    # print('i '+str(i))
    while not clic and tentative_clic < 5:
        if config.scriptType in config.allScriptType:
            scoreboard_player = driver.find_elements(By.CLASS_NAME, config.classes['scoreboard_player_score'][config.site_type] )
            scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, config.classes['ball_container'][config.site_type] )[0]
            first_player = scoreboard_player1.find_elements(By.CLASS_NAME, config.classes['score_ball'][config.site_type])
            if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 1
                    if config.scriptType == '4030':
                        config.win_type = ['40:30']
                    elif config.scriptType == '4015':
                        config.win_type = ['40:15']  # inversé
                    elif config.scriptType == '400':
                        config.win_type = ['40:0']  # inversé

                else:
                    first_player = 2
                    if config.scriptType == '4030':
                        config.win_type = ['30:40']  # inversé
                    elif config.scriptType == '4015':
                        config.win_type = ['15:40']  # inversé
                    elif config.scriptType == '400':
                        config.win_type = ['0:40']  # inversé
                if config.scriptType == '4030':
                    sType = 'Joueur ' + str(first_player) + ' va gagner le Jeu ' + str(config.looking_game) + ' 40-30'
                elif config.scriptType == '4015':
                    sType = 'Joueur ' + str(first_player) + ' va gagner le Jeu ' + str(config.looking_game) + ' 40-15'
                elif config.scriptType == '400':
                    sType = 'Joueur ' + str(first_player) + ' va gagner le Jeu ' + str(
                        config.looking_game) + ' 40-0'
            if config.scriptType == '030':
                sType = "Receveur va mener 30-0"
                print(sType)
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet) or (
                        len(first_player) > 0 and int(config.jeu_actuel) == int(config.looking_game)):
                    first_player = 1

                    if config.scriptType == '030':
                        config.win_type = '0:30'  # inversé
                else:
                    first_player = 2
                    if config.scriptType == '030':
                        config.win_type = '30:0'  # inversé
            if config.scriptType == '300':
                sType = "Serveur va mener 30-0"
                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 1
                    config.win_type = '30:0'  # inversé
                else:
                    first_player = 2
                    config.win_type = '0:30'  # inversé
            if config.scriptType == 'BREAK':
            

                if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                    first_player = 2
                    config.win_type = ['0:40', '15:40', '30:40', '40:A']
                else:
                    first_player = 1
                    config.win_type = ['40:0', '40:15', '40:30', 'A:40']
                sType = f"Game {jeu} - W{first_player}"
            if config.scriptType == "40A":
                sType = f"Jeu {jeu}: 40-40 - Oui" # signe : collé au num du jeu 
                config.win_type = '40:40'

            elif config.scriptType == "30A":
                sType = f"Jeu {jeu} 30-30 - Oui" # pas de : 
                config.win_type = '30:30'
            elif config.scriptType == "15A":
                sType = f"Jeu {jeu} 15-15 - Oui" # pas de  : 
                config.win_type = '15:15'

            if config.scriptType == '6P':
                sType = f"Jeu {jeu}, 6"
                config.win_type = ['40:30', '30:40']  # inversé
            if config.scriptType == '5P':
                sType = f"Jeu {jeu}, 5"
                config.win_type = ['40:15', '15:40']  # inversé
            if config.scriptType == '4P':
                sType = f"Jeu {jeu}, 4"
                config.win_type = ['40:0', '0:40']  # inversé
            if config.site_type == 'mobile_site':
                x_path = (
                        '//ul[contains(@class, "game-markets-group__list")]'
                        '//li//button[contains(@class, "game-markets-group__market") and .//span[contains(@class, "ui-market__name") and contains(text(), "' + str(sType) + '")]]'
                )
            else:
                x_path = (
                        '//div[contains(@class, "bet_group_col")]'
                        '//div[not(contains(@style, "display: none;"))]'
                        '//div[contains(@class, "bet-inner") and not(contains(@class, "blockSob"))]'
                        '//span[contains(text(), "' + str(sType) + '")]'
                )
            # TODO le xpath direct sur le mtodu bouton ne ofnctionne plus
        else:
            x_path = (
                    '//div[contains(@class, "bet_group_col")]'
                    '//div[not(contains(@style, "display: none;"))]'
                    '//div[contains(@class, "bet-inner") and not(contains(@class, "blockSob"))]'
                    '//span[contains(text(), "' + str(sType) + '")]'
            )
        print('sType', sType)
        try:
            print('tentative_clic',tentative_clic)
            print('site_type', config.site_type)
            search_text = f"Jeu {jeu} {sType} - Oui"
            print(f"Searching for: '{search_text}'")
            print(f"XPath: {x_path}")
            if tentative_clic < 2 and config.site_type != 'mobile_site':

                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, x_path))
                )
            else:
                x_path = (
                    '//ul[contains(@class, "game-markets-group__list")]'
                    '//li//button[contains(@class, "game-markets-group__market")]'
                )
                list_of_bet_type = driver.find_elements(By.XPATH, x_path)
                bet_list = []
                betclic = False

                for bet in list_of_bet_type:
                    try:
                        if config.site_type == 'mobile_site':
                            bet_text = bet.find_element(By.CLASS_NAME, 'ui-market__name').text
                            print('bet_text', bet_text)
                        else:
                            bet_text = bet.find_element(By.CLASS_NAME, 'bet_type').text
                        if bet_text.strip() and sType.lower() in bet_text.strip().lower():  # Only append if bet_text is not empty
                            bet.click()
                            betclic = True
                            print('clic ok')
                            break
                    except Exception as e:
                        continue
                if not betclic:
                    for bet in list_of_bet_type:
                        try:
                            if config.site_type == 'mobile_site':
                                bet_text = bet.find_element(By.CLASS_NAME, 'ui-market__name').text
                            else:
                                bet_text = bet.find_element(By.CLASS_NAME, 'bet_type').text
                            if bet_text.strip():  # Only append if bet_text is not empty
                                bet_list.append(bet_text)
                        except Exception as e:
                            continue
                    bet_list = '[' + ','.join(bet_list) + ']'
                    sType = compare_selection(config.match_name, sType, bet_list)
                    if sType:
                        for bet in list_of_bet_type:
                            try:
                                if config.site_type == 'mobile_site':
                                    bet_text = bet.find_element(By.CLASS_NAME, 'ui-market__name').text
                                else:
                                    bet_text = bet.find_element(By.CLASS_NAME, 'bet_type').text
                                if bet_text.strip() and sType.lower() in bet_text.strip().lower():  # Only append if bet_text is not empty
                                    bet.click()
                                    betclic = True
                                    break
                            except Exception as e:
                                continue

                    else:
                        return False
                if betclic:
                    try:
                        if config.site_type == 'mobile_site':
                            class_name = 'quick-coupon-events-card'
                        else:
                            class_name = 'cpn-bet-market__label'
                        print('class_nameclass_name', class_name)
                        element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, class_name))
                        )
                    except Exception as e:
                        config.log(f'Pas de paris affiché!{e}', 'error', True, 2)
                        tentative_clic += 1
                    else:
                        time.sleep(1)
                        cpn_bet_market_label = driver.find_element(By.CLASS_NAME, class_name).text
                        print('sType', sType)
                        print('cpn_bet_market_label',cpn_bet_market_label)
                        if sType.lower() in cpn_bet_market_label.lower():
                            config.log('JEU TROUVÉ! : ' + cpn_bet_market_label, 'success', False, 2)
                            print('click ok ok ')
                            clic = True
                            return clic
                        else:
                            tentative_clic += 1
                            DeleteBet(driver)
                else:
                    return False

        except Exception as e:
            tentative_clic += 1
            config.log(f'error recup lin #ERR345 jeu : {jeu}, stype : {sType} {e}', 'error', False)
    return False


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver
    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    print(config.site_type)
    print(GetBetOld(driver))
