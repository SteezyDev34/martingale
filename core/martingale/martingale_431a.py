#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stratégie de martingale 431A
"""

import sys
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .base import Martingale


class Martingale431A(Martingale):
    """
    Stratégie de martingale 431A
    """
    
    def __init__(self, config_manager=None):
        """
        Initialisation de la stratégie 431A
        
        Args:
            config_manager: Instance du gestionnaire de configuration
        """
        super().__init__(config_manager, script_type="431A")
        self.nom_strategie = "431A"
        self.priorite = 1
        
    def get_script_type(self):
        """
        Retourne le type de script pour cette stratégie
        
        Returns:
            str: Type de script '431A'
        """
        return "431A"
    
    def synchroniser_avec_config(self):
        """
        Synchronise les attributs de la classe avec le module config global
        """
        try:
            import config as global_config
            
            # Synchroniser depuis config global vers les attributs de la classe
            self.etat_jeu["cote"] = float(getattr(global_config, 'cote', self.etat_jeu["cote"]))
            self.etat_jeu["wantwin"] = float(getattr(global_config, 'wantwin', self.etat_jeu["wantwin"]))
            self.etat_jeu["perte"] = float(getattr(global_config, 'perte', self.etat_jeu["perte"]))
            self.etat_jeu["rattrape_perte"] = bool(getattr(global_config, 'rattrape_perte', self.etat_jeu["rattrape_perte"]))
            self.etat_jeu["script_type"] = str(getattr(global_config, 'scriptType', self.etat_jeu["script_type"]))
            self.etat_jeu["tipster"] = str(getattr(global_config, 'tipster', self.etat_jeu["tipster"]))
            self.etat_jeu["site_type"] = str(getattr(global_config, 'site_type', self.etat_jeu["site_type"]))
            self.etat_jeu["classes"] = getattr(global_config, 'classes', self.etat_jeu["classes"])
            
            # Synchroniser depuis les attributs de la classe vers config global
            global_config.cote = self.etat_jeu["cote"]
            global_config.wantwin = self.etat_jeu["wantwin"]
            global_config.perte = self.etat_jeu["perte"]
            global_config.rattrape_perte = self.etat_jeu["rattrape_perte"]
            global_config.scriptType = self.etat_jeu["script_type"]
            global_config.tipster = self.etat_jeu["tipster"]
            global_config.site_type = self.etat_jeu["site_type"]
            global_config.classes = self.etat_jeu["classes"]
            
        except ImportError:
            # Le module config global n'est pas disponible
            pass
    
    def obtenir_mise(self, driver, log_callback):
        """
        Obtient la mise en utilisant la méthode get_mise de la classe de base
        
        Args:
            driver: Instance du driver Selenium
            log_callback: Fonction de callback pour les logs
            
        Returns:
            float: Montant de la mise calculée
        """
        # Synchroniser avec le module config global avant d'appeler get_mise
        self.synchroniser_avec_config()
        
        # Appeler la méthode get_mise de la classe de base
        return self.get_mise(driver, log_callback)