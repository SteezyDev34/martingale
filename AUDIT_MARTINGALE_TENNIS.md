# Audit technique — Bot de paris martingale tennis (`mrtingal`)

Date de l'audit : 2026-07-27

## 0. Constat préliminaire capital : deux architectures coexistent, une seule est réellement active

Le dépôt contient **deux implémentations parallèles et non connectées** de la même stratégie :

1. **L'architecture OOP moderne** (`main.py`, `core/engine.py`, `core/martingale/base.py`, `core/surveillance/surveillance_matchs.py`, `core/file_paris/file_paris.py`, `core/config/config_manager.py`, `core/martingale/martingale_300.py`, etc.) — orientée objet, avec docstrings soignées, gestion async, abstraction `Martingale(ABC)`.
2. **L'architecture procédurale historique**, pilotée par un module d'état global unique `config.py` (689 lignes de variables globales mutables) et une boucle `Functions_431a.all_script(driver)` / `Functions_15V1.all_script(driver)` appelée depuis les scripts `SCRIPTS 15V1/15V1-1.py`, `SCRIPTS 15V2/15V2-1.py`, `SCRIPTS 1530A_V2/1530A_V2-1.py`.

**Preuve que l'architecture OOP est morte/non fonctionnelle** :
- `main.py:13-21` importe `core.config.config_manager`, `core.martingale.martingale_300`, `core.martingale.martingale_15a`, `core.martingale.martingale_30a`, `core.notification.notification_manager`, `core.interface.interface_utilisateur` — mais `core/martingale/` ne contient **aucun** fichier `martingale_300.py`, `martingale_15a.py`, ni `martingale_30a.py` (seulement `all_script_v2.py`, `base.py`, `match_manager.py`, `script_types.py`). `main.py` est donc **cassé et n'a jamais tourné dans cet état** (`ImportError` garanti dès le premier import).
- `core/martingale/base.py:674-750` (`_get_bet_new`) et `_get_bet_old` sont des stubs qui `return False` (« Méthode get_bet en cours d'implémentation », ligne 741) — jamais terminés.
- `core/surveillance/surveillance_matchs.py:109-125` (`obtenir_donnees_match`) simule un appel API avec `asyncio.sleep(0.5)` et retourne les données déjà en cache — **aucune intégration réelle avec un bookmaker ou Sofascore**. C'est un squelette de démonstration.

Le vrai bot en production est donc le flux procédural : `SCRIPTS */-1.py` → `Functions_431a.py` / `Functions_15V1.py` → `config.py` (état global) → `Functions/*` (Selenium) → `Functions/RedisIPC.py` (persistance inter-process).

Il existe en plus un **troisième sous-système** indépendant : `Functions/Bookmakers/router.py` (multi-bookmaker Winamax/Betclic/Lollybet/Stake via Playwright, comparaison de cotes, détection de défis par IA) qui ne partage aucun code avec le moteur tennis martingale — un produit distinct logé dans le même dépôt.

**Recommandation prioritaire** : documenter clairement (README/CLAUDE.md) que `core/` (hors `RedisIPC` et parties réutilisées) et `main.py` sont du code mort/prototype, pour éviter qu'un futur audit ou qu'un contributeur perde du temps à le faire fonctionner ou à le lire comme référence.

---

## 1. Architecture générale (flux réellement actif)

```
SCRIPTS 15V1/15V1-1.py (point d'entrée process)
  └─ config.scriptType/script_num déduits du nom de fichier
  └─ ChromeDriver/SetDriver.get_script_driver()  → attache Selenium à Chrome (remote debugging)
  └─ boucle "while config.win < 100":
       └─ Functions_15V1.all_script(driver)  [ou Functions_431a.all_script pour 4315A]
            ├─ Functions/ScriptRechercheDeMatch.rechercheDeMatch  (trouve un match tennis live)
            ├─ Functions/GetPlayersName, GetLigueName
            ├─ Functions/Managers/MatchManager (SQLite: matches_todo → lien Sofascore)
            ├─ ouverture d'un onglet Sofascore séparé (driver.switch_to.new_window)
            ├─ pour chaque scriptType (15A/30A/40A/15V1/15V2/…) :
            │     config.switchScript(st) → recharge l'état global depuis ScriptConfig/Redis
            │     Functions/GetJsonData.getGlobalPerte / get1setGlobalPerte / DispatchPerte
            │     Functions/FisrtGameBet.FirstGameBet → Functions/AfficherParis, Functions/GetBet, Functions/PlacerMise, Functions/ValidationDuParis
            ├─ boucle principale "while not config.error":
            │     Functions/GetJeuActuel, GetSetActuel, GetScoreActuel (score, mis en cache dans config.saved_score / config.all_scores)
            │     Functions/GetAndPlaceBet (place le pari du prochain jeu)
            │     Functions/GetResult (WIN/LOSE/RUN)
            │     Functions/RedisIPC (persistance perte/gain/running, IPC multi-fenêtres)
            └─ fin de match : DeleteBet, RedisIPC.reset_gain, match_manager.remove_match
```

Le "cerveau" de l'état est **`config.py`**, un module global partagé par lecture/écriture directe (`config.mise`, `config.perte`, `config.validated_bet`, `config.score_actuel`, `config.classes`, etc.), pattern singleton implicite. `config.switchScript(script_type)` fait office de context-switch : il sauvegarde/restaure les variables globales pour simuler plusieurs martingales concurrentes (15A, 30A, 40A, 15V1, 15V2…) **dans un seul process/thread séquentiel**, pas en parallèle réel.

---

## 2. Couplage, duplication, dette technique

- **Duplication de la boucle principale** : `Functions_431a.py` (543 lignes) et `Functions_15V1.py` (779 lignes) contiennent quasiment le même corps de boucle (comparaison `config.global_match_win[st] >= config.total_want_win[st]`, gestion RUN/WIN/LOSE, `RedisIPC.set_running`, etc.) copié-collé avec de légères variantes (`Functions_431a.py:70-115` vs `Functions_15V1.py:134-180`). Toute correction de bug doit être répliquée manuellement dans les deux fichiers (`15V2` a probablement un troisième exemplaire — non lu intégralement mais nommé de façon identique).
- **`core/martingale/base.py`, `core/martingale/script_types.py` et `core/martingale/all_script_v2.py`** réimplémentent une troisième fois la même logique (`FirstGameBet`, `get_bet`, `placer_mise`, `validation_du_paris`) en version « propre » orientée objet, mais **inachevée** (`_get_bet_new` retourne `False`, `script_types.py` `BaseScript.contexte_actif` appelle `config.switchScript` — donc dépend quand même de l'état global procédural, ce n'est pas une vraie isolation OOP).
- **Couplage fort à `config` global** : quasiment toutes les fonctions (`ModalHandler`, `ValidationDuParis`, `GetScoreActuel`, `GetAndPlaceBet`…) lisent/écrivent `config.<attr>` sans passage de paramètres explicite. Cela rend le code non thread-safe par nature (variables partagées mutables, aucun verrou) et impossible à paralléliser proprement sans réécriture (cf. §6 concurrence).
- **Bug avéré** dans `Functions/GetGainFromCapital.py:6` : `print(f"Avec un capital de {capital}€ ...")` référence la variable globale `capital` (définie seulement dans le bloc `if __name__ == '__main__'`, ligne 34) au lieu du paramètre `solde_initial` de la fonction. Appelé depuis un autre module, ceci lève un `NameError`. Fonction visiblement non testée hors exécution directe.

---

## 3. Logique métier par marché

| Script | Détection du score déclencheur | Fichier/ligne |
|---|---|---|
| `40A` (jeu à 40-40) | Attente que `score_actuel` sorte de `["40:40","A:40","40:A"]` pour le 1er pari | `core/martingale/base.py:887` |
| `30A` | Scores valides `["0:0","0:15","15:0","15:15"]` (`base.py:876`), sinon `next_bet=True` et `looking_game+1` |
| `15A` / `300` / `030` / etc. | Uniquement `"0:0"` accepté comme 1er jeu (`base.py:882`) |
| `15V1` / `15V2` | Traités à part partout dans le code (conditions spéciales dans `ValidationDuParis.py:130`, `ModalHandler.py:25-26`, `GetScoreActuel.py:126`, `GetAndPlaceBet.py:51-54`) — ce sont les scripts « point par point », avec des tolérances de tentatives réduites (`attempt=2` au lieu de 3, `atempts=1` au lieu de 2) et une logique de `looking_point`/`numero_point` dédiée (`GetScoreActuel.py:162-197`, fonction `get_numero_point`). |
| Tie-break (jeu 12/13) | Gérée explicitement dans `Functions_431a.py:357-386` : boucles d'attente sur les scores `"0:1"/"1:0"/"1:1"/"2:0"/"0:2"`, mais logique dupliquée deux fois presque identique dans le même fichier (357-367 et 368-386) — code à factoriser, risque de divergence si un correctif n'est appliqué qu'à un des deux blocs. |

**Cas limites NON gérés identifiés** :
- **Walkover / abandon / retrait de joueur** : aucune recherche de texte "retired"/"w.o."/"abandon" trouvée — `GetIfMatchPage(driver)` semble seulement vérifier que la page match est toujours affichée, pas le statut du match. Un abandon en cours de martingale pourrait bloquer le bot dans une boucle d'attente de score qui ne changera jamais.
- **Changement de serveur en cours de jeu** : le code déduit le jeu courant en additionnant les jeux des deux joueurs (`base.py:1152,1169`), robuste au serveur mais pas aux corrections de score.
- **Score corrigé par l'arbitre / point rejoué** : `get_vainqueur_point_precedent` (`GetScoreActuel.py:200-249`) suppose une progression monotone point par point ; une correction de score (score qui recule) n'est pas détectée et fausserait `numero_point`/`vainqueur_point`.
- **Jeu décisif à 10 points (double)** : logique de tie-break câblée en dur sur jeu 12/13, pas paramétrée par format de match.

---

## 4. Gestion des états de match et risques de désynchronisation

- **Bug identifié dans la détection de changement de score** — `Functions/GetScoreActuel.py:71-132` :
```python
if config.saved_score != config.score_actuel:
    if not first:
        first = False
        record_scores(driver)
    else:
        first = False
        if config.scriptType not in ['15V1', '15V2']:
            time.sleep(2)
        continue
```
`first` est initialisé à `True` en haut de la fonction (ligne 75) et n'est jamais remis à `False` avant ce bloc, donc la branche `if not first` (qui appelle `record_scores`) n'est **jamais atteinte au premier passage** — elle ne s'exécute qu'à partir du second changement de score détecté dans la même invocation de boucle. Source plausible de désynchronisation entre `config.all_scores` (historique utilisé pour compter les cycles de deuce) et le score réel affiché. **À vérifier/corriger en priorité.**

- **Mécanisme Sofascore — DÉSACTIVÉ** : `GetScoreActuel.py:77` :
```python
config.score_actuel = False #GetSofaScoreActuel(driver)
```
`GetSofaScoreActuel(driver)` existe (lignes 18-69), ouvre bien l'onglet Sofascore déjà créé (`Functions_15V1.py:73-107`) et sait parser le score — mais **elle n'est jamais appelée** : le bot lit systématiquement le score depuis le DOM du bookmaker uniquement, malgré la latence de 10s mentionnée. La fenêtre Sofascore est ouverte pour rien dans le flux actif. **Écart majeur entre l'intention métier et le code réellement exécuté.**

- **Concurrence multi-process** : chaque script (`15V1-1.py`, `15V2-1.py`, `1530A_V2-1.py`) est un **process Python séparé**, chacun avec son propre driver Selenium sur sa propre fenêtre Chrome, communiquant via `Functions/RedisIPC.py`. Pas de vrai multithreading dans un même process. La donnée partagée transite par SQLite (`Functions/RedisIPC.py` : Redis est **désactivé de force**, ligne 109-111 `get_redis_client()` retourne toujours `None`) via un fichier unique (`redis_fallback.sqlite`), connexions ouvertes/fermées à chaque appel, sans pool. Sous forte fréquence concurrente, risque de `sqlite3.OperationalError: database is locked` transitoire, non catché spécifiquement.

---

## 5. Mises, martingale, garde-fous 15V1/15V2

- **Formule de mise** (`base.py:479-488`) : `mise = (wantwin + perte) / (cote - 1)`, arrondie, plancher à `0.2`. `misemax` est lu depuis le site (`_get_mise_max`) mais **n'est jamais comparé/appliqué** pour plafonner la mise calculée — **aucun plafond dur** préventif, seulement un traitement réactif après rejet (ModalHandler détectant "Maximum").
- **Garde-fou 15V1/15V2** : `attempt`/`atempts` réduits pour aller plus vite — cohérent avec l'objectif de récupération partielle rapide. **Mais** le calcul de mise reste la **même formule martingale de récupération complète**, sans logique visible de plafonnement spécifique "récupère seulement une fraction". **Risque réel** : si 15V1/15V2 tournent en parallèle des autres scripts sur le même match, le total misé peut **s'additionner** au lieu de se compenser, contrairement à l'intention déclarée.
- **Incohérence de granularité identifiée** : `RedisIPC.get_total_loss()` fait la somme de toutes les pertes **tous scripts confondus, tous matchs confondus** (`RedisIPC.py:829-846`) alors que `get_total_gain(newmatch)` est filtré par match — un gain sur le match A peut être comparé à une perte cumulée globale, faussant le solde en cas de matchs multiples en parallèle.
- **`deduct_largest()`** (`RedisIPC.py:485-526`) déduit forfaitairement 50% de la perte la plus importante — un simple transfert comptable entre scripts, pas une réduction réelle du risque.

---

## 6. Robustesse générale

184 `except:` nus + 331 `except Exception:` génériques dans le dépôt. Exemples typiques :
- `ModalHandler.py` catche silencieusement toute exception Selenium et loggue un warning générique — impossible de distinguer un vrai bug d'une absence normale de popup. De plus, les blocs "NOTIF QUESTION"/"NOTIF ALERT" sont dupliqués presque à l'identique (lignes 74-111 et 112-158).
- `RedisIPC.py` catche `except Exception` partout et renvoie une valeur par défaut — un bug SQLite pourrait être masqué comme "valeur absente", menant le moteur à repartir de `perte=0` alors que la vraie perte existe en base.
- `Functions_431a.py:66-69` catch-all générique qui masque la ligne d'origine de l'erreur, contrairement à `15V1-1.py:75-86` qui extrait bien `traceback.extract_tb` (bonne pratique non généralisée).

**Loader de validation** (`ValidationDuParis.py:216-236`) : attente bloquante du `preloader` en boucle `while`. **Aucun thread parallèle ne surveille le score pendant ce temps** dans le même process — attente strictement séquentielle. `QuickValidationDuParis` réduit le timeout (5s→1s) mais reste synchrone par construction.

**Sélecteurs DOM** : centralisés dans `config.classes[<clé>][site_type]`, avec fallback silencieux vers `''` en cas de clé manquante → exception Selenium peu claire plutôt qu'un message explicite.

---

## 7. Synchronisation Sofascore / latence

Le mécanisme Sofascore existe mais est désactivé, et même actif il n'aurait jamais été asynchrone (lecture DOM synchrone, pas de WebSocket). **Architecture cible recommandée** — producteur/consommateur :

- Un thread **ScoreWatcher** qui poll l'API interne Sofascore (HTTP direct, pas Selenium) à haute fréquence, pousse chaque changement dans une `queue.Queue` thread-safe horodatée.
- Un thread **BookmakerWatcher** qui fait pareil côté DOM bookmaker (Selenium), horodaté séparément.
- Un composant de **réconciliation** : Sofascore peut préparer/anticiper la navigation vers le bon marché, mais **la validation/mise ne doit jamais partir sur la seule foi de Sofascore** — toujours attendre la confirmation croisée par le DOM bookmaker (ou un timeout de sécurité qui retombe sur le DOM seul). Cela répond exactement à la contrainte de continuer à surveiller pendant le loader : le ScoreWatcher continue de tourner et rattrape son retard dès que le thread de décision se libère.
- Un seul thread doit piloter un driver Selenium donné (Selenium n'est pas thread-safe), mais rien n'empêche qu'il consomme une queue alimentée en parallèle.

---

## 8. Recommandations priorisées

**Quick wins** :
1. Corriger le bug `first` dans `GetScoreActuel.py:75-128` qui empêche `record_scores` d'être appelé au premier changement de score.
2. Corriger `GetGainFromCapital.py:6` (`capital` → `solde_initial`) et décider si la fonction doit être branchée au calcul réel de plafond de mise.
3. Décider du sort du chemin mort Sofascore (`GetScoreActuel.py:77`) : soit le réactiver et le fiabiliser, soit supprimer l'ouverture d'onglet inutile (`Functions_15V1.py:64-116`).
4. Uniformiser `RedisIPC.get_total_loss()` pour qu'elle soit filtrée par match comme `get_total_gain()`.
5. Remplacer les `except:`/`except Exception:` critiques (`RedisIPC.py`, `ModalHandler.py`) par des exceptions spécifiques (`sqlite3.OperationalError`, `TimeoutException`/`NoSuchElementException`/`StaleElementReferenceException`).
6. Factoriser les deux blocs de tie-break dupliqués dans `Functions_431a.py:357-386`.

**Refactors profonds** :
7. Trancher le sort de `main.py`/`core/` (terminer la réécriture OOP ou la retirer — actuellement `main.py` ne peut pas s'exécuter, `ImportError` garanti).
8. Fusionner la logique dupliquée entre `Functions_431a.py`/`Functions_15V1.py` (et probablement `15V2`) en une seule fonction paramétrée.
9. Implémenter l'architecture producteur/consommateur Sofascore/bookmaker décrite en §7, avec réconciliation stricte avant toute action irréversible.
10. Appliquer réellement un plafond dur (mise max/perte max/capital engagé) en utilisant `misemax` déjà récupéré mais non exploité.
11. Clarifier et implémenter une vraie logique de plafonnement partiel pour 15V1/15V2 en tant que garde-fou (au-delà du simple nombre de tentatives réduit).

---

## Point le plus important à trancher

**Le mécanisme Sofascore décrit comme actif est en réalité désactivé dans le code** (`GetScoreActuel.py:77`) — le bot ne lit que le score du bookmaker aujourd'hui, malgré la fenêtre Sofascore ouverte pour chaque match.
