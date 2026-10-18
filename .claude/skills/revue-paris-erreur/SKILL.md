---
name: revue-paris-erreur
description: Revue interactive des paris qui ont échoué à être placés (match déjà terminé, libellé de marché introuvable chez le bookmaker, erreur technique...), pari par pari, avec alimentation des règles de correspondance de marché quand c'est pertinent. À utiliser quand Steeven demande de revoir/analyser les paris en erreur, les échecs de placement, ou pourquoi un pari n'est pas passé.
---

# Revue des paris en erreur

Ce skill sert à étudier, **un par un et sur demande explicite** (jamais en
masse, jamais automatiquement), les paris qui ont échoué à être placés — pour
distinguer les cas sans remède (match déjà terminé, session expirée...) des
cas où le libellé de marché retenu par l'IA d'extraction ne correspond pas au
texte réel utilisé par le bookmaker (auquel cas on corrige la règle
d'extraction ensemble).

Prérequis déjà en place (Phase 1, commits `b1d3851af` et suivants) : chaque
échec de placement remonte maintenant un `bookmaker` + `error` exploitable
(et les `candidates` — textes de marché réels vus sur la page — quand
pertinent) jusque dans `Logs/bet_traces/<date>/<bet_id>/trace.jsonl`.

## Outil

Tout passe par `Functions/Logs/review_failed_bets.py` (toujours avec le venv
du projet) :

```bash
./venv/bin/python3 Functions/Logs/review_failed_bets.py list
```
Liste les paris dont la **dernière tentative connue** est un échec, pas
encore revus (un pari peut être retenté plusieurs fois par
`ProcessTelegramBets.py` — seul le dernier essai compte). Ajouter `--all`
pour revoir aussi ceux déjà traités, `--date YYYY-MM-DD` pour filtrer.

Sortie TSV, une ligne par pari :
```
date  bet_id  tipster  match  selection  bookmaker  error  "N tentative(s)"  candidates=N  [DEJA_REVU]
```

```bash
./venv/bin/python3 Functions/Logs/review_failed_bets.py show <date> <bet_id>
```
Détail complet : contexte du dernier essai (match, marché, sélection, cote),
puis l'historique de toutes les tentatives (start/mise/placement/résultat),
avec les `candidates` et le chemin de la capture d'écran quand présents.

```bash
./venv/bin/python3 Functions/Logs/review_failed_bets.py mark <date> <bet_id> \
  --status resolved|skipped --category match_ended|label_mismatch|technical|unknown \
  --note "texte libre"
```
Enregistre la décision prise ensemble dans `Logs/bet_traces/_review_state.json`
pour ne plus re-proposer ce pari la prochaine fois.

## Déroulé

1. **Lancer `list`** (sans argument = seulement les non-revus). S'il n'y a
   rien, le dire simplement et s'arrêter là — ne pas inventer de travail.

2. **Présenter un seul pari à la fois**, dans l'ordre de `list`, jamais
   plusieurs en rafale. Pour celui-ci, lancer `show` et résumer en 3-4
   lignes : match, marché/sélection tentée, bookmaker, erreur, nombre de
   tentatives, et une **proposition de diagnostic** basée sur l'erreur :
   - `match_not_found` / erreur évoquant un match introuvable, **et**
     l'heure du match (`context.date`) est passée depuis longtemps par
     rapport à l'heure de la dernière tentative → probablement
     **match déjà terminé/retiré** avant que le placement n'ait pu se faire.
   - `selection_not_found` / `market_locked` **avec des `candidates` non
     vides** → probablement **libellé de marché qui ne correspond pas**
     au texte réel du bookmaker (c'est le cas à creuser en priorité : les
     `candidates` sont les textes réels vus sur la page).
   - `session_expired`, `driver_unavailable`, `stake_failed`,
     `validation_failed`, exception Python brute (message technique peu
     lisible) → probablement **problème technique/session**, pas un souci
     de mapping de marché.
   - Erreur vide/`null` (traces d'avant le correctif Phase 1, ou absente) →
     dire clairement qu'il n'y a pas assez d'info, ne pas deviner.
   - Sinon → dire honnêtement qu'on ne sait pas, demander à Steeven.

   Ne JAMAIS trancher seul sur la vraie cause : proposer le diagnostic et
   **attendre sa confirmation ou sa correction** avant d'agir.

3. **Si le diagnostic confirmé est `label_mismatch`** :
   - Comparer la `selection` tentée (et `categorie`/`type_de_pari` si
     présents) aux `candidates` réels affichés par `show`.
   - **Important (appris le 2026-10-18 sur 1xBet)** : ne pas supposer que
     tous les bookmakers fonctionnent comme 1xBet. Sur 1xBet,
     `categorie`/`type_de_pari` sont purement cosmétiques — seul le texte
     de `selection` est utilisé pour matcher le marché sur la page
     (`chrome_extension/content_scripts/1xbet.js`, fonction
     `selectMarketByText`, correspondance par sous-chaîne). Avant de
     proposer un correctif pour un AUTRE bookmaker (Stake, Lollybet...),
     vérifier d'abord dans son scraper (`Functions/Bookmakers/*.py`,
     `_bridge_place_bet`/`place_bet`/`get_odds`) si le mécanisme de
     matching est le même (texte libre) ou différent (ex: recherche par
     `categorie`+`type_de_pari` structurés) — ça change complètement la
     nature du correctif à proposer.
   - Pour 1xBet spécifiquement : le correctif est une règle ajoutée au
     prompt système de `extraire_pari_depuis_image`/`extraire_pari_depuis_texte`
     dans `Functions/getTextFromImageGPT.py` (voir la règle "buteur à tout
     moment" ajoutée le 2026-10-18 comme modèle — un bloc `RÈGLE` avec le
     motif de texte source, le mapping exact vers `categorie`/`type_de_pari`/
     `selection`, basé sur du HTML réel si possible, pas une supposition).
   - Proposer le texte exact de la règle à ajouter, **avec la citation du
     `candidates` réel qui la justifie**, et attendre validation avant
     d'éditer le fichier. Après édition : `py_compile` le fichier modifié.
   - Si Steeven fournit du HTML/une capture d'un autre bookmaker pour
     clarifier un libellé (comme il l'a fait pour 1xBet le 2026-10-18),
     s'en servir comme source de vérité plutôt que de deviner depuis un
     fichier de référence existant (`xbet_selections.json` n'est qu'un
     exemple pour le prompt IA, pas la logique de matching réelle).

4. **Si le diagnostic confirmé est `match_ended` ou `technical`** : rien à
   corriger dans le code en général — juste comprendre et classer. Si un
   même type d'erreur technique revient souvent sur le même bookmaker,
   le signaler à Steeven (ça peut valoir une investigation séparée, mais
   ne pas la lancer sans qu'il le demande).

5. **Marquer avec `mark`** une fois la décision prise (`--status resolved`
   si un correctif a été appliqué ou si la cause est actionnable et
   comprise, `--status skipped` si on laisse de côté sans agir — préciser
   pourquoi dans `--note`), puis **demander si on continue au suivant** —
   ne jamais enchaîner seul sur le pari suivant.

## Ce que ce skill ne fait PAS (pour l'instant)

- Pas de correction automatique en masse : chaque cas est discuté avant
  toute modification de code.
- Pas encore de fichier de référence de marché par bookmaker type
  `xbet_selections.json` pour Stake/Lollybet (Phase 3, pas commencée) —
  tant que ça n'existe pas, les cas `label_mismatch` sur ces bookmakers se
  traitent au cas par cas comme pour 1xBet.
- Ne touche jamais aux paris déjà engagés/placés avec succès — uniquement
  ceux dont la dernière tentative connue est un échec.
