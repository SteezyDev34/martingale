#!/usr/bin/env python3
"""Lance Functions/GetProbas.py dans Docker et récupère les probabilités.

Le script `Functions/GetProbas.py` écrit une ligne marqueur en fin d'exécution:
    __GETPROBAS_JSON__=<json>

Ce launcher capture cette ligne et la parse pour vous permettre de récupérer un
dict Python depuis votre code.

Usage:
    python3 tools/run_getprobas_docker.py
"""

import os
import subprocess
import json
from datetime import datetime


_JSON_MARKER_PREFIX = "__GETPROBAS_JSON__="


def build_getprobas_service() -> None:
    """Construit le service Docker `getprobas`.

    Raises:
        RuntimeError: si le build échoue.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(project_root)

    try:
        build = subprocess.call(["docker", "compose", "build", "getprobas"])
    except FileNotFoundError:
        raise RuntimeError("Docker est introuvable (installe Docker Desktop).")

    if build != 0:
        raise RuntimeError(f"Échec docker compose build (code={build}).")


def run_getprobas(playerName1: str, playerName2: str, *, build: bool = True, stream_output: bool = True) -> dict:
    """Exécute GetProbas dans Docker et retourne le dict des probabilités.

    Args:
        playerName1 (str): Nom du joueur 1
        playerName2 (str): Nom du joueur 2

    Returns:
        dict: Dictionnaire {"event": prob} calculé par GetProbas.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(project_root)

    try:
        if build:
            build_getprobas_service()

        if not playerName1 or not playerName2:
            raise RuntimeError("playerName1 et playerName2 ne doivent pas être vides.")

        cmd = [
            "docker",
            "compose",
            "run",
            "--rm",
            "-T",
            "-e",
            f"GETPROBAS_PLAYER1={playerName1}",
            "-e",
            f"GETPROBAS_PLAYER2={playerName2}",
            "getprobas",
            "python",
            "-u",
            "Functions/GetProbas.py",
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        json_payload = None
        assert proc.stdout is not None
        for line in proc.stdout:
            if stream_output:
                print(line, end="")
            if line.startswith(_JSON_MARKER_PREFIX):
                json_payload = line[len(_JSON_MARKER_PREFIX):].strip()

        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"Le container s'est terminé en erreur (code={rc}).")

        if not json_payload:
            raise RuntimeError(
                "Impossible de récupérer la sortie JSON. "
                "Vérifie que GetProbas affiche bien la ligne __GETPROBAS_JSON__=."
            )

        parsed = json.loads(json_payload)
        if not isinstance(parsed, dict):
            raise RuntimeError("La sortie JSON ne contient pas un dict.")
        return parsed
    except FileNotFoundError:
        raise RuntimeError("Docker est introuvable (installe Docker Desktop).")


def main() -> int:
    try:
        # Variables à envoyer au container Docker
        




        playerName1 = "Valentin Vacherot"
        playerName2 = "Nuno Borges"

        probas = run_getprobas(playerName1, playerName2)
        print("\nProbas récupérées (dict Python):")
        print(probas)

        output_path = os.path.join(os.getcwd(), "proba_match.json")

        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "player1": playerName1,
            "player2": playerName2,
            "probas": probas,
        }

        history = []
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

                if isinstance(existing, list):
                    history = existing
                elif isinstance(existing, dict):
                    # Compatibilité : ancien format où le fichier contenait un dict unique.
                    history = [existing]
                else:
                    raise RuntimeError("Format JSON inattendu dans proba_match.json (attendu: liste ou dict).")
            except json.JSONDecodeError:
                raise RuntimeError("proba_match.json existe mais n'est pas un JSON valide.")

        history.append(entry)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"\nFichier mis à jour: {output_path} (entrées={len(history)})")

        # Génère automatiquement la sélection des top matchs par événement
        # S'assurer que le projet racine est dans sys.path pour importer `tools`
        import sys
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            from tools.select_top_matches import select_top_matches
        except Exception as exc:
            print(f"Erreur d'import de tools.select_top_matches: {exc}")
            select_top_matches = None

        selection = select_top_matches(history) if select_top_matches else []
        selection_path = os.path.join(os.getcwd(), "selection_match.json")
        with open(selection_path, "w", encoding="utf-8") as f:
            json.dump(selection, f, ensure_ascii=False, indent=2)
        print(f"Sélection mise à jour: {selection_path} (matchs sélectionnés={len(selection)})")

        return 0
    except Exception as exc:
        print(f"Erreur: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
