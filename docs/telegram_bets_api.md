# API Telegram Bets

Cette API permet de stocker et gérer les paris extraits automatiquement des messages Telegram via GPT.

## Structure de l'API

### Endpoints disponibles

- **POST** `/api/telegram_bets/insert.php` - Insérer un nouveau pari
- **GET** `/api/telegram_bets/get.php` - Récupérer les paris avec filtres
- **POST** `/api/telegram_bets/update.php` - Mettre à jour le statut d'un pari
- **DELETE** `/api/telegram_bets/delete.php` - Supprimer un pari
- **GET** `/api/telegram_bets/index.php` - Documentation et statistiques

### Format des données

#### Insertion d'un pari

```json
{
  "date": "25/09/2025",
  "equipe_1": "Al Shabab Riyadh",
  "equipe_2": "Al Kholood",
  "categorie": "Temps réglementaire",
  "type_de_pari": "Total 1",
  "selection": "Total Individuel 1 Plus de 0.5",
  "odds": "1.432",
  "message_original": "Message telegram original (optionnel)",
  "sender_username": "@username (optionnel)"
}
```

## Utilisation en Python

### Classe TelegramBetsAPI

```python
from Functions.TelegramBetsAPI import telegram_bets_api

# Envoyer un pari
bet_data = {
    "date": "20/10/2025",
    "equipe_1": "Equipe A",
    "equipe_2": "Equipe B",
    "categorie": "Temps réglementaire",
    "type_de_pari": "Vainqueur",
    "selection": "V1",
    "odds": "2.50",
}

success = telegram_bets_api.send_bet_to_api(bet_data, "Message original", "@sender")

# Récupérer les paris non traités
unprocessed = telegram_bets_api.get_unprocessed_bets(limit=10)

# Marquer un pari comme traité
telegram_bets_api.mark_bet_as_processed(bet_id=123)
```

### Fonctions utilitaires

```python
from Functions.TelegramBetsAPI import (
    send_bet_data_to_api,
    get_unprocessed_telegram_bets,
    mark_telegram_bet_processed
)

# Utilisation simplifiée
send_bet_data_to_api(bet_data)
bets = get_unprocessed_telegram_bets()
mark_telegram_bet_processed(123)
```

## Intégration dans le script WATCH

Le script `SCRIPTS WATCH/main.py` a été modifié pour :

1. **Envoyer automatiquement** les paris détectés vers l'API
2. **Traiter périodiquement** les paris stockés dans l'API (toutes les 5 minutes)
3. **Maintenir la compatibilité** avec le système de paris en temps réel

### Flux de traitement

```
Message Telegram → GPT → Extraction données → API + betList local
                                                 ↓
                                           Traitement périodique
```

## Scripts d'administration

### Script de gestion

```bash
# Mode interactif
python tools/manage_telegram_bets.py --interactive

# Afficher les statistiques
python tools/manage_telegram_bets.py --stats

# Lister les paris non traités
python tools/manage_telegram_bets.py --list --unprocessed --limit 10

# Filtrer par tipster
python tools/manage_telegram_bets.py --list --tipster marco

# Marquer un pari comme traité
python tools/manage_telegram_bets.py --mark-processed 123
```

### Script de traitement

```python
from Functions.ProcessTelegramBets import process_api_bets, monitor_telegram_bets

# Traiter les paris en attente
processed_count = process_api_bets(driver, limit=5)

# Afficher les statistiques
monitor_telegram_bets()
```

## Base de données

### Table `telegram_bets`

| Champ              | Type          | Description                         |
|--------------------|---------------|-------------------------------------|
| `id`               | INT           | Identifiant unique (auto-increment) |
| `date_pari`        | VARCHAR(20)   | Date du pari (DD/MM/YYYY)           |
| `equipe_1`         | VARCHAR(255)  | Première équipe/joueur              |
| `equipe_2`         | VARCHAR(255)  | Deuxième équipe/joueur              |
| `categorie`        | VARCHAR(100)  | Catégorie du pari                   |
| `type_de_pari`     | VARCHAR(255)  | Type de pari                        |
| `selection`        | VARCHAR(500)  | Sélection effectuée                 |
| `odds`             | DECIMAL(10,3) | Cote du pari                        |
| `tipster`          | VARCHAR(50)   | Nom du tipster                      |
| `message_original` | TEXT          | Message Telegram original           |
| `sender_username`  | VARCHAR(100)  | Username de l'expéditeur            |
| `created_at`       | TIMESTAMP     | Date de création                    |
| `processed`        | BOOLEAN       | Pari traité (défaut: FALSE)         |

### Index

- `idx_processed` sur le champ `processed`
- `idx_date_pari` sur le champ `date_pari`
- `idx_tipster` sur le champ `tipster`

## Avantages du système

1. **Persistance** : Les paris sont stockés même en cas d'arrêt du bot
2. **Traçabilité** : Historique complet des paris reçus
3. **Flexibilité** : Traitement asynchrone et gestion des erreurs
4. **Statistiques** : Analyse des performances par tipster
5. **Administration** : Interface pour gérer les paris manuellement

## Sécurité

- Validation des données d'entrée
- Gestion des erreurs de base de données
- Headers CORS configurés
- Timeout sur les requêtes HTTP

## Monitoring

L'API fournit automatiquement :

- Nombre total de paris
- Paris traités vs non traités
- Nombre de tipsters uniques
- Répartition par catégorie et tipster
