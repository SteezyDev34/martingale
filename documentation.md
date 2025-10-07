# Documentation du Programme Martingale-40A1

## Introduction

Ce programme est un système automatisé de paris sportifs utilisant la stratégie de martingale pour les matchs de tennis sur le site 1xBet. Il permet de suivre différentes stratégies de paris (identifiées par des codes comme 40A, 30A, etc.) et de placer des paris automatiquement selon des critères prédéfinis.

## Structure du Projet

Le projet est organisé en plusieurs dossiers principaux :

- **Functions/** : Contient les fonctions spécifiques à chaque stratégie et les utilitaires communs
- **SCRIPTS_XXX/** : Contient les scripts d'exécution pour chaque stratégie (40A, 30A, etc.)
- **DataFiles/** : Stocke les données nécessaires au fonctionnement du programme
- **Logs/** : Contient les fichiers de journalisation des opérations
- **conf/** : Contient les fichiers de configuration

## Configuration Principale

Le fichier `config.py` est le cœur de la configuration du programme. Il définit :

- Les variables globales utilisées par tous les scripts
- Les chemins d'accès aux fichiers
- Les URLs des sites de paris
- Les paramètres de base pour les stratégies

### Variables Principales

```python
# Types de scripts disponibles
scriptTypeList = ['300', '15A', '30A']
allScriptType = ['030', '300', '15A', '30A', '40A', '4P', '5P', '6P', '4030', '4015', '400', 'BREAK', '1SET']

# Configuration du site
api_url = "http://auxobetbot.sc2vagr6376.universe.wf"
site_url = 'https://1xbet.com/fr/live/tennis'
site_line_url = 'https://1xbet.com/fr/line/tennis'

# Variables de jeu
mise = 0.2           # Mise de base
probamini = 0.1      # Probabilité minimale pour placer un pari
cotebase = 1         # Cote de base
wantwin = 0.2        # Gain souhaité
```

## Classes Principales

### ScriptConfig

Cette classe gère la configuration spécifique à chaque type de script. Elle utilise le pattern Singleton pour maintenir une seule instance par type de script.

```python
class ScriptConfig:
    _instances = {}  # Dictionnaire pour stocker les instances par type de script

    def __init__(self, script_type):
        # Initialisation avec récupération des données depuis l'API
        # ...

    def get(self, var_name):
        """Récupère une variable par son nom"""
        return self.variables.get(var_name)

    def set(self, var_name, value):
        """Définit une variable"""
        self.variables[var_name] = value

    def reset(self):
        """Force la réinitialisation de la configuration"""
        # ...
```

## Fonctions Principales

### Configuration du Site

```python
def configure_site_type(use_ca_site=None):
    """
    Configure le type de site et les URLs en fonction du choix utilisateur.
    
    Args:
        use_ca_site (bool, optional): Si True, utilise le site CA. Si False, utilise le site standard.
    
    Returns:
        str: Le type de site configuré ('new_site' ou 'old_site')
    """
```

### Gestion des Variables

```python
def init_variable():
    """Initialise les variables globales à partir des données de stratégie"""
    # Charge les configurations depuis l'API ou les valeurs par défaut

def save_variables():
    """Sauvegarde l'état actuel des variables dans la configuration"""
    # Enregistre les valeurs actuelles dans l'instance ScriptConfig

def switchScript(newScriptType):
    """Change le type de script actuel et réinitialise les variables"""
    # Permet de passer d'une stratégie à une autre
```

### Journalisation

```python
def saveLog(txt):
    """
    Enregistre un message dans un fichier de log.
    
    Args:
        txt: Le texte à enregistrer
    """
    # Crée un fichier de log avec la date et l'heure

def log(message, type="", clear=True, indent=0):
    """
    Affiche un message dans le terminal avec formatage couleur.
    
    Args:
        message: Le texte du message
        type: Type de message (info, title, success, warning, error)
        clear: Si True, efface la ligne précédente
        indent: Niveau d'indentation
    """
    # Affiche le message avec la couleur appropriée et l'enregistre dans le log
```

## Stratégies de Paris

Le programme supporte plusieurs stratégies de paris, chacune identifiée par un code :

- **40A** : Stratégie principale pour les paris sur le tennis
- **30A** : Variante de la stratégie principale
- **15A** : Stratégie pour les paris à faible cote
- **4P**, **5P**, **6P** : Stratégies pour différents types de paris
- **1SET** : Stratégie spécifique pour les paris sur le premier set

Chaque stratégie a ses propres paramètres et règles de paris, définis dans les fichiers de configuration et les modules spécifiques.

---

## Fonctionnement détaillé de la martingale

Cette section explique en détail comment la martingale est implémentée dans ce projet, comment les mises sont calculées et mises à jour, et quelles limites/garanties sont prévues.

### 1) Principe général

La martingale vise à récupérer les pertes cumulées et à garantir un gain net cible (wantwin) lorsqu’un pari gagne, en augmentant la mise après une perte.

Terminologie utilisée dans le code (voir `config.py` et `Functions/GetMise.py`) :
- `wantwin` : gain net souhaité par victoire.
- `perte` : pertes cumulées à rattraper au prochain pari.
- `cote` : cote du pari en cours (récupérée depuis la page, sinon `cotebase`).
- `mise` : montant à engager sur le prochain pari.

La formule centrale utilisée est dans `Functions/GetMise.py` :

```python
mise = (wantwin + perte) / (cote - 1)
```

- Un minimum est appliqué: `mise` est arrondie à 2 décimales et ne peut pas être inférieure à 0.2 EUR.
- Si la cote ne peut pas être lue, le système retombe sur `config.cotebase`.

Après un pari:
- Si le pari est perdu (LOSE), on met à jour `perte` en y ajoutant la mise perdue (éventuellement multipliée par la cote si l’on suit un suivi externe). Dans ce projet, les flux d’actualisation se font via les résultats retournés par `Functions/GetResult.py` et la gestion des pertes via `Functions/GetJsonData.py` (Dispatch/SendPerte, etc.).
- Si le pari est gagné (WIN), `perte` est remise à zéro et la boucle repart avec `wantwin` uniquement.

### 2) Où la logique est-elle appliquée ?

- Calcul de la mise: `Functions/GetMise.py`
  - Lit la cote en cours (ou utilise `cotebase`).
  - Calcule `mise` selon la formule ci-dessus et applique le minimum de 0.2.
- Déclenchement et validation des paris: `Functions/FirstGameBet.py`, `Functions/GetAndPlaceBet.py`, `Functions/ValidationDuParis.py`, `Functions/PlacerMise.py`.
- Détermination du résultat et mise à jour: `Functions/GetResult.py` (détermine WIN/LOSE selon le score), puis mise à jour des pertes/gains via `Functions/GetJsonData.py`.

### 3) Exemple chiffré

Supposons:
- wantwin = 0.20 EUR
- perte = 0 EUR au départ
- cote = 2.40

Mise1 = (0.20 + 0.00) / (2.40 - 1) = 0.20 / 1.40 ≈ 0.14 → minimum 0.20 EUR

- Si LOSE: pertes cumulées `perte` ≈ 0.20 EUR.
- Nouveau calcul:
  Mise2 = (0.20 + 0.20) / 1.40 ≈ 0.29 → 0.29 EUR
- Si LOSE encore: `perte` ≈ 0.20 + 0.29 = 0.49 EUR.
- Nouveau calcul:
  Mise3 = (0.20 + 0.49) / 1.40 ≈ 0.49 EUR, etc.

Au premier WIN, le gain brut ≈ Mise × (cote - 1) rembourse `perte` et laisse ~`wantwin` en net. Ensuite `perte` est remise à 0.

Remarques:
- Les arrondis à 2 décimales peuvent légèrement dévier du théorique.
- Si `cote` varie entre le calcul et l’envoi, la modale peut proposer d’accepter un changement de cote; la logique de modale est gérée dans `Functions/ModalHandler.py` et `ValidationDuParis`.

### 4) Nombre de tours et gestion du capital

L’approche martingale a un risque de croissance rapide des mises. Il est essentiel d’évaluer le capital disponible vs le nombre maximum de tours (pertes d’affilée) que l’on souhaite pouvoir encaisser.

Ce dépôt inclut un utilitaire dans `Functions/GetGainFromCapital.py`:

```python
def max_gain_pour_16_tours(solde_initial, cote=2.4, tours_max=16):
    # Calcule le gain net maximal visé (wantwin) compatible avec le capital
```

Idée: pour un capital donné et un nombre de tours maximum, on cherche le `wantwin` maximal tel que la somme des mises successives reste ≤ capital. Cela permet d’ajuster `wantwin` de façon réaliste.

Recommandations:
- Fixer un nombre de tours max (nb_tour) raisonnable par stratégie.
- Calculer un `wantwin` compatible avec le capital et la cote moyenne attendue.
- Mettre en place un stop-loss global si `nb_tour` est atteint ou si la mise à venir dépasse une limite (misemax si disponible sur le site).

### 5) Spécificités par stratégie (quand parier)

La martingale (calcul de mise) est commune, mais chaque stratégie définit quand déclencher le pari en fonction du score en direct:
- 40A: on cible des moments proches de 40-40/avantage (voir `FirstGameBet`/`GetAndPlaceBet`).
- 30A: déclenche lorsque le score atteint des états comme 0:0, 15:15, etc. (voir `FirstGameBet` et `GetResult`).
- 15A, 030/300: déclenche à 0:0 ou autres états précisés dans le code.
- 4P/5P/6P/400/4015/4030: stratégies multi-paris avec conditions propres de déclenchement et de validation.
- 1SET: logique sur le résultat du set (V1/V2) avec récupération de pertes dédiée.

Le calcul `mise = (wantwin + perte) / (cote - 1)` est réutilisé dans toutes ces stratégies; seules les conditions de déclenchement/validation varient.

### 6) Garde-fous et limites

- Mise minimale: 0.2 EUR (hard-stop dans `GetMise`).
- Cote non disponible: fallback sur `cotebase`.
- Limite de mise (misemax): si disponible via l’UI, la logique tente de détecter les plafonds (partie optionnelle dans `GetMise`).
- Changement de cote/modales: `ModalHandler.py` accepte/annule selon les cas.
- Seuil de profit cible global: `config.total_want_win[...]` permet d’arrêter la stratégie dès que le profit net visé de la session/match est atteint.
- Nombre de tours max: contrôlé côté scripts; si atteint, arrêter pour éviter l’explosion du risque.

### 7) Pseudo-code récapitulatif

```text
perte = pertes cumulées (0 au départ)
while session_active:
    lire cote (ou cotebase)
    mise = max(0.2, round((wantwin + perte)/(cote - 1), 2))
    envoyer le pari
    attendre résultat (WIN/LOSE)
    si WIN:
        perte = 0
        si profit global ≥ objectif: arrêter
    sinon (LOSE):
        perte += mise
        si nb_tour dépasse le max ou mise suivante > misemax: arrêter (stop-loss)
```

En résumé, la martingale ici est une martingale « classique » à cible fixe wantwin, avec récupération des pertes via `perte` et un ensemble de garde-fous pour limiter le risque opérationnel.

### 8) Précisions techniques supplémentaires

- Variables clés et où elles vivent:
  - `config.wantwin`, `config.perte`, `config.cotebase`, `config.cote`, `config.mise` pilotent le calcul (voir `Functions/GetMise.py`).
  - Suivi de session: `config.global_match_win` (dict par stratégie) est confronté à `conf.total_want_win[...]` pour décider l'arrêt d’une stratégie au cours d’un match.
  - État du pari courant: `config.validated_bet` contient set/jeu/score gagnant attendu pour l’évaluation de résultat (voir `Functions/GetResult.py`).
- rattrape_perte (modes):
  - Lorsque `config.rattrape_perte == 3`, `GetMise` force la cote à `cotebase` (fallback conservateur). Les autres valeurs (ex. `1`) gardent la cote lue à l’écran.
- Gestion des cotes et divisions:
  - Si la cote lue est vide/0/1, on retombe sur `cotebase` afin d’éviter une division par zéro dans `(cote - 1)`.
  - Les changements de cotes entre saisie et envoi sont traités via `Functions/ModalHandler.py` (accepter/refuser selon cas) et `ValidationDuParis`.
- Arrondis, devise et minimum:
  - `config.mise` est arrondie à 2 décimales, minimum 0,20 EUR par sécurité opérationnelle. La devise suit celle du site 1xBet affichée dans l’UI.
- Limite de mise (misemax):
  - Un bloc de récupération de la limite depuis l’UI existe dans `GetMise`. Par défaut, il n’est pas actif (la boucle est neutralisée). Si vous souhaitez l’utiliser, adaptez la condition `getmisemax` pour interroger la limite et comparer avant d’envoyer la mise.
- Mise à jour des pertes/gains:
  - Après `GetResult`, plusieurs chemins mettent à jour/persistent les pertes: `DispatchPerte`/`SendGlobalPerte`/`set1DispatchPerte` dans `Functions/GetJsonData.py` selon la stratégie (standard, global, 1SET). Sur WIN, `perte` est remise à 0.
- Arrêts et orchestration multi‑stratégies:
  - Chaque stratégie d’une session est évaluée dans des boucles qui comparent `global_match_win[scriptType]` à `total_want_win[scriptType]` et respectent `nb_tour` max. Une stratégie peut s’arrêter indépendamment des autres.
- Cas particulier LIVE:
  - Si `config.scriptType == 'LIVE'`, `GetMise` n’utilise pas la formule de martingale locale: la mise recommandée est obtenue via l’API `recommended_stake` avec `recover_losses=1`.
- Croissance des mises (intuition):
  - À cote constante C, après k pertes, la somme des mises ≈ Σ_{i=0..k} (wantwin + Σ mises précédentes)/(C−1). Cette croissance peut devenir très rapide lorsque C se rapproche de 1.5–2.0; d’où l’importance de dimensionner `wantwin` et `tours_max` via `GetGainFromCapital.py`.

## Paramétrage du Programme

### Configuration de Base

1. Éditer le fichier `config.py` pour ajuster les paramètres globaux :
   - `mise` : Montant de base pour les paris
   - `wantwin` : Gain souhaité
   - `probamini` : Probabilité minimale pour placer un pari

2. Choisir le type de site 1xBet à utiliser :
   ```python
   configure_site_type(True)  # Pour utiliser le site CA
   configure_site_type(False)  # Pour utiliser le site standard
   ```

### Configuration des Stratégies

Chaque stratégie peut être configurée individuellement via l'API ou en modifiant les fichiers de configuration spécifiques dans le dossier `conf/`.

Exemple pour la stratégie 40A :
```python
config_40A = ScriptConfig('40A')
config_40A.set("mise", 0.5)  # Augmente la mise de base pour cette stratégie
config_40A.set("wantwin", 0.3)  # Modifie le gain souhaité
```

## Exécution du Programme

Pour exécuter le programme avec une stratégie spécifique :

1. Choisir le script correspondant dans le dossier SCRIPTS_XXX/
2. Exécuter le script Python, par exemple :
   ```
   python SCRIPTS_40A/40A-1.py
   ```

Le programme va alors :
1. Initialiser la configuration
2. Rechercher des matchs de tennis en direct
3. Analyser les matchs selon les critères de la stratégie
4. Placer des paris automatiquement lorsque les conditions sont remplies
5. Suivre les résultats et ajuster les mises selon la stratégie de martingale

## Journalisation et Suivi

Tous les paris et résultats sont enregistrés dans :
- Des fichiers de log dans le dossier `Logs/`
- Des fichiers JSON pour les paris validés
- Potentiellement dans une base de données via l'API

## Maintenance et Dépannage

En cas de problème :
1. Vérifier les fichiers de log pour identifier l'erreur
2. S'assurer que les URLs du site 1xBet sont à jour
3. Vérifier la connexion à l'API
4. Réinitialiser la configuration avec `ScriptConfig('type').reset()`

## Conclusion

Ce programme offre un système complet pour automatiser les paris sportifs sur les matchs de tennis en utilisant différentes stratégies de martingale. Il est hautement configurable et peut être adapté à différentes approches de paris.

## Description détaillée des fonctions principales

### Functions/GetMise.py
Cette fonction calcule la mise selon la stratégie martingale :
```python
def getMise(driver):
    """
    Calcule la mise selon la stratégie martingale.
    
    Args:
        driver: Instance du navigateur Selenium
        
    Returns:
        float: Montant de la mise calculée
    """
    mise = (config.wantwin + config.perte) / (config.cote - 1)
    return max(0.2, round(mise, 2))
```

### Functions/FirstGameBet.py
Gère le premier pari d'une série :
```python
def firstGameBet(driver):
    """
    Vérifie les conditions initiales et place le premier pari.
    
    - Vérifie le score actuel
    - Valide les conditions de la stratégie
    - Place le pari si toutes les conditions sont remplies
    """
```

### Functions/GetResult.py
Détermine le résultat du pari :
```python
def getResult(driver):
    """
    Analyse le score final pour déterminer si le pari est gagné/perdu.
    
    Returns:
        str: 'WIN' ou 'LOSE'
    """
```

### Functions/ModalHandler.py
Gère les popups de changement de cote :
```python
def handleModal(driver):
    """
    Gère les fenêtres modales de changement de cote.
    - Accepte si la nouvelle cote est favorable
    - Refuse sinon
    """
```

### Functions/ValidationDuParis.py
Valide que le pari a bien été placé :
```python
def validateBet(driver):
    """
    Vérifie que le pari a été correctement enregistré.
    - Vérifie le ticket de pari
    - Confirme les montants et cotes
    """
```

## Cycle complet d'un pari

1. Initialisation
- ScriptConfig charge les paramètres de la stratégie
- Connexion au site via ChromeDriver

2. Recherche de match
- ScriptRechercheDeMatch.py analyse les matchs en direct
- Filtre selon les critères de la stratégie

3. Placement du pari
- FirstGameBet vérifie les conditions initiales
- GetMise calcule le montant à parier
- PlacerMise place physiquement le pari
- ValidationDuParis confirme l'enregistrement

4. Suivi et résultat
- GetResult surveille le score
- Met à jour config.perte selon le résultat
- Prépare la mise suivante si nécessaire

5. Gestion des erreurs
- ModalHandler gère les changements de cote
- Retry mécanisme en cas d'erreur technique
- Logging des événements

## Sécurités et limites

1. Limites financières
- Mise minimum : 0.2€
- Capital maximum par stratégie
- Stop-loss après X pertes consécutives

2. Contrôles de cohérence
- Validation des cotes avant pari
- Vérification des tickets de paris
- Double contrôle des résultats

3. Gestion des erreurs
- Retry sur les opérations critiques
- Rollback en cas d'erreur
- Logging détaillé