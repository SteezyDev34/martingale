#!/usr/bin/env python3
"""
Exemple d'intégration de GetScoreActuelAsync avec le script principal
Ce fichier montre comment utiliser la surveillance asynchrone des scores
"""

import asyncio
import sys
import os

# Ajouter le répertoire du projet au path
project_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_directory)

import config
from Functions.GetScoreActuelAsync import start_score_monitoring, stop_score_monitoring


# Fonction: Exemple d'intégration complète
# Commentaire: Montre comment intégrer la surveillance asynchrone dans un script principal
async def exemple_integration_complete():
    """
    Exemple complet d'intégration de la surveillance asynchrone
    """
    print("=== Exemple d'intégration complète ===")
    
    try:
        # 1. Initialiser le driver (remplacez par votre méthode d'initialisation)
        print("1. Initialisation du driver...")
        try:
            import ChromeDriver.SetDriver1 as SetDriver
            driver = SetDriver.driver
            print("   ✅ Driver initialisé avec succès")
        except Exception as e:
            print(f"   ❌ Erreur d'initialisation du driver : {e}")
            print("   ℹ️  Utilisation d'un driver simulé pour la démonstration")
            driver = None  # Driver simulé
        
        # 2. Configurer les paramètres
        config.site_type = 'new_site'  # ou votre type de site
        
        # 3. Démarrer la surveillance asynchrone
        print("2. Démarrage de la surveillance asynchrone des scores...")
        if driver:
            task, stop_event = await start_score_monitoring(driver)
            print("   ✅ Surveillance démarrée")
        else:
            print("   ⚠️  Surveillance simulée (pas de driver réel)")
            task, stop_event = None, None
        
        # 4. Exécuter le script principal
        print("3. Exécution du script principal...")
        await executer_script_principal()
        
        # 5. Arrêter la surveillance
        print("4. Arrêt de la surveillance...")
        if task and stop_event:
            await stop_score_monitoring(task, stop_event)
            print("   ✅ Surveillance arrêtée")
        else:
            print("   ℹ️  Pas de surveillance à arrêter")
        
        print("✅ Intégration complète terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration : {e}")


# Fonction: Script principal simulé
# Commentaire: Simule l'exécution du script principal avec surveillance des scores
async def executer_script_principal():
    """
    Simule l'exécution du script principal
    """
    print("   Début du script principal...")
    
    # Simuler différentes étapes du script
    etapes = [
        "Chargement de la page",
        "Recherche des éléments",
        "Analyse des données",
        "Traitement des résultats",
        "Finalisation"
    ]
    
    for i, etape in enumerate(etapes, 1):
        print(f"   Étape {i}/{len(etapes)}: {etape}")
        
        # Vérifier si des scores ont été détectés
        if hasattr(config, 'score_actuel') and config.score_actuel:
            print(f"      📊 Score détecté : {config.score_actuel}")
        
        # Simuler du travail
        await asyncio.sleep(2)
    
    print("   Script principal terminé.")


# Fonction: Exemple d'utilisation avec gestion d'erreurs
# Commentaire: Montre comment gérer les erreurs dans l'intégration asynchrone
async def exemple_avec_gestion_erreurs():
    """
    Exemple avec gestion complète des erreurs
    """
    print("=== Exemple avec gestion d'erreurs ===")
    
    task = None
    stop_event = None
    
    try:
        # Initialisation avec gestion d'erreurs
        print("Initialisation...")
        
        # Simuler l'initialisation du driver
        driver = None  # Remplacez par votre driver réel
        
        if driver:
            # Démarrer la surveillance avec timeout
            print("Démarrage de la surveillance avec timeout...")
            task, stop_event = await asyncio.wait_for(
                start_score_monitoring(driver),
                timeout=10.0
            )
            print("Surveillance démarrée avec succès")
        
        # Exécuter le script principal avec timeout
        print("Exécution du script principal avec timeout...")
        await asyncio.wait_for(
            executer_script_principal(),
            timeout=30.0
        )
        
    except asyncio.TimeoutError:
        print("❌ Timeout lors de l'exécution")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
    finally:
        # Nettoyage garanti
        if task and stop_event:
            try:
                print("Nettoyage : arrêt de la surveillance...")
                await stop_score_monitoring(task, stop_event)
                print("✅ Nettoyage terminé")
            except Exception as e:
                print(f"⚠️  Erreur lors du nettoyage : {e}")


# Fonction: Menu principal
# Commentaire: Interface pour choisir l'exemple à exécuter
async def main():
    """
    Menu principal pour les exemples
    """
    print("=== Exemples d'intégration GetScoreActuelAsync ===")
    print("1. Intégration complète")
    print("2. Exemple avec gestion d'erreurs")
    print("3. Exécuter tous les exemples")
    
    choice = input("Choisissez un exemple (1-3) : ").strip()
    
    if choice == "1":
        await exemple_integration_complete()
    elif choice == "2":
        await exemple_avec_gestion_erreurs()
    elif choice == "3":
        print("Exécution de tous les exemples...\n")
        await exemple_integration_complete()
        print("\n" + "="*60 + "\n")
        await exemple_avec_gestion_erreurs()
        print("\n✅ Tous les exemples terminés !")
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
            config.classes = {
                'score_container': {
                    'old_site': 'score-class-default'
                }
            }
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nExemple interrompu par l'utilisateur.")
    except Exception as e:
        print(f"Erreur lors de l'exécution des exemples : {e}")