# Documentation — Functions/RedisIPC.py

## But du module

Ce module fournit une interface légère et performante pour communiquer avec Redis depuis les scripts du projet. Il expose un client Redis singleton et des fonctions utilitaires pour stocker/consulter la "perte" par type de script, publier des notifications et effectuer des déductions atomiques en cascade.

Le module vise la latence minimale : utilisation d'un client réutilisable (pool de connexions), pipeline pour opérations groupées, support socket Unix si configurée.

---

## Variables d'environnement

- `REDIS_UNIX_SOCKET` : (optionnel) chemin du socket Unix à utiliser. Si présent, priorisé.
- `REDIS_HOST` : hôte Redis (par défaut `localhost`).
- `REDIS_PORT` : port Redis (par défaut `6379`).
- `REDIS_DB` : index de la base Redis (par défaut `0`).

Assurez-vous que le serveur Redis est installé et démarré localement pour une latence maximale.

---

## Fonctions publiques

Toutes les fonctions suivantes se trouvent dans `Functions/RedisIPC.py`.

### `get_redis_client()` -> `Optional[redis.Redis]`

- Retourne un client Redis singleton (`redis.Redis`) ou `None` si le paquet `redis` n'est pas installé.
- Le client est configuré automatiquement depuis les variables d'environnement.
- Utilisation typique : appeler `get_redis_client()` depuis le module si vous avez besoin du client brut.

### `set_loss(script_type: str, loss_value: float, publish: bool = True) -> bool`

- Stocke la perte `loss_value` pour le `script_type` sous la clé `PERTE_<SCRIPT>` (ex: `PERTE_40A`).
- Si `publish=True`, effectue dans un pipeline : `SET key value` puis `PUBLISH 'perte_updates' "KEY:VALUE"`.
- Retourne `True` si l'opération réussit, `False` sinon.

Exemple :

```python
from Functions.RedisIPC import set_loss
set_loss('40A', 12.5)
```

### `get_loss(script_type: str, default: float = 0.0) -> float`

- Lit la valeur stockée dans `PERTE_<SCRIPT>` et renvoie un `float`.
- Si la clé est absente ou en cas d'erreur, renvoie `default`.

Exemple :

```python
from Functions.RedisIPC import get_loss
perte = get_loss('40A', 0.0)
```

### `publish_update(channel: str, message: str) -> bool`

- Publie `message` sur le `channel` Redis via `PUBLISH`.
- Retourne `True` si succès, `False` sinon.
- Utile pour avertir d'autres scripts que la perte a changé.

### `deduct_amount_from_largest(amount: float) -> list[tuple[str, float]]`

- Comportement :
  1. Recherche toutes les clés `PERTE_*` dans Redis.
  2. Récupère leurs valeurs et les trie par valeur décroissante (la plus grande d'abord).
  3. Déduit `amount` en commençant par la plus grande : si `amount` dépasse la valeur d'une clé, met cette clé à `0` et continue avec le reliquat.
  4. Met à jour Redis via `pipeline()` (exécution groupée) pour minimiser les RTT.
- Retour : une liste de tuples `(script_type, nouvelle_perte)` pour chaque clé modifiée, dans l'ordre d'application.
- Utilisation typique : lors de la récupération d'un paiement qui doit être appliqué aux pertes globales les plus importantes.

Exemple :

```python
from Functions.RedisIPC import deduct_amount_from_largest
mods = deduct_amount_from_largest(25.0)
# mods pourrait ressembler à [('40A', 0.0), ('30A', 5.0)] si 25 a consommé 40A puis 30A partiellement
```

---

## Exemples d'intégration dans le projet

- Écriture de la perte après validation d'un pari (existant dans `Functions/ValidationDuParis.py`) :

```python
from Functions.RedisIPC import set_loss
set_loss(config.scriptType, config.perte)
```

- Lecture rapide à l'initialisation (remplace un appel réseau lent) :

```python
from Functions.RedisIPC import get_loss
config.perte = get_loss(config.scriptType, default=0.0)
```

- Application d'un paiement global pour décrémenter les pertes (ex: depuis une routine d'ordonnancement) :

```python
from Functions.RedisIPC import deduct_amount_from_largest
modifications = deduct_amount_from_largest(100.0)
# traiter modifications pour synchroniser la DB distante si nécessaire
```

---

## Performance & bonnes pratiques

- Instancier une seule fois le client Redis par process (le singleton du module fait cela).
- Préférer le socket Unix (`REDIS_UNIX_SOCKET`) si Redis tourne sur la même machine — cela réduit sensiblement la latence.
- Utiliser `pipeline()` pour grouper plusieurs commandes et réduire les allers-retours.
- Pour des notifications en temps réel, utiliser le canal `perte_updates` (ou définir un canal spécifique).
- Pour des opérations atomiques complexes, préférer `EVAL` (Lua) ou les commandes atomiques (`INCRBYFLOAT`) côté serveur.

---

## Installation requise

Ajouter à `requirements.txt` :

```
redis>=4.8.0
hiredis>=2.0.0
```

Installer Redis sur macOS (homebrew) :

```bash
brew install redis
brew services start redis
```

---

## Notes sur la résilience

- Le module renvoie `None` ou valeurs par défaut si le package `redis` est absent — prévoir un fallback (appel réseau) si Redis est indisponible.
- Toujours traiter les retours `False`/`[]` pour gérer les erreurs silencieuses et ne pas interrompre les scripts.

---

## Emplacement du fichier source

- Module source : [Functions/RedisIPC.py](../Functions/RedisIPC.py)

---

## Licence & style

- Documentation rédigée en français conformément aux conventions du projet.
- Respecter les conventions de nommage et ne pas exposer d'API globales non documentées.


