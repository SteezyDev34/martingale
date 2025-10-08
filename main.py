#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application principale pour le système de paris Martingale
"""

import os
import sys
import argparse

# Importer les modules nécessaires
from core.config.config_manager import ConfigManager
from core.logging.log_manager import LogManager
from core.martingale.martingale_300 import Martingale300
from core.martingale.martingale_15a import Martingale15A
from core.martingale.martingale_30a import Martingale30A
from core.surveillance.surveillance_matchs import SurveillanceMatchs
from core.file_paris.file_paris import FileParis
from core.notification.notification_manager import NotificationManager
from core.interface.interface_utilisateur import InterfaceUtilisateur


def main():
    """
    Fonction principale pour démarrer l'application
    """
    # Analyser les arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Système de paris Martingale")
    parser.add_argument("--console", action="store_true", help="Exécuter en mode console (sans interface graphique)")
    parser.add_argument("--config", type=str, default="config.json", help="Chemin vers le fichier de configuration")
    args = parser.parse_args()

    # Initialiser le gestionnaire de configuration
    config_manager = ConfigManager(args.config)
    
    # Initialiser le gestionnaire de journalisation
    log_manager = LogManager(config_manager)
    logger = log_manager.get_logger()
    
    logger.info("Démarrage du système de paris Martingale")
    
    # Initialiser le gestionnaire de notifications
    notification_manager = NotificationManager(config_manager, logger)
    
    # Initialiser la file d'attente des paris
    file_paris = FileParis(logger)
    
    # Initialiser les stratégies Martingale
    strategies = [
        Martingale300(config_manager),
        Martingale15A(config_manager),
        Martingale30A(config_manager)
    ]
    
    # Initialiser le système de surveillance des matchs
    surveillance = SurveillanceMatchs(config_manager, logger, file_paris)
    
    # Ajouter les stratégies au système de surveillance
    for strategy in strategies:
        if strategy.etat_jeu["active"]:
            surveillance.ajouter_strategie(strategy)
            logger.info(f"Stratégie {strategy.nom_strategie} activée")
    
    # Démarrer la file d'attente des paris
    file_paris.demarrer()
    logger.info("File d'attente des paris démarrée")
    
    # Démarrer l'application en mode console ou avec interface graphique
    if args.console:
        try:
            # Démarrer la surveillance des matchs
            surveillance.demarrer()
            logger.info("Surveillance des matchs démarrée en mode console")
            
            # Attendre que l'utilisateur arrête le programme
            print("Appuyez sur Ctrl+C pour arrêter le programme")
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("Arrêt du programme demandé par l'utilisateur")
        finally:
            # Arrêter la surveillance des matchs
            surveillance.arreter()
            logger.info("Surveillance des matchs arrêtée")
            
            # Arrêter la file d'attente des paris
            file_paris.arreter()
            logger.info("File d'attente des paris arrêtée")
    else:
        # Démarrer l'interface graphique
        interface = InterfaceUtilisateur(config_manager, logger, surveillance, file_paris, notification_manager)
        logger.info("Interface graphique démarrée")
        interface.run()


if __name__ == "__main__":
    main()