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
