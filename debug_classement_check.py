"""
Script de debug UNIQUEMENT lecture : exécute juste la phase de classement
(scraping 1xBet + appels AuxoTracker /api/matches/tennis/link) pour comparer
avec la liste de référence AuxoTracker (/api/matches/today), SANS jamais
appeler Functions_XXX.all_script / aucune logique de pari.

Pré-requis avant de lancer :
1. Avoir rechargé l'extension dans chrome://extensions (le fix ITF dans
   chrome_extension/content_scripts/1xbet.js ne prend effet qu'après reload).
2. Avoir Chrome ouvert avec un onglet sur le site de paris 1xBet (ligue/line),
   connecté au port 9999 (port de debug manuel, ne touche pas aux ports
   9001-9016/9101-9102 utilisés par les bots en prod).
3. Aucun bot de prod ne doit tourner en même temps sur le port 9999.

Sortie : DataFiles/debug_classement_<timestamp>.json avec :
  - matchlist_brute : tous les matchs scrapés sur 1xBet (full menu)
  - par_match_api   : pour chaque match, le résultat de l'appel AuxoTracker
                       (introuvable / échec API / scriptTypes trouvés)
  - goodmatch       : matchs avec au moins un scriptType actif
  - top_matches     : tous les matchs qualifiés, dans l'ordre de priorité par
                       ligue (ATP > Challenger > WTA > ITF) — plus de plafond
"""
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from websocket_server import start_bridge

print("Démarrage du bridge sur le port 9999 (attente de connexion de l'extension Chrome)...")
start_bridge(wait_timeout=30, port=9999)
print("Bridge connecté.")

config.site_type = 'new_site'

from Functions.ScriptRechercheDeMatch import _bridge_scan_matchlist_full, traiter_matchlist

# Capture des logs [auxotracker]/ScriptTypes API pour reconstituer, par match,
# si l'appel AuxoTracker a réussi, échoué, ou n'a rien trouvé.
api_trace = []
_orig_log = config.log
def _capture(message, *a, **kw):
    msg = str(message)
    if msg.startswith('[auxotracker]') or msg.startswith('ScriptTypes API (') or msg.startswith('Aucun scriptType activé'):
        api_trace.append(msg)
    return _orig_log(message, *a, **kw)
config.log = _capture

print("Scraping complet des ligues 1xBet (menu complet, peut prendre 1-3 min)...")
matchlist = _bridge_scan_matchlist_full()
print(f"Matchlist brute : {len(matchlist)} matchs")

print("Appel AuxoTracker par match (peut prendre plusieurs minutes pour un classement complet)...")
goodmatch = traiter_matchlist([list(m) for m in matchlist])  # copie pour ne pas muter l'original
print(f"{len(goodmatch)}/{len(matchlist)} matchs avec au moins un scriptType actif")

config.log = _orig_log  # restaure le logger normal

tableau_trie = sorted(goodmatch, key=lambda x: x[4], reverse=True)


def prioritize_matches_by_league(matches):
    # Plus de plafond (retiré du code de prod le 2026-10-17) : ordre de
    # priorité par ligue uniquement, tous les matchs qualifiés sont gardés.
    priority_groups = {i: [] for i in range(1, 9)}
    for match in matches:
        ligue_name = match[1].lower()
        has_qualification = 'qualification' in ligue_name
        if 'atp' in ligue_name:
            priority = 4 if has_qualification else 1
        elif 'challenger' in ligue_name:
            priority = 5 if has_qualification else 2
        elif any(wta_term in ligue_name for wta_term in ['wta', 'féminin', 'femmes', 'women']):
            priority = 6 if has_qualification else 3
        elif 'itf' in ligue_name or 'world tennis' in ligue_name:
            priority = 8 if has_qualification else 7
        else:
            priority = 8
        priority_groups[priority].append(match)

    final_matches = []
    for priority in sorted(priority_groups.keys()):
        group_sorted = sorted(priority_groups[priority], key=lambda x: x[4], reverse=True)
        final_matches.extend(group_sorted)
    return final_matches


top_matches = prioritize_matches_by_league(tableau_trie)
print(f"Matchs retenus (sans plafond) : {len(top_matches)}")

output = {
    "timestamp": datetime.now().isoformat(),
    "matchlist_brute": [
        {"players": m[0], "ligue": m[1], "match_id": m[2], "date": m[3]}
        for m in matchlist
    ],
    "api_trace": api_trace,
    "goodmatch": [
        {"players": m[0], "ligue": m[1], "proba40A": m[4], "script_types": m[6]}
        for m in goodmatch
    ],
    "top_matches": [
        {"players": m[0], "ligue": m[1], "proba40A": m[4], "script_types": m[6]}
        for m in top_matches
    ],
}

out_path = os.path.join(config.projectPath, "DataFiles", f"debug_classement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Résultat écrit dans : {out_path}")
