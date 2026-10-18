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
   - **Architecture (tranchée le 2026-10-18)** : l'IA d'extraction
     (`getTextFromImageGPT.py`) produit TOUJOURS une sélection "pivot" basée
     sur la taxonomie 1xBet, et ne peut pas faire autrement — au moment de
     l'extraction, le bookmaker qui recevra le pari n'est pas encore connu
     (`get_best_odds` compare après coup). La correspondance vers le texte
     réel d'un bookmaker spécifique se fait donc **au placement**, pas à
     l'extraction. Deux mécanismes distincts selon le bookmaker en échec :

     - **1xBet** : lui-même est la source de vérité du pivot — un
       `label_mismatch` ici veut dire que l'IA a mal choisi le libellé
       pivot. Le correctif est une règle ajoutée au prompt système de
       `extraire_pari_depuis_image`/`extraire_pari_depuis_texte` dans
       `Functions/getTextFromImageGPT.py` (voir la règle "buteur à tout
       moment" du 2026-10-18 comme modèle — un bloc `RÈGLE` avec le motif de
       texte source, le mapping exact vers `categorie`/`type_de_pari`/
       `selection`, basé sur du HTML réel si possible, pas une supposition).
       Matching 1xBet confirmé par le code : seul le texte de `selection`
       compte, par sous-chaîne (`chrome_extension/content_scripts/1xbet.js`,
       `selectMarketByText`) — `categorie`/`type_de_pari` sont cosmétiques.

     - **Stake, Lollybet, Betclic, Winamax** : ces 4 scrapers appellent déjà
       `get_label(bookmaker, sport_id, selection)` (`Functions/BetLabelsDB.py`,
       table SQLite `bet_labels.db`) juste avant de chercher le marché sur
       la page, avec repli sur la sélection pivot si rien n'est mappé. Le
       pivot lui-même reste correct dans ce cas (c'est le bon libellé côté
       1xBet) — seule la traduction pour CE bookmaker manque. Corriger avec :
       ```bash
       ./venv/bin/python3 Functions/Logs/review_failed_bets.py label \
         --bookmaker <Stake|Lollybet|Betclic|Winamax> --sport <sport_id> \
         --standard "<selection pivot exacte>" --target "<texte réel, cité depuis candidates>"
       ```
       Ne JAMAIS deviner `--target` : le prendre dans les `candidates` réels
       affichés par `show`, ou dans un HTML/capture que Steeven fournit.
       1xBet n'utilise PAS cette table (il n'appelle pas `get_label`) — ne
       jamais proposer `label` pour un échec 1xBet.

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

## Ce que ce skill ne fait PAS

- Pas de correction automatique en masse : chaque cas est discuté avant
  toute modification de code ou d'entrée dans `bet_labels.db`.
- Ne touche jamais aux paris déjà engagés/placés avec succès — uniquement
  ceux dont la dernière tentative connue est un échec.
- Ne propose jamais `label` (table `bet_labels.db`) pour un échec 1xBet —
  ce bookmaker n'appelle pas `get_label()`, il faut corriger le prompt
  d'extraction à la place (cf. section 3 ci-dessus).
