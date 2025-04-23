import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise


def GetAndPlaceBet(driver):
    bet_40a = False
    tentative = 0
    print('GetAndPlaceBet error', config.error)
    config.game_start = False
    while not bet_40a and not config.error:
        GetScoreActuel(driver)
        config.looking_game = int(config.jeu_actuel) + 1
        if not config.game_start and config.score_actuel != "0:0":
            config.game_start = True
        elif config.score_actuel == "0:0" and config.game_start:
            print('NEXT GAME START SPEED UP!!!!!')
            config.looking_game = int(config.jeu_actuel)

        config.log(f'jeu recherhcé : {config.looking_game}', 'info', True)
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
    GetMise(driver)
    while not send_mise and not config.error:
        if PlacerMise(driver):
            send_mise = True
        else:
            config.error = True
            print('error placer mise')
