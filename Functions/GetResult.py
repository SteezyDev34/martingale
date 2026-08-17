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
    _getresult_iterations = 0
    while not result and not config.error:
        getresult = False
        _getresult_iterations += 1
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
            elif int(config.jeu_actuel) != int(config.validated_bet.get('jeu')):
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
            if _getresult_iterations > 300:
                # Timeout long (5 min) : forcer uniquement si on a dépassé le jeu du pari
                _past_bet = (
                    int(config.set_actuel) != int(config.validated_bet.get('set'))
                    or int(config.jeu_actuel) != int(config.validated_bet.get('jeu'))
                    or config.point_actuel > int(config.validated_bet.get('numero_point'))
                )
                if _past_bet:
                    config.log(f"GetResult timeout (300 iter) — forçage getresult", 'warning', False)
                    getresult = True
                else:
                    config.log(f"GetResult timeout (300 iter) — encore sur le même jeu, on continue", 'warning', False)
            elif int(config.set_actuel) != int(config.validated_bet.get('set')):
                getresult = True
            elif int(config.jeu_actuel) != int(config.validated_bet.get('jeu')):
                getresult = True
            elif config.point_actuel > int(config.validated_bet.get('numero_point')):
                getresult = True

            if getresult:
                # Chercher l'entrée exacte dans all_scores pour le set+jeu+numero_point du pari.
                # On utilise vainqueur_point (enregistré lors de la transition) et non une
                # comparaison de score brut — ex: 0:30→15:30 donne vainqueur=1 même si 15<30.
                vb_set = config.validated_bet.get('set')
                vb_jeu = config.validated_bet.get('jeu')
                vb_np  = config.validated_bet.get('numero_point')
                vb_ws  = config.validated_bet.get('winscore')

                target_entry = None
                for v in config.all_scores.values():
                    try:
                        if (v.get('set') is not None and vb_set is not None
                                and int(v.get('set')) == int(vb_set)
                                and v.get('jeu') is not None and vb_jeu is not None
                                and int(v.get('jeu')) == int(vb_jeu)
                                and v.get('numero_point') is not None and vb_np is not None
                                and int(v.get('numero_point')) == int(vb_np)):
                            target_entry = v
                            break
                    except Exception:
                        continue

                config.log(f'Checking results for set {vb_set} jeu {vb_jeu} point {vb_np}', 'info', indent=3)

                if target_entry is None:
                    # Fallback 1 : chercher le vainqueur_point dans l'entrée 0:0 du jeu suivant
                    # (même set). Quand un autre process a réclamé le punto final du jeu, le 0:0
                    # (début jeu+1) enregistre qui a remporté ce dernier punto via vainqueur_point.
                    try:
                        next_jeu = int(vb_jeu) + 1
                        for v in config.all_scores.values():
                            try:
                                if (int(v.get('set', -1)) == int(vb_set)
                                        and int(v.get('jeu', -1)) >= next_jeu
                                        and int(v.get('numero_point', -1)) == 0):
                                    target_entry = v
                                    config.log(f"Fallback via jeu suivant (0:0): {target_entry}", 'warning', indent=3)
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                if target_entry is None:
                    # Fallback 2 : le punto était le dernier du set — le set a changé avant que
                    # le score intermédiaire (A:40 / 40:A) soit capturé. Le 0:0 de début du
                    # set suivant (set+1, jeu=1, punto=0) a vainqueur_point = qui a gagné la
                    # transition finale, c'est-à-dire le punto du pari.
                    try:
                        next_set = int(vb_set) + 1
                        for v in config.all_scores.values():
                            try:
                                if (int(v.get('set', -1)) == next_set
                                        and int(v.get('jeu', -1)) == 1
                                        and int(v.get('numero_point', -1)) == 0):
                                    target_entry = v
                                    config.log(f"Fallback via début set suivant (0:0 set {next_set}): {target_entry}", 'warning', indent=3)
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                if target_entry is not None:
                    vp = target_entry.get('vainqueur_point')
                    config.log(f"Entry trouvée: {target_entry}", 'info', indent=3)
                    try:
                        if vp is not None and vb_ws is not None and int(vp) == int(vb_ws):
                            result = 'WIN'
                            config.log(f"Result: {result}", 'success', False, 2)
                        else:
                            result = 'LOSE'
                            config.log(f"Result > : {result} (vainqueur={vp}, attendu={vb_ws})", 'error', False, 2)
                    except Exception:
                        result = 'LOSE'
                        config.log(f"Result > : {result} (erreur comparaison)", 'error', False, 2)
                else:
                    result = 'LOSE'
                    config.log(f"Result > : LOSE (aucune entrée set={vb_set} jeu={vb_jeu} point={vb_np} dans all_scores)", 'error', False, 2)

                config.validated_bet['result'] = result
                return result
                

        elif config.scriptType in ['4P', '6P', '5P', 'BREAK', 'HOLD', '400', '4030', '4015']:
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
