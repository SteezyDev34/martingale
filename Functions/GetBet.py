import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetScoreActuel import GetScoreActuel


def GetBet(driver, nextBet=False):
    config.log("RECHERCHE DES PARIS " + config.scriptType + "....", 'info', True, 2)
    if_get_jeu = False
    clic = False
    print('nextbet', nextBet)
    if config.scriptType == "40A":
        sType = ": 40-40"
        config.win_type = '40:40'

    elif config.scriptType == "30A":
        sType = " 30-30"
        config.win_type = '30:30'
    elif config.scriptType == "15A":
        sType = " 15-15"
        config.win_type = '15:15'
    tentative_clic = 0
    tentative = 0
    try:
        print('recup canvas')
        canvas = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.CLASS_NAME,
                                              'market-grid-canvas__container'))
        )
    except:
        print('erreur recup canvas')
        config.log('erreur recup market-grid-canvas__container', 'error', True, 2)
        return False
    # Récupérer les coordonnées du div
    location = canvas.location
    size = canvas.size
    print('continiue')
    if config.systeme == 'Darwin':
        if config.scriptType == '300' or config.scriptType == '030':
            sautDeLigne = 50 * 3
        else:
            sautDeLigne = 50
        decalageX = size['width'] / -2 + 50
    elif config.systeme == 'Windows':
        y = 0
        if config.scriptType == '300' or config.scriptType == '030':
            sautDeLigne = 50 * 3
        else:
            sautDeLigne = 68
        decalageX = -50

    ligne = 1
    i = 1
    GetScoreActuel(driver)
    print('error', config.error)
    while not clic and tentative < 4 and tentative_clic < 4 and not config.error:
        GetJeuActuel(driver)
        GetScoreActuel(driver)
        DeleteBet(driver)
        config.log(f'jeu recherhcé : {config.looking_game}', 'info', True)
        if_get_jeu = False
        print('eher')

        if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
            scoreboard_player = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-body__container')
            scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-inning')[0]
            first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'scoreboard-periods-inning__ico')
            if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                first_player = 1
                if config.scriptType == '4030':
                    config.win_type = '30:40'  # inversé
                    win_texte = '40-30'
                    sType = "Jeu " + str(config.looking_game) + " 40-30, Joueur " + str(first_player)
                elif config.scriptType == '4015':
                    config.win_type = '15:40'  # inversé
                    win_texte = '40-15'
                    sType = "Jeu " + str(config.looking_game) + " 40-15, Joueur " + str(first_player)
                elif config.scriptType == '400':
                    config.win_type = '0:40'  # inversé
                    win_texte = '40-0'
                    sType = "Jeu " + str(config.looking_game) + " 40-0, Joueur " + str(first_player)

            else:
                first_player = 2
                if config.scriptType == '4030':
                    config.win_type = '40:30'  # inversé
                    win_texte = '30-40'
                    sType = "Jeu " + str(config.looking_game) + " 30-40, Joueur " + str(first_player)
                elif config.scriptType == '4015':
                    config.win_type = '40:15'  # inversé
                    win_texte = '15-40'
                    sType = "Jeu " + str(config.looking_game) + " 15-40, Joueur " + str(first_player)
                elif config.scriptType == '400':
                    win_texte = '0-40'
                    config.win_type = '40:0'  # inversé
                    sType = "Jeu " + str(config.looking_game) + " 0-40, Joueur " + str(first_player)
        if config.scriptType == '030':

            scoreboard_player = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-body__container')
            scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-inning')[0]
            first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'scoreboard-periods-inning__ico')
            sType = "Receveur va mener 30-0"
            if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                first_player = 1
                if config.scriptType == '030':
                    config.win_type = ':30'  # inversé
                    win_texte = '30-0'
            else:
                first_player = 2
                if config.scriptType == '030':
                    config.win_type = '30:0'  # inversé
                    win_texte = '30-0'
        if config.scriptType == '300':
            scoreboard_player = driver.find_elements(By.CLASS_NAME, 'scoreboard-periods-body__container')
            scoreboard_player1 = scoreboard_player[0].find_elements(By.CLASS_NAME, 'scoreboard-periods-inning')[0]
            first_player = scoreboard_player1.find_elements(By.CLASS_NAME, 'scoreboard-periods-inning__ico')
            sType = "Serveur va mener 30-0"
            if (len(first_player) > 0 and not nextBet) or (len(first_player) == 0 and nextBet):
                first_player = 1
                config.win_type = '30:0'  # inversé
                win_texte = '30-0'
                print('plyer 1 to win')
            else:
                first_player = 2
                config.win_type = '0:30'  # inversé
                win_texte = '30-0'
                print('plyer 2 to win')
        if config.scriptType == '6P':
            sType = ", 6"
            config.win_type = ['40:30', '30:40']  # inversé
            win_texte = ', 6'
        if config.scriptType == '5P':
            sType = ", 5"
            config.win_type = ['40:15', '15:40']  # inversé
            win_texte = ', 5'
        if config.scriptType == '4P':
            sType = ", 4"
            config.win_type = ['40:0', '0:40']  # inversé
            win_texte = ', 4'
        # print('i '+str(i))
        GetJeuActuel(driver)
        print('win_type', config.win_type)
        # print('Ligne suivante')
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
        print('size', size['height'])
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
                if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                    if config.systeme == 'Darwin':
                        if i % 2 != 0:
                            sautDeLigne = sautDeLigne
                            decalageX = 50
                        else:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = size['width'] / -2 + 50
                    else:
                        if i % 2 != 0:
                            # print('gauche')
                            sautDeLigne = sautDeLigne
                            decalageX = 50
                        else:
                            # print('droite')
                            sautDeLigne = sautDeLigne + 30
                            decalageX = size['width'] / -2 + 50
                    if config.systeme == 'Darwin':
                        if i % 2 != 0:
                            sautDeLigne = sautDeLigne
                            decalageX = 50
                        else:
                            sautDeLigne = sautDeLigne + 30
                            decalageX = size['width'] / -2 + 50
                    else:
                        if i % 2 != 0:
                            # print('gauche')
                            decalageX = 50
                        else:
                            # print('droite')
                            sautDeLigne = sautDeLigne + 30
                            decalageX = -50
                else:
                    sautDeLigne = sautDeLigne + 30
                ligne = ligne + 1
            tentative_clic = tentative_clic + 1
        else:
            # print('Infos de paris affiché')
            try:
                # print('Lecture des infos')
                time.sleep(1)
                list_of_bet_type = WebDriverWait(driver, 1).until(
                    EC.visibility_of_element_located((By.CLASS_NAME,
                                                      'ui-coupon-bet-market__name'))
                )
            except Exception as e:
                if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':

                    if config.systeme == 'Darwin':
                        if i % 2 != 0:
                            sautDeLigne = sautDeLigne
                            decalageX = 50
                        else:
                            sautDeLigne = sautDeLigne + 50
                            decalageX = size['width'] / -2 + 50
                    else:
                        if i % 2 != 0:
                            # print('gauche')
                            decalageX = 50
                        else:
                            # print('droite')
                            sautDeLigne = sautDeLigne + 30
                            decalageX = -50
                else:
                    sautDeLigne = sautDeLigne + 30
                config.log(f"#E0015 Infos de paris non lisible")
            else:
                list_of_newbet_type = list_of_bet_type.text
                print(list_of_newbet_type)
                if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
                    # print(sType)
                    list_of_newbet_type_text = list_of_newbet_type
                    # print(list_of_newbet_type_text)
                    list_of_newbet_type = list_of_newbet_type_text.split(sType)
                    # print(len(list_of_newbet_type))
                    # print(list_of_newbet_type)
                    if len(list_of_newbet_type) > 1:
                        list_of_newbet_type_text = list_of_newbet_type_text.split(" " + win_texte)[0]
                        getjeu_actuel = int(list_of_newbet_type_text.split("Jeu ")[1])
                        if str(config.looking_game) == str(getjeu_actuel):
                            # print('paris trouvé')
                            clic = True
                            return clic
                        else:
                            print('mauvais jeu')
                            if config.systeme == 'Darwin':
                                if i % 2 != 0:
                                    sautDeLigne = sautDeLigne
                                    decalageX = 50
                                else:
                                    sautDeLigne = sautDeLigne + 30
                                    decalageX = size['width'] / -2 + 50
                            else:
                                print('win')
                                if i % 2 != 0:
                                    print('gauche')
                                    decalageX = 50
                                else:
                                    print('droite')
                                    sautDeLigne = sautDeLigne + 30
                                    decalageX = -50
                    else:
                        print('Mauvais paris')
                        if config.systeme == 'Darwin':
                            if i % 2 != 0:
                                sautDeLigne = sautDeLigne
                                decalageX = 50
                            else:
                                sautDeLigne = sautDeLigne + 30
                                decalageX = size['width'] / -2 + 50
                        else:
                            # print('win')
                            if i % 2 != 0:
                                print('gauche')
                                decalageX = 50
                            else:
                                print('droite')
                                sautDeLigne = sautDeLigne + 30
                                decalageX = -50
                        ligne = ligne + 1
                elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
                    list_of_newbet_type = list_of_newbet_type.split(sType)
                    if len(list_of_newbet_type) > 1:
                        getjeu_actuel = list_of_newbet_type[0].split("Jeu ")[1]
                        getjeu_actuel = ''.join(caractere for caractere in getjeu_actuel if caractere.isdigit())
                        if str(config.looking_game) == str(getjeu_actuel):
                            # print('paris trouvé')
                            clic = True
                            return clic
                        else:
                            # print('mauvais jeu')
                            sautDeLigne = sautDeLigne + 30
                    else:
                        # print('Mauvais paris')
                        sautDeLigne = sautDeLigne + 30
                        ligne = ligne + 1
                        # print('ligne ' + str(ligne))
                else:
                    print('stype', sType)
                    list_of_newbet_type = list_of_newbet_type.split(sType + " - Oui")
                    if len(list_of_newbet_type) > 1:
                        getjeu_actuel = list_of_newbet_type[0].split("Jeu ")[1]
                        getjeu_actuel = ''.join(caractere for caractere in getjeu_actuel if caractere.isdigit())
                        if str(config.looking_game) == str(getjeu_actuel):
                            print('paris trouvé')
                            clic = True
                            return clic
                        else:
                            print('mauvais jeu')
                            sautDeLigne = sautDeLigne + 30
                    else:
                        print('Mauvais paris')
                        sautDeLigne = sautDeLigne + 30
                        ligne = ligne + 1
                        # print('ligne ' + str(ligne))
        if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400':
            max_line = 16
        else:
            max_line = 10
        if config.systeme == 'Darwin':
            if y > size['height'] / 2 or ligne > max_line:
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
            if y > size['height'] or ligne > max_line:
                # print('size height :' + str(size['height']))
                # print('Aucun paris trouvé, nouvelle tentative : ' + str(tentative))
                if config.scriptType == '300' or config.scriptType == '030':
                    sautDeLigne = 50 * 3
                else:
                    sautDeLigne = 68
                decalageX = 50
                decalageX = -50
                y = 0
                ligne = 1
                tentative = tentative + 1
                i = 0
        i = i + 1


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '030'
    GetBet(driver, True)
