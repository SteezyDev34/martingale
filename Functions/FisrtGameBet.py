import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetIfGameStart import GetIfGameEnd
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


def FirstGameBet(driver):
    ##PREPARATTION PREMIER PARIS
    bet_40a = False
    tentative = 0
    nextBet = False
    while not bet_40a and not config.error:
        if config.scriptType == '30A':
            GetScoreActuel(driver)
            if config.score_actuel != "0:0" and config.score_actuel != "0:15" and config.score_actuel != "15:0" and config.score_actuel != "15:15":
                config.saveLog(f'score : {config.score_actuel} ...first game passss', 1, config.newmatch)
                nextBet = True
        elif config.scriptType == '15A':
            GetScoreActuel(driver)
            if config.score_actuel != "0:0":
                config.saveLog(f'score : {config.score_actuel} ...first game passss', 1, config.newmatch)
                nextBet = True

        txtlog = 'PREPARATION DU PREMIER PARIS'
        config.saveLog(txtlog, 1, config.newmatch)
        # Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris', 1, config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            break
        # On recherche le jeu actuel
        config.saveLog('liste des pariis affichée, On recherche le jeu actuel', 1, config.newmatch)
        if not GetBet(driver, nextBet):
            tentative = tentative + 1
            if tentative > 5:
                config.saveLog('error recup jeu #ERR345', 1, config.newmatch)
                config.error = True
            continue

        config.saveLog('Premier PAris 40A cliqué', config.newmatch)
        send_mise = 0
        # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        print('Rattrapage : ' + str(config.rattrape_perte))
        tentative_placermise = 0
        validate_bet = False
        txtlog = 'On place la mise'
        config.saveLog(txtlog, 1, config.newmatch)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 3:
            tentative_placermise += 1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.saveLog('On vérifie le score pour valider le paris', config.newmatch)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 3:
            # VÉRIFICATION DU SCORE ACTUEL
            tentative = tentative + 1
            print('tentative validation ' + str(tentative))
            GetScoreActuel(driver)
            if config.score_actuel == "0:0" and not gamestart:
                txtlog = "GAME NOT START"
                config.saveLog(txtlog, 1, config.newmatch)
            elif config.score_actuel == "0:0" and gamestart:
                txtlog = "GAME PASS WITHOUT VALIDATE ON FIRST"
                config.saveLog(txtlog, 1, config.newmatch)
                gamestart = False
                break
            elif nextBet or config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:40":
                print("GAME PASS WITHOUT VALIDATE #2#")
                gamestart = False
                GetIfGameEnd(driver)
                if not nextBet:
                    break
            else:
                gamestart = True
                txtlog = "GAME START"
                config.saveLog(txtlog, 1, config.newmatch)
            if ValidationDuParis(driver):
                validate_bet = True
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                bet_40a = True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])

    print(FirstGameBet(driver))
