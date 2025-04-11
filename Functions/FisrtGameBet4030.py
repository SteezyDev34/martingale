import inspect

import config
from AfficherParis import AfficherParis
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetBet import GetBet
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


def FirstGameBet(driver):
    ##PREPARATTION PREMIER PARIS
    config.log('PREPARATION DU PREMIER PARIS', 1, config.newmatch)
    bet_40a = False
    tentative = 0
    while not bet_40a and not config.error:
        # Affichage de la liste des paris
        config.log('Affichage de la liste des paris', 0, config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            current_frame = inspect.currentframe()
            config.log(
                f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                'error', True)
            break
        else:
            # On recherche le jeu actuel
            config.log('liste des pariis affichée, On recherche le jeu actuel', 0, config.newmatch)
            jeu = GetBet(driver)

        if not jeu:
            tentative += 1
            if tentative > 5:
                config.error = True
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
                config.log('error recup jeu #ERR345', 1, config.newmatch)
        else:
            win_score30 = jeu[1]
            config.log('Premier PAris 40A cliqué', 1, config.newmatch)
            send_mise = 0
            # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
            GetMise(driver)
            config.log('cotemini : ' + str(config.cotemini) + ' cote : ' + str(config.cote), 1)
            config.log('proba mini : ' + str(config.probamini) + ' proba : ' + str(config.proba40A), 1)
            config.log('Rattrapage : ' + str(config.rattrape_perte), 1)
            if float(config.proba40A) < float(config.probamini) and float(config.cote) < float(config.cotemini):
                bet_40a = True
                config.error = True
                config.log('Cote trop faible 0,2', config.newmatch)
                break
            tentative_placermise = 0
            validate_bet = False
            config.log('On place la mise', 1, config.newmatch)
            while not PlacerMise(driver) and not config.error and tentative_placermise < 2:
                tentative_placermise += 1
                if tentative_placermise == 2:
                    validate_bet = True
                else:
                    validate_bet = False
            gamestart = False
            tentative = 0
            config.saved_score = ""
            config.log('On vérifie le score pour valider le paris', 0, config.newmatch)
            ##VALIDATION DU PARIS SI SCORE OK
            while not validate_bet and not config.error and tentative < 30:
                # VÉRIFICATION DU SCORE ACTUEL
                GetScoreActuel(driver)
                config.saved_score = config.score_actuel
                if config.score_actuel == "0:0" and not gamestart:
                    config.log("GAME NOT START", config.newmatch)
                elif config.score_actuel == "0:0" and gamestart:
                    validate_bet = True
                    config.jeu_actuel += 1
                    config.log("GAME PASS WITHOUT VALIDATE ON FIRST", config.newmatch)
                    gamestart = False
                    result = True
                    lose = True
                    findbtn = True
                    if win_score30 == '30:40':
                        win_score30 = '40:30'
                    else:
                        win_score30 = '30:40'
                else:
                    gamestart = True
                    config.log("GAME START", config.newmatch)
                if ValidationDuParis(driver):
                    validate_bet = True
                    bet_40a = True
                    config.jeu_actuel += 1
                    config.perte = float(config.perte) + float(config.mise)
                    config.wantwin = float(config.wantwin) + float(config.increment)
                    config.log("prochain jeu : " + str(config.jeu_actuel), config.newmatch)
                    config.log("wantwin : " + str(config.wantwin), config.newmatch)
                    config.log("perte : " + str(config.perte), config.newmatch)
                    config.log("mise : " + str(config.mise), config.newmatch)
                    config.log("increment : " + str(config.increment), config.newmatch)
                else:
                    GetJeuActuel(driver)
                    tentative = tentative + 1
                    validate_bet = True
                    config.log("Erreur lor de la validation, nouvelle tentative", config.newmatch)


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])

    print(FirstGameBet(driver))
