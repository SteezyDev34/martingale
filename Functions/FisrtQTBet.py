import inspect

import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetQTScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


def FirstQTBet(driver):
    config.log('PREPARATTION PREMIER PARIS', 'title', False, 0)
    bet_qt = False
    tentative = 0
    nextBet = False
    while not bet_qt and not config.error and tentative < 3:
        if not AfficherParis(driver):
            current_frame = inspect.currentframe()
            config.log(
                f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                'error', True)
            tentative = tentative + 1
            continue

        if not GetBet(driver, nextBet):
            tentative = tentative + 1
            if tentative > 5:
                config.error = True
                config.log('error recup jeu #ERR345', 'error', True, 2)
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
            continue
        # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        GetMise(driver)
        config.log('Rattrapage : ' + str(config.rattrape_perte), 'error', True, 2)
        tentative_placermise = 0
        validate_bet = False
        config.log('On place la mise', 'infos', True, 2)
        config.log_clear_line()
        while not PlacerMise(driver) and not config.error and tentative_placermise < 3:
            tentative_placermise += 1
            if tentative_placermise == 2:
                validate_bet = True
            else:
                validate_bet = False
        gamestart = False
        tentative = 0
        config.saved_score = ""
        config.log('On vérifie le score pour valider le paris', 'info', False, 2)
        config.log_clear_line()
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 3:
            # VÉRIFICATION DU SCORE ACTUEL
            tentative = tentative + 1
            GetQTScoreActuel(driver)
            if config.score_actuel == "0:0" and not config.game_start:
                config.log('        GAME NOT START', 1)
            elif config.score_actuel == "0:0" and config.game_start:
                config.log('GAME PASS WITHOUT VALIDATE ON FIRST', '', 2)
                break
            else:
                config.game_start = True
                config.log('FIRST GAME START', '', 2)
            if ValidationDuParis(driver, nextBet):
                validate_bet = True
                bet_qt = True
            else:
                break


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    print(FirstQTBet(driver))
