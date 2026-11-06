"""
Script de debug UNIQUEMENT lecture : se connecte à l'extension Chrome sur le
port de debug manuel (9999) et liste les options de catégorie actuellement
visibles dans le DOM (.game-sub-games__list) sur l'onglet 1xBet ouvert --
pour diagnostiquer "category_list_not_found" vu en live sur plusieurs
matchs/scriptTypes le 2026-11-06 (Functions/AfficherParis.py, log ajouté
pour exposer cette raison d'échec jusque-là silencieuse).

Pré-requis avant de lancer :
1. Avoir rechargé l'extension dans chrome://extensions si elle a été
   modifiée récemment.
2. Avoir Chrome ouvert avec un onglet sur la page MOBILE d'un match 1xBet
   en cours (celle que le bot utiliserait), avec l'onglet "Événements
   rapides" (ou équivalent) visible à l'écran.
3. Port 9999 (seul port "usage manuel/debug" connu de l'extension) : doit
   être libre. SCRIPTS_WATCH/main-1.py l'utilise en continu -- l'arrêter
   temporairement (Ctrl+C) le temps du diagnostic, puis le relancer.
   Vérifier avec `lsof -nP -iTCP:9999 -sTCP:LISTEN` avant de lancer.

Usage :
    venv/bin/python3 debug_category_list.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from websocket_server import start_bridge, bridge

print("Démarrage du bridge sur le port 9999 (attente de connexion de l'extension Chrome)...")
start_bridge(wait_timeout=30, port=9999)
print("Bridge connecté.")

# Le bridge ne sait associer un onglet à CETTE connexion qu'après un navigate()
# explicite (cf. service_worker.js resolveTabId) -- sans ça, toute commande
# renvoie 'no_tab' même si un onglet 1xBet est déjà ouvert. Si l'URL donnée
# est déjà celle affichée, l'extension ne recharge pas la page (pas de
# perturbation de l'onglet déjà ouvert).
url = input("Colle l'URL complète de l'onglet 1xBet déjà ouvert sur le match : ").strip()
nav = bridge.navigate(url)
print("navigate ack:", nav)

print("Lecture de la page...")
result = bridge.debug_list_category_options()
print()
print("Résultat brut :", result)
print()
if result.get('success'):
    options = result.get('options', [])
    print(f"{len(options)} option(s) trouvée(s) dans .game-sub-games__list :")
    for o in options:
        print(f"  - {o!r}")
    if not options:
        print("  (liste vide ou conteneur trouvé mais sans item .game-sub-games__item)")
else:
    print(f"Échec : {result.get('error')} -- le conteneur .game-sub-games__list lui-même est introuvable sur la page actuelle.")
    print("Vérifier dans Chrome (clic droit > Inspecter) si cette classe existe toujours, ou si la page est sur la bonne vue (mobile, onglet marché visible).")
