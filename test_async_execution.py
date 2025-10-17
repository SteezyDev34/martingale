#!/usr/bin/env python3
"""
Script de test pour vérifier l'exécution asynchrone de GetScoreActuel
avec le script principal 4315A-1
"""

import asyncio
import sys
import os

# Ajouter le répertoire du projet au path
project_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_directory)

import config
from Functions.GetScoreActuelAsync import start_score_monitoring, stop_score_monitoring


# Fonction: Test simple de la surveillance asynchrone
# Commentaire: Teste la surveillance des scores sans le script complet
async def test_score_monitoring_only():
    """
    Test simple de la surveillance asynchrone des scores
    """
    print("=== Test de surveillance asynchrone des scores ===")
    
    try:
        # Importer le module SetDriver pour initialiser le driver
        import ChromeDriver.SetDriver as SetDriver
        driver = SetDriver.driver
        config.site_type = 'old_site'  # ou votre type de site
        
        print("Démarrage de la surveillance des scores...")
        task, stop_event = await start_score_monitoring(driver)
        
        # Laisser la surveillance tourner pendant 10 secondes
        print("Surveillance en cours pendant 10 secondes...")
        await asyncio.sleep(10)
        
        print("Arrêt de la surveillance...")
        await stop_score_monitoring(task, stop_event)
        
        print("Test terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test : {e}")
        return False


# Fonction: Test de simulation d'exécution parallèle
# Commentaire: Simule l'exécution du script principal avec surveillance
async def test_parallel_execution():
    """
    Test de simulation d'exécution parallèle
    """
    print("=== Test d'exécution parallèle simulée ===")
    
    try:
        # Importer le module SetDriver pour initialiser le driver
        import ChromeDriver.SetDriver as SetDriver
        driver = SetDriver.driver
        config.site_type = 'old_site'
        
        # Démarrer la surveillance
        print("Démarrage de la surveillance des scores...")
        task, stop_event = await start_score_monitoring(driver)
        
        # Simuler le travail du script principal
        print("Simulation du script principal...")
        for i in range(5):
            print(f"Étape {i+1}/5 du script principal")
            await asyncio.sleep(2)  # Simuler du travail
            
            # Vérifier si des scores ont été mis à jour
            if hasattr(config, 'score_actuel') and config.score_actuel:
                print(f"Score actuel détecté : {config.score_actuel}")
        
        # Arrêter la surveillance
        print("Arrêt de la surveillance...")
        await stop_score_monitoring(task, stop_event)
        
        print("Test d'exécution parallèle terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test parallèle : {e}")
        return False


# Fonction: Menu de test interactif
# Commentaire: Permet de choisir quel test exécuter
async def main_test():
    """
    Menu principal pour les tests
    """
    print("=== Tests d'exécution asynchrone ===")
    print("1. Test surveillance seule")
    print("2. Test exécution parallèle simulée")
    print("3. Exécuter tous les tests")
    
    choice = input("Choisissez un test (1-3) : ").strip()
    
    if choice == "1":
        await test_score_monitoring_only()
    elif choice == "2":
        await test_parallel_execution()
    elif choice == "3":
        print("Exécution de tous les tests...\n")
        result1 = await test_score_monitoring_only()
        print("\n" + "="*50 + "\n")
        result2 = await test_parallel_execution()
        
        if result1 and result2:
            print("\n✅ Tous les tests ont réussi !")
        else:
            print("\n❌ Certains tests ont échoué.")
    else:
        print("Choix invalide.")


if __name__ == "__main__":
    try:
        # Initialiser les variables de config nécessaires
        if not hasattr(config, 'all_scores'):
            config.all_scores = {}
        if not hasattr(config, 'saved_score'):
            config.saved_score = None
        if not hasattr(config, 'score_actuel'):
            config.score_actuel = False
        if not hasattr(config, 'classes'):
            # Configuration par défaut pour les tests
            config.classes = {
                'score_container': {
                    'old_site': 'score-class-default'
                }
            }
        
        asyncio.run(main_test())
        
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur.")
    except Exception as e:
        print(f"Erreur lors de l'exécution des tests : {e}")