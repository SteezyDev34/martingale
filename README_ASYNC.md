# Documentation - Fonctionnalités Asynchrones

## Vue d'ensemble

Ce projet inclut maintenant des fonctionnalités asynchrones pour la surveillance des scores en temps réel, permettant d'exécuter la surveillance en parallèle avec le script principal.

## Fichiers créés

### 1. `Functions/GetScoreActuelAsync.py`
Version asynchrone de la fonction `GetScoreActuel` qui permet :
- Surveillance continue des scores en arrière-plan
- Exécution non-bloquante
- Contrôle de démarrage/arrêt de la surveillance

### 2. `SCRIPTS_4315A/4315A-1-async.py`
Version modifiée du script principal `4315A-1.py` avec intégration asynchrone :
- Exécution parallèle de la surveillance et du script principal
- Gestion asynchrone des tâches
- Intégration transparente avec le code existant

### 3. Scripts de test
- `test_async_simple.py` : Tests de base de la logique asynchrone
- `test_async_execution.py` : Tests complets avec driver
- `exemple_integration.py` : Exemples d'utilisation pratique

## Utilisation

### Utilisation basique

```python
import asyncio
from Functions.GetScoreActuelAsync import start_score_monitoring, stop_score_monitoring

async def main():
    # Initialiser votre driver
    driver = votre_driver
    
    # Démarrer la surveillance
    task, stop_event = await start_score_monitoring(driver)
    
    # Votre code principal ici
    await votre_script_principal()
    
    # Arrêter la surveillance
    await stop_score_monitoring(task, stop_event)

# Exécuter
asyncio.run(main())
```

### Utilisation avec le script 4315A-1

```python
# Utiliser directement le script modifié
python3 "SCRIPTS_4315A/4315A-1-async.py"
```

### Fonctions principales

#### `start_score_monitoring(driver)`
- **Paramètre** : `driver` - Instance du WebDriver
- **Retour** : `(task, stop_event)` - Tâche asynchrone et événement d'arrêt
- **Description** : Démarre la surveillance asynchrone des scores

#### `stop_score_monitoring(task, stop_event)`
- **Paramètres** : 
  - `task` - Tâche asynchrone retournée par `start_score_monitoring`
  - `stop_event` - Événement d'arrêt retourné par `start_score_monitoring`
- **Description** : Arrête proprement la surveillance

#### `get_score_actuel_async(driver, stop_event)`
- **Paramètres** :
  - `driver` - Instance du WebDriver
  - `stop_event` - Événement pour arrêter la surveillance
- **Description** : Fonction de surveillance continue (usage interne)

## Avantages

1. **Performance** : La surveillance des scores n'interrompt plus l'exécution du script principal
2. **Réactivité** : Détection en temps réel des changements de score
3. **Flexibilité** : Possibilité de démarrer/arrêter la surveillance à tout moment
4. **Compatibilité** : Fonctionne avec le code existant

## Tests

### Exécuter les tests simples
```bash
python3 test_async_simple.py
```

### Exécuter les tests complets
```bash
python3 test_async_execution.py
```

### Exécuter les exemples
```bash
python3 exemple_integration.py
```

## Configuration requise

- Python 3.7+
- Module `asyncio` (inclus dans Python)
- Selenium WebDriver
- Configuration existante du projet

## Gestion des erreurs

Le code inclut une gestion complète des erreurs :
- Timeout de surveillance
- Erreurs de WebDriver
- Interruptions utilisateur
- Nettoyage automatique des ressources

## Exemple complet

```python
import asyncio
import config
from Functions.GetScoreActuelAsync import start_score_monitoring, stop_score_monitoring

async def mon_script_avec_surveillance():
    try:
        # Initialiser le driver
        import ChromeDriver.SetDriver as SetDriver
        driver = SetDriver.driver
        
        # Configurer
        config.site_type = 'old_site'
        
        # Démarrer la surveillance
        task, stop_event = await start_score_monitoring(driver)
        print("Surveillance démarrée")
        
        # Votre code principal
        for i in range(10):
            print(f"Étape {i+1}/10")
            
            # Vérifier les scores détectés
            if config.score_actuel:
                print(f"Score détecté : {config.score_actuel}")
            
            await asyncio.sleep(1)
        
        # Arrêter la surveillance
        await stop_score_monitoring(task, stop_event)
        print("Surveillance arrêtée")
        
    except Exception as e:
        print(f"Erreur : {e}")

# Exécuter
if __name__ == "__main__":
    asyncio.run(mon_script_avec_surveillance())
```

## Notes importantes

1. **Thread Safety** : Les variables `config` sont partagées entre les tâches asynchrones
2. **Ressources** : Toujours arrêter la surveillance pour libérer les ressources
3. **Performance** : La surveillance utilise un délai configurable pour éviter la surcharge CPU
4. **Compatibilité** : Compatible avec les versions existantes des scripts

## Support

Pour toute question ou problème, vérifiez :
1. La configuration du driver
2. Les variables de configuration dans `config.py`
3. Les logs d'erreur dans les tests
4. La compatibilité des versions Python/Selenium