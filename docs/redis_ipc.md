# Redis IPC — Architecture et référence technique

## Pourquoi Redis ?

Le bot fait tourner plusieurs scripts Python **en parallèle** (ex : `15A`, `30A`, `300` dans la même session). Chaque script doit :

- lire et écrire son propre état sans écraser celui des autres
- partager les pertes entre processus (cross-script)
- être aussi rapide que possible (Selenium est déjà le vrai goulot)

**Redis répond à ces trois besoins** :

| Besoin | Solution Redis |
|---|---|
| État isolé par script | Hash `ETAT_<SCRIPT>` |
| Pertes cross-script | Clé string `PERTE_<SCRIPT>` |
| Rapidité | ~0.1 ms/opération en mémoire |
| Pas de race condition | Écriture atomique via pipeline |

---

## Schéma des clés

```
ETAT_15A        → Hash  { mise, perte, wantwin, ... }
ETAT_30A        → Hash  { mise, perte, wantwin, ... }
ETAT_300        → Hash  { mise, perte, wantwin, ... }

PERTE_15A       → String  "12.5"
PERTE_30A       → String  "0.0"
PERTE_300       → String  "7.2"
```

### Champs du Hash `ETAT_<SCRIPT>`

| Champ | Type Python | Exemple |
|---|---|---|
| `mise` | `float` | `"0.5"` |
| `perte` | `float` | `"12.5"` |
| `wantwin` | `float` | `"10.0"` |
| `increment` | `float` | `"1.5"` |
| `gain` | `float` | `"3.2"` |
| `netprofit` | `float` | `"-2.1"` |
| `cote` | `float` | `"1.75"` |
| `rattrape_perte` | `int` | `"3"` |
| `looking_game` | `int` | `"4"` |
| `placed_game` | `int` | `"2"` |
| `saved_score` | `str` | `"15:0"` |
| `win_type` | `str` | `"WIN"` |
| `result` | `str` | `"WIN"` |
| `error` | `bool` → `"true"/"false"` | `"false"` |
| `validated_bet` | `dict` → JSON | `'{"jeu": 3, ...}'` |

> Toutes les valeurs sont stockées en **string** dans Redis (c'est le seul type disponible pour les champs de Hash). Le cast automatique est fait à la lecture.

---

## Configuration de la connexion

Via variables d'environnement :

```bash
# Option 1 — socket Unix (plus rapide, même machine)
export REDIS_UNIX_SOCKET=/tmp/redis.sock

# Option 2 — TCP (par défaut)
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

Le socket Unix évite la couche TCP/IP → **latence encore plus basse** sur macOS/Linux.

Le client est un **singleton** : il est créé une seule fois au premier appel de `get_redis_client()` et réutilisé pour toute la durée du processus.

---

## API publique — `Functions/RedisIPC.py`

### `set_data(champ, valeur, script_type)` → `bool`

Écrit un champ dans `ETAT_<SCRIPT_TYPE>`.

```python
from Functions import RedisIPC

RedisIPC.set_data('mise', 0.5, '15A')       # HSET ETAT_15A mise 0.5
RedisIPC.set_data('validated_bet', {'jeu': 3}, '15A')  # dict → JSON automatique
RedisIPC.set_data('mise', None, '15A')      # supprime le champ (HDEL)
```

- `dict` et `list` sont sérialisés en JSON automatiquement
- Retourne `False` si Redis est indisponible (ne lève pas d'exception)

---

### `get_data(champ, script_type, default=None)` → `Any`

Lit un champ depuis `ETAT_<SCRIPT_TYPE>` avec cast automatique.

```python
mise = RedisIPC.get_data('mise', '15A')            # → 0.5  (float)
jeu  = RedisIPC.get_data('looking_game', '15A')    # → 4    (int)
bet  = RedisIPC.get_data('validated_bet', '15A')   # → dict
ok   = RedisIPC.get_data('champ_absent', '15A', default=0)  # → 0
```

**Logique de cast** (dans l'ordre) :

1. Si la valeur commence par `{` ou `[` → `json.loads()`
2. Si la valeur contient `.` → `float()`
3. Sinon → `int()`
4. Si tout échoue → `str` brut

---

### `set_loss(script_type, loss_value, publish=True)` → `bool`

Écrit la perte dans la clé string `PERTE_<SCRIPT>`.

```python
RedisIPC.set_loss('15A', 12.5)          # SET PERTE_15A 12.5 + PUBLISH
RedisIPC.set_loss('15A', 12.5, publish=False)  # sans notification pub/sub
```

Utilisé pour la rétrocompatibilité avec `DispatchPerte()` et `getGlobalPerte()`.

---

### `get_loss(script_type, default=0.0)` → `float`

```python
perte = RedisIPC.get_loss('15A')   # → 12.5
```

---

### `sauvegarder_etat(script_type)` → `bool`

Snapshot complet de `config.*` → `ETAT_<SCRIPT>` via pipeline atomique.  
Équivalent haut niveau de `desactiver()` pour usage ponctuel hors `BaseScript`.

```python
RedisIPC.sauvegarder_etat('15A')
```

---

### `charger_etat(script_type)` → `bool`

Charge `ETAT_<SCRIPT>` → `config.*` avec cast automatique.  
Retourne `False` si la clé n'existe pas (premier lancement = comportement normal).

```python
trouvé = RedisIPC.charger_etat('15A')
if not trouvé:
    config.switchScript('15A')  # premier lancement, pas de sauvegarde Redis
```

---

### `lire_etat(script_type)` → `dict`

Lit l'état **sans** le charger dans `config`. Utile pour debug ou monitoring.

```python
etat = RedisIPC.lire_etat('15A')
print(etat['mise'], etat['perte'])
```

---

### `reinitialiser_etat(script_type)` → `bool`

Supprime `ETAT_<SCRIPT>` et `PERTE_<SCRIPT>` (équivalent d'un reset complet).

```python
RedisIPC.reinitialiser_etat('15A')
```

---

### `deduct_amount_from_largest(amount)` → `list[tuple]`

Déduit un montant des pertes cross-script en commençant par la plus élevée.

```python
modifications = RedisIPC.deduct_amount_from_largest(5.0)
# → [('30A', 7.5), ('15A', 0.0)]  si 30A avait 7.5 et 15A avait 4.5
```

---

## Intégration dans `BaseScript` — `core/martingale/script_types.py`

### `_CHAMPS_CONFIG`

Tuple de classe qui liste les 15 champs de `config` gérés par Redis :

```python
_CHAMPS_CONFIG: tuple[tuple[str, type], ...] = (
    ("mise",           float),
    ("perte",          float),
    ("wantwin",        float),
    # ... 12 autres
)
```

Ce tuple est la **source de vérité unique** : `activer()` et `desactiver()` itèrent dessus. Pour ajouter un champ, il suffit de l'ajouter ici.

---

### `activer()` — chargement depuis Redis

Appelé en début de tour à la place de `config.switchScript(scriptType)`.

```
activer('15A')
    │
    ├─ get_data('mise', '15A') → 0.5  → setattr(config, 'mise', 0.5)
    ├─ get_data('perte', '15A') → 12.5 → setattr(config, 'perte', 12.5)
    ├─ ... (15 champs)
    ├─ config.scriptType = '15A'
    │
    └─ Si Redis down → config.switchScript('15A')  (fallback)
```

**Important** : si un champ est absent de Redis (ex : premier lancement), il est ignoré et la valeur actuelle de `config` est conservée.

---

### `desactiver()` — sauvegarde via pipeline

Appelé en fin de tour à la place de `config.save_variables()`.

```
desactiver('15A')
    │
    ├─ Construit mapping { 'mise': '0.5', 'perte': '12.5', ... }  (1 passe)
    │
    ├─ pipeline(transaction=False)
    │     HSET ETAT_15A mapping   ← 1 seule commande pour 15 champs
    │     SET  PERTE_15A 12.5     ← rétrocompatibilité
    │     EXECUTE                 ← 1 seul aller-retour réseau
    │
    └─ Si Redis down ou exception → config.save_variables()  (fallback)
```

**Pourquoi `transaction=False` ?**  
On n'a pas besoin de `MULTI/EXEC` ici. `transaction=False` évite le surcoût du verrou côté serveur Redis tout en groupant les commandes en un seul paquet réseau.

**Gain mesuré** : 15 `HSET` séparés = 15 allers-retours → 1 pipeline = **1 aller-retour**. Sur socket Unix : ~0.1 ms au lieu de ~1.5 ms.

---

## Cycle de vie d'un tour complet

```
all_script_v2(driver)
│
├── pour chaque script in [15A, 30A, 300]
│       │
│       ├── script.activer()
│       │     └── Redis → config.* chargés pour CE script
│       │
│       ├── (vérifications, paris, GetResult...)
│       │
│       └── script.desactiver()
│             └── config.* → Redis pipeline (1 aller-retour)
│
└── fin de match → reinitialiser_etat() pour chaque script
```

---

## Fallback si Redis est indisponible

Le système ne **bloque jamais** si Redis est down. Chaque fonction retourne `False` ou la valeur `default` silencieusement, et le comportement bascule sur les fonctions classiques de `config.py` :

| Situation | Comportement |
|---|---|
| Redis down à `activer()` | `config.switchScript(script_type)` |
| Redis down à `desactiver()` | `config.save_variables()` |
| `get_data()` absent | retourne `default` |
| `set_data()` échoue | retourne `False` |

> ⚠️ **Risque opérationnel** : si Redis est down, les scripts fonctionnent mais **l'état cross-script n'est plus partagé**. Deux scripts peuvent avoir des états incohérents. Il est recommandé de vérifier que Redis tourne avant de lancer les scripts.

### Vérification au démarrage (recommandée)

```python
from Functions import RedisIPC

client = RedisIPC.get_redis_client()
if client is None:
    raise RuntimeError("Redis est requis. Lancer : redis-server")
try:
    client.ping()
except Exception:
    raise RuntimeError("Redis ne répond pas. Vérifier redis-server.")
```

---

## Lancer Redis sur macOS

```bash
# Installation (une seule fois)
brew install redis

# Lancement en arrière-plan
brew services start redis

# Vérification
redis-cli ping   # → PONG

# Socket Unix (optionnel, plus rapide)
redis-server --unixsocket /tmp/redis.sock --unixsocketperm 700
export REDIS_UNIX_SOCKET=/tmp/redis.sock
```

---

## Debug et monitoring

```python
from Functions import RedisIPC

# Inspecter l'état d'un script sans toucher config
etat = RedisIPC.lire_etat('15A')
print(etat)
# → {'mise': 0.5, 'perte': 12.5, 'wantwin': 10.0, ...}

# Lire toutes les pertes
for script in ['15A', '30A', '300']:
    print(f"PERTE_{script} =", RedisIPC.get_loss(script))

# Reset complet d'un script
RedisIPC.reinitialiser_etat('15A')
```

En ligne de commande Redis :

```bash
redis-cli HGETALL ETAT_15A
redis-cli GET PERTE_15A
redis-cli KEYS "ETAT_*"
redis-cli KEYS "PERTE_*"
```
