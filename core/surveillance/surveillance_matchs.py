#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de surveillance asynchrone des matchs
"""

import asyncio
import time
import json
import sys
import os
import logging
from datetime import datetime

# Ajout du chemin racine au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class SurveillanceMatchs:
    """
    Classe pour la surveillance asynchrone des matchs de tennis
    """
    
    def __init__(self, file_paris=None, config_manager=None, logger=None):
        """
        Initialisation du système de surveillance
        
        Args:
            file_paris: Instance du gestionnaire de file d'attente des paris
            config_manager: Instance du gestionnaire de configuration
            logger: Instance du système de journalisation
        """
        self.file_paris = file_paris
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(__name__)
        self.matchs_surveilles = {}
        self.strategies = []
        self.running = False
        self.intervalle_verification = 5  # secondes
    
    def ajouter_strategie(self, strategie):
        """
        Ajoute une stratégie de martingale à surveiller
        
        Args:
            strategie: Instance d'une classe dérivée de Martingale
        """
        self.strategies.append(strategie)
        self.logger.info(f"Stratégie {strategie.nom_strategie} ajoutée au système de surveillance")
    
    def ajouter_match(self, match_id, match_data):
        """
        Ajoute un match à surveiller
        
        Args:
            match_id: Identifiant unique du match
            match_data: Données du match
        """
        if match_id not in self.matchs_surveilles:
            self.matchs_surveilles[match_id] = match_data
            self.logger.info(f"Match {match_id} ajouté à la surveillance: {match_data.get('home_team')} vs {match_data.get('away_team')}")
    
    def supprimer_match(self, match_id):
        """
        Supprime un match de la surveillance
        
        Args:
            match_id: Identifiant unique du match
        """
        if match_id in self.matchs_surveilles:
            match_data = self.matchs_surveilles.pop(match_id)
            self.logger.info(f"Match {match_id} supprimé de la surveillance: {match_data.get('home_team')} vs {match_data.get('away_team')}")
    
    async def verifier_match(self, match_id, match_data):
        """
        Vérifie un match pour toutes les stratégies
        
        Args:
            match_id: Identifiant unique du match
            match_data: Données du match
        """
        # Mise à jour des données du match (à implémenter avec l'API réelle)
        match_data_updated = await self.obtenir_donnees_match(match_id)
        
        if not match_data_updated:
            self.logger.warning(f"Impossible d'obtenir les données mises à jour pour le match {match_id}")
            return
        
        # Mettre à jour les données dans notre dictionnaire
        self.matchs_surveilles[match_id] = match_data_updated
        
        # Vérifier si le match correspond aux critères d'une stratégie
        for strategie in sorted(self.strategies, key=lambda s: s.priorite, reverse=True):
            if not strategie.en_cours and strategie.verifier_conditions_match(match_data_updated):
                self.logger.info(f"Match {match_id} correspond aux critères de la stratégie {strategie.nom_strategie}")
                
                # Ajouter le pari à la file d'attente
                if self.file_paris:
                    self.file_paris.ajouter_pari(strategie, match_data_updated)
                    self.logger.info(f"Pari ajouté à la file d'attente pour la stratégie {strategie.nom_strategie}")
                else:
                    # Si pas de file d'attente, placer le pari directement
                    success = strategie.placer_pari(match_data_updated)
                    if success:
                        self.logger.info(f"Pari placé directement pour la stratégie {strategie.nom_strategie}")
                    else:
                        self.logger.warning(f"Échec du placement du pari pour la stratégie {strategie.nom_strategie}")
    
    async def obtenir_donnees_match(self, match_id):
        """
        Obtient les données mises à jour d'un match
        
        Args:
            match_id: Identifiant unique du match
            
        Returns:
            dict: Données mises à jour du match
        """
        # Simuler une requête API pour obtenir les données du match
        # À remplacer par l'appel réel à l'API
        await asyncio.sleep(0.5)  # Simuler un délai réseau
        
        # Pour l'exemple, on retourne simplement les données existantes
        # Dans une implémentation réelle, il faudrait faire une requête à l'API
        return self.matchs_surveilles.get(match_id, {})
    
    async def surveiller_matchs(self):
        """
        Boucle principale de surveillance des matchs
        """
        self.logger.info("Démarrage de la surveillance des matchs")
        self.running = True
        
        while self.running:
            try:
                # Créer une copie des clés pour éviter les erreurs de modification pendant l'itération
                match_ids = list(self.matchs_surveilles.keys())
                
                # Créer des tâches pour vérifier chaque match en parallèle
                tasks = [self.verifier_match(match_id, self.matchs_surveilles[match_id]) 
                         for match_id in match_ids]
                
                # Exécuter toutes les tâches en parallèle
                await asyncio.gather(*tasks)
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.intervalle_verification)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance des matchs: {e}")
                await asyncio.sleep(self.intervalle_verification)
    
    def demarrer(self):
        """
        Démarre la surveillance des matchs dans une boucle asyncio
        """
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.surveiller_matchs())
        except KeyboardInterrupt:
            self.arreter()
            self.logger.info("Surveillance des matchs arrêtée par l'utilisateur")
        finally:
            loop.close()
    
    def arreter(self):
        """
        Arrête la surveillance des matchs
        """
        self.running = False
        self.logger.info("Arrêt de la surveillance des matchs")