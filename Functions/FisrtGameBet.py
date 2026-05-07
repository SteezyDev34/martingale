import inspect
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions.PlacerMise import PlacerMise
import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
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
    attempts = 3
    GetJeuActuel(driver)
    if config.scriptType in ['15V1', '15V2']:
        attempts = 1
    while not bet_40a and not config.error and tentative < attempts:
        GetScoreActuel(driver)
        print(f'config.scriptTypepass ici: {config.scriptType}')
        config.looking_game = int(config.jeu_actuel)

        if config.scriptType == '30A' or config.scriptType == '4030' or config.scriptType == '4015':
            if config.score_actuel != "0:0" and config.score_actuel != "0:15" and config.score_actuel != "15:0" and config.score_actuel != "15:15":
                nextBet = True
                config.log(f'Score : {config.score_actuel} nextBet : {nextBet}', 'warning', indent=3)
                config.looking_game = int(config.jeu_actuel) + 1
        elif config.scriptType == '150' or config.scriptType == '015' or config.scriptType == '15A' or config.scriptType == '400' or config.scriptType == '15V1' or config.scriptType == '15V2' or config.scriptType == '030' or config.scriptType == '300' or config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            if config.score_actuel != "0:0":
                nextBet = True
                config.log(f'Score : {config.score_actuel} nextBet : {nextBet}', 'warning', indent=3)
                if config.scriptType not in ['15V1', '15V2']:
                    config.looking_game = int(config.jeu_actuel) + 1
                else:
                    config.looking_game = int(config.jeu_actuel)
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
            if config.scriptType not in ['15V1', '15V2']:
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
        # config.log('On place la mise', 'infos', True, 2)
        while not PlacerMise(driver) and not config.error and tentative_placermise < 1:
            tentative_placermise += 1
            if tentative_placermise == 2:
                validate_bet = True
            else:
                validate_bet = False
        config.saved_score = ""
        config.log('On vérifie le score pour valider le paris', 'info', indent=2)
        ##VALIDATION DU PARIS SI SCORE OK
        attempts = 3
        if config.scriptType in ['15V1', '15V2']:
            attempts = 2
        tentative_a = 0
        while not validate_bet and not config.error and tentative_a < attempts:
            # VÉRIFICATION DU SCORE ACTUEL
            print('pass ici')
            tentative_a = tentative_a + 1
            GetScoreActuel(driver)
            if ValidationDuParis(driver, nextBet):
                validate_bet = True
                bet_40a = True
                if config.scriptType in ['15V1', '15V2']:
                    def _last_numero_point():
                        try:
                            if not config.all_scores:
                                return None
                            # support list-like or dict-like structures
                            if isinstance(config.all_scores, dict):
                                vals = list(config.all_scores.values())
                                if not vals:
                                    return None
                                last = vals[-1]
                            else:
                                last = config.all_scores[-1]
                            return int(last['numero_point'])
                        except Exception:
                            return None

                    target = None
                    try:
                        target = int(config.validated_bet['numero_point']) - 1
                    except Exception:
                        target = None

                    # attendre que le dernier score enregistré corresponde au point attendu
                    config.log(f'Attente du point {target} pour valider le pari', 'info', indent=3)
                    while not config.error:
                        last = _last_numero_point()
                        config.log(f'Last point: {last}, Target point: {target}', 'debug', indent=4)
                        if config.score_actuel == "0:0":
                            break
                        if last is None or target is None:
                            break
                        if last >= target:
                            break
                        
                        GetScoreActuel(driver)
                        time.sleep(0.1)
            else:
                break
    return bet_40a


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    # driver.switch_to.window(driver.window_handles[0])
    config.site_type = 'mobile_site'
    config.scriptType = '15V1'
    config.mise = 0.2
    GetSetActuel(driver)

    print(FirstGameBet(driver))
