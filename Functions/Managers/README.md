# Documentation des Gestionnaires (Managers)

Ce document décrit l'architecture et l'utilisation des différents gestionnaires dans le projet de paris Martingale.

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [MatchManager](#matchmanager)
3. [ScriptManager](#scriptmanager)
4. [Bonnes Pratiques](#bonnes-pratiques)

## Vue d'Ensemble

Les gestionnaires (Managers) sont des classes qui implémentent le pattern Singleton pour garantir une instance unique par type de ressource. Cette approche permet de :

- Centraliser la gestion des ressources
- Éviter les conflits de données
- Optimiser l'utilisation de la mémoire
- Assurer la cohérence des états

## MatchManager

### Description

Le `MatchManager` est responsable de la gestion des matchs pour chaque stratégie. Il implémente un pattern Singleton par stratégie pour garantir une gestion cohérente des matchs.

### Caractéristiques

- Instance unique par stratégie de paris
- Stockage local via SQLite
- Synchronisation avec une API distante
- Gestion des états des matchs

### Utilisation

```python
# Obtenir l'instance du gestionnaire pour une stratégie
match_manager = MatchManager.get_instance("40A")

# Ajouter un nouveau match
match_manager.add_match("match-123")

# Vérifier si un match existe
exists = match_manager.match_exists("match-123")

# Supprimer un match
match_manager.remove_match("match-123")
```

### Tables de la Base de Données

1. `matches`

   - `match_id` (TEXT): Identifiant unique du match
   - `strategy` (TEXT): Nom de la stratégie
   - `created_at` (TIMESTAMP): Date de création
   - `status` (TEXT): Statut du match

2. `matches_todo`
   - `match_id` (TEXT): Identifiant unique du match
   - `match_info` (TEXT): Informations du match
   - `created_at` (TIMESTAMP): Date de création

## ScriptManager

### Description

Le `ScriptManager` gère l'exécution et le statut des différents scripts de paris. Il assure qu'il n'y a pas de conflits entre les différentes stratégies en cours d'exécution.

### Fonctionnalités

- Gestion des scripts en cours d'exécution
- Prévention des conflits entre scripts
- Surveillance de l'état des scripts

### Utilisation

```python
# Obtenir l'instance du gestionnaire de scripts
script_manager = ScriptManager.get_instance()

# Démarrer un script
script_manager.start_script("40A", "1")

# Vérifier si un script est en cours
is_running = script_manager.is_script_running("40A", "1")

# Arrêter un script
script_manager.stop_script("40A", "1")
```

## Bonnes Pratiques

1. **Toujours utiliser get_instance()**

   ```python
   # Correct
   manager = MatchManager.get_instance(strategy_name)

   # Incorrect
   manager = MatchManager(strategy_name)
   ```

2. **Gestion des Ressources**

   - Toujours fermer les connexions à la base de données
   - Utiliser des contextes (with) pour les opérations de fichiers
   - Nettoyer les anciens matchs régulièrement

3. **Gestion des Erreurs**

   ```python
   try:
       match_manager = MatchManager.get_instance(strategy)
       match_manager.add_match(match_id)
   except Exception as e:
       config.log(f"Erreur lors de l'ajout du match: {str(e)}", 'error', True)
   ```

4. **Maintenance**
   - Nettoyer régulièrement les vieux matchs
   - Vérifier la synchronisation avec l'API distante
   - Monitorer la taille de la base de données

## Migration et Évolution

Pour ajouter un nouveau gestionnaire :

1. Implémenter le pattern Singleton
2. Ajouter la gestion des erreurs
3. Documenter les méthodes publiques
4. Ajouter les tests unitaires
5. Mettre à jour cette documentation

## Support et Dépannage

En cas de problèmes :

1. Vérifier les logs d'erreur
2. S'assurer que la base de données est accessible
3. Vérifier la connexion à l'API distante
4. Consulter les tests unitaires pour le comportement attendu
