#!/usr/bin/env python3
"""
Script d'administration pour l'API Telegram Bets.
Permet de visualiser, gérer et nettoyer les paris stockés.
"""
import sys
import os
import argparse
from datetime import datetime, timedelta

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Functions.TelegramBetsAPI import telegram_bets_api
from Functions.ProcessTelegramBets import monitor_telegram_bets, get_betting_statistics


def list_bets(processed=None, tipster=None, limit=20):
    """Affiche la liste des paris avec filtres optionnels."""
    print(f"\n=== LISTE DES PARIS ===")
    
    if processed is not None:
        bets = []  # TODO: Implémenter la récupération avec filtre processed
        print("Note: Filtre 'processed' pas encore implémenté dans l'API")
    else:
        bets = telegram_bets_api.get_unprocessed_bets(limit)
    
    if tipster:
        bets = telegram_bets_api.get_bets_by_tipster(tipster, processed, limit)
    
    if not bets:
        print("Aucun pari trouvé avec ces critères")
        return
    
    print(f"Trouvé {len(bets)} paris:")
    print("-" * 120)
    print(f"{'ID':<5} {'Date':<12} {'Équipes':<40} {'Catégorie':<20} {'Odds':<8} {'Tipster':<10} {'Traité':<8}")
    print("-" * 120)
    
    for bet in bets:
        match_name = f"{bet.get('equipe_1', '')} vs {bet.get('equipe_2', '')}"
        if len(match_name) > 38:
            match_name = match_name[:35] + "..."
        
        processed_status = "✓" if bet.get('processed') else "✗"
        
        print(f"{bet.get('id', 0):<5} "
              f"{bet.get('date_pari', ''):<12} "
              f"{match_name:<40} "
              f"{bet.get('categorie', ''):<20} "
              f"{bet.get('odds', 0):<8} "
              f"{bet.get('tipster', ''):<10} "
              f"{processed_status:<8}")


def show_bet_details(bet_id):
    """Affiche les détails complets d'un pari."""
    # TODO: Implémenter une méthode pour récupérer un pari par ID
    print(f"Détails du pari ID {bet_id} - Fonction à implémenter")


def mark_processed(bet_id):
    """Marque un pari comme traité."""
    success = telegram_bets_api.mark_bet_as_processed(bet_id)
    if success:
        print(f"✓ Pari ID {bet_id} marqué comme traité")
    else:
        print(f"✗ Erreur lors du marquage du pari ID {bet_id}")


def show_statistics():
    """Affiche les statistiques détaillées."""
    monitor_telegram_bets()


def interactive_mode():
    """Mode interactif pour administrer l'API."""
    while True:
        print("\n=== ADMINISTRATION TELEGRAM BETS API ===")
        print("1. Afficher les statistiques")
        print("2. Lister les paris non traités")
        print("3. Lister tous les paris récents")
        print("4. Filtrer par tipster")
        print("5. Marquer un pari comme traité")
        print("6. Quitter")
        
        choice = input("\nChoisissez une option (1-6): ").strip()
        
        try:
            if choice == '1':
                show_statistics()
            
            elif choice == '2':
                limit = input("Nombre de paris à afficher (défaut 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                list_bets(processed=False, limit=limit)
            
            elif choice == '3':
                limit = input("Nombre de paris à afficher (défaut 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                list_bets(limit=limit)
            
            elif choice == '4':
                tipster = input("Nom du tipster: ").strip()
                if tipster:
                    limit = input("Nombre de paris à afficher (défaut 20): ").strip()
                    limit = int(limit) if limit.isdigit() else 20
                    list_bets(tipster=tipster, limit=limit)
                else:
                    print("Nom de tipster requis")
            
            elif choice == '5':
                bet_id = input("ID du pari à marquer comme traité: ").strip()
                if bet_id.isdigit():
                    mark_processed(int(bet_id))
                else:
                    print("ID invalide")
            
            elif choice == '6':
                print("Au revoir!")
                break
            
            else:
                print("Option invalide")
                
        except KeyboardInterrupt:
            print("\n\nInterruption utilisateur")
            break
        except Exception as e:
            print(f"Erreur: {e}")


def main():
    """Fonction principale avec arguments en ligne de commande."""
    parser = argparse.ArgumentParser(description="Administration de l'API Telegram Bets")
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Mode interactif')
    parser.add_argument('--stats', '-s', action='store_true', 
                       help='Afficher les statistiques')
    parser.add_argument('--list', '-l', action='store_true', 
                       help='Lister les paris')
    parser.add_argument('--unprocessed', '-u', action='store_true', 
                       help='Afficher uniquement les paris non traités')
    parser.add_argument('--tipster', '-t', type=str, 
                       help='Filtrer par tipster')
    parser.add_argument('--limit', type=int, default=20, 
                       help='Nombre maximum de paris à afficher')
    parser.add_argument('--mark-processed', type=int, metavar='ID',
                       help='Marquer un pari comme traité')
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_mode()
        elif args.stats:
            show_statistics()
        elif args.list:
            processed = False if args.unprocessed else None
            list_bets(processed=processed, tipster=args.tipster, limit=args.limit)
        elif args.mark_processed:
            mark_processed(args.mark_processed)
        else:
            # Par défaut, afficher les statistiques
            show_statistics()
            
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()