import config
from Functions.AfficherParis import AfficherParis
from Functions.Function_GetJeuActuel import GetJeuActuel
from Functions.GetBet import GetBet
from Functions.GetIfGameStart import GetIfGameEnd
from Functions.GetMise import GetMise
from Functions.GetScoreActuel import GetScoreActuel
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis
from AfficherParis import AfficherParis



def FirstGameBet(driver):
    ##PREPARATTION PREMIER PARIS
    config.saveLog('PREPARATION DU PREMIER PARIS',1,config.newmatch)
    bet_40a = False
    tentative = 0
    while not bet_40a and not config.error:
        #Affichage de la liste des paris
        config.saveLog('Affichage de la liste des paris',0,config.newmatch)
        if not AfficherParis(driver):
            config.error = True
            break
        else:
            #On recherche le jeu actuel
            config.saveLog('liste des pariis affichée, On recherche le jeu actuel',0,config.newmatch)
            jeu = GetBet4030(driver)

        if not jeu:
            tentative +=1
            if tentative>5:
                config.error = True
                config.saveLog('error recup jeu #ERR345',1,config.newmatch)
        else:
            win_score30 = jeu[1]
            config.saveLog('Premier PAris 40A cliqué',1,config.newmatch)
            send_mise = 0
            #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
            GetMise(driver)
            config.saveLog('cotemini : ' + str(config.cotemini) + ' cote : ' + str(config.cote),1)
            config.saveLog('proba mini : ' + str(config.probamini) + ' proba : ' + str(config.proba40A),1)
            config.saveLog('Rattrapage : ' + str(config.rattrape_perte),1)
            if float(config.proba40A) < float(config.probamini) and float(config.cote) < float(config.cotemini):
                bet_40a = True
                config.error = True
                config.saveLog('Cote trop faible 0,2', config.newmatch)
                break
            tentative_placermise = 0
            validate_bet = False
            config.saveLog('On place la mise',1,config.newmatch)
            while not PlacerMise4030(driver,config.mise) and not config.error and tentative_placermise < 2:
                tentative_placermise+=1
                if tentative_placermise == 2:
                    validate_bet = True
                else:
                    validate_bet = False
            gamestart = False
            tentative = 0
            config.saved_score = ""
            config.saveLog('On vérifie le score pour valider le paris',0,config.newmatch)
            ##VALIDATION DU PARIS SI SCORE OK
            while not validate_bet and not config.error and tentative < 30:
                # VÉRIFICATION DU SCORE ACTUEL
                GetScoreActuel(driver)
                config.saved_score = config.score_actuel
                if config.score_actuel == "0:0" and not gamestart:
                    config.saveLog("GAME NOT START",config.newmatch)
                elif config.score_actuel == "0:0" and gamestart:
                    validate_bet = True
                    config.jeu_actuel += 1
                    config.saveLog("GAME PASS WITHOUT VALIDATE ON FIRST",config.newmatch)
                    gamestart = False
                    result = True
                    lose = True
                    findbtn = True
                    if win_score30 == '30:40':
                        win_score30 = '40:30'
                    else:
                        win_score30 = '30:40'
                else:
                    gamestart = True
                    config.saveLog("GAME START",config.newmatch)
                if ValidationDuParis4030(driver, config.mise):
                    validate_bet = True
                    bet_40a = True
                    config.jeu_actuel +=1
                    config.perte = float(config.perte) + float(config.mise)
                    config.wantwin = float(config.wantwin) + float(config.increment)
                    config.saveLog("prochain jeu : " + str(config.jeu_actuel), config.newmatch)
                    config.saveLog("wantwin : " + str(config.wantwin), config.newmatch)
                    config.saveLog("perte : " + str(config.perte), config.newmatch)
                    config.saveLog("mise : " + str(config.mise), config.newmatch)
                    config.saveLog("increment : " + str(config.increment), config.newmatch)
                else:
                    GetJeuActuel(driver)
                    tentative = tentative + 1
                    validate_bet = True
                    config.saveLog("Erreur lor de la validation, nouvelle tentative",config.newmatch)
if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    driver.switch_to.window(driver.window_handles[0])

    print(FirstGameBet(driver))