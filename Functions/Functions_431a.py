#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module Functions_431a.py
------------------------

Ce module contient les fonctions principales pour l'exécution de la stratégie de martingale 431a.
Il gère l'ensemble du flux de travail pour les paris sur les matchs de tennis, incluant:
- La recherche de matchs appropriés
- La gestion des paris (placement, validation, suppression)
- Le suivi des scores et des jeux
- La gestion des résultats (gains/pertes)
- La stratégie de martingale pour récupérer les pertes

Le module est conçu pour fonctionner avec le système de paris 1XBET et utilise
Selenium pour l'automatisation du navigateur.

Auteur: Steeven
Date de création: Non spécifiée
"""

# Modules standards
import inspect  # Pour obtenir des informations sur les frames d'exécution (utilisé pour le logging d'erreurs)
import time     # Pour les délais d'attente entre les actions

# Modules internes
import config   # Configuration globale du système

# Fonctions d'interaction avec 1XBET
from Functions import Functions_1XBET  # Fonctions générales pour interagir avec 1XBET
from Functions import GetLigueName, AddRunning  # Obtenir le nom de la ligue et ajouter un match en cours
from Functions.Authenticator import is_logged_in, loginProcess  # Gestion de l'authentification
from Functions.DeleteBet import DeleteBet  # Suppression des paris
from Functions.FisrtGameBet import FirstGameBet  # Placement du premier pari
from Functions.Function_scriptDelRunning import scriptDelRunning  # Suppression des scripts en cours
from Functions.Functions_1XBET import update_match_done  # Mise à jour des matchs terminés
from Functions.GetAndPlaceBet import GetAndPlaceBet  # Obtention et placement des paris
from Functions.GetIfGameStart import GetIfGameEnd, GetIfGameStart  # Vérification du début/fin de jeu
from Functions.GetIfMatchPage import GetIfMatchPage  # Vérification de la page de match
from Functions.GetIfNewSite import GetIfNewSite  # Vérification du nouveau site
from Functions.GetJeuActuel import GetJeuActuel  # Obtention du jeu actuel
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, get1setGlobalPerte  # Gestion des pertes
from Functions.GetPlayersName import GetPlayersName  # Obtention des noms des joueurs
from Functions.GetResult import GetResult  # Obtention du résultat
from Functions.GetScoreActuel import GetScoreActuel  # Obtention du score actuel
from Functions.GetSetActuel import GetSetActuel  # Obtention du set actuel
from Functions.ScriptRechercheDeMatch import rechercheDeMatch  # Recherche de match
from Functions.ValidationDuParis import ValidationDuParis  # Validation du pari
from Functions.VerificationMatchTrouve import newmatchFromUrl  # Vérification du match trouvé
from Functions.retour_section_tps_reglementaire import RetourTpsReg  # Retour à la section temps réglementaire


def all_script(driver):
    """
    Fonction principale qui gère l'ensemble du flux de travail pour la stratégie de martingale 431a.
    
    Cette fonction coordonne toutes les étapes du processus de paris:
    1. Vérification du site et préparation de l'environnement
    2. Recherche d'un match approprié
    3. Collecte des informations sur le match
    4. Placement des paris initiaux
    5. Suivi du match et gestion des paris en fonction des résultats
    6. Application de la stratégie de martingale en cas de perte
    
    Args:
        driver: Instance du WebDriver Selenium utilisée pour l'automatisation du navigateur
        
    Returns:
        bool: True si le script s'est exécuté avec succès, False en cas d'erreur
    """
    # Vérification si le site a changé et adaptation en conséquence
    GetIfNewSite(driver)
    
    # Nettoyage des scripts en cours d'exécution dans le fichier de suivi
    scriptDelRunning()
    
    # Initialisation du dictionnaire de scores
    config.all_scores = {}
    
    # -------- RECHERCHE DE MATCH --------
    # Boucle jusqu'à trouver un match approprié ou rencontrer une erreur
    print('test')
    while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match!', 'error', False, 2)
    print('test2')
    print('error', config.error)
    
    # Marque qu'un match a été trouvé
    config.match_found = True

    # Si un match est trouvé et qu'il n'y a pas d'erreur, collecte les informations sur le match
    if config.match_found and not config.error:
        print('config.script_num', config.script_num)
        print('config.running_file_name', config.running_file_name)
        
        # Ajoute le script en cours d'exécution au fichier de suivi
        AddRunning.main(config.script_num, config.running_file_name)
        
        # Récupère le nom de la ligue et l'URL du match
        config.ligue_name = GetLigueName.fromUrl(driver)[0]
        config.match_Url = GetLigueName.fromUrl(driver)[1]
        
        # Récupère les noms des joueurs
        config.teams = GetPlayersName(driver)
        
        # Vérifie et enregistre le nouveau match
        newmatchFromUrl(driver)
        update_match_done("add", config.newmatch, config.matchlist_file_name)
    
    print('error', config.error)
    # En cas d'erreur, termine l'exécution
    if config.error:
        return False
        
    # -------- RECHERCHE D'INFORMATIONS DE MISE POUR CHAQUE TYPE DE SCRIPT --------
    for scriptType in config.scriptTypeList:
        # Change le type de script actif
        config.switchScript(scriptType)
        config.log(f'RECHERCHE INFOS DE MISE {scriptType.upper()}', 'title', False)
        
        # Récupère les informations de perte pour le premier set si aucune perte n'est définie
        if config.perte == 0:
            get1setGlobalPerte()
            
        # Récupère les informations de perte globale si toujours aucune perte n'est définie
        if config.perte == 0:
            getGlobalPerte()
            
        # Initialise les compteurs de gain et de matchs gagnés pour ce type de script s'ils n'existent pas
        if scriptType not in config.global_match_win:
            config.global_match_win[scriptType] = 0
        if scriptType not in config.winmatch:
            config.winmatch[scriptType] = 0

    # -------- RÉCUPÉRATION DU SCORE ACTUEL --------
    # Obtient le score actuel du match
    GetScoreActuel(driver)
    
    # Vérifie si le set actuel est défini, sinon marque une erreur
    if not config.set_actuel:
        config.error = True
        
    # Initialisation des variables de suivi
    firstjeu = True
    current_game = int(config.jeu_actuel)
    
    # -------- PRÉPARATION ET PLACEMENT DU PREMIER PARI POUR CHAQUE TYPE DE SCRIPT --------
    for scriptType in config.scriptTypeList:
        # Change le type de script actif
        config.switchScript(scriptType)
        # Place le premier pari pour le jeu actuel
        FirstGameBet(driver)

    # -------- RETOUR SUR LA SECTION TEMPS RÉGLEMENTAIRE ET ATTENTE FIN DE JEU --------
    print('FIRST GAME DONE')
    
    # Détermine s'il faut attendre la fin du jeu actuel
    waitendgame = True
    firstjeu = True
    
    # Vérifie pour chaque type de script si un pari a été validé pour le jeu et set actuels
    for scriptType in config.scriptTypeList:
        config.switchScript(scriptType)
        # Si un pari est validé pour le jeu et set actuels, pas besoin d'attendre la fin du jeu
        if config.validated_bet and int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) and int(
                config.set_actuel) == int(
            config.validated_bet.get('set')):
            waitendgame = False
            break

    # Attend la fin du jeu si nécessaire
    if waitendgame:
        GetIfGameEnd(driver)
        
    # Retourne à la section temps réglementaire pour suivre le match
    RetourTpsReg(driver)
    
    # Variable pour suivre le passage à un nouveau set
    passageset = False
    
    # -------- BOUCLE PRINCIPALE DE SUIVI DU MATCH --------
    # -------- BOUCLE PRINCIPALE DE SUIVI DU MATCH --------
    # Continue tant qu'il n'y a pas d'erreur
    while not config.error:
        # Récupère le jeu actuel
        GetJeuActuel(driver)
        
        # -------- GESTION DU PASSAGE À UN NOUVEAU SET --------
        if passageset:
            # Vérifie si l'utilisateur est connecté, sinon reconnexion
            if not is_logged_in(driver):
                print('not logged in ')
                loginProcess(driver)
                
            # Récupère le set actuel
            GetSetActuel(driver)
            config.game_start = True
            
            # -------- STRATÉGIE DE RATTRAPAGE DE PERTE --------
            if config.rattrape_perte == 1:
                # Réinitialise l'état d'erreur
                config.error = False
                
                # Journalisation du passage au set suivant
                txtlog = f"passage set {config.newset}"
                config.newset = int(config.set_actuel) + 1
                print(txtlog)
                config.log(txtlog, config.newmatch)
                
                # Attente avant de continuer
                txtlog = "attente 30 sec"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                # -------- VÉRIFICATION DES PROFITS POUR CHAQUE TYPE DE SCRIPT --------
                for scriptType in config.scriptTypeList:
                    # Vérifie si l'utilisateur est connecté, sinon reconnexion
                    if not is_logged_in(driver):
                        print('not logged in ')
                        loginProcess(driver)
                        
                    # Change le type de script actif
                    config.switchScript(scriptType)
                    
                    # Vérifie si tous les types de script ont atteint leur objectif de profit
                    all_below_one = all(
                        float(config.global_match_win[st]) >= float(config.total_want_win[st]) for st in
                        config.scriptTypeList)
                        
                    # Si tous les objectifs sont atteints, termine le script avec succès
                    if all_below_one:
                        for st in config.scriptTypeList:
                            config.log(
                                f' {st} : Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                                'success', False)
                        return True
                        
                    # Affiche le profit net actuel pour le type de script
                    if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    else:
                        # Si l'objectif est atteint pour ce type de script, affiche et continue
                        config.log(
                            f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                        config.log(f" {scriptType} FIN {config.scriptType}", 'success', False)
                        continue
                        
                    # -------- GESTION DES RÉSULTATS ET PROFITS --------
                    # Obtient le résultat du pari
                    config.result = GetResult(driver)
                    
                    # Si le pari est gagnant
                    if config.result == 'WIN':
                        # Met à jour le profit global et le compteur de matchs gagnés
                        config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                            config.netprofit)
                        config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                        
                        # Réinitialise les configurations et variables
                        config.ScriptConfig(scriptType).reset()
                        config.init_variable()
                        
                        # Supprime le pari
                        DeleteBet(driver)
                        
                        # Si l'objectif n'est pas encore atteint, continue avec de nouveaux paris
                        if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                            print("#RECHERCHE INFOS DE MISE")
                            
                            # Récupère les informations de perte globale
                            getGlobalPerte()
                            config.error = False
                            
                            # Journalisation et redémarrage
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"Restart {config.scriptType}", 'success', False)
                        else:
                            # Si l'objectif est atteint, termine pour ce type de script
                            config.log(
                                f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                            config.log(f"FIN {config.scriptType}", 'success', False)
                            continue
                    else:
                        # Si le pari est perdant, place un nouveau premier pari
                        firstjeu = True
                        FirstGameBet(driver)

            # -------- GESTION DES PERTES ET STRATÉGIE DE MARTINGALE --------
            elif config.perte > 0:
                # Répartit la perte selon la stratégie de martingale
                DispatchPerte()
                
                # Réinitialise les variables
                config.init_variable()
                
                # Journalisation du redémarrage au set 2
                txtlog = "passage set 2 restart"
                print(txtlog)
                config.log(txtlog, config.newmatch)
                
                # Attente avant de continuer
                txtlog = "attente 30 sec"
                print(txtlog)
                
                # Attente supplémentaire si le résultat n'est pas gagnant
                if config.result != 'WIN':
                    time.sleep(30)
                    
                # Place un nouveau premier pari
                FirstGameBet(driver)
                firstjeu = True
            else:
                # En cas d'erreur inattendue, journalise et termine
                current_frame = inspect.currentframe()
                config.log(
                    f'Error in file {inspect.getfile(current_frame)} at line {current_frame.f_lineno} in function {current_frame.f_code.co_name}',
                    'error', True)
                print("erreur perte en 1 set")
                DispatchPerte()
        else:
            if str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                txtlog = " ON EST SUR LE PROCHAIN SET"
                passageset = True
                config.newset = int(config.set_actuel) + 1
                config.log(txtlog, config.newmatch)
                DeleteBet(driver)
                continue
            if firstjeu or int(current_game) != int(config.jeu_actuel):
                print('firstgame')
                time.sleep(2)
                firstjeu = False
                current_game = config.jeu_actuel
            else:
                GetIfGameEnd(driver)
        # JEU FINI ON PREPARE LE IPROCHAIN BET
        txtlog = "JEU FINI ON PREPARE LE PROCHAIN BET"
        config.log(txtlog, config.newmatch)
        passageset = False
        current_game = int(config.jeu_actuel)
        for scriptType in config.scriptTypeList:
            if not is_logged_in(driver):
                print('not logged in ')
                loginProcess(driver)
            config.switchScript(scriptType)
            print('passage prochain script ', scriptType)
            # Check if all script types have global_match_win > 1
            all_below_one = all(
                float(config.global_match_win[st]) >= float(config.total_want_win[st]) for st in
                config.scriptTypeList)
            if all_below_one:
                for st in config.scriptTypeList:
                    config.log(f' {st} Net profit: {config.global_match_win[st]} / {config.total_want_win[st]}',
                               'success', False)
                return True
            if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
            else:
                config.log(
                    f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                config.log(f"FIN {config.scriptType}", 'success', False)
                continue
            if config.jeu_actuel == 13:
                config.log('Tie break en cours attente début')
                while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                    GetScoreActuel(driver)
                    if not GetIfMatchPage(driver):
                        config.error = True
                        break
                config.log('tie break commencé... attente fin')
                GetIfGameEnd(driver)
                passageset = True
                break
            elif config.jeu_actuel == 12:
                GetJeuActuel(driver)
                GetIfGameStart(driver)
                while config.score_actuel != "0:0":
                    print('possible tie break, attente debut ...')
                    GetIfGameEnd(driver)
                    GetScoreActuel(driver)
                GetJeuActuel(driver)
                if config.jeu_actuel == 13:
                    print('Tie break en cours attente début')
                    while config.score_actuel != "0:1" and config.score_actuel != "1:0" and config.score_actuel != "1:1" and config.score_actuel != "2:0" and config.score_actuel != "0:2":
                        GetScoreActuel(driver)
                        if not GetIfMatchPage(driver):
                            config.error = True
                            break
                    print('tie break commencé... attente fin')
                    GetIfGameEnd(driver)
                passageset = True
                break
            else:
                GetAndPlaceBet(driver)
                print(config.global_match_win)
            if config.result == 'RUN':
                print('RUN')
                continue
            GetScoreActuel(driver)
            if config.validated_bet:
                if int(config.jeu_actuel) == int(config.validated_bet.get('jeu')) - 1 and int(config.set_actuel) == int(
                        config.validated_bet.get('set')):
                    print('set du paris supérieur!')
                    continue
            if config.validated_bet.get('result') is None:
                print('result', config.validated_bet.get('result'))
                GetResult(driver)

            if config.validated_bet.get('result') == 'WIN':
                config.global_match_win[scriptType] = float(config.global_match_win[scriptType]) + float(
                    config.netprofit)
                config.winmatch[scriptType] = config.winmatch[scriptType] + 1
                config.ScriptConfig(scriptType).reset()
                config.init_variable()
                DeleteBet(driver)
                if float(config.global_match_win[scriptType]) < float(config.total_want_win[scriptType]):
                    print("#RECHERCHE INFOS DE MISE")
                    getGlobalPerte()
                    config.error = False
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"Restart {config.scriptType}", 'success', False)
                    # VÉRIFCATION DU SET ACTUEL
                    GetScoreActuel(driver)
                    if not config.set_actuel:
                        config.error = True
                    config.log('set ' + str(config.set_actuel) + ' - nex set ' + str(config.newset))
                    if str(int(config.newset) - 1) == str(config.set_actuel):  ## si on est toujours sur le meme set
                        config.log('on est toujours sur le meme set', config.newmatch)
                        ##VALIDATION DU PARIS SI SCORE OK
                        validate_bet = False
                        tentative = 0
                        while not validate_bet and not config.error and tentative < 3:
                            # VÉRIFICATION DU SCORE ACTUEL
                            tentative = tentative + 1
                            print('tentative validation ' + str(tentative))
                            if ValidationDuParis(driver, True):
                                validate_bet = True
                            else:
                                FirstGameBet(driver)
                                validate_bet = True
                                firstjeu = True
                                current_game = int(config.jeu_actuel)
                    current_game = int(config.jeu_actuel)
                else:
                    config.log(
                        f' {scriptType} Net profit: {config.global_match_win[scriptType]} / {config.total_want_win[scriptType]}')
                    config.log(f"FIN {config.scriptType}", 'success', False)
            else:
                # VÉRIFCATION DU SET ACTUEL
                GetScoreActuel(driver)
                if not config.set_actuel:
                    config.error = True
                config.log('set ' + str(config.set_actuel) + ' - nex set ' + str(config.newset))
                if str(int(config.newset) - 1) == str(config.set_actuel):  ## si on est toujours sur le meme set
                    config.log('on est toujours sur le meme set', config.newmatch)
                    ##VALIDATION DU PARIS SI SCORE OK
                    validate_bet = False
                    tentative = 0
                    while not validate_bet and not config.error and tentative < 3:
                        # VÉRIFICATION DU SCORE ACTUEL
                        tentative = tentative + 1
                        print('tentative validation ' + str(tentative))
                        if ValidationDuParis(driver, True):
                            validate_bet = True
                        else:
                            FirstGameBet(driver)
                            validate_bet = True
                            firstjeu = True
                            current_game = int(config.jeu_actuel)
                elif str(config.newset) == str(config.set_actuel):  ##SI ON EST SUR LE PROCHAIN SET
                    txtlog = " ON EST SUR LE PROCHAIN SET"
                    passageset = True
                    config.newset = int(config.set_actuel) + 1
                    for scriptType in config.scriptTypeList:
                        config.switchScript(scriptType)
                        if config.validated_bet.get('montant'):
                            config.perte -= float(config.validated_bet.get('montant'))
                    config.log(txtlog, config.newmatch)
                    print('Revert perte : ', config.perte)
                    DeleteBet(driver)
                    txtlog = 'Wait 30 sec'
                    config.log(txtlog, config.newmatch)
                    break
                else:
                    print("ERROR : ecup set " + str(config.set_actuel))
                    config.error = True
        GetIfMatchPage(driver)
    config.switchScript('4315A')
    print("update : " + config.newmatch)
    for i in config.scriptTypeList:
        config.switchScript(i)
        print('perte', config.perte)
        DispatchPerte()
        config.ScriptConfig(i).reset()
        config.init_variable()
        config.global_match_win[i] = 0  # Initialize win counter for script type
        config.winmatch[i] = 0  # Initialize match counter for script type
    config.all_scores = {}
    Functions_1XBET.update_match_done("del", config.newmatch, config.matchlist_file_name)
    Functions_1XBET.del_running(config.script_num, config.running_file_name)
    DeleteBet(driver)
    return True
