#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de la boucle principale de martingale refactorisée.

Remplace Functions/Functions_15V1.py et Functions/Functions_431a.py
en utilisant la nouvelle architecture BaseScript / ScriptFactory.

NE MODIFIE AUCUN FICHIER EXISTANT.

Utilisation depuis un script de lancement :

    from core.martingale.all_script_v2 import all_script_v2

    config.scriptTypeList = ['15A', '30A', '300']
    for i in config.scriptTypeList:
        config.ScriptConfig(i)
    config.winmatch       = {st: 0   for st in config.scriptTypeList}
    config.global_match_win = {st: 0.0 for st in config.scriptTypeList}

    while config.win < 100:
        all_script_v2(driver)
"""

import sys
import os
import time

# Ajout du chemin racine au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from core.martingale.script_types import ScriptFactory, BaseScript

# Imports des fonctions existantes (inchangées)
from Functions import GetLigueName
from Functions.DeleteBet import DeleteBet
from Functions.FisrtGameBet import FirstGameBet
from Functions.GetAndPlaceBet import GetAndPlaceBet
from Functions.GetIfGameStart import GetIfGameEnd, GetIfGameStart
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetIfNewSite import GetIfNewSite
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, get1setGlobalPerte
from Functions.GetPlayersName import GetPlayersName
from Functions.GetResult import GetResult
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.Managers.MatchManager import match_manager
from Functions.Managers.ScriptManager import script_manager
from Functions.ScriptRechercheDeMatch import rechercheDeMatch
from Functions.ValidationDuParis import ValidationDuParis
from Functions.VerificationMatchTrouve import newmatchFromUrl
from Functions.retour_section_tps_reglementaire import RetourTpsReg

# Scores de tie-break (set)
_SCORES_TIE_BREAK_DEBUT = {"0:1", "1:0", "1:1", "2:0", "0:2"}


# ---------------------------------------------------------------------------
# Fonctions utilitaires internes
# ---------------------------------------------------------------------------

def _tous_objectifs_atteints(scripts: list[BaseScript]) -> bool:
    """
    Vérifie si tous les scripts ont atteint leur objectif de gain.

    Args:
        scripts (list[BaseScript]): Liste des scripts actifs

    Returns:
        bool: True si tous les objectifs sont atteints
    """
    return all(s.a_atteint_objectif() for s in scripts)


def _log_tous_objectifs(scripts: list[BaseScript]) -> None:
    """Affiche la progression de tous les scripts dans les logs."""
    for s in scripts:
        config.log(
            f' {s.script_type} Net profit: '
            f'{config.global_match_win.get(s.script_type, 0)} / '
            f'{config.total_want_win.get(s.script_type, 0)}',
            'success', False
        )


def _initialiser_mises(scripts: list[BaseScript]) -> None:
    """
    Récupère les données de mise pour chaque script depuis l'API/Redis.
    Équivalent du bloc RECHERCHE INFOS DE MISE dans all_script() original.

    Args:
        scripts (list[BaseScript]): Liste des scripts à initialiser
    """
    for script in scripts:
        script.activer()
        config.log(f'RECHERCHE INFOS DE MISE {script.script_type.upper()}', 'title', False)
        config.ScriptConfig(script.script_type).reset()
        config.init_variable()

        # Tentative Redis (rapide) puis fallback API
        if config.perte == 0:
            try:
                from Functions import RedisIPC
                val = RedisIPC.get_loss(script.script_type, default=0.0)
                if float(val) > 0:
                    config.perte = float(val)
                    config.log(f'Perte chargée depuis Redis : {config.perte}', 'info', False)
                else:
                    getGlobalPerte()
            except Exception:
                getGlobalPerte()

        if config.perte == 0:
            get1setGlobalPerte()

        config.log_clear_line()
        script.desactiver()


def _placer_premier_pari_tous(scripts: list[BaseScript], driver) -> bool:
    """
    Place le premier pari pour chaque script qui n'a pas encore atteint
    son objectif. Équivalent de la boucle allfirstgamebet.

    Args:
        scripts (list[BaseScript]): Liste des scripts
        driver: Instance du driver Selenium

    Returns:
        bool: True si tous les premiers paris sont placés ou objectifs atteints
    """
    tous_prets = False
    while not tous_prets:
        tous_prets = True
        for script in scripts:
            script.activer()

            if _tous_objectifs_atteints(scripts):
                _log_tous_objectifs(scripts)
                script.desactiver()
                return True

            if script.a_atteint_objectif():
                script.log_progression()
                config.log(f'FIN {script.script_type}', 'success', False)
                script.desactiver()
                continue

            script.log_progression()
            if not script.preparer_premier_pari():
                # Premier pari non placé — recommencer la boucle
                tous_prets = False

            script.desactiver()

    return True


def _gerer_tie_break(driver) -> None:
    """
    Attend la fin d'un tie-break avant de continuer.

    Args:
        driver: Instance du driver Selenium
    """
    config.log('Tie break détecté — attente du début', 'info')
    while config.score_actuel not in _SCORES_TIE_BREAK_DEBUT:
        GetScoreActuel(driver)
        if not GetIfMatchPage(driver):
            config.error = True
            return
    config.log('Tie break commencé — attente de la fin', 'info')
    GetIfGameEnd(driver)


def _boucle_principale(scripts: list[BaseScript], driver) -> bool:
    """
    Boucle de jeu principale — s'exécute tant que le match est en cours
    et qu'il n'y a pas d'erreur.

    Remplace le ``while not config.error:`` de all_script() original.

    Args:
        scripts (list[BaseScript]): Liste des scripts actifs
        driver: Instance du driver Selenium

    Returns:
        bool: True si le match s'est terminé normalement
    """
    passageset = False
    firstjeu = True
    current_game = int(config.jeu_actuel)

    while not config.error:
        GetJeuActuel(driver)

        # --- Gestion du changement de set ---
        if passageset:
            GetSetActuel(driver)
            config.game_start = True
            passageset = False

            if config.perte > 0:
                # Dispatch des pertes et re-préparation des premiers paris
                for script in scripts:
                    script.activer()
                    config.ScriptConfig(script.script_type).reset()
                    DispatchPerte()
                    config.init_variable()
                    config.log('Passage set 2 — restart', config.newmatch)
                    script.desactiver()

                if not _placer_premier_pari_tous(scripts, driver):
                    config.error = True
                    break
                firstjeu = True
            else:
                config.log('Erreur perte en 1 set', 'error', True)
                DispatchPerte()

            continue

        # --- Vérification nouveau set ---
        if str(config.newset) == str(config.jeu_actuel):
            config.newset = int(config.jeu_actuel) + 1
            config.log('Nouveau set détecté', config.newmatch)
            DeleteBet(driver)
            continue

        # --- Attente du premier jeu ---
        if firstjeu or int(current_game) != int(config.jeu_actuel):
            time.sleep(2)
            firstjeu = False
            current_game = config.jeu_actuel
            continue

        # --- Boucle sur chaque script pour le jeu courant ---
        passageset = False
        current_game = int(config.jeu_actuel)

        for script in scripts:
            script.activer()

            # Condition de fin globale
            if _tous_objectifs_atteints(scripts):
                _log_tous_objectifs(scripts)
                script.desactiver()
                return True

            if script.a_atteint_objectif():
                script.log_progression()
                config.log(f'FIN {script.script_type}', 'success', False)
                script.desactiver()
                continue

            # --- Gestion tie-break (jeu 13 = tie-break) ---
            if config.jeu_actuel == 13:
                _gerer_tie_break(driver)
                passageset = False
                script.desactiver()
                break

            # --- Jeu 12 : possible tie-break au prochain jeu ---
            if config.jeu_actuel == 12:
                GetJeuActuel(driver)
                GetIfGameStart(driver)
                while config.score_actuel != "0:0":
                    config.log('Possible tie-break — attente début', 'info')
                    GetIfGameEnd(driver)
                    GetScoreActuel(driver)
                GetJeuActuel(driver)
                if config.jeu_actuel == 13:
                    _gerer_tie_break(driver)
                passageset = False
                script.desactiver()
                break

            # --- Placement du pari ---
            GetAndPlaceBet(driver)

            if config.result == 'RUN':
                script.desactiver()
                continue

            # --- Récupération du résultat si non disponible ---
            GetScoreActuel(driver)
            if not config.validated_bet or config.validated_bet.get('result') is None:
                GetResult(driver)

            resultat = config.validated_bet.get('result') if config.validated_bet else None

            # --- Traitement WIN ---
            if resultat == 'WIN':
                script.gerer_resultat('WIN')

                # Vérifier si on est encore sur le même jeu pour re-parier immédiatement
                if (
                    str(int(config.looking_game)) == str(config.jeu_actuel)
                    and config.score_actuel != "0:0"
                    and not script.a_atteint_objectif()
                ):
                    config.log('Même jeu — re-validation immédiate', config.newmatch)
                    ValidationDuParis(driver, True)
                else:
                    config.ScriptConfig(script.script_type).reset()
                    FirstGameBet(driver)
                    firstjeu = True

                current_game = int(config.jeu_actuel)

            # --- Traitement LOSE ---
            elif resultat == 'LOSE':
                GetScoreActuel(driver)
                if not config.set_actuel:
                    config.error = True

                if (
                    str(int(config.looking_game)) == str(config.jeu_actuel)
                    and config.score_actuel != "0:0"
                ):
                    # Même jeu — tentative de validation du pari suivant
                    config.log('LOSE — même jeu, re-validation', config.newmatch)
                    validated = False
                    for _ in range(2):
                        if ValidationDuParis(driver, True):
                            validated = True
                            break
                    if not validated:
                        FirstGameBet(driver)
                        firstjeu = True
                else:
                    # Jeu suivant — dispatch perte et recommencer
                    script.gerer_resultat('LOSE')
                    FirstGameBet(driver)
                    firstjeu = True

            script.desactiver()

        # --- Vérification page de match ---
        if not GetIfMatchPage(driver):
            config.error = True
            break

    return True


def _nettoyer_fin_match(scripts: list[BaseScript], driver) -> None:
    """
    Dispatch les pertes résiduelles et remet à zéro les compteurs de tous
    les scripts en fin de match.

    Args:
        scripts (list[BaseScript]): Liste des scripts actifs
        driver: Instance du driver Selenium
    """
    for script in scripts:
        script.activer()
        config.log(f'Nettoyage fin de match : {script.script_type}', 'info', False)
        DispatchPerte()
        config.ScriptConfig(script.script_type).reset()
        config.init_variable()
        config.global_match_win[script.script_type] = 0.0
        config.winmatch[script.script_type] = 0
        script.desactiver()

    config.all_scores = {}
    match_manager.remove_match(config.newmatch)
    script_manager.stop_script(config.scriptType, config.script_num)
    DeleteBet(driver)


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def all_script_v2(driver) -> bool:
    """
    Boucle principale de la martingale refactorisée.

    Remplace all_script() de Functions_15V1.py et Functions_431a.py.
    Prend en charge plusieurs types de scripts simultanément via
    config.scriptTypeList (ex: ['15A', '30A', '300']).

    Args:
        driver: Instance du driver Selenium

    Returns:
        bool: True si le match s'est terminé normalement, False en cas d'erreur
    """
    GetIfNewSite(driver)
    script_manager.stop_script(config.scriptType, config.script_num)
    config.all_scores = {}

    # ------------------------------------------------------------------
    # Étape 1 — Recherche de match
    # ------------------------------------------------------------------
    while not rechercheDeMatch(driver) and not config.error:
        config.log('Erreur lors de la recherche de match — nouvelle tentative', 'error', False, 2)

    if config.error:
        config.log('Erreur après recherche de match — arrêt', 'error')
        return False

    # ------------------------------------------------------------------
    # Étape 2 — Initialisation du contexte match
    # ------------------------------------------------------------------
    config.match_found = True
    script_manager.start_script(config.scriptType, config.script_num)

    ligue_info = GetLigueName.fromUrl(driver)
    config.ligue_name = ligue_info[0]
    config.match_Url = ligue_info[1]
    config.teams = GetPlayersName(driver)
    newmatchFromUrl(driver)
    match_manager.add_match(config.newmatch)

    config.log("-" * 60, 'success', False, False, False)
    config.log(f'MATCH OK : {config.teams} | {config.ligue_name}', 'success', False, 0, False)
    config.log("-" * 60, 'success', False, False, False)

    # ------------------------------------------------------------------
    # Étape 3 — Création des instances de scripts
    # ------------------------------------------------------------------
    scripts = ScriptFactory.create_scripts(config.scriptTypeList, driver)

    # ------------------------------------------------------------------
    # Étape 4 — Chargement des mises depuis l'API / Redis
    # ------------------------------------------------------------------
    _initialiser_mises(scripts)

    GetScoreActuel(driver)
    if not config.set_actuel:
        config.error = True
        return False

    # ------------------------------------------------------------------
    # Étape 5 — Placement des premiers paris
    # ------------------------------------------------------------------
    if _tous_objectifs_atteints(scripts):
        _log_tous_objectifs(scripts)
        _nettoyer_fin_match(scripts, driver)
        return True

    if not _placer_premier_pari_tous(scripts, driver):
        config.error = True
        return False

    # ------------------------------------------------------------------
    # Étape 6 — Boucle principale de jeu
    # ------------------------------------------------------------------
    _boucle_principale(scripts, driver)

    # ------------------------------------------------------------------
    # Étape 7 — Nettoyage fin de match
    # ------------------------------------------------------------------
    _nettoyer_fin_match(scripts, driver)

    return not config.error
