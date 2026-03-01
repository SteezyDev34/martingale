#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de journalisation amélioré
"""

import os
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    """
    Formateur de logs avec couleurs pour la console
    """
    COLORS = {
        'DEBUG': '\033[94m',  # Bleu
        'INFO': '\033[92m',   # Vert
        'WARNING': '\033[93m', # Jaune
        'ERROR': '\033[91m',  # Rouge
        'CRITICAL': '\033[91m\033[1m', # Rouge gras
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        level_name = record.levelname
        if level_name in self.COLORS:
            log_message = f"{self.COLORS[level_name]}{log_message}{self.COLORS['RESET']}"
        return log_message

class LogManager:
    """
    Gestionnaire de journalisation amélioré
    """
    
    def __init__(self, config_manager=None):
        """
        Initialisation du gestionnaire de journalisation
        
        Args:
            config_manager: Instance du gestionnaire de configuration
        """
        self.config_manager = config_manager
        self.loggers = {}
        
        # Configuration par défaut
        self.log_level = logging.INFO
        self.log_dir = os.path.join(self._get_project_path(), "Logs")
        self.file_rotation = True
        self.max_file_size = 10 * 1024 * 1024  # 10 Mo
        self.backup_count = 5
        
        # Charger la configuration
        self._load_config()
        
        # Créer le répertoire de logs s'il n'existe pas
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _get_project_path(self):
        """
        Détermine le chemin du projet
        
        Returns:
            str: Chemin absolu du projet
        """
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def _load_config(self):
        """
        Charge la configuration de journalisation
        """
        if self.config_manager:
            log_config = self.config_manager.get_logging_config()
            
            # Niveau de log
            level_str = log_config.get("level", "INFO")
            self.log_level = getattr(logging, level_str, logging.INFO)
            
            # Rotation des fichiers
            self.file_rotation = log_config.get("file_rotation", True)
            self.max_file_size = log_config.get("max_file_size", 10485760)
            self.backup_count = log_config.get("backup_count", 5)
    
    def get_logger(self, name):
        """
        Obtient un logger configuré
        
        Args:
            name: Nom du logger
            
        Returns:
            logging.Logger: Logger configuré
        """
        if name in self.loggers:
            return self.loggers[name]
        
        # Créer un nouveau logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Supprimer les handlers existants
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Ajouter un handler pour la console avec couleurs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Ajouter un handler pour le fichier
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{name}_{today}.log")
        
        if self.file_rotation:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Stocker le logger configuré
        self.loggers[name] = logger
        
        return logger
    
    def set_level(self, level):
        """
        Définit le niveau de journalisation
        
        Args:
            level: Niveau de journalisation (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_value = getattr(logging, level, None)
        if level_value:
            self.log_level = level_value
            
            # Mettre à jour tous les loggers existants
            for logger in self.loggers.values():
                logger.setLevel(level_value)
                for handler in logger.handlers:
                    handler.setLevel(level_value)
            
            # Mettre à jour la configuration
            if self.config_manager:
                log_config = self.config_manager.get_logging_config()
                log_config["level"] = level
                self.config_manager.set_logging_config(log_config)
    
    def save_log(self, message, level="INFO", logger_name="default"):
        """
        Enregistre un message dans les logs
        
        Args:
            message: Message à enregistrer
            level: Niveau de journalisation
            logger_name: Nom du logger
        """
        logger = self.get_logger(logger_name)
        
        level_method = getattr(logger, level.lower(), None)
        if level_method:
            level_method(message)
        else:
            logger.info(message)