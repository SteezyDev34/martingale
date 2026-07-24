---
description: Placement automatique des paris non traités via Selenium (Lollybet/Stake).
---

Vérifier l'API pour les paris non traités et les placer via Python Selenium.

Setup: config.localhost = 43151, ./venv/bin/python, fenêtre Selenium 11=Stake, 8=Lollybet.

Pour chaque pari (telegram_bets_api.get_unprocessed_bets(10)) :

1. Récupérer la mise via get_recommended_stake(cote, tipster, bankroll_id=2), fallback 1€ si exception — endpoint /api/auxobot/recommended-stake?user_id=3&bankroll_id=2.
2. Router :
   - combined_events présent → SGM → StakeScraper (Stake.bet MyMatch)
   - len(matches) > 1 → combiné → place_combined_bet(matches, mise, xbet_driver=driver) sur Lollybet
   - sinon → place_best_bet(match, xbet_driver=driver) meilleure cote
3. Succès → mark_bet_as_processed(id, processed=1) puis envoyer le pari à POST https://api.auxotracker.p-com.studio/api/auxobot/bets avec : bet_date, global_odds, bet_code="<bookmaker>-<id>", result="pending", stake, stake_type="currency", bankroll_id=2, tipster, sport_id (2=tennis 1=football), event_list=[{equipe_1, equipe_2, selection, odds, sport_id}] — sport_id obligatoire pour reconnaissance d'équipe automatique.
4. Échec → mark_bet_as_processed(id, processed=2) — ne jamais marquer échec sans avoir tenté.
5. Si erreur inconnue (sélecteur manquant, nouveau marché) : analyser le DOM, corriger StakeScraper.py ou LollybetScraper.py, relancer.

Règles :
- Handicap X(0) = "Remboursé si match nul" sur Stake
- Bookmakers actifs : Lollybet ✅ Stake ✅ Winamax ❌ Betclic ❌
- AUXOBOT_TOKEN dans .env (attention à l'espace avant le =)
- Ne jamais arrêter la loop
