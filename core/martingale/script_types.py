#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classes spécialisées pour chaque type de script de la stratégie 431A
"""

import sys
import os
from abc import ABC, abstractmethod

# Ajout du chemin racine au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from Functions.FisrtGameBet import FirstGameBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetJeuActuel import GetJeuActuel


class BaseScript(ABC):
    """
    Classe de base abstraite pour tous les types de scripts de martingale
    """
    
    def __init__(self, driver, script_type):
        """
        Initialise le script de base
        
        Args:
            driver: Instance du driver web
            script_type: Type de script (ex: '300', '15A', '30A')
        """
        self.driver = driver
        self.script_type = script_type

    @abstractmethod
    def get_script_name(self) -> str:
        """
        Retourne le nom du script pour les logs
        
        Returns:
            str: Nom du script (ex: "Script 300", "Script 15A")
        """
        pass

    @abstractmethod
    def is_valid_score(self, score: str) -> bool:
        """
        Vérifie si le score actuel est valide pour ce type de script
        
        Args:
            score: Score actuel (ex: "0:0", "15:0")
            
        Returns:
            bool: True si le score est valide pour ce script
        """
        pass

    def first_game_bet(self, driver) -> bool:
        """
        Méthode commune pour placer le premier pari, utilisée par tous les scripts
        
        Args:
            driver: Instance du driver web
            
        Returns:
            bool: True si le pari a été placé avec succès
        """
        # Sauvegarde du type de script actuel
        original_script_type = config.scriptType
        
        try:
            # Configuration du type de script
            config.scriptType = self.script_type
            
            # Log de préparation avec le nom spécifique du script
            config.log(f'PREPARATION PREMIER PARIS - {self.get_script_name()}', 'title', False, 0)
            
            # Récupération du jeu actuel
            GetJeuActuel(driver)
            
            # Variables communes à tous les scripts
            bet_40a = False
            tentative = 0
            nextBet = False
            
            while not bet_40a and not config.error and tentative < 3:
                # Vérification des conditions communes
                GetScoreActuel(driver)
                config.looking_game = int(config.jeu_actuel)
                
                # Vérification du score spécifique à chaque script
                if not self.is_valid_score(config.score_actuel):
                    config.log(f'Score : {config.score_actuel} - 1er jeu passé pour {self.get_script_name().lower()}!', 'warning', True)
                    nextBet = True
                    config.looking_game = int(config.jeu_actuel) + 1
                
                if int(config.looking_game) == 0:
                    config.looking_game = 1
                
                # Appel de la fonction FirstGameBet originale
                result = FirstGameBet(driver)
                
                if result:
                    bet_40a = True
                    return bool(True)
                else:
                    tentative += 1
            
            return bool(False)
            
        finally:
            # Restauration du type de script original
            config.scriptType = original_script_type


class Script300(BaseScript):
    """
    Classe spécialisée pour le script de type '300'
    """
    
    def __init__(self, driver, config_manager=None):
        """
        Initialise le script 300
        
        Args:
            driver: Instance du driver web
            config_manager: Gestionnaire de configuration (optionnel)
        """
        super().__init__(driver, '300')
        self.config_manager = config_manager
    
    def get_script_name(self) -> str:
        """
        Retourne le nom du script 300
        
        Returns:
            str: "Script 300"
        """
        return "Script 300"
    
    def is_valid_score(self, score: str) -> bool:
        """
        Vérifie si le score est valide pour le script 300
        
        Args:
            score: Score actuel
            
        Returns:
            bool: True si le score est "0:0"
        """
        return score == "0:0"


class Script15A(BaseScript):
    """
    Classe spécialisée pour le script de type '15A'
    """
    
    def __init__(self, driver, config_manager=None):
        """
        Initialise le script 15A
        
        Args:
            driver: Instance du driver web
            config_manager: Gestionnaire de configuration (optionnel)
        """
        super().__init__(driver, '15A')
        self.config_manager = config_manager
    
    def get_script_name(self) -> str:
        """
        Retourne le nom du script 15A
        
        Returns:
            str: "Script 15A"
        """
        return "Script 15A"
    
    def is_valid_score(self, score: str) -> bool:
        """
        Vérifie si le score est valide pour le script 15A
        
        Args:
            score: Score actuel
            
        Returns:
            bool: True si le score est "0:0"
        """
        return score == "0:0"


class Script30A(BaseScript):
    """
    Classe spécialisée pour le script de type '30A'
    """
    
    def __init__(self, driver, config_manager=None):
        """
        Initialise le script 30A
        
        Args:
            driver: Instance du driver web
            config_manager: Gestionnaire de configuration (optionnel)
        """
        super().__init__(driver, '30A')
        self.config_manager = config_manager
    
    def get_script_name(self) -> str:
        """
        Retourne le nom du script 30A
        
        Returns:
            str: "Script 30A"
        """
        return "Script 30A"
    
    def is_valid_score(self, score: str) -> bool:
        """
        Vérifie si le score est valide pour le script 30A
        
        Args:
            score: Score actuel
            
        Returns:
            bool: True si le score est dans la liste des scores valides
        """
        valid_scores = ["0:0", "0:15", "15:0", "15:15"]
        return score in valid_scores


class ScriptFactory:
    """
    Factory pour créer les instances de scripts appropriées
    """
    
    @staticmethod
    def create_script(script_type, driver, config_manager=None):
        """
        Crée une instance de script selon le type spécifié
        
        Args:
            script_type: Type de script ('300', '15A', '30A')
            driver: Instance du driver web
            config_manager: Gestionnaire de configuration (optionnel)
            
        Returns:
            Instance de la classe de script appropriée
            
        Raises:
            ValueError: Si le type de script n'est pas supporté
        """
        script_classes = {
            '300': Script300,
            '15A': Script15A,
            '30A': Script30A
        }
        
        if script_type in script_classes:
            return script_classes[script_type](driver, config_manager)
        else:
            raise ValueError(f"Type de script non supporté : {script_type}")