import pandas as pd
import random
import time

import DeleteBet
import Functions_stats1
import GetIfGameStart
import GetInfosDeMise
import Function_GetJeuActuel
import GetLigueName
import GetMatchScore
import Function_GetMise
import GetScoreActuel
import Function_GetSetActuel
import OuverturePageMatch
import PlacerMise
import ValidationDuParis
import VerificationListeMatchLive
import VerificationMatchTrouve
import GetCompetOk
import Functions_gsheets
import Functions_1XBET
import Functions_stats
import Function_scriptDelRunning
import GetIfScriptsRunning
import GetIfMatchPage
import re
from Function_scriptDelRunning import scriptDelRunning
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

import retour_section_tps_reglementaire

score_gamestart_list = [
    '15:0',
    '0:15',
    '15:15',
    '30:15',
    '15:30',
    '40:15',
    '15:40',
    '0:30',
    '30:0',
    '30:30',
    '30:40',
    '40:30',
    '0:40',
    '40:0',
    '40:40',
    'A:40',
    '40:A'
]
score_to_start = [
    "00(0)00(0)",
    "00(15)00(0)",
    "00(0)00(15)",
    "00(15)00(15)",
    "00(30)00(15)",
    "00(15)00(30)",
    "00(30)00(0)",
    "00(0)00(30)"
]


def all_script(driver, script_num, setaffiche, error, win, mise, perte, wantwin, increment, cote, lose, firstgame,
               jeu, set_actuel, set, score_actuel, passageset, x, match_list, match_done_key, match_found,
               rattrape_perte, matchlist_file_name, running_file_name):
    error = False
    newmatch = "no-newmatch"
    compet_ok = "no-compet-ok"

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk.main()
    compet_ok_list = get_compet[0]
    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet[1]

    ##RECHERCHE DE MATCH

    # SCRIPT NON EN COURS, SUPPRESSION DE LA LISTE RUNNING
    scriptDelRunning(script_num, running_file_name)

    # VÉRIFICATION SI PAGE DE MATCH
    match_found = GetIfMatchPage.main(driver)

    printtext = False  # est ce que le print a déjà été affiché

    # SCRIPT RECHERCHE DE MATCH
    while not match_found and not error:

        if not printtext:  # SI LE TEXTE D'ATTENTE N'EST PAS ENCORE AFFICHÉ
            print("wainting for go!")

        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        print_running_text = False  # est ce que le texte a déjà été affiché
        while not GetIfScriptsRunning.main(script_num, running_file_name):
            if not print_running_text:
                print("script " + str(script_num) + " STOP!")
                print_running_text = True

        if not printtext:# SI LE TEXTE DE LANCEMENTT N'EST PAS ENCORE AFFICHÉ
            print("script " + str(script_num) + " GO!")



        # VERIFICATION SI PAGE DE MATCH LIVE
        if VerificationListeMatchLive.main(driver):
            if not printtext:
                print('LISTE MATCH LIVE OK!')
                printtext = True
        else:
            print('LISTE MATCH LIVE NOT OK ERREUR!')
            error = True
            break

        # RECUPERATION DES LIGUES EN COURS
        bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                              'dashboard-champ-content')
        for bet_ligue in bet_list_ligue:
            # ON RÉCUPÈRE LE NOM DE LA LIGUE
            ligue_name = ""
            ligue_name = GetLigueName.main(bet_ligue)
            if not ligue_name:
                error = False
                break

            # ON VÉRIFIE QUE LA COMPET EST JOUABLE
            if any(compet_ok in ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in ligue_name for
                compet_not_ok in compet_not_ok_list):

                # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                try:
                    bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                        'c-events-scoreboard__item')
                except:
                    #s'il y une erreur on passe au suivant
                    continue
                else:
                    if len(bet_items) <= 0:
                        continue# SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
                    for bet_item in bet_items:
                        try:
                            # on récupère le score
                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                   'c-events-scoreboard__lines_tennis')
                        except:
                            print("Impossible de récupérer le score")
                            continue
                        else:
                            # si le score est récupéré
                            if len(div_bet_score) <= 0:
                                continue
                            # on le vérifie
                            bet_score = GetMatchScore.main(div_bet_score[0],
                                                                        score_to_start)
                            if bet_score:  # SI LE MATCH EST PRET
                                # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                newmatch = VerificationMatchTrouve.main(driver,bet_item,
                                                                                     matchlist_file_name)
                                if newmatch[0]:
                                    print('non non non')
                                    if OuverturePageMatch.main(bet_item, script_num,
                                                                            newmatch[1],
                                                                            running_file_name,
                                                                            matchlist_file_name):
                                        newmatch = newmatch[1]
                                        match_found = True
                                        break
                                    else:
                                        continue
            # si un match est trouvé on arrete la recherche
            if match_found:
                break


        # FIN# VERIFICATION SI PAGE DE MATCH LIVE
    # END SCRIPT RECHERCHE DE MATCH

    if GetIfMatchPage.main(driver) and not error:
        ligue_name = GetLigueName.fromUrl(driver)[0]
        match_Url = GetLigueName.fromUrl(driver)[1]# ON
        newmatch = VerificationMatchTrouve.fromUrl(driver, matchlist_file_name)[1]

        # RECHERCHE INFOS DE MISE
        players = Functions_1XBET.get_players_name(driver)
        proba40A = 0
        if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
            proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
        else:
            proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
            if proba40A ==  0:
                proba40A = Functions_stats1.get_proba_40A_other(players[0], players[1],driver,match_Url)


        print("#RECHERCHE INFOS DE MISE")
        infos_de_mise = GetInfosDeMise.main(ligue_name, rattrape_perte, perte, wantwin, mise, increment,
                                                            proba40A)
        perte = float(infos_de_mise[0])
        wantwin = float(infos_de_mise[1])
        mise = float(infos_de_mise[2])
        increment = float(infos_de_mise[3])
        rattrape_perte = infos_de_mise[4]

        # END RECHERCHE INFOS DE MISE
        saved_set = ""
        set_actuel = Function_GetSetActuel.main(driver, error, saved_set)
        saved_set = set_actuel
        if not set_actuel:
            error = True
        try:
            numset = int(set_actuel.split(' ')[0])
        except:
            error = True
        else:
            set = str(numset) + " Set"
            set_actuel = set
            # print("set actuel : " + set)

    ##PREPARATTION PREMIER PARIS
    bet_40a = False
    while not bet_40a and not error:
        #Affichage de la liste des paris
        if not Functions_1XBET.selection_des_paris_du_set(driver, set):
            error = True
            break
        #On recherche le jeu actuel
        jeu = GetJeuActuel.main(driver)
        if not Functions_1XBET.recherche_paris_40a(driver, jeu)[0]:
            error = True
            print('error recup jeu #ERR345')

        send_mise = 0
        #ON RECHERCHE LES PERTES ET ON CALCUL LA MISE
        infos_de_mise = GetMise.main(driver, rattrape_perte, wantwin, perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        if proba40A < 0.35 and cote < 3.5:
            if perte >0:
                Functions_gsheets.suivi_lost([perte, wantwin, mise, ligue_name])
            bet_40a = True
            error = True
            perte = 0
            rattrape_perte = 0
            mise = 0.2
            wantwin = 2
            print('Cote trop faible 0,2')
            break
        tentative_placermise = 0
        validate_bet = 0
        while not PlacerMise.main(driver, mise) and not error and tentative_placermise < 5:
            tentative_placermise+=1
            if tentative_placermise == 5:
                validate_bet = 1
            else:
                validate_bet = 0
        gamestart = 0
        tentative = 0
        saved_score = ""
        ##VALIDATION DU PARIS SI SCORE OK
        while not validate_bet and not error and tentative < 30:
            # VÉRIFICATION DU SCORE ACTUEL
            score_actuel = GetScoreActuel.main(driver, saved_score)
            saved_score = score_actuel
            if not score_actuel:
                error = True
            if score_actuel == "0:0" and gamestart == 0:
                print("GAME NOT START")
            elif score_actuel == "0:0" and gamestart == 1:
                validate_bet = True
                jeu = jeu + 1
                print("GAME PASS WITHOUT VALIDATE")
                gamestart = 0
                result = 1
                lose = 1
                findbtn = 1
            elif score_actuel == "40:40" or score_actuel == "40:A" or score_actuel == "A:40":
                error = True
                print("40A leave!")
                DeleteBet.main(driver, error)
                break
            else:
                gamestart = 1
            if ValidationDuParis.main(driver, jeu, mise):
                validate_bet = True
                jeu = jeu + 1
                perte = float(perte) + float(mise)
                wantwin = float(wantwin) + float(increment)
                bet_40a = True
                print("prochain jeu : " + str(jeu))
                print("wantwin : " + str(wantwin))
                print("perte : " + str(perte))
                print("mise : " + str(mise))
                print("increment : " + str(increment))
            else:
                getjeu = GetJeuActuel.main(driver)
                tentative = tentative + 1
                validate_bet = 2
                if getjeu != jeu:
                    break

        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    print("retour tps reg 1")
    retour_section_tps_reglementaire.main(driver)
    ### AND PREPARE FIRST GAME
    winmatch = 0
    while (winmatch <= 0 and not error):
        # WAIT FOR GAME START
        if passageset == 1:
            score_actuel = '0:0'
            gamestart = 1
            jeu = 1
            if rattrape_perte > 0:
                error = 0
                print("passage set 2")
                time.sleep(30)
                passageset = 0
            else:
                error = True
                print("erreur perte en 1 set")
        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            GetIfGameStart.main(driver, saved_score)
        printext = 0
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        bet_40a = 0
        while bet_40a == 0 and error == 0:

            if Functions_1XBET.selection_des_paris_du_set(driver, set) == True:
                error = 0
            else:
                Functions_1XBET.verification_page_de_match(driver)
                error = 1
                break
            jeu = Functions_1XBET.recherche_paris_40a(driver, jeu)
            if jeu[0] == True:
                jeu = jeu[1]
                bet_40a = 1
        # ON ENVOIE LA MISE
        send_mise = 0
        infos_de_mise = Functions_1XBET.get_mise(driver, rattrape_perte, wantwin, perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        while send_mise == 0 and error == 0:
            if PlacerMise.main(driver, mise) == True:
                send_mise = 1
            else:
                error = 1
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        validate_bet = 0
        saved_score = ""
        saved_set = ""
        timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
        result = 0
        #print("retour tps reg 2")
        retour_section_tps_reglementaire.main(driver)
        while (result <= 0 and error == 0):
            time.sleep(timesleep)
            score_actuel = GetScoreActuel.main(driver, saved_score)
            saved_score = score_actuel
            if score_actuel == False:
                error = 1
            if score_actuel == '40:A' or score_actuel == 'A:40' or score_actuel == '40:40':
                result = 1
                lose = 0
                winmatch = 1
                DeleteBet.main(driver, error)
                print('WIN')
            elif score_actuel == '0:0':
                print('LOSE')
                validate_bet = 0
                tentative = 0
                gamestart = 0
                lose = 1
                result = 1
                set_actuel = "nac"
                # print("vide sec actu " + set_actuel)
                set_actuel = GetSetActuel.main(driver, error, saved_set)
                saved_set = set_actuel
                if set_actuel == False:
                    error = 1
                # print("recup set ectu" + set_actuel)
                numset = int(set.split(' ')[0])
                print('numset actuel ' + str(numset))
                newset = int(set.split(' ')[0]) + 1
                print('num prochain set ' + str(newset))
                # print('VERIFICATION DU SET PAR COPIE : ' + set_actuel)
                if len(re.findall(str(numset) + ' Set', set_actuel)) > 0:  ## si on est toujours sur le meme set

                    if jeu >= 13:  # SI TIE BREAK
                        print("attente fin de tie break")
                        passageset = 1
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while validate_bet == 0 and error == 0:
                            # VÉRIFICATION DU SCORE ACTUEL
                            score_actuel = GetScoreActuel.main(driver, saved_score)
                            if score_actuel == False:
                                error = 1
                            if score_actuel == "0:0" and gamestart == 0:
                                print("GAME NOT START")
                            elif score_actuel == "0:0" and gamestart == 1:
                                validate_bet = 0
                                jeu = jeu + 1
                                print("GAME PASS WITHOUT VALIDATE")
                                gamestart = 0
                                result = 1
                                lose = 1
                                findbtn = 1

                                ###ajouter ici les actions avant de reprendre
                            elif score_actuel == "40:40" or score_actuel == "40:A" or score_actuel == "A:40":
                                error = 1
                                print("40A leave!")
                                DeleteBet.main(driver, error)
                                ###ajouter ici les actions avant de reprendre
                                break
                            else:
                                gamestart = 1
                            if ValidationDuParis.main(driver, jeu, mise) == True:
                                validate_bet = 1
                                jeu = jeu + 1
                                perte = perte + mise
                                wantwin = float(wantwin) + float(increment)
                                print("prochain jeu : " + str(jeu))
                                print("wantwin : " + str(wantwin))
                                print("perte : " + str(perte))
                                print("mise : " + str(mise))
                                print("increment : " + str(increment))
                            else:
                                getjeu = GetJeuActuel.main(driver)
                                tentative = tentative + 1
                                if getjeu != jeu:
                                    validate_bet = 0
                                    jeu = jeu + 1
                                    print("GAME PASS WITHOUT VALIDATE")
                                    gamestart = 0
                                    result = 1
                                    lose = 1
                                    findbtn = 1
                                    break
                        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                        print("retour tps reg 3")
                        retour_section_tps_reglementaire.main(driver)
                elif len(re.findall(str(newset) + ' Set', set_actuel)) > 0:  ##SI ON EST SUR LE PROCHAIN SET
                    findset = 1
                    findbtn = 1
                    validate = 1
                    set = str(newset) + " Set"
                    passageset = 1
                    result = 1
                    lose = ""
                    score_actuel = '0:0'
                    print('Passage prochain set')
                    DeleteBet.main(driver, error)
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + set_actuel)
                    error = 1
            else:
                result = 0
                set_actuel = "nac"
                set_actuel = Function_GetSetActuel.main(driver, error, saved_set)
                saved_set = set_actuel
                if set_actuel == False:
                    error = 1
                else:
                    if saved_score != score_actuel:
                        print(score_actuel)
                        saved_score = score_actuel
                    numset = int(set.split(' ')[0])
                    newset = int(set.split(' ')[0]) + 1
                    if re.search('40', score_actuel):
                        timesleep = 1
                    else:
                        timesleep = 20
        if lose == 1 and error == 0:
            print('lose : ' + str(perte))
        elif lose == 0 and error == 0:
            win = win + 1
            try:
                btn_close = driver.find_elements(By.CLASS_NAME,
                                                 'cpn-bet__remove')
            except:
                print('cpn-bet__remove not found')
            else:
                for close in btn_close:
                    try:
                        close.click()
                    except:
                        continue
            if rattrape_perte > 0:
                x = x + 1
                print("x : " + str(x))
                print("cote : " + str(cote))
                gain = (mise * cote) - perte - mise
                print("gain : " + str(gain))
                Functions_gsheets.maj_perte(script_num, gain, x)
            else:
                x = -1
            perte = 0
            mise = 0.5
            increment = 0
            wantwin = 1
            break
    if perte > 0:
        if perte >= 200:
            Functions_gsheets.update_lost(script_num, perte)
            perte = 0
            mise = 0.5
            increment = 0
            wantwin = 1
        else:
            while perte > 2:
                #perte_partiel=5
                #comp_list = ['wta']
                #ligue_name = random.choice(comp_list)
                Functions_gsheets.suivi_lost([2, 0, 1, ligue_name])
                perte = perte - 2
                if perte>1:
                    comp_list = ['wta', 'atp', 'challenger']
                    ligue_name = random.choice(comp_list)
                    Functions_gsheets.suivi_lost30([1, 0, 61, ligue_name])
                    perte = perte - 1

            mise = (float(wantwin) + float(perte)) / (float(cote) - 1)
            mise = round(mise, 2)
            Functions_gsheets.suivi_lost([perte, wantwin, mise, ligue_name])
            perte = 0
            mise = 0.5
            increment = 0
            wantwin = 1

    infos = [win, perte, wantwin, mise, x]
    print("update " + newmatch)
    Functions_1XBET.update_match_done("del", newmatch, matchlist_file_name)
    Functions_1XBET.del_running(script_num, running_file_name)
    DeleteBet.main(driver,error)
    return infos
