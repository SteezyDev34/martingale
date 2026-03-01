#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire centralisé de configuration
"""

import os
import sys
import json
import platform
from pathlib import Path

class ConfigManager:
    """
    Classe pour centraliser la gestion de la configuration
    """
    
    def __init__(self, config_file=None):
        """
        Initialisation du gestionnaire de configuration
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        # Détection du système d'exploitation
        self.os_type = platform.system()
        
        # Initialisation des chemins
        self.project_path = self._get_project_path()
        
        # Fichier de configuration
        self.config_file = config_file or os.path.join(self.project_path, "config.json")
        
        # Configuration par défaut
        self.config = {
            "site_type": "1xbet",
            "urls": {
                "1xbet": {
                    "base": "https://1xbet.com",
                    "login": "https://1xbet.com/login",
                    "tennis": "https://1xbet.com/live/tennis"
                }
            },
            "strategies": {},
            "display": {
                "show_browser": True,
                "debug_mode": False
            },
            "logging": {
                "level": "INFO",
                "file_rotation": True,
                "max_file_size": 10485760,  # 10 Mo
                "backup_count": 5
            }
        }
        
        # Charger la configuration
        self.charger_configuration()
    
    def _get_project_path(self):
        """
        Détermine le chemin du projet
        
        Returns:
            str: Chemin absolu du projet
        """
        # Obtenir le chemin du script en cours d'exécution
        script_path = os.path.abspath(sys.argv[0])
        
        # Si c'est un fichier .py, prendre son répertoire parent
        if script_path.endswith('.py'):
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Sinon, utiliser le répertoire de travail actuel
        return os.getcwd()
    
    def charger_configuration(self):
        """
        Charge la configuration depuis le fichier
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Mettre à jour la configuration avec les valeurs chargées
                    self._update_dict(self.config, loaded_config)
                    print(f"Configuration chargée depuis {self.config_file}")
            else:
                # Créer le fichier de configuration avec les valeurs par défaut
                self.sauvegarder_configuration()
                print(f"Fichier de configuration créé à {self.config_file}")
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
    
    def _update_dict(self, target, source):
        """
        Met à jour un dictionnaire de manière récursive
        
        Args:
            target: Dictionnaire cible
            source: Dictionnaire source
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def sauvegarder_configuration(self):
        """
        Sauvegarde la configuration dans le fichier
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                print(f"Configuration sauvegardée dans {self.config_file}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def get_strategy_config(self, strategy_name):
        """
        Récupère la configuration d'une stratégie
        
        Args:
            strategy_name: Nom de la stratégie
            
        Returns:
            dict: Configuration de la stratégie
        """
        return self.config.get("strategies", {}).get(strategy_name, {})
    
    def set_strategy_config(self, strategy_name, config):
        """
        Définit la configuration d'une stratégie
        
        Args:
            strategy_name: Nom de la stratégie
            config: Configuration de la stratégie
        """
        if "strategies" not in self.config:
            self.config["strategies"] = {}
        
        self.config["strategies"][strategy_name] = config
        self.sauvegarder_configuration()
    
    def get_site_url(self, url_type="base"):
        """
        Récupère l'URL du site selon le type
        
        Args:
            url_type: Type d'URL (base, login, tennis, etc.)
            
        Returns:
            str: URL du site
        """
        site_type = self.config.get("site_type", "1xbet")
        return self.config.get("urls", {}).get(site_type, {}).get(url_type, "")
    
    def set_site_type(self, site_type):
        """
        Définit le type de site
        
        Args:
            site_type: Type de site (1xbet, etc.)
        """
        self.config["site_type"] = site_type
        self.sauvegarder_configuration()
    
    def get_display_config(self, key=None):
        """
        Récupère la configuration d'affichage
        
        Args:
            key: Clé spécifique (optionnel)
            
        Returns:
            dict ou valeur: Configuration d'affichage
        """
        if key:
            return self.config.get("display", {}).get(key)
        return self.config.get("display", {})
    
    def set_display_config(self, key, value):
        """
        Définit une valeur de configuration d'affichage
        
        Args:
            key: Clé de configuration
            value: Valeur à définir
        """
        if "display" not in self.config:
            self.config["display"] = {}
        
        self.config["display"][key] = value
        self.sauvegarder_configuration()
    
    def get_logging_config(self):
        """
        Récupère la configuration de journalisation
        
        Returns:
            dict: Configuration de journalisation
        """
        return self.config.get("logging", {})
    
    def set_logging_config(self, config):
        """
        Définit la configuration de journalisation
        
        Args:
            config: Configuration de journalisation
        """
        self.config["logging"] = config
        self.sauvegarder_configuration()