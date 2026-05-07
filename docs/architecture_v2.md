# Architecture V2 — Système de Martingale Refactorisé

## Vue d'ensemble

L'architecture V2 remplace les fonctions monolithiques `Functions_15V1.py` et
`Functions_431a.py` (~600 lignes chacune) par un système orienté objet structuré
en trois couches :

```
SCRIPTS 1530A_V2/1530A_V2-1.py     ← script de lancement
        │
        └── core/martingale/all_script_v2.py   ← boucle principale découpée
                │
                └── core/martingale/script_types.py  ← BaseScript + sous-classes + ScriptFactory
                        │
                        └── Functions/RedisIPC.py    ← état cross-script via Redis
```

**Principe fondamental** : aucun fichier existant (`config.py`, `Functions_15V1.py`,
`Functions_431a.py`) n'a été modifié. Tout est additionnel.

---

## Problèmes de l'ancien système

| Problème | Ancien code | Solution V2 |
|---|---|---|
| État partagé | 25 variables globales dans `config.*` mutées à chaque `switchScript()` | Redis Hash isolé par script |
| Code dupliqué | Bloc `all_below_one` répété 4× | `tous_objectifs_atteints()` |
| Couplage fort | `for scriptType in config.scriptTypeList:` avec logique inline | `for script in scripts:` avec méthodes encapsulées |
| Bug silencieux | `allfirstgamebet: False` (annotation Python, pas affectation) | `_placer_premier_pari_tous()` |
| Boucle monolithique | 600 lignes dans une seule fonction `all_script()` | 7 fonctions découpées |
| Ajout d'un script | Copier-coller + adapter dans toute la fonction | Hériter de `BaseScript` + 2 méthodes |

---

## Fichiers créés

```
core/
└── martingale/
    ├── __init__.py
    ├── script_types.py     ← BaseScript, 10 sous-classes, ScriptFactory
    └── all_script_v2.py    ← boucle principale refactorisée

SCRIPTS 1530A_V2/
└── 1530A_V2-1.py           ← script de lancement (15A + 30A + 300)

Functions/
└── RedisIPC.py             ← IPC Redis enrichi (set_data, get_data, pipeline)

docs/
├── architecture_v2.md      ← ce fichier
└── redis_ipc.md            ← référence Redis détaillée
```

---

## `core/martingale/script_types.py`

### Hiérarchie des classes

```
BaseScript (ABC)
├── Script300
├── Script015
├── Script150
├── Script15A
├── Script30A
├── Script40A
├── Script15V1
├── Script15V2
├── Script1SET
└── ScriptBREAK

ScriptFactory
```

---

### `BaseScript` — classe abstraite

Chaque instance porte :

```python
self.driver       # Instance Selenium
self.script_type  # ex: '15A'
self.gain_match   # float — gain cumulé sur le match
self.nb_victoires # int   — paris gagnés sur le match
```

#### Méthodes abstraites (à implémenter dans chaque sous-classe)

| Méthode | Rôle |
|---|---|
| `get_script_name() → str` | Nom lisible pour les logs (ex: `"Script 15A"`) |
| `is_valid_score(score) → bool` | Score de déclenchement (ex: `score == "0:0"`) |

#### `_CHAMPS_CONFIG` — source de vérité unique

Tuple de classe qui liste les 15 champs de `config` gérés par Redis.
`activer()` et `desactiver()` itèrent dessus. Pour ajouter un nouveau champ
à persister, il suffit de l'ajouter ici :

```python
_CHAMPS_CONFIG: tuple[tuple[str, type], ...] = (
    ("mise",           float),
    ("perte",          float),
    ("wantwin",        float),
    ("increment",      float),
    ("gain",           float),
    ("netprofit",      float),
    ("cote",           float),
    ("rattrape_perte", int),
    ("looking_game",   int),
    ("placed_game",    int),
    ("saved_score",    str),
    ("win_type",       str),
    ("result",         str),
    ("error",          bool),
    ("validated_bet",  dict),
)
```

#### `activer()` — remplace `config.switchScript(scriptType)`

```
activer('15A')
│
├── Ping Redis : get_data('mise', '15A')
│     │
│     ├── Redis disponible → charge les 15 champs dans config.*
│     │     champ absent   → skip (garde valeur actuelle de config)
│     │     cast bool      → str.lower() == "true"
│     │     cast dict      → vérifie isinstance, sinon {}
│     │     cast int/float → cast() avec except silencieux
│     │
│     └── Redis down → config.switchScript('15A')  (fallback)
│
└── config.scriptType = '15A'
```

#### `desactiver()` — remplace `config.save_variables()`

```
desactiver('15A')
│
├── get_redis_client()
│     │
│     ├── None → config.save_variables()  (fallback)
│     │
│     └── Disponible :
│           Construit mapping { 'mise': '0.5', ... }  ← 1 passe sur _CHAMPS_CONFIG
│           dict/list → json.dumps()
│           autre     → str()
│
│           pipeline(transaction=False)
│             HSET ETAT_15A mapping       ← 15 champs en 1 commande
│             SET  PERTE_15A <perte>      ← rétrocompatibilité
│           pipe.execute()               ← 1 seul aller-retour réseau
│
└── Exception → config.save_variables()  (fallback)
```

**Pourquoi `transaction=False`** : pas besoin de `MULTI/EXEC`, on évite le surcoût
du verrou serveur tout en groupant les commandes en un seul paquet réseau.
Résultat : ~15× moins d'allers-retours vs 15 `HSET` séparés.

#### `contexte_actif()` — gestionnaire de contexte alternatif

```python
with script.contexte_actif():
    # config.scriptType == self.script_type ici
    ...
```

Appelle `config.switchScript()` classique. Utile pour les blocs ponctuels
n'utilisant pas le cycle `activer()/desactiver()`.

#### `a_atteint_objectif() → bool`

```python
float(config.global_match_win[script_type]) >= float(config.total_want_win[script_type])
```

#### `tous_objectifs_atteints(script_list) → bool`

```python
all(s.a_atteint_objectif() for s in script_list)
```

Remplace le bloc `all_below_one` répété 4× dans l'ancien code.

#### `preparer_premier_pari() → bool`

Encapsule la logique `FirstGameBet` avec :
- `GetJeuActuel()`
- Validation du score via `is_valid_score()`
- 3 tentatives max
- `looking_game` mis à jour si score invalide

#### `gerer_resultat(resultat)` — dispatcher WIN/LOSE

```python
script.gerer_resultat('WIN')   # → _traiter_victoire()
script.gerer_resultat('LOSE')  # → _traiter_defaite()
```

`_traiter_victoire()` :
1. Met à jour `config.global_match_win[script_type]` + `config.winmatch`
2. `config.init_variable()`
3. Si objectif non atteint → recharge la mise (`getGlobalPerte()`)
4. Si objectif atteint → `ScriptConfig.reset()` + log `FIN`

`_traiter_defaite()` :
1. `ScriptConfig.reset()`
2. `DispatchPerte()`
3. `config.init_variable()`

---

### Sous-classes — scores de déclenchement

| Classe | `script_type` | `is_valid_score()` |
|---|---|---|
| `Script300` | `'300'` | `score == "0:0"` |
| `Script015` | `'015'` | `score == "0:0"` |
| `Script150` | `'150'` | `score == "0:0"` |
| `Script15A` | `'15A'` | `score == "0:0"` |
| `Script30A` | `'30A'` | `score in {"0:0", "0:15", "15:0", "15:15"}` |
| `Script40A` | `'40A'` | `score in {"0:0", "0:15", ..., "15:30"}` (8 scores) |
| `Script15V1` | `'15V1'` | `score == "0:0"` |
| `Script15V2` | `'15V2'` | `score == "0:0"` |
| `Script1SET` | `'1SET'` | `score == "0:0"` |
| `ScriptBREAK` | `'BREAK'` | `score == "0:0"` |

---

### `ScriptFactory`

#### Registre interne

```python
_CLASSES: dict = {
    '300':   Script300,
    '015':   Script015,
    '150':   Script150,
    '15A':   Script15A,
    '30A':   Script30A,
    '40A':   Script40A,
    '15V1':  Script15V1,
    '15V2':  Script15V2,
    '1SET':  Script1SET,
    'BREAK': ScriptBREAK,
}
```

Pour ajouter un nouveau type : hériter de `BaseScript`, implémenter les 2 méthodes
abstraites, puis ajouter une entrée dans `_CLASSES`. C'est tout.

#### `create_script(script_type, driver) → BaseScript`

Retourne une instance concrète. Lève `ValueError` si le type n'est pas enregistré.

#### `create_scripts(script_type_list, driver) → list[BaseScript]`

Point d'entrée principal. Remplace la boucle de configuration dans `all_script()` :

```python
# Avant
for scriptType in config.scriptTypeList:
    config.switchScript(scriptType)
    # ... logique inline sur 100 lignes

# Après
scripts = ScriptFactory.create_scripts(config.scriptTypeList, driver)
for script in scripts:
    script.activer()
    ...
    script.desactiver()
```

---

## `core/martingale/all_script_v2.py`

### Découpage de `all_script()` en 7 fonctions

```
all_script_v2(driver)
│
├── Étape 1 — rechercheDeMatch()
├── Étape 2 — init contexte match (ligue, teams, match_manager)
├── Étape 3 — ScriptFactory.create_scripts(config.scriptTypeList, driver)
├── Étape 4 — _initialiser_mises(scripts)
├── Étape 5 — _placer_premier_pari_tous(scripts, driver)
├── Étape 6 — _boucle_principale(scripts, driver)
└── Étape 7 — _nettoyer_fin_match(scripts, driver)
```

---

### `_initialiser_mises(scripts)`

Récupère les mises initiales pour chaque script :

```
pour chaque script :
    script.activer()
    ScriptConfig(script_type).reset()
    config.init_variable()

    si config.perte == 0 :
        → RedisIPC.get_loss()   ← tentative rapide
        → getGlobalPerte()      ← fallback API
    si toujours 0 :
        → get1setGlobalPerte()

    script.desactiver()
```

---

### `_placer_premier_pari_tous(scripts, driver)`

Boucle `while not tous_prets` :
- Pour chaque script → `activer()` → vérif objectif → `preparer_premier_pari()` → `desactiver()`
- Si un premier pari échoue → recommence toute la boucle
- Retourne `True` quand tous sont prêts

---

### `_boucle_principale(scripts, driver)`

Remplace le `while not config.error:` monolithique. Variables internes :

```python
passageset = False   # True quand un passage de set vient d'être détecté
firstjeu   = True    # True au début de chaque jeu
current_game = int(config.jeu_actuel)
```

**Séquence par itération** :

```
GetJeuActuel()
│
├── passageset == True
│     → GetSetActuel()
│     → si perte > 0 : dispatch + _placer_premier_pari_tous()
│     → sinon : DispatchPerte() + log erreur
│
├── config.newset == jeu_actuel (nouveau set)
│     → DeleteBet()
│
├── firstjeu ou jeu_actuel changé
│     → sleep(2), firstjeu = False, continue
│
└── Pour chaque script :
      script.activer()
      │
      ├── tous objectifs atteints → return True
      ├── ce script atteint → continue
      ├── jeu_actuel == 13 → _gerer_tie_break()
      ├── jeu_actuel == 12 → gestion tie-break prochain jeu
      │
      ├── GetAndPlaceBet()
      │
      ├── résultat == 'WIN'
      │     → script.gerer_resultat('WIN')
      │     → même jeu en cours → ValidationDuParis()
      │     → sinon → FirstGameBet(), firstjeu = True
      │
      ├── résultat == 'LOSE'
      │     → même jeu → ValidationDuParis() × 2 tentatives
      │     → sinon → script.gerer_resultat('LOSE'), FirstGameBet()
      │
      └── script.desactiver()
```

---

### `_gerer_tie_break(driver)`

```
Attente score ∈ {"0:1", "1:0", "1:1", "2:0", "0:2"} (début tie-break)
→ GetIfGameEnd()  (attente fin tie-break)
```

---

### `_nettoyer_fin_match(scripts, driver)`

```
Pour chaque script :
    script.activer()
    DispatchPerte()
    ScriptConfig.reset()
    init_variable()
    global_match_win[st] = 0.0
    winmatch[st] = 0
    script.desactiver()

config.all_scores = {}
match_manager.remove_match()
script_manager.stop_script()
DeleteBet()
```

---

### `_tous_objectifs_atteints(scripts)` et `_log_tous_objectifs(scripts)`

Fonctions utilitaires module-level (non membres de classe) :

```python
def _tous_objectifs_atteints(scripts):
    return all(s.a_atteint_objectif() for s in scripts)

def _log_tous_objectifs(scripts):
    for s in scripts:
        config.log(f'{s.script_type} Net profit: ...')
```

---

## `SCRIPTS 1530A_V2/1530A_V2-1.py` — Script de lancement

### Détection automatique du type et numéro

Le nom du fichier est parsé automatiquement :

```
1530A_V2-1.py
    │    │  └── extension ignorée
    │    └───── script_num = 1
    └────────── scriptType = '1530A_V2'
```

```python
config.localhost = int(''.join(c for c in '1530A_V21' if c.isdigit()))
# → 15301  (si < 1024, +1024 appliqué)
```

### Configuration des stratégies

```python
# ← modifier ici pour changer les stratégies jouées
STRATEGIES_ACTIVES = ['15A', '30A', '300']
```

La liste est directement assignée à `config.scriptTypeList`.

### Classement des matchs (optionnel)

Au démarrage, deux options :
- `1` → `classementeDeMatch(driver)` (rapide)
- `2` → `newclassementeDeMatch()` + `classementeDeMatch()` (complet)

### Boucle principale

```python
while config.win < 100:
    try:
        all_script_v2(driver)

    except KeyboardInterrupt:
        break  # Ctrl+C propre

    except Exception as e:
        # Log avec fichier + ligne + fonction + traceback complet
        config.log(f"ERREUR : {e} | Fichier : ... | Ligne : ...", 'error')

    else:
        # Après chaque match réussi :
        DispatchPerte()  # pertes résiduelles
        for st in config.scriptTypeList:
            config.switchScript(st)
            config.ScriptConfig(st).reset()
            config.init_variable()
            DispatchPerte()
            config.global_match_win[st] = 0.0
            config.winmatch[st] = 0

    # Retour page tennis pour le prochain match
    driver.get(config.site_url)
```

---

## Flux complet d'un match

```
1530A_V2-1.py
│
└── while config.win < 100:
        │
        └── all_script_v2(driver)
                │
                ├── rechercheDeMatch()        # trouve un match 1xBet
                │
                ├── init match                # URL, ligue, équipes
                │
                ├── ScriptFactory             # crée Script15A, Script30A, Script300
                │
                ├── _initialiser_mises()
                │     ├── Redis.get_loss()   ← rapide
                │     └── getGlobalPerte()   ← fallback API
                │
                ├── _placer_premier_pari_tous()
                │     └── FirstGameBet() pour chaque script
                │
                ├── _boucle_principale()
                │     └── pour chaque jeu :
                │           pour chaque script :
                │             activer()           ← Redis → config
                │             GetAndPlaceBet()
                │             gerer_resultat()
                │             desactiver()        ← config → Redis (pipeline)
                │
                └── _nettoyer_fin_match()
                      └── reset + dispatch + DeleteBet()
```

---

## Ajouter un nouveau type de script

**3 étapes, aucun fichier existant à modifier :**

**1.** Créer la sous-classe dans `script_types.py` :

```python
class ScriptQT(BaseScript):
    """Stratégie QT — description."""

    def __init__(self, driver, config_manager=None) -> None:
        super().__init__(driver, 'QT')

    def get_script_name(self) -> str:
        return "Script QT"

    def is_valid_score(self, score: str) -> bool:
        return score == "0:0"
```

**2.** L'enregistrer dans `ScriptFactory._CLASSES` :

```python
_CLASSES: dict = {
    ...
    'QT': ScriptQT,  # ← ajout
}
```

**3.** L'utiliser dans le script de lancement :

```python
STRATEGIES_ACTIVES = ['15A', '30A', 'QT']
```

---

## Compatibilité avec l'ancien système

L'architecture V2 est **100% additive** :

- `config.py` → non modifié
- `Functions_15V1.py` → non modifié
- `Functions_431a.py` → non modifié
- `Functions_456P.py` → non modifié

Les anciens scripts (`SCRIPTS 15V1/`, `SCRIPTS 31A/`, etc.) continuent de
fonctionner exactement comme avant. Seuls les scripts dans `SCRIPTS 1530A_V2/`
utilisent la nouvelle architecture.

Les clés Redis `PERTE_<SCRIPT>` sont maintenues en synchronisation dans
`desactiver()` → `DispatchPerte()` et `getGlobalPerte()` continuent de
fonctionner normalement depuis les anciens scripts.

---

## Dépendances et imports

```python
# script_types.py
from abc import ABC, abstractmethod
from contextlib import contextmanager
import config
from Functions.FisrtGameBet import FirstGameBet
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetJsonData import DispatchPerte, getGlobalPerte, get1setGlobalPerte
from Functions import RedisIPC

# all_script_v2.py
from core.martingale.script_types import ScriptFactory, BaseScript
# + tous les imports Functions existants (inchangés)
```

Aucune dépendance externe nouvelle hormis `redis` (déjà dans `requirements.txt`).
