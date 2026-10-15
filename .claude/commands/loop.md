---
description: Placement automatique des paris non traités (Lollybet via Selenium, Stake et 1xBet via l'extension Chrome).
---

Vérifier l'API pour les paris non traités et les placer via process_api_bets.

Setup: config.localhost = 43151, ./venv/bin/python, fenêtre Selenium 8=Lollybet. Pour Stake et 1xBet : le bridge WebSocket doit être démarré (StakeBridge.start_stake_bridge() / websocket_server.start_bridge(), démarrés automatiquement à l'import de router.py) et l'extension Chrome connectée sur un onglet Stake/1xBet — pas de fenêtre Selenium dédiée (Stake retombe sur Selenium seulement si l'extension n'est pas connectée).

Pour chaque pari (telegram_bets_api.get_unprocessed_bets(10)) :

1. Récupérer la mise via get_recommended_stake(cote, tipster, bankroll_id=2), fallback 1€ si exception — endpoint /api/auxobot/recommended-stake?user_id=3&bankroll_id=2.
2. Router :
   - combined_events présent → SGM → StakeScraper (Stake.bet MyMatch)
   - len(matches) > 1 → combiné → place_combined_bet(matches, mise) sur Lollybet
   - sinon → place_best_bet(match) meilleure cote parmi les bookmakers actifs (comparaison inclut 1xBet)
3. Succès → mark_bet_as_processed(id, processed=1) puis envoyer le pari à POST https://api.auxotracker.p-com.studio/api/auxobot/bets avec : bet_date, global_odds, bet_code="<bookmaker>-<id>", result="pending", stake, stake_type="currency", bankroll_id=2, tipster, sport_id (2=tennis 1=football), event_list=[{equipe_1, equipe_2, selection, odds, sport_id}] — sport_id obligatoire pour reconnaissance d'équipe automatique.
4. Échec → mark_bet_as_processed(id, processed=2) — ne jamais marquer échec sans avoir tenté.
5. Si erreur inconnue (sélecteur manquant, nouveau marché) : analyser le DOM, corriger LollybetScraper.py (Selenium), chrome_extension/content_scripts/stake.js (Stake) ou chrome_extension/content_scripts/1xbet.js (1xBet), relancer.

Règles :
- Handicap X(0) = "Remboursé si match nul" sur Stake
- Bookmakers actifs (cf. router.BOOKMAKER_STATE) : Lollybet ❌ Stake ✅ 1xBet ✅ Winamax ❌ Betclic ❌
- AUXOBOT_TOKEN dans .env (attention à l'espace avant le =)
- Ne jamais arrêter la loop
