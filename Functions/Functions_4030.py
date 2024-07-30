import time
import Functions_gsheets
import Functions_1XBET
import re
import Functions_stats
import Functions_stats1
from selenium.webdriver.common.by import By

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
    ##RECHERCHE DE MATCH
    Functions_1XBET.del_running(script_num, running_file_name)  # SCRIPT NON EN COURS, SUPPRESSION DE LA LISTE RUNNING
    error = 0
    newmatch = "no-newmatch"
    compet_ok = "no-compet-ok"

    # ON RÉCUPÈRE LES COMPET À JOUER
    get_compet = Functions_gsheets.get_compet_ok()
    compet_ok_list = get_compet[0]
    ligue_name = ''
    # ON RÉCUPÈRE LES COMPET À NE PAS JOUER
    compet_not_ok_list = get_compet[1]
    # AUCUN MATCH TROUVE

    printtext = 0  # est ce que le print a déjà été affiché

    # VÉRIFICATION SI PAGE DE MATCH
    if Functions_1XBET.verification_page_de_match(driver) == True:
        print('PAGE MATCH OK!')
        match_found = 1
        ligue_name = Functions_1XBET.get_ligue_name_from_url(driver)  # ON
        newmatch = Functions_1XBET.verification_match_trouve_url(driver, matchlist_file_name)[1]
    # FIN# VÉRIFICATION SI PAGE DE MATCH

    # SCRIPT RECHERCHE DE MATCH
    while (match_found == 0 and error == 0):
        if printtext == 0:  # SI LE TEXTE D'ATTENTE N'EST PAS ENCORE AFFICHÉ
            print("wainting for go!")

        print_running_text = 0  # est ce que le texte a déjà été affiché

        # EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)
        while Functions_1XBET.get_if_running(script_num, running_file_name) != True:
            if print_running_text == 0:
                print("script " + str(script_num) + " STOP!")
                print_running_text = 1

            # script_running = 1 #A SUPP
        # FIN# EST CE QUE LE SCRIPT PEUT DÉMARRER? (NUM SCRIPT PRECEDENT EN COURS)

        if printtext == 0:
            print("script " + str(script_num) + " GO!")
            print('RECHERHCE DE MATCH')
            printtext = 1

        # VERIFICATION SI PAGE DE MATCH LIVE
        if Functions_1XBET.verification_liste_match_live(driver) == True:
            if printtext == 0:
                print('LISTE MATCH LIVE OK!')
                printtext = 1
            # RECUPERATION DES LIGUES EN COURS
            bet_list_ligue = driver.find_elements(By.CLASS_NAME,
                                                  'dashboard-champ-content')
            if len(bet_list_ligue) > 0:  # SI DES LIGUES SONT RÉCUPÉRÉES
                for bet_ligue in bet_list_ligue:
                    # ON RÉCUPÈRE LE NOM DE LA LIGUE
                    ligue_name = ""
                    ligue_name = Functions_1XBET.get_ligue_name(bet_ligue)

                    if ligue_name != False:
                        # ON VÉRIFIE QUE LA COMPET EST JOUABLE
                        if any(compet_ok in ligue_name for compet_ok in
                               compet_ok_list) and not any(
                            compet_not_ok in ligue_name for
                            compet_not_ok in compet_not_ok_list):
                            #print('Nom de ligue = ' + ligue_name)
                            # DEBUG DE COMPET OK MAIS CE SCRIPT EST FACULTATIF
                            for compet_ok in compet_ok_list:
                                if compet_ok in ligue_name:
                                    #print('compet ok in : ' + compet_ok)
                                    for compet_not_ok in compet_not_ok_list:
                                        if compet_not_ok in ligue_name:
                                            #print('compet not ok in : ' + compet_not_ok)
                                            continue
                                        else:
                                            compet_ok = ligue_name
                                            #print('stop compet ok : ' + compet_ok)
                                            break

                            # ON RÉCUPÈRE LES MATCHS DE LA LIGUE
                            try:
                                bet_items = bet_ligue.find_elements(By.CLASS_NAME,
                                                                    'c-events-scoreboard__item')
                            except:
                                continue

                            else:
                                if len(bet_items) > 0:  # SI DES MATCHS SONT RÉCUPÉRÉS
                                    # print('Vérification du score!')
                                    for bet_item in bet_items:
                                        if match_found != 0:
                                            break  # si un match est trouvé on arrete la recherche
                                        try:
                                            div_bet_score = bet_item.find_elements(By.CLASS_NAME,
                                                                                   'c-events-scoreboard__lines_tennis')
                                        except:
                                            print("Impossible de récupérer le score")
                                        else:
                                            if len(div_bet_score) > 0:
                                                bet_score = Functions_1XBET.get_match_score(div_bet_score[0],
                                                                                            score_to_start)
                                                if bet_score == True:  # SI LE MATCH EST PRET
                                                    # ON VERIFIE QU'IL N'A PAS DÉJA ÉTÉ PARIÉ
                                                    newmatch = Functions_1XBET.verification_match_trouve(bet_item,
                                                                                                         matchlist_file_name)
                                                    if newmatch[0] == True:
                                                        if Functions_1XBET.ouverture_page_match(bet_item, script_num,
                                                                                                newmatch[1],
                                                                                                running_file_name,
                                                                                                matchlist_file_name) == True:
                                                            newmatch = newmatch[1]
                                                            match_found = 1
                                                        else:
                                                            error = 1
                    else:
                        error = 1

                    # si un match est trouvé on arrete la recherche
                    if match_found != 0:
                        break
        else:
            error = 1
        # FIN# VERIFICATION SI PAGE DE MATCH LIVE

    # END SCRIPT RECHERCHE DE MATCH
    proba40A = 0.45
    # RECHERCHE INFOS DE MISE
    players = Functions_1XBET.get_players_name(driver)
    proba40A = 0
    if 'wta' in ligue_name.lower() or 'féminin' in ligue_name.lower() or 'femmes' in ligue_name.lower() or 'women' in ligue_name.lower():
        proba40A = Functions_stats.get_wta_proba_40A(players[0], players[1])
    else:
        proba40A = Functions_stats1.get_proba_40A(players[0], players[1])
    if proba40A >= 0.43:
        rattrape_perte = 2
    infos_de_mise = Functions_gsheets.get_infos_de_mise(ligue_name, rattrape_perte, perte, wantwin, mise, increment,
                                                        proba40A)
    print("#RECHERCHE INFOS DE MISE")
    perte = infos_de_mise[0]
    wantwin = infos_de_mise[1]
    mise = infos_de_mise[2]
    increment = infos_de_mise[3]
    rattrape_perte = infos_de_mise[4]
    saved_set = ""
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
    bet_40a = 0
    while bet_40a == 0 and error == 0:
        if Functions_1XBET.selection_des_paris_30_40_du_set(driver, set) == True:
            error = 0
        else:
            Functions_1XBET.verification_page_de_match(driver)
            error = 1
            break
        jeu_actuel = Functions_1XBET.get_jeu_actuel(driver)
        jeu = Functions_1XBET.recherche_first_paris_40_30(driver, jeu_actuel)
        if jeu[0] == True:
            win_score = jeu[2]
            print('first win score :'+win_score)
            jeu = jeu_actuel

        else:
            error = 1
            print('error recup jeu #ERR345')

        send_mise = 0
        infos_de_mise = Functions_1XBET.get_mise(driver, rattrape_perte, wantwin, perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        print('nouvelle perte : ' + str(perte))
        while send_mise == 0 and error == 0:
            if Functions_1XBET.placer_mise(driver, mise) == True:
                send_mise = 1
            else:
                error = 1
        validate_bet = 0
        gamestart = 0
        tentative = 0
        saved_score = ""
        ##VALIDATION DU PARIS SI SCORE OK
        while validate_bet == 0 and error == 0 and tentative < 30:
            # VÉRIFICATION DU SCORE ACTUEL
            score_actuel = Functions_1XBET.get_score_actuel(driver, saved_score)
            saved_score = score_actuel
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
                if win_score == '30:40':
                    win_score = '40:30'
                else:
                    win_score = '30:40'

                ###ajouter ici les actions avant de reprendre
                '''elif score_actuel == "40:40" or score_actuel == "40:A" or score_actuel == "A:40":
                    error = 1
                    print("40A leave!")
                    Functions_1XBET.delete_bet(driver, error)
                    ###ajouter ici les actions avant de reprendre
                    break'''
            else:
                gamestart = 1
            if Functions_1XBET.validation_du_paris(driver, jeu, mise) == True:
                validate_bet = 1
                jeu = jeu + 1
                perte = perte + mise
                wantwin = wantwin + increment
                bet_40a = 1
                print("prochain jeu : " + str(jeu))
                print("wantwin : " + str(wantwin))
                print("perte : " + str(perte))
                print("mise : " + str(mise))
                print("increment : " + str(increment))
            else:
                getjeu = Functions_1XBET.get_jeu_actuel(driver)
                tentative = tentative + 1
                validate_bet = 2
                if getjeu != jeu:
                    break

        # RETOUR SUR LA SECTION TPS REGLEMENTAIRE
    print("retour tps reg 1")
    Functions_1XBET.retour_section_tps_reglementaire(driver)
    ### AND PREPARE FIRST GAME
    winmatch = 0
    while (winmatch <= 0 and error == 0):
        # WAIT FOR GAME START
        if passageset == 1:
            score_actuel = '0:0'
            gamestart = 1
            jeu_actuel = 0
            if rattrape_perte < 3:
                error = 0
                print("passage set 2")
                time.sleep(30)
                passageset = 0
            else:
                error = 1
                print("erreur perte en 1 set")
        else:
            gamestart = 0
            ##ATTENTE QUE LE JEU COMMENCE
            Functions_1XBET.get_if_game_start(driver, saved_score)
        printext = 0
        # JEU COMMENCÉ ON PREPARE LE PROCHAIN BET
        bet_40a = 0
        while bet_40a == 0 and error == 0:

            if Functions_1XBET.selection_des_paris_30_40_du_set(driver, set) == True:
                error = 0
            else:
                Functions_1XBET.verification_page_de_match(driver)
                error = 1
                break
            if jeu_actuel != 0:
                jeu_actuel = Functions_1XBET.get_jeu_actuel(driver) + 1
            jeu = Functions_1XBET.recherche_paris_40_30(driver, jeu_actuel)

            if jeu[0] == True:
                #win_score = jeu[2]
                jeu = jeu_actuel

                bet_40a = 1
            else:
                error = 1
        # ON ENVOIE LA MISE
        send_mise = 0
        infos_de_mise = Functions_1XBET.get_mise(driver, rattrape_perte, wantwin, perte)
        mise = infos_de_mise[0]
        cote = infos_de_mise[1]
        while send_mise == 0 and error == 0:
            if Functions_1XBET.placer_mise(driver, mise) == True:
                send_mise = 1
            else:
                error = 1
        ##ON ATTEND LE RESULTAT POUR VALIDER LE PARIS
        validate_bet = 0
        saved_score = ""
        saved_set = ""
        timesleep = 1  # TEMPS D'ATTENTE AVANT DE RECUPERER LE SCORE PASSE À 1 SI 40 DANS LE SCORE
        result = 0
        print("retour tps reg 2")
        Functions_1XBET.retour_section_tps_reglementaire(driver)
        while (result <= 0 and error == 0):
            time.sleep(timesleep)
            saved_score = score_actuel
            score_actuel = Functions_1XBET.get_score_actuel(driver, saved_score)
            print('win score = '+ win_score)
            if score_actuel == False:
                error = 1
            if score_actuel == '0:0' and saved_score == win_score:
                result = 1
                lose = 0
                winmatch = 1
                Functions_1XBET.delete_bet(driver, error)
                print('WIN')
            elif score_actuel == '0:0' and saved_score != win_score :
                print('LOSE')
                validate_bet = 0
                tentative = 0
                gamestart = 0
                lose = 1
                result = 1
                if win_score == '30:40':
                    win_score = '40:30'
                else:
                    win_score = '30:40'
                set_actuel = "nac"
                # print("vide sec actu " + set_actuel)
                set_actuel = Functions_1XBET.get_set_actuel(driver, error, saved_set)
                saved_set = set_actuel
                saved_score = score_actuel
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
                            score_actuel = Functions_1XBET.get_score_actuel(driver, saved_score)
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
                                Functions_1XBET.delete_bet(driver, error)
                                ###ajouter ici les actions avant de reprendre
                                break
                            else:
                                gamestart = 1
                            if Functions_1XBET.validation_du_paris(driver, jeu, mise) == True:
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
                                getjeu = Functions_1XBET.get_jeu_actuel(driver)
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
                        Functions_1XBET.retour_section_tps_reglementaire(driver)
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
                    Functions_1XBET.delete_bet(driver, error)
                    time.sleep(30)
                else:
                    print("ERROR : recup set " + set_actuel)
                    error = 1
            else:
                saved_score = score_actuel
                result = 0
                set_actuel = "nac"
                set_actuel = Functions_1XBET.get_set_actuel(driver, error, saved_set)
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
            """while perte > 5.79:
                #perte_partiel=5
                #comp_list = ['wta']
                #ligue_name = random.choice(comp_list)
                Functions_gsheets.suivi_lost([5.79, 1.2, 2.33, ligue_name])
                perte = perte - 5.79
                '''if perte>3.15:
                    comp_list = ['wta', 'atp', 'challenger']
                    ligue_name = random.choice(comp_list)
                    Functions_gsheets.suivi_lost30([3.15, 0.8, 1.65, ligue_name])
                    perte = perte - 3.15'''"""

            mise = (wantwin + perte) / (cote - 1)
            mise = round(mise, 2)
            Functions_gsheets.suivi_lost30(perte, wantwin, mise, ligue_name)
            perte = 0
            mise = 0.2
            increment = 0
            wantwin = 0.2

    infos = [win, perte, wantwin, mise, x]
    print("update " + newmatch)
    Functions_1XBET.update_match_done("del", newmatch, matchlist_file_name)
    Functions_1XBET.del_running(script_num, running_file_name)
    return infos
