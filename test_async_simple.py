#!/usr/bin/env python3
"""
Test simple de la logique asynchrone sans driver
"""

import asyncio
import sys
import os

# Ajouter le répertoire du projet au path
project_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_directory)

import config


# Fonction: Simulation de surveillance asynchrone
# Commentaire: Simule la surveillance sans utiliser de driver réel
async def simulate_score_monitoring(duration=10):
    """
    Simule la surveillance des scores de manière asynchrone
    """
    print(f"Démarrage de la surveillance simulée pour {duration} secondes...")
    
    for i in range(duration):
        # Simuler la détection d'un score
        simulated_score = f"Score simulé {i+1}"
        config.score_actuel = simulated_score
        print(f"Score détecté : {simulated_score}")
        
        await asyncio.sleep(1)  # Attendre 1 seconde
    
    print("Surveillance simulée terminée.")


# Fonction: Simulation du script principal
# Commentaire: Simule l'exécution du script principal
async def simulate_main_script(duration=8):
    """
    Simule l'exécution du script principal
    """
    print(f"Démarrage du script principal simulé pour {duration} secondes...")
    
    for i in range(duration):
        print(f"Étape {i+1}/{duration} du script principal")
        
        # Vérifier si un score a été détecté
        if hasattr(config, 'score_actuel') and config.score_actuel:
            print(f"  → Score reçu de la surveillance : {config.score_actuel}")
        
        await asyncio.sleep(1)  # Attendre 1 seconde
    
    print("Script principal simulé terminé.")


# Fonction: Test d'exécution parallèle
# Commentaire: Lance les deux tâches en parallèle
async def test_parallel_execution():
    """
    Test d'exécution parallèle des deux fonctions
    """
    print("=== Test d'exécution parallèle ===")
    
    # Initialiser les variables de config
    config.score_actuel = None
    
    # Créer les tâches asynchrones
    task_monitoring = asyncio.create_task(simulate_score_monitoring(10))
    task_main = asyncio.create_task(simulate_main_script(8))
    
    # Attendre que les deux tâches se terminent
    await asyncio.gather(task_monitoring, task_main)
    
    print("✅ Test d'exécution parallèle terminé avec succès !")


# Fonction: Test de démarrage/arrêt de tâche
# Commentaire: Teste la capacité d'arrêter une tâche en cours
async def test_task_control():
    """
    Test du contrôle des tâches (démarrage/arrêt)
    """
    print("=== Test de contrôle des tâches ===")
    
    # Créer un événement d'arrêt
    stop_event = asyncio.Event()
    
    async def controlled_monitoring():
        """Surveillance avec contrôle d'arrêt"""
        count = 0
        while not stop_event.is_set():
            count += 1
            config.score_actuel = f"Score contrôlé {count}"
            print(f"Surveillance contrôlée : {config.score_actuel}")
            
            try:
                await asyncio.wait_for(asyncio.sleep(1), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # Continue la boucle
    
    # Démarrer la surveillance
    task = asyncio.create_task(controlled_monitoring())
    
    # Laisser tourner pendant 5 secondes
    await asyncio.sleep(5)
    
    # Arrêter la surveillance
    print("Arrêt de la surveillance...")
    stop_event.set()
    
    # Attendre que la tâche se termine
    await task
    
    print("✅ Test de contrôle des tâches terminé avec succès !")


async def main():
    """
    Menu principal des tests
    """
    print("=== Tests de logique asynchrone ===")
    print("1. Test d'exécution parallèle")
    print("2. Test de contrôle des tâches")
    print("3. Exécuter tous les tests")
    
    choice = input("Choisissez un test (1-3) : ").strip()
    
    if choice == "1":
        await test_parallel_execution()
    elif choice == "2":
        await test_task_control()
    elif choice == "3":
        print("Exécution de tous les tests...\n")
        await test_parallel_execution()
        print("\n" + "="*50 + "\n")
        await test_task_control()
        print("\n✅ Tous les tests terminés !")
    else:
        print("Choix invalide.")


if __name__ == "__main__":
    try:
        # Initialiser les variables de config nécessaires
        if not hasattr(config, 'score_actuel'):
            config.score_actuel = None
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur.")
    except Exception as e:
        print(f"Erreur lors de l'exécution des tests : {e}")