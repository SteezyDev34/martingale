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
from Functions.TelegramBetsAPI import telegram_bets_api, send_bet_to_auxotracker
from Functions.Bookmakers.router import place_best_bet, refresh_all_challenges, place_combined_bet
from Functions.Logs.Logger import log, log_clear_line
from Functions.Logs import BetTrace
from Functions.GetMise import get_recommended_stake


def _report_bet_to_auxotracker(bet_id, result, mise, tipster, events_source):
    """
    Envoie le pari place a POST /api/auxobot/bets (AuxoTracker), pour qu'il
    apparaisse dans le suivi/bankroll -- gap trouve le 2026-10-16 : un pari
    place avec succes etait marque "traite" localement mais jamais remonte
    a l'API, contrairement a ce que documente /loop (skill Claude Code).
    Champs alignes sur cette doc (event_list, pas events -- different de
    l'ancien PlacerPari.py). N'echoue jamais le traitement du pari si ce
    reporting rate (deja logge dans send_bet_to_auxotracker) : le pari est
    reellement place sur le bookmaker, ca prime sur le suivi.
    """
    try:
        event_list = [{
            "equipe_1": m.get("equipe_1", ""),
            "equipe_2": m.get("equipe_2", ""),
            "selection": m.get("selection", ""),
            "odds": m.get("odds"),
            "sport_id": m.get("sport", "1"),
        } for m in events_source]
        bet_dict = {
            "bet_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "global_odds": result.get("odds"),
            "bet_code": f"{result.get('bookmaker', '?')}-{bet_id}",
            "result": "pending",
            "stake": mise,
            "stake_type": "currency",
            "bankroll_id": 2,
            "tipster": tipster,
            "sport_id": events_source[0].get("sport", "1") if events_source else "1",
            "event_list": event_list,
        }
        send_bet_to_auxotracker(bet_dict)
    except Exception as e:
        log(f"⚠️ Échec report AuxoTracker pour pari ID {bet_id}: {e}", "warning", clear=False)

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
                # Données corrompues (ex: JSON tronqué par une ancienne limite de
                # colonne DB, cf. api/src/Database.php) — irrécupérable. Marquer
                # en échec plutôt que "continue" seul : sinon ce pari non-traité
                # reste indéfiniment dans la file et refait échouer le parsing à
                # chaque passage de la boucle (process_bets_loop.py tourne en
                # continu désormais, contrairement à l'ancien /loop ponctuel).
                log(f"Erreur parsing selection pour pari ID {bet.get('id')} (données corrompues, marqué échec)", "error")
                telegram_bets_api.mark_bet_as_processed(bet['id'], processed=2)
                continue

        if not bet_data:
            log(f"Impossible de récupérer les données pour pari ID {bet.get('id')} (marqué échec)", "error")
            telegram_bets_api.mark_bet_as_processed(bet['id'], processed=2)
            continue

        tipster = bet_data.get("tipster", "")
        all_matches = bet_data.get("matches", [])

        trace_dir = BetTrace.start(bet['id'], {"tipster": tipster, "matches": all_matches})

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
        BetTrace.step(trace_dir, "mise_calculee", {"mise": mise, "ref_odds": ref_odds})
        # ────────────────────────────────────────────────────────────────

        # ── Combiné : plusieurs matches → un seul ticket accumulateur ───
        if len(all_matches) > 1:
            log(f"🎯 Pari combiné ID {bet['id']}: {len(all_matches)} legs", "info", clear=False)
            for m in all_matches:
                log(f"   · {m.get('equipe_1')} vs {m.get('equipe_2')} | {m.get('selection')}", "info", clear=False)
            BetTrace.step(trace_dir, "placement_tente", {"type": "combine", "bookmaker": "Lollybet", "legs": len(all_matches)})
            result = place_combined_bet(all_matches, mise, trace_dir=trace_dir)
            events_for_report = all_matches
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
            match["trace_dir"] = trace_dir
            log(f"Pari simple ID {bet['id']}: {match.get('equipe_1')} vs {match.get('equipe_2')} | {match.get('selection')}", "info", clear=False)
            BetTrace.step(trace_dir, "placement_tente", {"type": "simple", "match": f"{match.get('equipe_1')} vs {match.get('equipe_2')}", "selection": match.get('selection')})
            result = place_best_bet(match)
            events_for_report = [match]

        if result.get("success"):
            log(f"✅ Pari placé sur {result.get('bookmaker')} @ {result.get('odds','?')} (mise={mise}€)", "info", clear=False)
            BetTrace.step(trace_dir, "resultat", {"success": True, "bookmaker": result.get('bookmaker'), "odds": result.get('odds')})
            _report_bet_to_auxotracker(bet['id'], result, mise, tipster, events_for_report)
            if telegram_bets_api.mark_bet_as_processed(bet['id']):
                processed_count += 1
                log(f"Pari ID {bet['id']} marqué traité", "info", clear=False)
        else:
            log(f"❌ Échec placement ID {bet['id']}: {result.get('error','')}", "error", clear=False)
            BetTrace.step(trace_dir, "resultat", {"success": False, "bookmaker": result.get('bookmaker'), "error": result.get('error'), "candidates": result.get('candidates')}, level="error")
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