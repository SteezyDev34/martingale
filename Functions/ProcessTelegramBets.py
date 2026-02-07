"""
Script utilitaire pour traiter les paris stockés dans l'API Telegram Bets.
Récupère les paris non traités et les passe au système de placement de paris.
"""
import json
import sys
import os
import time
from typing import List, Dict

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.TelegramBetsAPI import telegram_bets_api
from Functions.PlacerPari import placer_pari
from Functions.Logs.Logger import log, log_clear_line

def process_api_bets(driver, limit: int = 10) -> int:
    """
    Traite les paris non traités depuis l'API.
    
    Args:
        driver: Instance du driver Selenium
        limit (int): Nombre maximum de paris à traiter
        
    Returns:
        int: Nombre de paris traités avec succès
    """
    try:
        # Récupérer les paris non traités
        unprocessed_bets = telegram_bets_api.get_unprocessed_bets(limit)
        
        if not unprocessed_bets:
            log("Aucun pari non traité trouvé dans l'API", "info")
            return 0
        
        log(f"Trouvé {len(unprocessed_bets)} paris non traités", "info")
        processed_count = 0
        
        for bet in unprocessed_bets:
            try:
                # Convertir les données de l'API au format attendu par placer_pari
                bet_data = {
                    "date": bet.get("date_pari"),
                    "equipe_1": bet.get("equipe_1"),
                    "equipe_2": bet.get("equipe_2"),
                    "categorie": bet.get("categorie"),
                    "type_de_pari": bet.get("type_de_pari"),
                    "selection": bet.get("selection"),
                    "odds": bet.get("odds"),
                    "tipster": bet.get("tipster")
                }
                
                log(f"Traitement du pari ID {bet['id']}: {bet_data['equipe_1']} vs {bet_data['equipe_2']}", "info", clear=False)
                
                # Placer le pari
                success = placer_pari(driver, [bet_data])
                
                if success:
                    # Marquer le pari comme traité dans l'API
                    if telegram_bets_api.mark_bet_as_processed(bet['id']):
                        processed_count += 1
                        log(f"Pari ID {bet['id']} traité avec succès", "info", clear=False)
                    else:
                        log(f"Erreur lors du marquage du pari ID {bet['id']} comme traité", "error", clear=False)
                else:
                    log(f"Échec du placement du pari ID {bet['id']}", "error", clear=False)
                
                # Attendre un peu entre chaque pari pour éviter de surcharger le système
                time.sleep(2)
                
            except Exception as e:
                log(f"Erreur lors du traitement du pari ID {bet.get('id', 'unknown')}: {e}", "error", clear=False)
        
        return processed_count
        
    except Exception as e:
        log(f"Erreur générale lors du traitement des paris API: {e}", "error", clear=False)
        return 0


def get_betting_statistics() -> Dict:
    """
    Récupère les statistiques des paris depuis l'API.
    
    Returns:
        Dict: Statistiques des paris
    """
    try:
        # Récupérer tous les paris (limite élevée pour avoir une vue d'ensemble)
        all_bets = telegram_bets_api.get_unprocessed_bets(1000)
        processed_bets = []
        
        # TODO: Ajouter une méthode pour récupérer les paris traités
        # En attendant, on peut faire une estimation
        
        stats = {
            "total_unprocessed": len(all_bets),
            "tipsters": {},
            "categories": {},
            "recent_bets": all_bets[:5]  # Les 5 derniers paris
        }
        
        # Analyser les paris par tipster et catégorie
        for bet in all_bets:
            tipster = bet.get("tipster", "unknown")
            categorie = bet.get("categorie", "unknown")
            
            stats["tipsters"][tipster] = stats["tipsters"].get(tipster, 0) + 1
            stats["categories"][categorie] = stats["categories"].get(categorie, 0) + 1
        
        return stats
        
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")
        return {"error": str(e)}


def monitor_telegram_bets():
    """
    Fonction de monitoring pour afficher les statistiques des paris.
    """
    try:
        stats = get_betting_statistics()
        
        print("\n=== STATISTIQUES PARIS TELEGRAM ===")
        print(f"Paris non traités: {stats.get('total_unprocessed', 0)}")
        
        print("\nRépartition par tipster:")
        for tipster, count in stats.get('tipsters', {}).items():
            print(f"  - {tipster}: {count} paris")
        
        print("\nRépartition par catégorie:")
        for categorie, count in stats.get('categories', {}).items():
            print(f"  - {categorie}: {count} paris")
        
        print("\nDerniers paris reçus:")
        for bet in stats.get('recent_bets', []):
            print(f"  - ID {bet.get('id')}: {bet.get('equipe_1')} vs {bet.get('equipe_2')} ({bet.get('tipster')})")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"Erreur lors du monitoring: {e}")


if __name__ == "__main__":
    # Exemple d'utilisation
    print("Script de traitement des paris API Telegram")
    
    # Afficher les statistiques
    monitor_telegram_bets()
    
    # Pour tester le traitement, décommentez les lignes suivantes:
    # from ChromeDriver.SetDriver import driver
    # processed = process_api_bets(driver, limit=5)
    # print(f"Nombre de paris traités: {processed}")