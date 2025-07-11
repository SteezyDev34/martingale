import json

# Charger le fichier JSON
with open("tennis_stats_cache.json", "r") as f:
    data = json.load(f)

# Supprimer les stats des joueurs ayant une valeur de 0
data_filtré = {k: v for k, v in data.items() if not (k.startswith("player_") and v == 0)}

# Sauvegarder le fichier nettoyé
with open("fichier_nettoye.json", "w") as f:
    json.dump(data_filtré, f, indent=2)
