#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour la classe FileParis
"""

import unittest
import os
import sys
import time
import threading
from unittest.mock import MagicMock, patch

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules à tester
from core.file_paris.file_paris import FileParis
from core.logging.log_manager import LogManager


class TestFileParis(unittest.TestCase):
    """
    Tests pour la classe FileParis
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        # Créer un mock pour le logger
        self.logger = MagicMock(spec=LogManager)
        
        # Créer une instance de FileParis
        self.file_paris = FileParis(self.logger)
    
    def tearDown(self):
        """
        Nettoyage après les tests
        """
        # Arrêter le traitement des paris si actif
        if self.file_paris.is_processing:
            self.file_paris.stop_processing()
            # Attendre que le thread se termine
            time.sleep(0.1)
    
    def test_initialization(self):
        """
        Teste l'initialisation de la classe FileParis
        """
        self.assertFalse(self.file_paris.is_processing)
        self.assertEqual(len(self.file_paris.bet_queue), 0)
    
    def test_add_bet(self):
        """
        Teste l'ajout d'un pari à la file d'attente
        """
        # Créer un pari de test
        bet = {
            "match_id": "123",
            "strategy": "Martingale300",
            "stake": 10.0,
            "odds": 1.5,
            "priority": 1
        }
        
        # Ajouter le pari à la file d'attente
        self.file_paris.add_bet(bet)
        
        # Vérifier que le pari a été ajouté
        self.assertEqual(len(self.file_paris.bet_queue), 1)
        
        # Vérifier que le pari a été ajouté avec la bonne priorité
        self.assertEqual(self.file_paris.bet_queue[0][0], bet["priority"])
        self.assertEqual(self.file_paris.bet_queue[0][1], bet)
    
    def test_add_multiple_bets_with_priority(self):
        """
        Teste l'ajout de plusieurs paris avec différentes priorités
        """
        # Créer des paris de test avec différentes priorités
        bet1 = {
            "match_id": "123",
            "strategy": "Martingale300",
            "stake": 10.0,
            "odds": 1.5,
            "priority": 2  # Priorité plus basse (2 est moins prioritaire que 1)
        }
        
        bet2 = {
            "match_id": "456",
            "strategy": "Martingale15A",
            "stake": 20.0,
            "odds": 1.8,
            "priority": 1  # Priorité plus haute
        }
        
        # Ajouter les paris à la file d'attente
        self.file_paris.add_bet(bet1)
        self.file_paris.add_bet(bet2)
        
        # Vérifier que les paris ont été ajoutés
        self.assertEqual(len(self.file_paris.bet_queue), 2)
        
        # Vérifier que les paris sont ordonnés par priorité
        # Le pari avec la priorité la plus haute (1) devrait être en premier
        self.assertEqual(self.file_paris.bet_queue[0][0], bet2["priority"])
        self.assertEqual(self.file_paris.bet_queue[0][1], bet2)
        
        # Le pari avec la priorité la plus basse (2) devrait être en second
        self.assertEqual(self.file_paris.bet_queue[1][0], bet1["priority"])
        self.assertEqual(self.file_paris.bet_queue[1][1], bet1)
    
    def test_start_and_stop_processing(self):
        """
        Teste le démarrage et l'arrêt du traitement des paris
        """
        # Vérifier que le traitement n'est pas actif au départ
        self.assertFalse(self.file_paris.is_processing)
        
        # Démarrer le traitement
        self.file_paris.start_processing()
        
        # Vérifier que le traitement est actif
        self.assertTrue(self.file_paris.is_processing)
        
        # Arrêter le traitement
        self.file_paris.stop_processing()
        
        # Attendre que le thread se termine
        time.sleep(0.1)
        
        # Vérifier que le traitement est arrêté
        self.assertFalse(self.file_paris.is_processing)
    
    def test_process_bets(self):
        """
        Teste le traitement des paris
        """
        # Créer un mock pour la fonction place_bet
        mock_place_bet = MagicMock(return_value=True)
        
        # Créer des paris de test
        bet1 = {
            "match_id": "123",
            "strategy": "Martingale300",
            "stake": 10.0,
            "odds": 1.5,
            "priority": 1,
            "place_bet": mock_place_bet
        }
        
        bet2 = {
            "match_id": "456",
            "strategy": "Martingale15A",
            "stake": 20.0,
            "odds": 1.8,
            "priority": 2,
            "place_bet": mock_place_bet
        }
        
        # Ajouter les paris à la file d'attente
        self.file_paris.add_bet(bet1)
        self.file_paris.add_bet(bet2)
        
        # Remplacer la méthode _process_bets par une version qui s'exécute une seule fois
        original_process_bets = self.file_paris._process_bets
        
        def process_bets_once():
            # Traiter tous les paris une seule fois
            while self.file_paris.bet_queue:
                _, bet = self.file_paris.bet_queue.pop(0)
                bet["place_bet"]()
        
        self.file_paris._process_bets = process_bets_once
        
        # Démarrer le traitement
        self.file_paris.start_processing()
        
        # Attendre que le traitement se termine
        time.sleep(0.1)
        
        # Vérifier que les deux paris ont été traités
        self.assertEqual(mock_place_bet.call_count, 2)
        
        # Restaurer la méthode originale
        self.file_paris._process_bets = original_process_bets
    
    def test_get_status(self):
        """
        Teste l'obtention du statut de la file d'attente
        """
        # Vérifier le statut initial
        status = self.file_paris.get_status()
        self.assertEqual(status["is_processing"], False)
        self.assertEqual(status["queue_length"], 0)
        self.assertEqual(status["processed_bets"], 0)
        
        # Ajouter des paris à la file d'attente
        bet1 = {
            "match_id": "123",
            "strategy": "Martingale300",
            "stake": 10.0,
            "odds": 1.5,
            "priority": 1
        }
        
        bet2 = {
            "match_id": "456",
            "strategy": "Martingale15A",
            "stake": 20.0,
            "odds": 1.8,
            "priority": 2
        }
        
        self.file_paris.add_bet(bet1)
        self.file_paris.add_bet(bet2)
        
        # Vérifier le statut après l'ajout des paris
        status = self.file_paris.get_status()
        self.assertEqual(status["is_processing"], False)
        self.assertEqual(status["queue_length"], 2)
        self.assertEqual(status["processed_bets"], 0)
        
        # Incrémenter manuellement le compteur de paris traités
        self.file_paris.processed_bets = 1
        
        # Vérifier le statut après le traitement d'un pari
        status = self.file_paris.get_status()
        self.assertEqual(status["processed_bets"], 1)


if __name__ == '__main__':
    unittest.main()