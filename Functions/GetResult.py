import time

import config
from Functions.GetBet import GetBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetResult(driver):
    ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
    print('error #5IYGJHKB ', config.error)
    RetourTpsReg(driver)
    txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"
    config.log(txtlog, config.newmatch)
    config.saved_set = ""
    timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
    result = False
    win = False
    print('error #3FRE ', config.error)
    while not result and not config.error:
        time.sleep(timesleep)
        previous_score = config.score_actuel
        GetScoreActuel(driver)

        if config.scriptType == "40A":
            if config.score_actuel == '40:A' or config.score_actuel == 'A:40' or config.score_actuel == '40:40':
                result = 'WIN'
                config.log(result, 'success', False, 2)
                while config.score_actuel == '40:A' or config.score_actuel == 'A:40' or config.score_actuel == '40:40':
                    GetScoreActuel(driver)
                return result
            elif config.score_actuel == '0:0':
                result = 'LOSE'
                config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == "30A":
            passed_score = [
                '40:15',
                '15:40',
                '30:40',
                '40:30',
                '40:0',
                '0:40',
                '40:40',
                '40:A',
                'A:40'
            ]
            if config.score_actuel in passed_score or config.set_actuel == float(config.validated_bet.get('set')) + 1:
                print('passed score')
                print('config.validated_bet = ', config.validated_bet)
                if win != 'WIN':
                    matching_scores = [score for score in config.all_scores.values()
                                       if float(score.get('set')) == float(config.validated_bet.get('set'))
                                       and float(score.get('jeu')) == float(config.validated_bet.get('jeu'))
                                       and score.get('score') == config.validated_bet.get('win_type')]
                    if matching_scores:
                        print("Matching score found:", matching_scores[0])
                        print(f"All recorded scores: {config.all_scores}")
                        win = 'WIN'
                        print(f"Result: {win}")
                    else:
                        win = 'LOSE'
                        config.log(win, 'error', False, 2)
                result = win
                return result
        elif config.scriptType == "15A":
            passed_score = [
                '30:0',
                '0:30',
                '30:15',
                '15:30',
                '30:30',
                '40:15',
                '15:40',
                '30:40',
                '40:30',
                '40:0',
                '0:40',
                '40:40',
                '40:A',
                'A:40'
            ]

            if config.score_actuel in passed_score or config.set_actuel == float(config.validated_bet.get('set')) + 1:
                print('passed score')
                print('config.validated_bet = ', config.validated_bet)
                if win != 'WIN':
                    matching_scores = [score for score in config.all_scores.values()
                                       if float(score.get('set')) == float(config.validated_bet.get('set'))
                                       and float(score.get('jeu')) == float(config.validated_bet.get('jeu'))
                                       and score.get('score') == config.validated_bet.get('win_type')]
                    if matching_scores:
                        print("Matching score found:", matching_scores[0])
                        print(f"All recorded scores: {config.all_scores}")
                        win = 'WIN'
                        print(f"Result: {win}")
                    else:
                        win = 'LOSE'
                        config.log(win, 'error', False, 2)
                result = win
                return result
        elif config.scriptType == '030' or config.scriptType == '300':
            passed_score = [
                '40:15',
                '15:40',
                '30:40',
                '40:30',
                '40:0',
                '0:40',
                '30:15',
                '15:30',
                '40:40',
                '40:A',
                'A:40',
                '15:15'
            ]
            if config.score_actuel in passed_score or config.set_actuel == float(config.validated_bet.get('set')) + 1:
                print('passed score')
                print('config.validated_bet = ', config.validated_bet)
                if win != 'WIN':
                    matching_scores = [score for score in config.all_scores.values()
                                       if float(score.get('set')) == float(config.validated_bet.get('set'))
                                       and float(score.get('jeu')) == float(config.validated_bet.get('jeu'))
                                       and score.get('score') == config.validated_bet.get('win_type')]
                    if matching_scores:
                        print("Matching score found:", matching_scores[0])
                        print(f"All recorded scores: {config.all_scores}")
                        win = 'WIN'
                        print(f"Result: {win}")
                    else:
                        win = 'LOSE'
                        config.log(win, 'error', False, 2)
                result = win
                return result
        elif config.scriptType == '4030' or config.scriptType == '4015':
            print('previous_score = ' + previous_score)
            print('xin score = ' + config.win_type)
            if config.score_actuel == '0:0' and previous_score == config.win_type:
                result = 'WIN'
                config.log(result, 'success', False, 2)
                return result
            elif config.score_actuel == '0:0' and previous_score != config.win_type:
                result = 'LOSE'
                config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            if config.score_actuel == '0:0' and previous_score in config.win_type:
                result = 'WIN'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '0:0' and previous_score not in config.win_type:
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
        elif config.scriptType == '400':
            print('previous_score = ' + previous_score)
            print('xin score = ' + config.win_type)
            if config.score_actuel == '0:0' and previous_score == config.win_type:
                result = 'WIN'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '40:15' or config.score_actuel == '15:40' or config.score_actuel == '40:30' or config.score_actuel == '30:40':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
            elif config.score_actuel == '0:0' and previous_score != config.win_type:
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '030'
    GetBet(driver, True)
    driver.switch_to.window(driver.window_handles[0])
    GetResult(driver)
