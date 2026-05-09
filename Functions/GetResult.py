import time

import config
from Functions.GetJeuActuel import GetSetScoreActuel
from Functions.GetScoreActuel import GetScoreActuel
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetResult(driver):
    ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
    if config.scriptType not in ['15V1', '15V2']:
        RetourTpsReg(driver)
    txtlog = "ON ATTEND LE RESULTAT POUR VALIDER LE PARIS"
    print('validated_bet = ', config.validated_bet)
    config.log(txtlog, config.newmatch)
    config.saved_set = ""
    timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
    result = False
    while not result and not config.error:
        getresult = False
        time.sleep(timesleep)
        GetScoreActuel(driver)
        if not config.validated_bet:
            result = 'LOSE'
            print('NO VALIDATED BET')
            config.log(result, 'error', False, 2)
            config.validated_bet['result'] = result
            return result

        if config.scriptType == "40A" or config.scriptType == '40:30' or config.scriptType == '6P':
            passed_score = ['0:0', '40:40', '40:A', 'A:40']
        elif config.scriptType == "30A":
            passed_score = [
                '30:30', '40:15', '15:40', '30:40',
                '40:30', '40:0', '0:40', '40:40', '40:A', 'A:40'
            ]
        elif config.scriptType == "15A":
            passed_score = [
                '15:15', '30:0', '0:30', '30:15', '15:30', '30:30', '40:15',
                '15:40', '30:40', '40:30', '40:0', '0:40', '40:40', '40:A', 'A:40'
            ]
        elif config.scriptType == "015" or config.scriptType == "150" or config.scriptType == '15V1' or config.scriptType == '15V2' :
            passed_score = [
                '0:15', '15:0', '15:15', '30:0', '0:30', '30:15', '15:30', '30:30', '40:15',
                '15:40', '30:40', '40:30', '40:0', '0:40', '40:40', '40:A', 'A:40'
            ]
        elif config.scriptType == '030' or config.scriptType == '300':
            passed_score = [
                '30:0', '0:30', '40:15', '15:40', '30:40', '40:30', '40:0',
                '0:40', '30:15', '15:30', '40:40', '40:A', 'A:40', '15:15'
            ]
            if config.validated_bet.get('winscore') is not None and config.validated_bet.get('winscore') == '0:30':
                passed_score.append('15:0')
            elif config.validated_bet.get('winscore') is not None and config.validated_bet.get('winscore') == '30:0':
                passed_score.append('0:15')
        elif config.scriptType == '400' or config.scriptType == '4P':
            passed_score = [
                '0:0', '15:15', '30:15', '15:30', '30:30',
                '40:15', '15:40', '40:30', '30:40', '40:40',

            ]
        elif config.scriptType == '40:15' or config.scriptType == '5P':
            passed_score = [
                '0:0', '30:30', '40:30', '30:40', '40:40',

            ]
        else:
            passed_score = [
                '0:0'
            ]

        if config.scriptType == "40A" or config.scriptType == "30A" or config.scriptType == "150" or config.scriptType == "015" or config.scriptType == "15A" or config.scriptType == '030' or config.scriptType == '300':
            if int(config.set_actuel) != int(config.validated_bet.get('set')):
                getresult = True
            elif config.jeu_actuel != int(config.validated_bet.get('jeu')):
                getresult = True
            elif config.score_actuel in passed_score:
                getresult = True

            if getresult:
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
                config.validated_bet['result'] = result
                return result
        elif config.scriptType == "15V1" or config.scriptType == "15V2":
            if int(config.set_actuel) != int(config.validated_bet.get('set')):
                getresult = True
            elif config.jeu_actuel != int(config.validated_bet.get('jeu')):
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
                    config.log(f"Last score for set {config.validated_bet.get('set')} jeu {config.validated_bet.get('jeu')}: {last_score}", 'info', indent=3)

                    # Déduction simple du vainqueur à partir du dernier score du jeu
                    s = str(last_score.get('score', '')).upper()
                    def _winner_from_score_simple(s):
                        if s == 'A:40':
                            return 1
                        if s == '40:A':
                            return 2
                        if ':' not in s:
                            return 0
                        l, r = s.split(':')
                        return 1 if int(l) > int(r) else (2 if int(r) > int(l) else 0)

                    inferred = _winner_from_score_simple(s)
                    expected = config.validated_bet.get('winscore')

                    if expected is not None and int(inferred) == int(expected):
                        print("Matching score found:", last_score)
                        result = 'WIN'
                        config.log(f"Result: {result}", 'success', False, 2)
                    else:
                        result = 'LOSE'
                        config.log(f"Result > : {result}", 'error', False, 2)
                config.validated_bet['result'] = result
                return result
            elif config.point_actuel > int(config.validated_bet.get('numero_point')):
                # Check if validated_bet['numero_point'] is greater than max numero_point recorded
                getresult = True

            if getresult:
                config.log(f'Checking results for set {config.validated_bet.get("set")}, jeu {config.validated_bet.get("jeu")}, point {config.validated_bet.get("numero_point")}', 'info', indent=3)
                print()
                matching_scores = [score for score in config.all_scores.values()
                                   if score.get('set') is not None
                                   and config.validated_bet.get('set') is not None
                                   and int(score.get('set')) == int(config.validated_bet.get('set'))
                                   and score.get('jeu') is not None
                                   and config.validated_bet.get('jeu') is not None
                                   and config.validated_bet.get('vainqueur_point') != 0
                                   and int(score.get('jeu')) == int(config.validated_bet.get('jeu'))
                                   and int(score.get('numero_point')) == int(config.validated_bet.get('numero_point'))
                                   and score.get('vainqueur_point') == config.validated_bet.get('winscore')]
                if matching_scores:
                    print("Matching score found:", matching_scores[0])
                    result = 'WIN'
                    config.log(f"Result: {result}", 'success', False, 2)
                else:
                    result = 'LOSE'
                    config.log(result, 'error', False, 2)
                config.validated_bet['result'] = result
                return result
                

        elif config.scriptType in ['4P', '6P', '5P', 'BREAK', '400', '4030', '4015']:
            if int(config.set_actuel) != int(config.validated_bet.get('set')):
                getresult = True
                print('get result set diff')
            elif int(config.jeu_actuel) != int(config.validated_bet.get('jeu')):
                getresult = True
                print('get result jeu diff')
            elif config.score_actuel in passed_score:
                getresult = True
            if getresult:
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
                config.validated_bet['result'] = result
                return result
        elif config.scriptType == '1SET':
            print(config.validated_bet)
            config.set_actuel = int(config.validated_bet.get('set'))
            GetSetScoreActuel(driver)
            if config.validated_bet.get('winscore') == 'V1' and config.jeu_actuel[0] > \
                    config.jeu_actuel[1]:
                print(config.jeu_actuel[0], config.jeu_actuel[1])
                result = 'WIN'
                config.log(f"Result: {result}", 'success', False, 2)
            elif config.validated_bet.get('winscore') == 'V2' and config.jeu_actuel[0] < \
                    config.jeu_actuel[1]:
                result = 'WIN'
                config.log(f"Result: {result}", 'success', False, 2)
            else:
                result = 'LOSE'
                config.log(result, 'error', False, 2)

            return result


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.scriptType = '1SET'
    config.validated_bet = {
        'set': 1,
        'win': 'V2'
    }
    # GetBet(driver, True)
    # driver.switch_to.window(driver.window_handles[0])
    GetResult(driver)
