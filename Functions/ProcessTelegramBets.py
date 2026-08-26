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
from Functions.Bookmakers.router import place_best_bet, refresh_all_challenges, place_combined_bet
from Functions.Logs.Logger import log, log_clear_line
from Functions.GetMise import get_recommended_stake

def process_api_bets(limit: int = 10) -> int:
    """
    Traite les paris non traités depuis l'API.

    Args:
        limit (int): Nombre maximum de paris à traiter

    Returns:
        int: Nombre de paris traités avec succès
    """
    # Récupérer les paris non traités
    unprocessed_bets = telegram_bets_api.get_unprocessed_bets(limit)

    if not unprocessed_bets:
        return 0

    log(f"Trouvé {len(unprocessed_bets)} paris non traités", "info")
    processed_count = 0

    for bet in unprocessed_bets:
        if not bet:
            continue
        bet = dict(bet)

        # Parser la sélection
        bet_data = None
        if bet.get('selection'):
            try:
                sel = json.loads(bet['selection'])
                if isinstance(sel, dict) and 'matches' in sel:
                    bet_data = sel
            except (json.JSONDecodeError, TypeError):
                log(f"Erreur parsing selection pour pari ID {bet.get('id')}", "error")
                continue

        if not bet_data:
            log(f"Impossible de récupérer les données pour pari ID {bet.get('id')}", "error")
            continue

        tipster = bet_data.get("tipster", "")
        all_matches = bet_data.get("matches", [])

        # ── Récupérer la mise ────────────────────────────────────────────
        ref_odds = all_matches[0].get("odds") if all_matches else bet_data.get("odds")
        try:
            stake_data = get_recommended_stake(cote=ref_odds, tipster=tipster)
            _rs = stake_data.get("recommended_stake")
            mise = float(_rs if _rs is not None else 1.0)
            log(f"💰 Mise: {mise}€ (tipster={tipster}, cote={ref_odds})", "info", clear=False)
        except Exception as e:
            mise = 1.0
            log(f"⚠️ Mise par défaut 1€ ({e})", "warning", clear=False)
        # ────────────────────────────────────────────────────────────────

        # ── Combiné : plusieurs matches → un seul ticket accumulateur ───
        if len(all_matches) > 1:
            log(f"🎯 Pari combiné ID {bet['id']}: {len(all_matches)} legs", "info", clear=False)
            for m in all_matches:
                log(f"   · {m.get('equipe_1')} vs {m.get('equipe_2')} | {m.get('selection')}", "info", clear=False)
            result = place_combined_bet(all_matches, mise)
        else:
            # ── Simple : 1 match ─────────────────────────────────────────
            if all_matches:
                match = all_matches[0]
            else:
                # Fallback champs root
                match = {
                    "equipe_1": bet_data.get("equipe_1", ""),
                    "equipe_2": bet_data.get("equipe_2", ""),
                    "selection": bet_data.get("selection", ""),
                    "odds": bet_data.get("odds"),
                    "date": bet_data.get("date", ""),
                    "sport": bet_data.get("sport", "1"),
                    "intitule": bet_data.get("intitule", ""),
                    "categorie": bet_data.get("categorie", "Temps réglementaire"),
                    "combined_events": bet_data.get("combined_events", []),
                }
            match["tipster"] = tipster
            match["mise"] = mise
            log(f"Pari simple ID {bet['id']}: {match.get('equipe_1')} vs {match.get('equipe_2')} | {match.get('selection')}", "info", clear=False)
            result = place_best_bet(match)

        if result.get("success"):
            log(f"✅ Pari placé sur {result.get('bookmaker')} @ {result.get('odds','?')} (mise={mise}€)", "info", clear=False)
            if telegram_bets_api.mark_bet_as_processed(bet['id']):
                processed_count += 1
                log(f"Pari ID {bet['id']} marqué traité", "info", clear=False)
        else:
            log(f"❌ Échec placement ID {bet['id']}: {result.get('error','')}", "error", clear=False)
            telegram_bets_api.mark_bet_as_processed(bet['id'], processed=2)

        time.sleep(2)

    return processed_count


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