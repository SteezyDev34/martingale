#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de file d'attente pour les paris séquentiels
"""

import time
import threading
import logging
from queue import PriorityQueue

class FileParis:
    """
    Classe pour gérer une file d'attente de paris avec priorité
    """
    
    def __init__(self, logger=None):
        """
        Initialisation de la file d'attente des paris
        
        Args:
            logger: Instance du système de journalisation
        """
        self.logger = logger or logging.getLogger(__name__)
        self.file = PriorityQueue()
        self.lock = threading.Lock()
        self.thread = None
        self.running = False
        self.pari_en_cours = None
    
    def ajouter_pari(self, strategie, match_data):
        """
        Ajoute un pari à la file d'attente
        
        Args:
            strategie: Instance d'une stratégie de martingale
            match_data: Données du match
        """
        # La priorité est inversée (plus petit = plus prioritaire)
        priorite = -strategie.priorite
        
        with self.lock:
            # Vérifier si un pari similaire est déjà dans la file
            for _, (s, m) in list(self.file.queue):
                if s.nom_strategie == strategie.nom_strategie and m.get("match_id") == match_data.get("match_id"):
                    self.logger.info(f"Pari déjà dans la file pour {strategie.nom_strategie} sur le match {match_data.get('match_id')}")
                    return
            
            # Ajouter le pari à la file
            self.file.put((priorite, (strategie, match_data)))
            self.logger.info(f"Pari ajouté à la file: {strategie.nom_strategie} (priorité: {-priorite}) - Match: {match_data.get('home_team')} vs {match_data.get('away_team')}")
    
    def traiter_paris(self):
        """
        Traite les paris dans la file d'attente de manière séquentielle
        """
        self.logger.info("Démarrage du traitement des paris")
        self.running = True
        
        while self.running:
            try:
                # Attendre qu'un pari soit disponible
                if self.file.empty():
                    time.sleep(1)
                    continue
                
                # Récupérer le pari le plus prioritaire
                with self.lock:
                    _, (strategie, match_data) = self.file.get(block=False)
                    self.pari_en_cours = (strategie, match_data)
                
                # Placer le pari
                self.logger.info(f"Traitement du pari: {strategie.nom_strategie} - Match: {match_data.get('home_team')} vs {match_data.get('away_team')}")
                mise = strategie.calculer_prochaine_mise()
                success = strategie.placer_pari(match_data, mise)
                
                if success:
                    self.logger.info(f"Pari placé avec succès: {strategie.nom_strategie}")
                else:
                    self.logger.warning(f"Échec du placement du pari: {strategie.nom_strategie}")
                
                # Marquer le pari comme traité
                with self.lock:
                    self.pari_en_cours = None
                    self.file.task_done()
                
                # Attendre un peu avant de traiter le prochain pari
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement des paris: {e}")
                time.sleep(1)
    
    def demarrer(self):
        """
        Démarre le traitement des paris dans un thread séparé
        """
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.traiter_paris)
            self.thread.daemon = True
            self.thread.start()
            self.logger.info("Thread de traitement des paris démarré")
    
    def arreter(self):
        """
        Arrête le traitement des paris
        """
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            self.logger.info("Thread de traitement des paris arrêté")
    
    def obtenir_statut(self):
        """
        Obtient le statut actuel de la file d'attente
        
        Returns:
            dict: Statut de la file d'attente
        """
        with self.lock:
            taille_file = self.file.qsize()
            pari_en_cours = None
            
            if self.pari_en_cours:
                strategie, match_data = self.pari_en_cours
                pari_en_cours = {
                    "strategie": strategie.nom_strategie,
                    "match": f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
                    "mise": strategie.etat_jeu["mise"]
                }
            
            return {
                "taille_file": taille_file,
                "pari_en_cours": pari_en_cours,
                "running": self.running
            }