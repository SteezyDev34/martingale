# Guide du Projet d'Automatisation de Paris Martingale

## Configuration Linguistique

- Utiliser uniquement le français pour tous les commentaires de code
- Utiliser uniquement le français pour tous les messages de commit
- Utiliser uniquement le français pour toutes les descriptions de fonctions et de variables
- Les noms de variables et fonctions restent en anglais pour la cohérence du code

### Conventions de Documentation

#### Format des Commentaires

```python
def update_match_status(match_id: str, status: str) -> bool:
    """
    Met à jour le statut d'un match dans la base de données.

    Args:
        match_id (str): Identifiant unique du match
        status (str): Nouveau statut à appliquer

    Returns:
        bool: True si la mise à jour est réussie, False sinon
    """
```

#### Messages de Commit

- feat: "Ajout de la fonctionnalité X"
- fix: "Correction du problème Y"
- refactor: "Amélioration de la structure Z"
- docs: "Mise à jour de la documentation"

## Vue d'Ensemble du Projet

Système d'automatisation de paris basé sur Python implémentant diverses stratégies Martingale pour les paris sportifs. Le projet utilise Selenium pour l'automatisation web et suit une architecture modulaire.

## Core Architecture

### Key Components

- `Functions/` - Utility functions for match analysis, betting, and automation
  - `Functions_431a.py` - Core betting logic implementation
  - `ScriptRechercheDeMatch.py` - Match search and analysis
  - `ValidationDuParis.py` - Bet validation and tracking

### Data Flow

1. Match Discovery:

   - Scripts scan for matches meeting strategy criteria
   - Match data saved to strategy-specific matchlist files

2. Betting Process:
   - Strategies validate matches against rules
   - Bets placed through Selenium automation
   - Results tracked in `*_validated_bets.json` files

## Development Workflows

### Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Key Dependencies:

- Selenium WebDriver (see `ChromeDriver/` directory)
- Python packages in `requirements.txt`

### Strategy Scripts

Each strategy (e.g., 30A, 40A, etc.) has dedicated scripts in `SCRIPTS_{strategy}/` folders:

- Configured through `config.json`
- Logs stored in `Logs/` directory
- Running status tracked in `running` files

### Debug Workflow

1. Check `*.log` files in strategy directories
2. Monitor `*_validated_bets.json` for bet history
3. Use `DynamicTerminalLogger.py` for real-time monitoring

## Project Conventions

### File Structure

- Strategy implementations in `SCRIPTS_{strategy}/`
- Utility functions in `Functions/`
- Configuration in `config.py` and `config.json`
- Data caching in `DataFiles/` and `*.json` files

### Naming Conventions

- Strategy scripts: `{strategy}-{number}.py` (e.g., `30A-1.py`)
- Function files: `Functions_{purpose}.py`
- Running files: `SCRIPTS {strategy}/running`
- Matchlist files: `SCRIPTS {strategy}/matchlist`

### Configuration

- Each strategy has a dedicated config section in `config.json`
- Runtime configs initialized via `config.ScriptConfig()`
- File paths managed through `config.projectPath`

## Integration Points

- Selenium WebDriver interface in `ChromeDriver/`
- Web API endpoints in `api/` directory
- External data sources in `DataFiles/`

## Conventions et bonnes pratiques Python

Voici un condensé des conventions et bonnes pratiques à respecter dans ce projet :

- **Style et formatage** : suivre PEP 8 ; utiliser `black` pour le formatage automatique et `isort` pour trier les imports.
- **Nommage** : `snake_case` pour fonctions/variables, `CamelCase` pour classes, `UPPER_SNAKE` pour constantes.
- **Docstrings** : documenter modules, fonctions et classes (PEP 257) — ici en français.

- **Structure du projet** : modules petits et cohérents, séparer `src/`, `tests/`, `docs/` si pertinent.
- **Packages** : ajouter `__init__.py` pour déclarer les packages et faciliter les imports.

- **Types** : utiliser les annotations de type (`typing`) et valider avec `mypy` en CI.
- **Tests** : écrire des tests unitaires avec `pytest`, isoler les tests (mocker IO/HTTP/DB).

- **Dépendances** : utiliser un environnement virtuel (`venv`/`poetry`), pinner les versions et conserver les fichiers de lock.
- **Secrets** : ne pas committer les secrets ; utiliser des variables d'environnement ou un vault.

- **Logging et erreurs** : utiliser le module `logging`, éviter `print` en production, attraper des exceptions ciblées.

- **Sécurité** : valider et assainir les entrées externes, éviter l'injection (paramétrer requêtes SQL/HTTP).

- **Concurrence** : différencier IO-bound (async/threads) et CPU-bound (multiprocessing), protéger les ressources partagées.

- **Performance** : profiler avant d'optimiser; privilégier générateurs/itertools et structures adaptées.

- **Git & workflow** : commits atomiques en français, branches de fonctionnalité, PR avec tests et CI passant.

Intégrer ces règles dans CI (linters, `black`, `isort`, `mypy`, tests) améliore la qualité et la maintenabilité.

## Organisation des fichiers de fonctions

Pour une meilleure hiérarchisation et maintenabilité du code, suivre ces recommandations lors de la création de nouveaux fichiers/fonctions :

- **Sous-dossiers dédiés** : regrouper les utilitaires par domaine sous `Functions/` (ex. `Functions/Utils/`, `Functions/Telegram/`, `Functions/IO/`) pour clarifier la responsabilité et faciliter la navigation.
- **Un fichier = une responsabilité** : privilégier un fichier par responsabilité cohérente (ex. `path_utils.py` pour gestion des chemins). Cela rend les fichiers plus courts, plus testables et plus faciles à relire.
- **Limiter la taille des fichiers** : viser des fichiers courts (idéalement < 200–300 lignes). Si un fichier grandit, scinder-le selon des responsabilités claires.
- **Vérifier l'existant avant de créer** : toujours rechercher d'abord s'il existe déjà un dossier ou un fichier similaire afin d'éviter les duplications et favoriser la réutilisation.
- **Nommage explicite** : nommer dossiers et fichiers de façon descriptive (`utils`, `telegram_api`, `image_processing`) pour réduire les confusions.
- **__init__.py** : ajouter `__init__.py` dans les nouveaux sous-dossiers si nécessaire pour clarifier le packaging et simplifier les imports.

Ces règles complètent les conventions générales ci‑dessus et doivent être appliquées par défaut lors de l'ajout de nouvelles fonctions ou utilitaires.

## Conventions pour les noms de dossiers

Respecter des règles cohérentes pour nommer les dossiers facilite l'import, la lecture et la maintenance :

- **Minuscules** : utiliser des lettres minuscules (ex. `functions`, `datafiles`).
- **Pas d'espaces** : remplacer les espaces par `_` si nécessaire (ex. `image_processing`).
- **Préférer `snake_case`** : éviter les `-` (ex. `telegram_api` plutôt que `telegram-api`) car `-` empêche l'import Python direct.
- **Noms descriptifs et courts** : choisir des noms clairs et représentatifs de la responsabilité (ex. `utils`, `telegram_api`, `image_processing`).
- **Cohérence singulier/pluriel** : adopter une convention et la respecter (ex. `tests` plutôt que `test` si le projet utilise `tests`).
- **Noms valides pour import** : pour les packages Python, utiliser des identifiants valides (lettres, chiffres, `_`, ne pas commencer par un chiffre) et ajouter `__init__.py` si vous voulez un package explicite.
- **Hiérarchie par domaine** : regrouper par responsabilité (ex. `functions/utils/`, `functions/telegram/`).
- **Vérifier l'existant** : ne pas créer un nouveau dossier si un dossier existant couvre déjà la même responsabilité — vérifier avant de créer.
- **Éviter la redondance** : ne pas multiplier des dossiers aux responsabilités confondues.

Exemples pratiques : `functions/utils/`, `functions/telegram/`, `datafiles/`, `tests/`.
