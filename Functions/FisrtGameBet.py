import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetIfGameStart import GetIfGameEnd
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


def FirstGameBet(driver):
    config.log('PREPARATTION PREMIER PARIS', 'title', False, 1)
    bet_40a = False
    tentative = 0
    nextBet = False
    while not bet_40a and not config.error:
        if config.scriptType == '30A':
            GetScoreActuel(driver)
            if config.score_actuel != "0:0" or config.score_actuel != "0:15" or config.score_actuel != "15:0" or config.score_actuel != "15:15":
                config.log(f'       score : {config.score_actuel} ...1er jeu passé !', 'warning', True)
                nextBet = True
        elif config.scriptType == '15A' or config.scriptType == '030' or config.scriptType == '300':
            GetScoreActuel(driver)
            if config.score_actuel != "0:0":
                config.log(f'       score : {config.score_actuel} ...1er jeu passé !', 'warning', True)
                nextBet = True
        elif config.scriptType == '40A':
            GetScoreActuel(driver)
            if config.score_actuel == "40:40" or config.score_actuel == "A:40" or config.score_actuel == "40:A":
                config.log(f'       score : {config.score_actuel} ...1er jeu passé !', 'warning', True)
                nextBet = True

        config.log(f'Affichage de la liste des paris', 'info', True, 2)

        if not AfficherParis(driver):
            config.error = True
            break
        # On recherche le jeu actuel
        config.log('liste des pariis affichée', '', True, 2)
        if not GetBet(driver, nextBet):
            tentative = tentative + 1
            if tentative > 5:
                config.log('error recup jeu #ERR345', 'error', True, 2)
                config.error = True
            continue
        # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        config.log('Rattrapage : ' + str(config.rattrape_perte), 'error', True, 2)
        tentative_placermise = 0
        validate_bet = False
        config.log('On place la mise', 'infos', True, 2)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 3:
            tentative_placermise += 1
            if tentative_placermise == 5:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.log('On vérifie le score pour valider le paris', 2)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 3:
            # VÉRIFICATION DU SCORE ACTUEL
            tentative = tentative + 1
            GetScoreActuel(driver)
            if config.score_actuel == "0:0" and not gamestart:
                config.log('        GAME NOT START', 1)
            elif config.score_actuel == "0:0" and gamestart:
                config.log('GAME PASS WITHOUT VALIDATE ON FIRST', '', 2)
                gamestart = False
                break
            elif nextBet or config.score_actuel == "40:40" or config.score_actuel == "40:A" or config.score_actuel == "A:4":
                config.log('GAME PASS WITHOUT VALIDATE #2', '', 2)
                gamestart = False
                GetIfGameEnd(driver)
                if not nextBet:
                    break
            else:
                gamestart = True
                config.log('GAME START', '', 2)
            if ValidationDuParis(driver):
                validate_bet = True
                config.perte = float(config.perte) + float(config.mise)
                config.wantwin = float(config.wantwin) + float(config.increment)
                bet_40a = True


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])

    print(FirstGameBet(driver))
