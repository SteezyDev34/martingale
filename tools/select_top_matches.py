#!/usr/bin/env python3
"""Sélectionne les 20 meilleurs matchs par événement depuis proba_match.json.

Pour chaque clé d'événement (15_0, 0_15, 40_40_first10, etc.),
on trie les matchs par probabilité décroissante et on retient les 20 premiers.

Un fichier `selection_match.json` est produit avec, pour chaque match
apparaissant dans au moins un top 20, un champ `selected` listant les
événements pour lesquels il a été retenu.

Usage:
    python3 tools/select_top_matches.py
    python3 tools/select_top_matches.py --top 10
    python3 tools/select_top_matches.py --input proba_match.json --output selection_match.json
"""

import json
import os
import sys
from collections import defaultdict


# Nombre de matchs retenus par événement (modifiable via --top)
DEFAULT_TOP_N = 20

# Chemins par défaut
DEFAULT_INPUT = "proba_match.json"
DEFAULT_OUTPUT = "selection_match.json"


def select_top_matches(matches: list[dict], top_n: int = DEFAULT_TOP_N) -> list[dict]:
    """Sélectionne les meilleurs matchs par événement.

    Args:
        matches (list[dict]): Liste des entrées de proba_match.json
        top_n (int): Nombre de matchs à retenir par événement

    Returns:
        list[dict]: Liste des matchs sélectionnés avec le champ "selected"
    """
    # Collecter toutes les clés d'événements présentes dans au moins un match
    all_event_keys: set[str] = set()
    for m in matches:
        probas = m.get("probas", {})
        all_event_keys.update(probas.keys())

    # Pour chaque événement, trier les matchs par proba décroissante et prendre les top_n
    # On identifie chaque match par son index dans la liste d'entrée
    selected_events_by_index: dict[int, list[str]] = defaultdict(list)

    for event_key in sorted(all_event_keys):
        # Construire la liste (index, proba) pour cet événement
        scored = []
        for idx, m in enumerate(matches):
            prob = m.get("probas", {}).get(event_key)
            if prob is not None:
                scored.append((idx, float(prob)))

        # Trier par probabilité décroissante
        scored.sort(key=lambda x: x[1], reverse=True)

        # Retenir les top_n
        for idx, _prob in scored[:top_n]:
            selected_events_by_index[idx].append(event_key)

    # Construire la liste de sortie : uniquement les matchs sélectionnés
    result = []
    for idx in sorted(selected_events_by_index.keys()):
        m = matches[idx]
        entry = {
            "timestamp": m.get("timestamp", ""),
            "player1": m.get("player1", ""),
            "player2": m.get("player2", ""),
            "selected": sorted(selected_events_by_index[idx]),
            "probas": m.get("probas", {}),
        }
        result.append(entry)

    return result


def main() -> int:
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Sélection des top matchs par événement")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Fichier d'entrée (proba_match.json)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Fichier de sortie (selection_match.json)")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="Nombre de matchs par événement (défaut: 20)")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    if not os.path.exists(input_path):
        print(f"Erreur: fichier introuvable: {input_path}")
        return 1

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Ancien format : un seul match
        data = [data]

    if not isinstance(data, list):
        print("Erreur: le fichier JSON doit contenir une liste ou un dict.")
        return 1

    print(f"Matchs chargés: {len(data)}")
    print(f"Top {args.top} par événement")

    selection = select_top_matches(data, top_n=args.top)

    print(f"Matchs sélectionnés: {len(selection)}")

    # Écrire le fichier de sortie
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(selection, f, ensure_ascii=False, indent=2)

    print(f"Fichier écrit: {output_path}")

    # Résumé par événement
    event_counts: dict[str, int] = defaultdict(int)
    for m in selection:
        for ek in m.get("selected", []):
            event_counts[ek] += 1

    print("\nRésumé par événement:")
    for ek in sorted(event_counts.keys()):
        print(f"  {ek}: {event_counts[ek]} match(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
