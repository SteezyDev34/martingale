# Nouveau système de calcul côté AuxoTracker (2026-09-28)

> Note ajoutée pour informer toute session future travaillant sur ce bot : l'API
> AuxoTracker expose désormais un nouvel indicateur de probabilité, pertinent
> pour la logique martingale de ce projet. Rien dans ce dépôt ne le consomme
> encore — c'est à faire si on veut en profiter.

## Ce qui a changé

Jusqu'ici, les probas 15A/30A/40A/30-0 exposées par AuxoTracker (endpoint
`GET /api/stats/tennis/player/{teamId}/tension`, champ `stats`) étaient un taux
**par jeu isolé** (fréquence qu'UN jeu donné atteigne 15-15/30-30/40-40/30-0).
Ce n'est pas ce qui compte pour une martingale jouée sur **plusieurs jeux
successifs** jusqu'à ce que l'événement arrive (exactement le fonctionnement de
ce bot — `Functions/FisrtGameBet.py`, `Functions/GetAndPlaceBet.py`) : un taux
par jeu de 33% ne dit rien sur la probabilité que l'événement arrive dans les
10 premiers jeux du set.

Un nouveau champ `stats_in_set` a été ajouté à ce même endpoint, avec la vraie
fréquence historique **"au moins une fois dans les 10 premiers jeux du 1er
set"** (capé à 10 jeux — capacité réelle d'une martingale, pas tout le set qui
peut aller jusqu'à 12-13 jeux). C'est un taux **par match**, pas par jeu.

```json
{
  "stats": {                      // ancien : taux PAR JEU (déjà existant)
    "reach_15a": 56.67,
    "reach_30a": 33.33,
    "reach_40a": 30,
    "reach_30love": 43.33,
    "..."
  },
  "stats_in_set": {                // NOUVEAU : taux PAR MATCH, capé à 10 jeux
    "reach_15a": 100,
    "reach_30a": 100,
    "reach_40a": 100,
    "reach_30love": 100,
    "game_40_0": 50,
    "game_40_15": 100,
    "game_40_30": 100,
    "leads_15_0": 100,
    "lost_first_point_on_serve": 100
  }
}
```

Ces taux sont blendés (shrinkage bayésien, K=5) entre la stat globale du
joueur et sa stat spécifique face au **tier de classement** de l'adversaire du
jour (top50 / 50-150 / 150+) — donc plus fiables qu'une simple moyenne
brute sur tous les adversaires confondus.

## Où le brancher dans ce projet

- `Functions/Functions_stats.py` (fonctions `get_wta_proba_40A_sofascore` et
  similaires, ~ligne 300) calcule aujourd'hui sa propre proba théorique
  (`svc * ret`) à partir de `/api/stats/tennis/player/{pid}` (stats de saison
  brutes), sans utiliser `/tension` ni son nouveau `stats_in_set` — c'est un
  calcul indépendant, pas connecté au nouveau système.
- `config.py` (commentaire ligne ~51) référence déjà l'API `/tension` comme
  source prévue pour le "mode de sélection des scriptTypes", mais aucun appel
  réel à cet endpoint n'a été trouvé dans le code actuel (recherche
  `grep -rn "tension"` dans `Functions/` et `core/` à refaire pour confirmer).
- Le point d'entrée le plus probable pour intégrer ceci : là où le bot décide
  SUR QUEL match/marché miser (`Functions/ScriptRechercheDeMatch.py`,
  `core/martingale/script_types.py` si un jour réactivé) — utiliser
  `stats_in_set` pour filtrer/prioriser les matchs plutôt que le `stats`
  actuel, qui n'est pas la bonne unité pour une décision de martingale.

## Vérification empirique (côté AuxoTracker, backtest leave-one-out)

Le filtre "ne parier que si `stats_in_set` blendé du match ≥ 85%" a été validé
sur ~1250 matchs réels (hors échantillon) : taux de réussite réel 92-100% pour
la plupart des marchés, sauf `game_40_0` plus faible (~84%). Voir
`tennis:backtest-scores --leave-one-out` côté AuxoTracker
(`backend/app/Console/Commands/BacktestTennisScores.php`) pour reproduire.

## Limite connue

`stats_in_set` demande un minimum d'historique point-by-point par joueur
(`reliable: true` dans la réponse, seuil `sample_games_set1 >= 15`) — sinon
l'API renvoie `success: false` (`TENSION_STAT_NOT_FOUND`) ou des taux à 0 pour
un joueur trop peu échantillonné. Gérer ce cas (repli sur l'ancien `stats` ou
sur le calcul théorique local existant) si intégré.
