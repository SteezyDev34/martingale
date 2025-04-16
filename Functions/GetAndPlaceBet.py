import config
from Functions.AfficherParis import AfficherParis
from Functions.GetBet import GetBet
from Functions.GetMise import GetMise
from Functions.PlacerMise import PlacerMise


def GetAndPlaceBet(driver):
    bet_40a = False
    tentative = 0
    print('GetAndPlaceBet error', config.error)
    while not bet_40a and not config.error:
        # Affichage de la liste des paris
        config.log('Affichage de la liste des paris', config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            print('error afficher paris')
            break
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
