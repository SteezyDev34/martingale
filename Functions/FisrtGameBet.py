import inspect
import time

import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


def FirstGameBet(driver):
    config.log('PREPARATTION PREMIER PARIS', 'title', False, 0)
    if config.set_actuel:
        config.newset = int(config.set_actuel) + 1
    else:
        config.newset = 1
    bet_40a = False
    tentative = 0
    nextBet = False
    GetJeuActuel(driver)
    while not bet_40a and not config.error and tentative < 3:
        GetScoreActuel(driver)
        config.looking_game = int(config.jeu_actuel)

        if config.scriptType == '30A' or config.scriptType == '4030' or config.scriptType == '4015':
            if config.score_actuel != "0:0" and config.score_actuel != "0:15" and config.score_actuel != "15:0" and config.score_actuel != "15:15":
                nextBet = True
                config.log(f'Score : {config.score_actuel} nextBet : {nextBet}', 'warning', indent=3)
                config.looking_game = int(config.jeu_actuel) + 1
        elif config.scriptType == '15A' or config.scriptType == '400' or config.scriptType == '030' or config.scriptType == '300' or config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            if config.score_actuel != "0:0":
                nextBet = True
                config.log(f'Score : {config.score_actuel} nextBet : {nextBet}', 'warning', indent=3)
                config.looking_game = int(config.jeu_actuel) + 1
        elif config.scriptType == '40A':
            if config.score_actuel == "40:40" or config.score_actuel == "A:40" or config.score_actuel == "40:A":
                nextBet = True
                config.log(f'Score : {config.score_actuel} nextBet : {nextBet}', 'warning', indent=3)
                config.looking_game = int(config.jeu_actuel) + 1
        if int(config.looking_game) == 0:
            config.looking_game = 1

        if not AfficherParis(driver):
            current_frame = inspect.currentframe()
            config.log(
                f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                'error', True)
            tentative = tentative + 1
            continue

        if not GetBet(driver, nextBet):
            tentative = tentative + 1
            time.sleep(5)
            if tentative > 5:
                config.error = True
                config.log('error recup jeu #ERR345', 'error', False, 2)
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', False)
            continue
        # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        tentative_placermise = 0
        validate_bet = False
        config.log('On place la mise', 'infos', True, 2)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 3:
            tentative_placermise += 1
            if tentative_placermise == 2:
                validate_bet = True
            else:
                validate_bet = False
        tentative = 0
        config.saved_score = ""
        config.log('On vérifie le score pour valider le paris', 'info', indent=2)
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not config.error and tentative < 3:
            # VÉRIFICATION DU SCORE ACTUEL
            tentative = tentative + 1
            GetScoreActuel(driver)
            if ValidationDuParis(driver, nextBet):
                validate_bet = True
                bet_40a = True
            else:
                break
    return bet_40a


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    # driver.switch_to.window(driver.window_handles[0])
    GetIfNewSite(driver)
    config.newset = 1
    GetSetActuel(driver)
    config.scriptType = '40A'

    print(FirstGameBet(driver))
