from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetScoreActuel import GetScoreActuel


def GetBetOld(driver, nextBet=False):
    config.log("RECHERCHE DES PARIS " + config.scriptType + "....", 'info', True, 2)
    GetScoreActuel(driver)
    DeleteBet(driver)
    if nextBet:
        jeu = int(config.jeu_actuel) + 1
    else:
        jeu = config.jeu_actuel
    if_get_jeu = False
    clic = False
    tentative_clic = 0
    if config.scriptType == "40A":
        sType = ": 40-40"
        config.win_type = '40:40'

    elif config.scriptType == "30A":
        sType = " 30-30"
    elif config.scriptType == "15A":
        sType = " 15-15"
    while not clic and tentative_clic < 30:
        x_path = (
                '//div[contains(@class, "bet_group_col")]'
                '//div[not(contains(@style, "display: none;"))]'
                '//div[contains(@class, "bet-inner") and not(contains(@class, "blockSob"))]'
                '//span[contains(text(), "Jeu ' + str(jeu) + '") '
                                                             'and contains(text(),"' + sType + ' - Oui")]'
        )
        try:
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, x_path))
            )
        except Exception as e:
            print(x_path)
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
                        else:
                            cpn_bet_market_label = driver.find_element(By.CLASS_NAME, 'cpn-bet-market__label').text
                            if 'Jeu ' + str(jeu) in cpn_bet_market_label and sType + ' - Oui' in cpn_bet_market_label:
                                clic = True
                                return clic
                            else:
                                DeleteBet(driver)
                else:
                    config.log("pas de btn 40 recuperé")
                    return clic


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '40A'
    GetIfNewSite(driver)
    print(config.site_type)
    print(GetBetOld(driver))
