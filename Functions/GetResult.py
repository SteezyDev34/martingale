import time

import config
from Functions.GetBet import GetBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetResult(driver):
    ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
    RetourTpsReg(driver)
    txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"
    print('validated_bet = ', config.validated_bet)
    config.log(txtlog, config.newmatch)
    config.saved_set = ""
    timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
    result = False
    print('is error ', config.error)
    print('is result ', result)
    print('jeu ', config.jeu_actuel)
    print('set ', config.set_actuel)
    print('scriptype ', config.scriptType)
    while not result and not config.error:
        time.sleep(timesleep)
        GetScoreActuel(driver)
        print('wait resukt')
        if config.scriptType == "40A":
            passed_score = [
                '0:0',
                '40:40',
                '40:A',
                'A:40'
            ]
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                matching_scores = [score for score in config.all_scores.values()
                                   if score.get('set') is not None
                                   and config.validated_bet.get('set') is not None
                                   and int(score.get('set')) == int(config.validated_bet.get('set'))
                                   and score.get('jeu') is not None
                                   and config.validated_bet.get('jeu') is not None
                                   and int(score.get('jeu')) == int(config.validated_bet.get('jeu'))
                                   and score.get('score') == config.validated_bet.get('winscore')]
                if matching_scores:
                    print("Matching score found:", matching_scores[0])
                    result = 'WIN'
                    config.log(f"Result: {result}", 'success', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == "30A":
            passed_score = [
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
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                matching_scores = [score for score in config.all_scores.values()
                                   if score.get('set') is not None
                                   and config.validated_bet.get('set') is not None
                                   and int(score.get('set')) == int(config.validated_bet.get('set'))
                                   and score.get('jeu') is not None
                                   and config.validated_bet.get('jeu') is not None
                                   and int(score.get('jeu')) == int(config.validated_bet.get('jeu'))
                                   and score.get('score') == config.validated_bet.get('winscore')]
                if matching_scores:
                    print("Matching score found:", matching_scores[0])
                    result = 'WIN'
                    config.log(f"Result: {result}", 'success', False, 2)

                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == "15A":
            passed_score = [
                '15:15',
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

            if config.score_actuel in passed_score or int(config.set_actuel) == int(
                    config.validated_bet.get('set')) + 1 or int(config.jeu_actuel) == int(
                config.validated_bet.get('jeu')) + 1:
                matching_scores = [score for score in config.all_scores.values()
                                   if score.get('set') is not None
                                   and config.validated_bet.get('set') is not None
                                   and int(score.get('set')) == int(config.validated_bet.get('set'))
                                   and score.get('jeu') is not None
                                   and config.validated_bet.get('jeu') is not None
                                   and int(score.get('jeu')) == int(config.validated_bet.get('jeu'))
                                   and score.get('score') == config.validated_bet.get('winscore')]
                if matching_scores:
                    print("Matching score found:", matching_scores[0])
                    result = 'WIN'
                    config.log(f"Result: {result}", 'success', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == '030' or config.scriptType == '300':
            passed_score = [
                '30:0',
                '0:30',
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
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                matching_scores = [score for score in config.all_scores.values()
                                   if score.get('set') is not None
                                   and config.validated_bet.get('set') is not None
                                   and int(score.get('set')) == int(config.validated_bet.get('set'))
                                   and score.get('jeu') is not None
                                   and config.validated_bet.get('jeu') is not None
                                   and int(score.get('jeu')) == int(config.validated_bet.get('jeu'))
                                   and score.get('score') == config.validated_bet.get('winscore')]
                if matching_scores:
                    print("Matching score found:", matching_scores[0])
                    result = 'WIN'
                    config.log(f"Result: {result}", 'success', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == '4030' or config.scriptType == '4015':
            passed_score = [
                '0:0'
            ]
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                # Check the last element in all_scores
                # Filter scores for matching set and jeu, excluding 0:0 scores
                matching_set_jeu_scores = {k: v for k, v in config.all_scores.items()
                                           if v.get('set') is not None
                                           and v.get('jeu') is not None
                                           and config.validated_bet.get('set') is not None
                                           and config.validated_bet.get('jeu') is not None
                                           and int(v.get('set')) == int(config.validated_bet.get('set'))
                                           and int(v.get('jeu')) == int(config.validated_bet.get('jeu'))
                                           and v.get('score') != '0:0'}

                if matching_set_jeu_scores:
                    last_score_key = max(matching_set_jeu_scores.keys())
                    last_score = matching_set_jeu_scores[last_score_key]

                    if last_score.get('score') == config.validated_bet.get('winscore'):
                        print("Matching score found:", last_score)
                        result = 'WIN'
                        config.log(f"Result: {result}", 'success', False, 2)
                    else:
                        result = 'LOSE'
                        config.log(result, 'error', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == '6P' or config.scriptType == '5P' or config.scriptType == '4P':
            passed_score = [
                '0:0'
            ]
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                # Check the last element in all_scores
                # Filter scores for matching set and jeu, excluding 0:0 scores
                matching_set_jeu_scores = {k: v for k, v in config.all_scores.items()
                                           if v.get('set') is not None
                                           and v.get('jeu') is not None
                                           and config.validated_bet.get('set') is not None
                                           and config.validated_bet.get('jeu') is not None
                                           and int(v.get('set')) == int(config.validated_bet.get('set'))
                                           and int(v.get('jeu')) == int(config.validated_bet.get('jeu'))
                                           and v.get('score') != '0:0'}

                if matching_set_jeu_scores:
                    last_score_key = max(matching_set_jeu_scores.keys())
                    last_score = matching_set_jeu_scores[last_score_key]

                    if last_score.get('score') in config.validated_bet.get('winscore'):
                        print("Matching score found:", last_score)
                        result = 'WIN'
                        config.log(f"Result: {result}", 'success', False, 2)
                    else:
                        result = 'LOSE'
                        config.log(result, 'error', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result
        elif config.scriptType == '400':
            passed_score = [
                '0:0'
            ]
            if config.score_actuel == '40:15' or config.score_actuel == '15:40' or config.score_actuel == '40:30' or config.score_actuel == '30:40':
                result = 'LOSE'
                config.log(result, config.newmatch)
                return result
            if config.score_actuel in passed_score or config.set_actuel == int(
                    config.validated_bet.get('set')) + 1 or config.jeu_actuel == int(
                config.validated_bet.get('jeu')) + 1:
                # Check the last element in all_scores
                # Filter scores for matching set and jeu, excluding 0:0 scores
                matching_set_jeu_scores = {k: v for k, v in config.all_scores.items()
                                           if v.get('set') is not None
                                           and v.get('jeu') is not None
                                           and config.validated_bet.get('set') is not None
                                           and config.validated_bet.get('jeu') is not None
                                           and int(v.get('set')) == int(config.validated_bet.get('set'))
                                           and int(v.get('jeu')) == int(config.validated_bet.get('jeu'))
                                           and v.get('score') != '0:0'}

                if matching_set_jeu_scores:
                    last_score_key = max(matching_set_jeu_scores.keys())
                    last_score = matching_set_jeu_scores[last_score_key]

                    if last_score.get('score') in config.validated_bet.get('winscore'):
                        print("Matching score found:", last_score)
                        result = 'WIN'
                        config.log(f"Result: {result}", 'success', False, 2)
                    else:
                        result = 'LOSE'
                        config.log(result, 'error', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                return result


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '030'
    GetBet(driver, True)
    # driver.switch_to.window(driver.window_handles[0])
    GetResult(driver)
