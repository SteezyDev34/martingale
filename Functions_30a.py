
import random

import time
import re

import DeleteBet
import Functions_gsheets
import Functions_1XBET


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

import Functions_stats
import Functions_stats1
import GetCompetOk
import GetIfMatchPage
import GetLigueName
import GetMatchScore
import OuverturePageMatch
import VerificationMatchTrouve

score_gamestart_list = [
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
    '40:A',
    '0:0'
]
compet_not_ok_list = [
    'cyber',
    'world',
    'ace',
    'russie'
]
score_to_start = [
    "00(0)00(0)",
"00(15)00(0)",
"00(15)00(15)",
"00(0)00(15)",


]
other = ["00(30)00(15)",
"00(15)00(30)",
"00(40)00(15)",
"00(15)00(40)",
"00(40)00(30)",
"00(30)00(40)",
"00(0)00(30)",
"00(30)00(0)",
"00(0)00(40)",
"00(40)00(0)",
"00(40)00(40)",
"00(40)00(A)",
"00(A)00(40)"]

def all_script(driver, script_num, setaffiche, error, win, mise, perte, wantwin, increment, cote, lose, firstgame,
               jeu, set_actuel, set, score_actuel, passageset, x, match_list, match_done_key, match_found,
               rattrape_perte,matchlist_file_name,running_file_name):
    ##RECHERCHE DE MATCH
    Functions_1XBET.del_running(script_num,running_file_name)
    newmatch = "newmatch"
    error = 0
    newmatch = "newmatch"
    compet_ok = ""
    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = GetCompetOk.main()
    compet_ok_list = get_compet[0]
    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet[1]
    # AUCUN MATCH TROUVE
    printtext = 0
    wintour =0
    #SCRIPT RECHERCHE DE MATCH
    if Functions_1XBET.verification_page_de_match(driver) == True:  # VÉRIFICATION SI PAGE DE MATCH
        print('PAGE MATCH OK!')
        match_found = 1
        Functions_1XBET.add_running(script_num, running_file_name)
        ligue_name = Functions_1XBET.get_ligue_name_from_url(driver)
        newmatch = Functions_1XBET.verification_match_trouve_url(driver, matchlist_file_name)[1]
    print_running_text = 0
    while (match_found == 0 and error == 0):
        ifrunning = False
        if printtext == 0:
            print("wainting for go!")
        while ifrunning != True:  # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
            ifrunning = Functions_1XBET.get_if_running(script_num, running_file_name)
            if ifrunning == True:
                print_running_text = 0
            else:
                if print_running_text == 0:
                    print("script " + str(script_num) + " STOP!")
                    print_running_text = 1

            script_running = 1
        if printtext == 0:
            print("script "+str(script_num)+" GO!")
        if printtext == 0:
            print('RECHERHCE DE MATCH')
        if Functions_1XBET.verification_liste_match_live(driver) == True:  # VERIFICATION SI PAGE DE MATCH LIVE
            if printtext == 0:
                print('LISTE MATCH LIVE OK!')
                printtext = 1
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
                        # s'il y une erreur on passe au suivant
                        continue
                    else:
                        if len(bet_items) <= 0:
                            continue  # SI AUCUN MATCHS RÉCUPÉRÉS ON PASSE AU SUIVANT
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
                                    newmatch = VerificationMatchTrouve.main(driver, bet_item,
                                                                            matchlist_file_name)
                                    if newmatch[0]:
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

        else:
            error = 1
    bet_30a = 0
    winmatch = 0
    error = False
    #END SCRIPT RECHERCHE DE MATCH
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
            proba40A = Functions_stats1.get_proba_40A(players[0], players[1],driver,match_Url)
    # RECHERCHE INFOS DE MISE
    infos_de_mise = Functions_gsheets.get_infos_de_mise30A(ligue_name, rattrape_perte, perte, wantwin, mise, increment)
    print("#RECHERCHE INFOS DE MISE")
    perte = infos_de_mise[0]
    wantwin = infos_de_mise[1]
    mise = infos_de_mise[2]
    increment = infos_de_mise[3]
    rattrape_perte = 1
    saved_set = ""
    saved_score = ""
    # END RECHERCHE INFOS DE MISE

    if error == 0:
        set_actuel = Functions_1XBET.get_set_actuel(driver, error, saved_set)
        saved_set = set_actuel
        if set_actuel == False:
            error = 1
        try:
            numset = int(set_actuel.split(' ')[0])
        except:
            error = 1
        else:
            set = str(numset) + " Set"
            set_actuel = set
            # print("set actuel : " + set)
    ##PREPARATTION PREMIER PARIS
    bet_30a = 0
    first_game_pass = 0
    while bet_30a == 0 and error == 0  and jeu <13:
        score_actuel = Functions_1XBET.get_score_actuel(driver,saved_score)

        if score_actuel == "30:30" or score_actuel == "30:15" or score_actuel == "15:30" or score_actuel == "30:0" or score_actuel == "0:30" or score_actuel == "30:40" or score_actuel == "40:30" or score_actuel == "0:40" or score_actuel == "15:40" or score_actuel == "40:40" or score_actuel == "A:40" or score_actuel == "40:A" or score_actuel == "40:0" or score_actuel == "40:15":
            first_game_pass = 1
            print('first game passss')
            bet_30a = 1
            break
        if Functions_1XBET.selection_des_paris_du_set(driver, set) == True:
            error = 0
        else:
            Functions_1XBET.verification_page_de_match(driver)
            error = 1
            break
        tentative1 =0
        sucess_get_paris30a  = 0
        while sucess_get_paris30a == 0:
            try:
                Functions_1XBET.recherche_paris_30a(driver, jeu)
            except:
                tentative1 = tentative1+1
                if tentative1 >5:
                    error=1
            else:
                sucess_get_paris30a = 1
        jeu = Functions_1XBET.get_jeu_actuel_30a(driver)
        send_mise = 0
        infos_de_mise = Functions_1XBET.get_mise30a(driver,rattrape_perte,wantwin,perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        if proba40A < 0.3 and cote < 3:
            if perte >0:
                Functions_gsheets.suivi_lost30([perte, wantwin, mise, ligue_name])
            bet_30a = True
            error = True
            perte = 0
            rattrape_perte = 0
            mise = 0.5
            wantwin = 1
            print('Cote trop faible')
            break
        print('nouvelle perte : '+str(perte))
        while send_mise == 0 and error == 0  and jeu <13:
            if Functions_1XBET.placer_mise(driver, mise) == True:
                send_mise = 1
            else:
                error = 1
        validate_bet = 0
        gamestart = 0
        tentative = 0
        saved_score = ""
        ##VALIDATION DU PARIS SI SCORE OK
        while validate_bet == 0 and error == 0 and tentative <10:
            #VÉRIFICATION DU SCORE ACTUEL
            score_actuel = Functions_1XBET.get_score_actuel(driver,saved_score)
            saved_score = score_actuel
            if score_actuel == False:
                error = 1
                ###ajouter ici les actions avant de reprendre
            elif score_actuel == "30:30":
                error = 1
                print("30A leave!")
                Functions_1XBET.delete_bet(driver, error)
                ###ajouter ici les actions avant de reprendre
                break
            else:
                print('gamestart')
                gamestart = 1
            if Functions_1XBET.validation_du_paris(driver,jeu,mise) == True:
                validate_bet = 1
                jeu = jeu + 1
                perte = perte + mise
                wantwin = wantwin + increment
                bet_30a = 1
                print("prochain jeu : " + str(jeu))
                print("wantwin : " + str(wantwin))
                print("perte : " + str(perte))
                print("mise : " + str(mise))
                print("increment : " + str(increment))
            else:
                Functions_1XBET.get_jeu_actuel_30a(driver)
                getjeu = Functions_1XBET.get_jeu_actuel_30a(driver)
                tentative = tentative + 1
                validate_bet = 2
                print('pari non validé')
                if getjeu != jeu:
                    break

        #RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    print("retour tps reg 1")
    Functions_1XBET.retour_section_tps_reglementaire(driver)
    ### AND PREPARE FIRST GAME
    winmatch = 0
    while (winmatch <= 0 and error == 0):
        # WAIT FOR GAME START
        if passageset == 1:
            score_actuel = '0:0'
            gamestart = 1
            if rattrape_perte == 1:
                error = 0
                print("passage set 2")
                gamestart = 0
                passageset = 0
            else:
                error = 1
                print("erreur perte en 1 set")
        else:
            gamestart = 0
        ##ATTENTE QUE LE JEU COMMENCE
        print('attente gamle start 546 '+str(first_game_pass))
        if first_game_pass == 0:
            Functions_1XBET.get_if_game_start_scnd(driver,saved_score)
        printext = 0
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        bet_30a = 0
        while bet_30a == 0 and error == 0  and jeu <13:

            if Functions_1XBET.selection_des_paris_du_set(driver, set) == True:
                error = 0
                Functions_1XBET.recherche_prochain_paris_30a(driver, jeu)
                jeu =Functions_1XBET.get_jeu_actuel_30a(driver)
                if jeu != 0:
                    jeu = jeu+1
                    print('jeu recup 6868 '+str(jeu))
                    bet_30a = 1
                else:
                    error = 1
            else:
                Functions_1XBET.verification_page_de_match(driver)
                error = 1
                break
        #ON ENVOIE LA MISE
        send_mise = 0
        print('envoie dela mise et calcul 6846')
        infos_de_mise = Functions_1XBET.get_mise30a(driver, rattrape_perte, wantwin, perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        while send_mise == 0 and error == 0  and jeu <13:
            if Functions_1XBET.placer_mise(driver, mise) == True:
                send_mise = 1
            else:
                error = 1
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        validate_bet = 0
        saved_score = ""
        saved_set = ""
        timesleep = 1#TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 30 DANS LE SCORE
        result = 0
        print("retour tps reg 2")
        Functions_1XBET.retour_section_tps_reglementaire(driver)
        while (result <= 0 and error == 0):
            time.sleep(timesleep)

            score_actuel = Functions_1XBET.get_score_actuel(driver,saved_score)
            saved_score = score_actuel
            if score_actuel == False:
                error = 1
            if score_actuel == '30:30':
                if first_game_pass !=1:
                    result = 1
                    lose = 0
                    winmatch = 1
                    Functions_1XBET.delete_bet(driver, error)
                    print('WIN')
            elif score_actuel == '40:0' or score_actuel == '40:15' or score_actuel == '0:40' or score_actuel == '15:40' or score_actuel == '40:30' or score_actuel == '30:40' or score_actuel == '40:40' or score_actuel == 'A:40' or score_actuel == '40:A':
                print('LOSE')
                first_game_pass = 0
                validate_bet = 0
                tentative = 0
                gamestart = 0
                lose = 1
                result = 1
                set_actuel = "nac"
                # print("vide sec actu " + set_actuel)
                set_actuel = Functions_1XBET.get_set_actuel(driver, error,saved_set)
                saved_set = set_actuel
                if set_actuel == False:
                    error = 1
                # print("recup set ectu" + set_actuel)
                numset = int(set.split(' ')[0])
                print('numset actuel ' + str(numset))
                newset = int(set.split(' ')[0]) + 1
                print('num prochain set ' + str(newset))
                # print('VERIFICATION DU SET PAR COPIE : ' + set_actuel)
                if len(re.findall(str(numset) + ' Set', set_actuel)) > 0:## si on est toujours sur le meme set

                    if jeu > 13:#SI TIE BREAK
                        print("attente fin de tie break")
                        passageset = 1
                    else:
                        ##VALIDATION DU PARIS SI SCORE OK
                        while validate_bet == 0 and error == 0:
                            # VÉRIFICATION DU SCORE ACTUEL
                            print('validation 987')
                            score_actuel = Functions_1XBET.get_score_actuel(driver,saved_score)
                            if score_actuel == False:
                                error = 1
                            if (score_actuel == "0:15" or score_actuel == "15:15" or score_actuel == "15:0" or score_actuel == "0:30" or score_actuel == "15:30" or score_actuel == "30:15" or score_actuel == "30:0") and gamestart == 1:
                                validate_bet = 0
                                #jeu = jeu + 1
                                print("GAME PASS WITHOUT VALIDATE")
                                gamestart = 1
                                result = 1
                                lose = 1
                                findbtn = 1

                                ###ajouter ici les actions avant de reprendre
                            elif score_actuel == "30:30":
                                error = 1
                                print("30A leave!")
                                Functions_1XBET.delete_bet(driver, error)
                                ###ajouter ici les actions avant de reprendre
                                break
                            else:
                                gamestart = 0
                                if Functions_1XBET.validation_du_paris(driver,jeu,mise) == True:
                                    print('validation 097')
                                    validate_bet = 1
                                    jeu = jeu + 1
                                    perte = perte + mise
                                    wantwin = wantwin + increment
                                    print("prochain jeu : " + str(jeu))
                                    print("wantwin : " + str(wantwin))
                                    print("perte : " + str(perte))
                                    print("mise : " + str(mise))
                                    print("increment : " + str(increment))
                                else:
                                    print('err validation 49686')
                                    getjeu = Functions_1XBET.get_jeu_actuel_30a(driver)
                                    tentative = tentative + 1
                                    validate_bet = 1
                                    if getjeu != jeu-1:
                                        validate_bet = 0
                                        #jeu = jeu + 1
                                        print("GAME PASS WITHOUT VALIDATE 2")
                                        gamestart = 0
                                        result = 1
                                        lose = 1
                                        findbtn = 1
                                        break
                        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
                        print("retour tps reg 3")
                        Functions_1XBET.retour_section_tps_reglementaire(driver)
                elif len(re.findall(str(newset) + ' Set', set_actuel)) > 0:##SI ON EST SUR LE PROCHAIN SET
                    findset = 1
                    findbtn = 1
                    validate = 1
                    set = str(newset) + " Set"
                    passageset = 1
                    result = 1
                    lose = ""
                    score_actuel = '0:0'
                    print('Passage prochain set')
                    Functions_1XBET.delete_bet(driver, error)
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + set_actuel)
                    error = 1
            else:
                first_game_pass = 0
                result = 0
                set_actuel = "nac"
                set_actuel = Functions_1XBET.get_set_actuel(driver, error,saved_set)
                saved_set = set_actuel
                if set_actuel == False:
                    error = 1
                else:
                    if saved_score != score_actuel:
                        print(score_actuel)
                        saved_score = score_actuel
                    numset = int(set.split(' ')[0])
                    newset = int(set.split(' ')[0]) + 1
                    if re.search('30', score_actuel):
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
            if wintour < 0 and jeu <1:
                print('wintout '+str(wintour))
                wintour = wintour+1
                x = x + 1
                print("x : " + str(x))
                print("cote : "+str(cote))
                gain = (mise * cote) - perte - mise
                print("gain : "+str(gain))
                Functions_gsheets.maj_perte(script_num, gain, x)

                # RECHERCHE INFOS DE MISE
                infos_de_mise = Functions_gsheets.get_infos_de_mise30A(ligue_name, rattrape_perte, perte, wantwin, mise,
                                                                       increment)
                print("#RECHERCHE INFOS DE MISE")
                perte = infos_de_mise[0]
                wantwin = infos_de_mise[1]
                mise = infos_de_mise[2]
                increment = infos_de_mise[3]
                rattrape_perte = 1
                saved_set = ""
                saved_score = ""
                # END RECHERCHE INFOS DE MISE
                winmatch = 0
                lose=1
            else:
                x=-1
            perte = 0
            mise = 0.71
            increment = 0
            wantwin = 1
    if perte > 0:
        if perte >= 200:
            Functions_gsheets.update_lost(script_num, perte)
            perte = 0
            mise = 0.71
            increment = 0
            wantwin = 1
        else:
            while perte > 6.12:
                #perte_partiel=5
                comp_list = ['wta', 'atp']
                compet_ok = random.choice(comp_list)
                Functions_gsheets.suivi_lost30([6.12, 1.2, 5.23, compet_ok])
                perte = perte-6.12
            mise = (wantwin + perte) / (cote - 1)
            mise = round(mise, 2)
            Functions_gsheets.suivi_lost30([perte, wantwin, mise,compet_ok])
            perte = 0
            mise = 0.71
            increment = 0
            wantwin = 1


    infos = [win, perte, wantwin, mise,x]
    print(newmatch)
    #Functions_1XBET.update_match_done("del", newmatch,matchlist_file_name)
    Functions_1XBET.del_running(script_num,running_file_name)
    DeleteBet.main(driver,error)
    return infos
