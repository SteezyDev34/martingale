#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classes spécialisées pour chaque type de script de la stratégie 431A.

Utilisation dans all_script() :

    scripts = ScriptFactory.create_scripts(config.scriptTypeList, driver)
    for script in scripts:
        script.activer()                   # switchScript équivalent
        if script.a_atteint_objectif():
            continue
        script.preparer_premier_pari()     # FirstGameBet équivalent
        ...
        resultat = GetResult(driver)
        script.gerer_resultat(resultat)
        script.desactiver()
"""

import sys
import os
import json
from abc import ABC, abstractmethod
from contextlib import contextmanager

# Ajout du chemin racine au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from Functions.FisrtGameBet import FirstGameBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, get1setGlobalPerte
from Functions import RedisIPC


class BaseScript(ABC):
    """
    Classe de base abstraite pour tous les types de scripts de martingale.

    Chaque instance porte son propre état (perte, mise, gain_cumulé) et
    expose les méthodes nécessaires à la boucle de all_script().

    Pattern d'utilisation dans all_script() :

        scripts = ScriptFactory.create_scripts(config.scriptTypeList, driver)
        for script in scripts:
            with script.contexte_actif():
                if script.a_atteint_objectif():
                    continue
                script.preparer_premier_pari()
    """

    def __init__(self, driver, script_type: str) -> None:
        """
        Initialise le script de base.

        Args:
            driver: Instance du driver Selenium
            script_type (str): Type de script (ex: '300', '15A', '30A')
        """
        self.driver = driver
        self.script_type = script_type
        # Gain cumulé sur le match en cours pour ce script
        self.gain_match: float = 0.0
        # Nombre de paris gagnés sur le match pour ce script
        self.nb_victoires: int = 0

    # ------------------------------------------------------------------
    # Méthodes abstraites — à implémenter dans chaque sous-classe
    # ------------------------------------------------------------------

    @abstractmethod
    def get_script_name(self) -> str:
        """
        Retourne le nom lisible du script pour les logs.

        Returns:
            str: Nom du script (ex: "Script 300", "Script 15A")
        """
        pass

    @abstractmethod
    def is_valid_score(self, score: str) -> bool:
        """
        Vérifie si le score actuel est valide pour déclencher ce script.

        Args:
            score (str): Score actuel (ex: "0:0", "15:0")

        Returns:
            bool: True si le score autorise le déclenchement
        """
        pass

    # ------------------------------------------------------------------
    # Gestion du contexte actif (remplace config.switchScript)
    # ------------------------------------------------------------------

    @contextmanager
    def contexte_actif(self):
        """
        Gestionnaire de contexte qui active ce script le temps du bloc,
        puis restaure le script précédent. Remplace config.switchScript().

        Utilisation :
            with script.contexte_actif():
                # config.scriptType == self.script_type ici
                ...
        """
        config.switchScript(self.script_type)
        try:
            yield self
        finally:
            # Pas de restauration forcée : c'est all_script() qui orchestre
            pass

    # Champs de config sauvegardés/restaurés dans Redis pour ce script
    _CHAMPS_CONFIG: tuple[tuple[str, type], ...] = (
        ("mise",           float),
        ("perte",          float),
        ("wantwin",        float),
        ("increment",      float),
        ("gain",           float),
        ("netprofit",      float),
        ("cote",           float),
        ("rattrape_perte", int),
        ("looking_game",   int),
        ("placed_game",    int),
        ("saved_score",    str),
        ("win_type",       str),
        ("result",         str),
        ("error",          bool),
        ("validated_bet",  dict),
    )

    def activer(self) -> None:
        """
        Active ce script en chargeant son état depuis Redis champ par champ.

        Utilise get_data(champ, script_type) pour chaque variable de config.
        Fallback : config.switchScript() classique si Redis est indisponible.

        Remplace le pattern config.switchScript(scriptType) dans all_script().
        """
        # Tenter une lecture Redis sur le premier champ pour détecter la disponibilité
        test = RedisIPC.get_data("mise", self.script_type, default=None)
        if test is None and not RedisIPC.get_redis_client():
            # Redis indisponible — fallback classique
            config.switchScript(self.script_type)
            return

        # Chargement champ par champ
        for champ, cast in self._CHAMPS_CONFIG:
            valeur = RedisIPC.get_data(champ, self.script_type, default=None)
            if valeur is None:
                continue  # Champ absent → on garde la valeur actuelle de config
            try:
                if cast is bool:
                    setattr(config, champ, str(valeur).lower() == "true")
                elif cast is dict:
                    setattr(config, champ, valeur if isinstance(valeur, dict) else {})
                else:
                    setattr(config, champ, cast(valeur))
            except (ValueError, TypeError):
                pass  # Valeur invalide — on garde la valeur actuelle

        config.scriptType = self.script_type

    def desactiver(self) -> None:
        """
        Sauvegarde l'état courant de ce script dans Redis en un seul pipeline.

        Un seul aller-retour réseau pour les 15 champs + PERTE_<SCRIPT>.
        Fallback : config.save_variables() classique si Redis est indisponible.

        Remplace le pattern config.save_variables() dans all_script().
        """
        client = RedisIPC.get_redis_client()
        if client is None:
            # Redis indisponible — fallback classique
            config.save_variables()
            return

        key = f"ETAT_{self.script_type.upper()}"
        key_perte = f"PERTE_{self.script_type.upper()}"

        # Construction du mapping en une passe
        mapping: dict = {}
        for champ, _ in self._CHAMPS_CONFIG:
            valeur = getattr(config, champ, None)
            if valeur is None:
                continue
            if isinstance(valeur, (dict, list)):
                mapping[champ] = json.dumps(valeur)
            else:
                mapping[champ] = str(valeur)

        # Un seul aller-retour réseau
        try:
            pipe = client.pipeline(transaction=False)
            if mapping:
                pipe.hset(key, mapping=mapping)
            # Rétrocompatibilité : PERTE_<SCRIPT> mis à jour en même temps
            pipe.set(key_perte, str(config.perte))
            pipe.execute()
        except Exception:
            # Fallback si le pipeline échoue
            config.save_variables()

    # ------------------------------------------------------------------
    # Condition d'arrêt — vérification de l'objectif atteint
    # ------------------------------------------------------------------

    def a_atteint_objectif(self) -> bool:
        """
        Indique si ce script a atteint son objectif de gain sur le match.

        Returns:
            bool: True si global_match_win >= total_want_win pour ce script
        """
        return float(config.global_match_win.get(self.script_type, 0)) >= float(
            config.total_want_win.get(self.script_type, 0)
        )

    def tous_objectifs_atteints(self, script_list: list) -> bool:
        """
        Vérifie si TOUS les scripts de la liste ont atteint leur objectif.
        Correspond au bloc all_below_one répété dans all_script().

        Args:
            script_list (list[BaseScript]): Liste des scripts à vérifier

        Returns:
            bool: True si tous les scripts ont atteint leur objectif
        """
        return all(s.a_atteint_objectif() for s in script_list)

    def log_progression(self) -> None:
        """Affiche la progression du script dans les logs."""
        config.log(
            f' {self.script_type} Net profit: '
            f'{config.global_match_win.get(self.script_type, 0)} / '
            f'{config.total_want_win.get(self.script_type, 0)}'
        )

    # ------------------------------------------------------------------
    # Premier pari — remplace le bloc FirstGameBet dans la boucle
    # ------------------------------------------------------------------

    def preparer_premier_pari(self) -> bool:
        """
        Prépare et place le premier pari du jeu pour ce script.
        Remplace le bloc FirstGameBet() appelé dans la boucle all_script().

        Returns:
            bool: True si le premier pari a été placé avec succès
        """
        config.log(f'PREPARATION PREMIER PARIS - {self.get_script_name()}', 'title', False, 0)
        GetJeuActuel(self.driver)

        bet_place = False
        tentative = 0

        while not bet_place and not config.error and tentative < 3:
            GetScoreActuel(self.driver)
            config.looking_game = int(config.jeu_actuel)

            if not self.is_valid_score(config.score_actuel):
                config.log(
                    f'Score : {config.score_actuel} — 1er jeu passé pour {self.get_script_name()}',
                    'warning', True
                )
                config.looking_game = int(config.jeu_actuel) + 1

            if int(config.looking_game) == 0:
                config.looking_game = 1

            if FirstGameBet(self.driver):
                bet_place = True
            else:
                tentative += 1

        return bet_place

    # ------------------------------------------------------------------
    # Gestion des résultats WIN / LOSE
    # ------------------------------------------------------------------

    def gerer_resultat(self, resultat: str) -> None:
        """
        Traite le résultat d'un pari (WIN ou LOSE) pour ce script.
        Centralise la logique dispersée dans all_script() après GetResult().

        Args:
            resultat (str): 'WIN' ou 'LOSE'
        """
        if resultat == 'WIN':
            self._traiter_victoire()
        else:
            self._traiter_defaite()

    def _traiter_victoire(self) -> None:
        """
        Met à jour les compteurs après une victoire et recharge la configuration
        si l'objectif du match n'est pas encore atteint.
        """
        config.global_match_win[self.script_type] = (
            float(config.global_match_win.get(self.script_type, 0)) + float(config.netprofit)
        )
        config.winmatch[self.script_type] = config.winmatch.get(self.script_type, 0) + 1
        config.init_variable()

        if not self.a_atteint_objectif():
            config.log(f'Rechargement de la mise pour {self.script_type}', 'info', False)
            config.perte = 0
            config.wantwin = 0.2
            getGlobalPerte()
            if config.perte == 0:
                get1setGlobalPerte()
            config.error = False
        else:
            config.ScriptConfig(self.script_type).reset()
            config.log(f'FIN {self.script_type}', 'success', False)

        self.log_progression()

    def _traiter_defaite(self) -> None:
        """
        Dispatch la perte et réinitialise le script pour la prochaine série.
        """
        config.ScriptConfig(self.script_type).reset()
        DispatchPerte()
        config.init_variable()
        config.log(f'LOSE — perte dispatchée pour {self.script_type}', 'warning', False)


class Script300(BaseScript):
    """Stratégie 300 — pari sur le score 0:0 en début de jeu."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '300')

    def get_script_name(self) -> str:
        return "Script 300"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script015(BaseScript):
    """Stratégie 015 — symétrique de 300."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '015')

    def get_script_name(self) -> str:
        return "Script 015"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script150(BaseScript):
    """Stratégie 150."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '150')

    def get_script_name(self) -> str:
        return "Script 150"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script15A(BaseScript):
    """Stratégie 15A — pari 15-15 après le premier point."""

    # Scores déclencheurs : le premier point vient de se jouer
    _SCORES_DECLENCHEURS = {"0:15", "15:0"}

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '15A')

    def get_script_name(self) -> str:
        return "Script 15A"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script30A(BaseScript):
    """Stratégie 30A — pari après le score 15:0 ou 0:15."""

    _SCORES_VALIDES = {"0:0", "0:15", "15:0", "15:15"}

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '30A')

    def get_script_name(self) -> str:
        return "Script 30A"

    def is_valid_score(self, score: str) -> bool:
        return score in self._SCORES_VALIDES


class Script40A(BaseScript):
    """Stratégie 40A — pari après 30:0 ou 0:30."""

    _SCORES_VALIDES = {"0:0", "0:15", "15:0", "15:15", "30:0", "0:30", "30:15", "15:30"}

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '40A')

    def get_script_name(self) -> str:
        return "Script 40A"

    def is_valid_score(self, score: str) -> bool:
        return score in self._SCORES_VALIDES


class Script15V1(BaseScript):
    """Stratégie 15V1 — pari 15-15 en V1."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '15V1')

    def get_script_name(self) -> str:
        return "Script 15V1"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script15V2(BaseScript):
    """Stratégie 15V2 — pari 15-15 en V2."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '15V2')

    def get_script_name(self) -> str:
        return "Script 15V2"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class Script1SET(BaseScript):
    """Stratégie 1SET — issue du premier set."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, '1SET')

    def get_script_name(self) -> str:
        return "Script 1SET"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class ScriptBREAK(BaseScript):
    """Stratégie BREAK — pari sur un break de service."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, 'BREAK')

    def get_script_name(self) -> str:
        return "Script BREAK"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"


class ScriptFactory:
    """
    Factory pour créer les instances de scripts.

    Supporte tous les types définis dans config.allScriptType.
    """

    # Registre complet des types de scripts disponibles
    _CLASSES: dict = {
        '300':   Script300,
        '015':   Script015,
        '150':   Script150,
        '15A':   Script15A,
        '30A':   Script30A,
        '40A':   Script40A,
        '15V1':  Script15V1,
        '15V2':  Script15V2,
        '1SET':  Script1SET,
        'BREAK': ScriptBREAK,
    }

    @classmethod
    def create_script(cls, script_type: str, driver, config_manager=None) -> BaseScript:
        """
        Crée une instance de script selon le type spécifié.

        Args:
            script_type (str): Type de script (ex: '300', '15A', '30A')
            driver: Instance du driver Selenium
            config_manager: Gestionnaire de configuration (optionnel)

        Returns:
            BaseScript: Instance concrète du script

        Raises:
            ValueError: Si le type de script n'est pas enregistré
        """
        if script_type not in cls._CLASSES:
            types_supportes = ', '.join(cls._CLASSES.keys())
            raise ValueError(
                f"Type de script non supporté : '{script_type}'. "
                f"Types disponibles : {types_supportes}"
            )
        return cls._CLASSES[script_type](driver, config_manager)

    @classmethod
    def create_scripts(
        cls, script_type_list: list[str], driver, config_manager=None
    ) -> list[BaseScript]:
        """
        Crée la liste d'instances correspondant à config.scriptTypeList.
        C'est le point d'entrée principal pour remplacer la boucle
        ``for scriptType in config.scriptTypeList`` de all_script().

        Exemple dans all_script() :

            scripts = ScriptFactory.create_scripts(config.scriptTypeList, driver)

            # Remplace : for scriptType in config.scriptTypeList:
            for script in scripts:
                script.activer()

                if script.tous_objectifs_atteints(scripts):
                    return True
                if script.a_atteint_objectif():
                    script.log_progression()
                    continue

                script.preparer_premier_pari()
                # ... GetAndPlaceBet, GetResult ...
                script.gerer_resultat(config.result)

                script.desactiver()

        Args:
            script_type_list (list[str]): Liste des types (ex: ['15V1', '30A'])
            driver: Instance du driver Selenium
            config_manager: Gestionnaire de configuration (optionnel)

        Returns:
            list[BaseScript]: Liste d'instances prêtes à l'emploi
        """
        return [cls.create_script(st, driver, config_manager) for st in script_type_list]

    @classmethod
    def types_supportes(cls) -> list[str]:
        """
        Retourne la liste des types de scripts disponibles.

        Returns:
            list[str]: Types supportés
        """
        return list(cls._CLASSES.keys())