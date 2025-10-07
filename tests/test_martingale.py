#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour les classes Martingale
"""

import unittest
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules à tester
from core.martingale.base import Martingale
from core.martingale.martingale_300 import Martingale300
from core.martingale.martingale_15a import Martingale15A
from core.martingale.martingale_30a import Martingale30A
from core.config.config_manager import ConfigManager


class TestMartingaleBase(unittest.TestCase):
    """
    Tests pour la classe de base Martingale
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        # Créer un mock pour le ConfigManager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_strategy_config.return_value = {
            "initial_stake": 10.0,
            "multiplier": 2.0,
            "min_odds": 1.2,
            "max_odds": 2.0,
            "min_probability": 70.0,
            "enabled": True
        }
        
        # Créer un mock pour le logger
        self.logger = MagicMock()
        
        # Créer une instance de la classe de test qui hérite de Martingale
        class TestMartingale(Martingale):
            def calculer_prochaine_mise(self):
                return 10.0
                
            def verifier_conditions_match(self, match_data):
                return True
                
            def placer_pari(self, match_data, stake):
                return True
        
        self.martingale = TestMartingale(self.config_manager)
    
    def test_initialization(self):
        """
        Teste l'initialisation de la classe Martingale
        """
        self.assertEqual(self.martingale.nom_strategie, "TestStrategy")
        self.assertEqual(self.martingale.etat_jeu["mise_initiale"], 10.0)
        self.assertEqual(self.martingale.etat_jeu["multiplicateur"], 2.0)
        self.assertEqual(self.martingale.etat_jeu["cote_mini"], 1.2)
        self.assertEqual(self.martingale.etat_jeu["cote_maxi"], 2.0)
        self.assertEqual(self.martingale.etat_jeu["proba_mini"], 70.0)
        self.assertTrue(self.martingale.etat_jeu["active"])
    
    def test_reset_state(self):
        """
        Teste la réinitialisation de l'état
        """
        # Modifier l'état
        self.martingale.etat_jeu["mise"] = 20.0
        self.martingale.etat_jeu["pertes_consecutives"] = 2
        self.martingale.etat_jeu["profit_total"] = -30.0
        
        # Réinitialiser l'état
        self.martingale.reinitialiser_etat()
        
        # Vérifier que l'état a été réinitialisé
        self.assertEqual(self.martingale.etat_jeu["mise"], self.martingale.etat_jeu["mise_initiale"])
        self.assertEqual(self.martingale.etat_jeu["pertes_consecutives"], 0)
        self.assertEqual(self.martingale.etat_jeu["profit_total"], 0.0)
    
    def test_record_win(self):
        """
        Teste l'enregistrement d'un gain
        """
        # Configurer l'état initial
        self.martingale.current_stake = 20.0
        self.martingale.consecutive_losses = 2
        self.martingale.total_profit = -30.0
        
        # Enregistrer un gain
        odds = 1.5
        profit = self.martingale.current_stake * (odds - 1)
        self.martingale.record_win(profit)
        
        # Vérifier que l'état a été mis à jour correctement
        self.assertEqual(self.martingale.current_stake, self.martingale.initial_stake)
        self.assertEqual(self.martingale.consecutive_losses, 0)
        self.assertEqual(self.martingale.total_profit, -30.0 + profit)
    
    def test_record_loss(self):
        """
        Teste l'enregistrement d'une perte
        """
        # Configurer l'état initial
        self.martingale.current_stake = 10.0
        self.martingale.consecutive_losses = 0
        self.martingale.total_profit = 0.0
        
        # Enregistrer une perte
        loss = self.martingale.current_stake
        self.martingale.record_loss(loss)
        
        # Vérifier que l'état a été mis à jour correctement
        self.assertEqual(self.martingale.consecutive_losses, 1)
        self.assertEqual(self.martingale.total_profit, -loss)
        
        # La mise suivante devrait être calculée par calculate_next_bet
        self.assertEqual(self.martingale.current_stake, 10.0)  # Valeur de retour du mock
    
    def test_save_and_load_state(self):
        """
        Teste la sauvegarde et le chargement de l'état
        """
        # Configurer l'état
        self.martingale.current_stake = 20.0
        self.martingale.consecutive_losses = 2
        self.martingale.total_profit = -30.0
        
        # Créer un fichier temporaire pour les tests
        temp_file = "temp_state.json"
        
        try:
            # Sauvegarder l'état
            self.martingale.save_state(temp_file)
            
            # Réinitialiser l'état
            self.martingale.reset_state()
            
            # Charger l'état
            self.martingale.load_state(temp_file)
            
            # Vérifier que l'état a été chargé correctement
            self.assertEqual(self.martingale.current_stake, 20.0)
            self.assertEqual(self.martingale.consecutive_losses, 2)
            self.assertEqual(self.martingale.total_profit, -30.0)
            
        finally:
            # Supprimer le fichier temporaire
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestMartingale300(unittest.TestCase):
    """
    Tests pour la classe Martingale300
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        # Créer un mock pour le ConfigManager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_strategy_config.return_value = {
            "initial_stake": 10.0,
            "multiplier": 2.0,
            "min_odds": 1.2,
            "max_odds": 2.0,
            "min_probability": 70.0,
            "enabled": True
        }
        
        # Créer un mock pour le logger
        self.logger = MagicMock()
        
        # Créer une instance de Martingale300
        self.martingale = Martingale300(self.config_manager, self.logger)
    
    def test_calculate_next_bet(self):
        """
        Teste le calcul de la mise suivante
        """
        # Configurer l'état initial
        self.martingale.current_stake = 10.0
        self.martingale.consecutive_losses = 0
        
        # Calculer la mise suivante (première perte)
        next_bet = self.martingale.calculate_next_bet()
        self.assertEqual(next_bet, 10.0 * 2.0)  # 10.0 * multiplier (2.0)
        
        # Configurer pour une deuxième perte
        self.martingale.current_stake = 20.0
        self.martingale.consecutive_losses = 1
        
        # Calculer la mise suivante (deuxième perte)
        next_bet = self.martingale.calculate_next_bet()
        self.assertEqual(next_bet, 20.0 * 2.0)  # 20.0 * multiplier (2.0)
    
    def test_check_match_conditions(self):
        """
        Teste la vérification des conditions du match
        """
        # Créer des données de match valides
        valid_match = {
            "sport": "tennis",
            "status": "live",
            "score": "30-0",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions sont remplies
        self.assertTrue(self.martingale.check_match_conditions(valid_match))
        
        # Créer des données de match invalides (mauvais score)
        invalid_score_match = {
            "sport": "tennis",
            "status": "live",
            "score": "15-0",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_score_match))
        
        # Créer des données de match invalides (probabilité trop faible)
        invalid_probability_match = {
            "sport": "tennis",
            "status": "live",
            "score": "30-0",
            "probability": 65.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_probability_match))
        
        # Créer des données de match invalides (pas de tennis)
        invalid_sport_match = {
            "sport": "football",
            "status": "live",
            "score": "30-0",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_sport_match))
        
        # Créer des données de match invalides (pas en direct)
        invalid_status_match = {
            "sport": "tennis",
            "status": "upcoming",
            "score": "30-0",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_status_match))


class TestMartingale15A(unittest.TestCase):
    """
    Tests pour la classe Martingale15A
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        # Créer un mock pour le ConfigManager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_strategy_config.return_value = {
            "initial_stake": 10.0,
            "multiplier": 2.0,
            "min_odds": 1.2,
            "max_odds": 2.0,
            "min_probability": 70.0,
            "enabled": True
        }
        
        # Créer un mock pour le logger
        self.logger = MagicMock()
        
        # Créer une instance de Martingale15A
        self.martingale = Martingale15A(self.config_manager, self.logger)
    
    def test_check_match_conditions(self):
        """
        Teste la vérification des conditions du match
        """
        # Créer des données de match valides
        valid_match = {
            "sport": "tennis",
            "status": "live",
            "score": "15-40",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions sont remplies
        self.assertTrue(self.martingale.check_match_conditions(valid_match))
        
        # Créer des données de match invalides (mauvais score)
        invalid_score_match = {
            "sport": "tennis",
            "status": "live",
            "score": "30-40",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_score_match))


class TestMartingale30A(unittest.TestCase):
    """
    Tests pour la classe Martingale30A
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests
        """
        # Créer un mock pour le ConfigManager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_strategy_config.return_value = {
            "initial_stake": 10.0,
            "multiplier": 2.0,
            "min_odds": 1.2,
            "max_odds": 2.0,
            "min_probability": 70.0,
            "enabled": True
        }
        
        # Créer un mock pour le logger
        self.logger = MagicMock()
        
        # Créer une instance de Martingale30A
        self.martingale = Martingale30A(self.config_manager, self.logger)
    
    def test_check_match_conditions(self):
        """
        Teste la vérification des conditions du match
        """
        # Créer des données de match valides
        valid_match = {
            "sport": "tennis",
            "status": "live",
            "score": "30-40",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions sont remplies
        self.assertTrue(self.martingale.check_match_conditions(valid_match))
        
        # Créer des données de match invalides (mauvais score)
        invalid_score_match = {
            "sport": "tennis",
            "status": "live",
            "score": "15-40",
            "probability": 75.0,
            "odds": 1.5
        }
        
        # Vérifier que les conditions ne sont pas remplies
        self.assertFalse(self.martingale.check_match_conditions(invalid_score_match))


if __name__ == '__main__':
    unittest.main()