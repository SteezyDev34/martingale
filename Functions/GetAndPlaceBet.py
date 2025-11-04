import config
from Functions.AfficherParis import AfficherParis
from Functions.FisrtGameBet import FirstGameBet
from Functions.GetBet import GetBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.retour_section_tps_reglementaire import RetourTpsReg


def GetAndPlaceBet(driver):
    bet_40a = False
    tentative = 0
    config.game_start = False
    actual_scryptType = config.scriptType
    while not bet_40a and not config.error:
        GetScoreActuel(driver)
        config.log('verification du jeu actuel dans tous les script')
        for scriptType in config.scriptTypeList:
            config.switchScript(scriptType)
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                config.log(f'Net profit: {config.global_match_win[scriptType]}')

            else:
                config.log(f'Net profit: {config.global_match_win[scriptType]}')
                config.log(f"FIN {config.scriptType}", 'success', False)
                continue
            if scriptType == actual_scryptType:
                continue
            if config.scriptType == '150' or config.scriptType == '015' or config.scriptType == '15A' or config.scriptType == '300' or config.scriptType == '030':
                if config.score_actuel == '0:0':
                    if not config.validated_bet or config.jeu_actuel > int(config.validated_bet.get('jeu', -1)):
                        FirstGameBet(driver)
            if config.scriptType == '30A':
                if config.score_actuel == '0:0' or config.score_actuel == '15:15' or config.score_actuel == '15:0' or config.score_actuel == '0:15':
                    if not config.validated_bet or config.jeu_actuel > int(config.validated_bet.get('jeu')):
                        FirstGameBet(driver)
            if config.scriptType == '40A':
                if config.score_actuel != "40:40" and config.score_actuel != "A:40" and config.score_actuel != "40:A":
                    if not config.validated_bet or config.jeu_actuel > int(config.validated_bet.get('jeu')):
                        FirstGameBet(driver)
                    else:
                        print('BET OK')
            if config.scriptType == '4030' or config.scriptType == '4015' or config.scriptType == '400' or config.scriptType == '4P' or config.scriptType == '5P' or config.scriptType == '6P':
                if not config.validated_bet or config.jeu_actuel > int(config.validated_bet.get('jeu')):
                    FirstGameBet(driver)
                else:
                    print('BET OK')
        config.switchScript(actual_scryptType)
        config.looking_game = int(config.jeu_actuel) + 1
        config.log(f'jeu recherhcé : {config.looking_game}', 'info', True)
        if int(config.looking_game) == 0:
            config.looking_game = 1
        elif int(config.looking_game) >= 13:
            config.result = 'RUN'
            return

        if config.jeu_actuel and int(config.jeu_actuel) > 6:
            RetourTpsReg(driver)
        # Affichage de la liste des paris
        config.log('Affichage de la liste des paris', config.newmatch)
        if not AfficherParis(driver):
            tentative = tentative + 1
            if tentative > 5:
                config.log('error recup jeu #ERR345', config.newmatch)
                config.error = True
                tentative = 0
            continue
        # On recherche le jeu actuel
        config.log('liste des paris affichée, On recherche le jeu actuel', config.newmatch)
        if not GetBet(driver, True):
            tentative = tentative + 1
            if tentative > 5:
                config.log('error recup jeu #ERR345', config.newmatch)
                config.error = True
                tentative = 0
            continue
        else:
            print('passage prochain jeu')
            bet_40a = True
        config.log('prochain PAris 40A cliqué', config.newmatch)

        # ON ENVOIE LA MISE
    txtlog = "ON ENVOIE LA MISE"
    config.log(txtlog, config.newmatch)
    send_mise = False
    # ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
    while not send_mise and not config.error:
        if PlacerMise(driver):
            send_mise = True
        else:
            config.error = True
            print('error placer mise')
