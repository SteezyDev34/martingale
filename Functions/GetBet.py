from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetScoreActuel import GetQTScoreActuel


def GetBet(driver, nextBet=False):
    config.log("RECHERCHE DES PARIS " + config.scriptType + "....", 'info', True, 2)
    if_get_jeu = False
    clic = False
    if config.scriptType == "QTV2":
        sType = "V2"
        config.win_type = "V2"
    else:
        sType = "V1"
        config.win_type = "V1"
    tentative_clic = 0
    tentative = 0
    try:
        canvas = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'market-grid-canvas__container'))
        )
    except:
        config.log('erreur recup market-grid-canvas__container', 'error', True, 2)
        return False
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    if config.systeme == 'Darwin':
        if config.scriptType == '300' or config.scriptType == '030':
            sautDeLigne = 50 * 3
        else:
            sautDeLigne = 50
        if config.scriptType == "QTV2":
            decalageX = size['width'] / 2 - 50
        else:
            decalageX = size['width'] / -2 + 50
    elif config.systeme == 'Windows':
        y = 0
        if config.scriptType == '300' or config.scriptType == '030':
            sautDeLigne = 50 * 3
        else:
            sautDeLigne = 68
        decalageX = size['width'] / 2 - 50

    ligne = 1
    i = 1
    GetQTScoreActuel(driver)
    while not clic and tentative < 4 and tentative_clic < 4 and not config.error:
        DeleteBet(driver)
        config.log(f'jeu recherhcé : {config.looking_game}', 'info', True)
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')
        # Récupérer les coordonnées du div
        location = canvas.location
        size = canvas.size
        if config.systeme == 'Darwin':
            y = size['height'] / -2 + 10 + sautDeLigne
            x = decalageX
        elif config.systeme == 'Windows':
            y = sautDeLigne
            if size['height'] > 68:
                y = size['height'] / -2 + sautDeLigne
            else:
                i = -1
                y = 0
        x = decalageX
        # Calculer les coordonnées pour cliquer au centre du div
        # print('Y offset : ' + str(y))
        # print('X offset : ' + str(x))
        # Créer une instance ActionChains
        actions = ActionChains(driver)
        # Cliquer aux coordonnées calculées
        try:
            actions.move_to_element_with_offset(canvas, x, y).click().perform()
            if i == -1:
                i = 1
                continue
        except:
            return False
        # print('Click sur la ligne')
        try:
            element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  'ui-coupon-bet-market__name'))
            )
        except Exception as e:
            config.log('tentative_clic : ' + str(tentative_clic))

            config.log('Pas d\'infos, suivant...')
            tentative_clic = tentative_clic + 1
            if tentative_clic < 4:
                ligne = ligne + 1
            tentative_clic = tentative_clic + 1
        else:
            # print('Infos de paris affiché')
            try:
                # print('Lecture des infos')
                list_of_bet_type = WebDriverWait(driver, 1).until(
                    EC.visibility_of_element_located((By.CLASS_NAME,
                                                      'ui-coupon-bet-market__name'))
                )
            except Exception as e:
                config.log(f"#E0015 Infos de paris non lisible")
            else:
                list_of_newbet_type = list_of_bet_type.text
                print(list_of_newbet_type)

                # print('stype', sType)
                list_of_newbet_type = list_of_newbet_type.lower().split(sType.lower())
                if len(list_of_newbet_type) > 1:
                    clic = True
                    return clic
        if config.systeme == 'Darwin':
            if y > size['height'] / 2:
                # print('size height :'+str(size['height'] ))
                # print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
                if config.scriptType == '300' or config.scriptType == '030':
                    sautDeLigne = 50 * 3
                else:
                    sautDeLigne = 50
                decalageX = size['width'] / -2 + 50
                ligne = 1
                tentative = tentative + 1
                i = 0
        elif config.systeme == 'Windows':
            if y > size['height']:
                sautDeLigne = 68
                decalageX = size['width'] / -2 + 50
                y = 0
                ligne = 1
                tentative = tentative + 1
                i = 0
        i = i + 1


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = 'QTV2'
    GetBet(driver, True)
