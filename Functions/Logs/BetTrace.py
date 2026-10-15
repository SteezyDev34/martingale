# -*- coding: utf-8 -*-
"""
Trace forensique par pari pour le pipeline /loop (process_api_bets -> router.py ->
StakeScraper/LollybetScraper/XBetScraper). Objectif : à chaque pari en échec,
pouvoir revenir dessus après coup (relire la séquence d'étapes + une capture
d'écran de ce qu'il y avait à l'écran au moment de l'échec) sans avoir à
reproduire le bug en live.

Usage :
    trace_dir = BetTrace.start(bet_id, {"tipster": ..., "match": ...})
    BetTrace.step(trace_dir, "mise_calculee", "2.0€")
    BetTrace.step(trace_dir, "placement_tente", "Stake @ 1.85")
    ...
    BetTrace.capture_failure(trace_dir, "selecteur introuvable", driver=driver)
    # ou, pour Stake/1xBet (bridge extension) :
    BetTrace.capture_failure(trace_dir, "selecteur introuvable", bridge=stake_bridge)

Ne lève jamais — une erreur dans le trace lui-même ne doit jamais faire
planter le vrai traitement du pari.
"""
import json
import os
import time
from datetime import datetime

import config

TRACE_ROOT = os.path.join(config.projectPath, "Logs", "bet_traces")


def start(bet_id, context: dict = None) -> str:
    """Crée le dossier de trace pour ce pari, écrit le contexte initial, retourne son chemin."""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        trace_dir = os.path.join(TRACE_ROOT, date_str, str(bet_id))
        os.makedirs(trace_dir, exist_ok=True)
        with open(os.path.join(trace_dir, "context.json"), "w", encoding="utf-8") as f:
            json.dump(context or {}, f, ensure_ascii=False, indent=2, default=str)
        step(trace_dir, "start", context or {})
        return trace_dir
    except Exception as e:
        print(f"[BetTrace] start échoué pour bet_id={bet_id}: {e}")
        return None


def step(trace_dir, label: str, detail=None, level: str = "info"):
    """Ajoute une ligne à trace.jsonl (une étape de la séquence)."""
    if not trace_dir:
        return
    try:
        entry = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": level,
            "label": label,
            "detail": detail,
        }
        with open(os.path.join(trace_dir, "trace.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        print(f"[BetTrace] step échoué ({label}): {e}")


def capture_failure(trace_dir, error, driver=None, bridge=None, tag: str = "error"):
    """
    Capture une screenshot au moment de l'échec (Selenium `driver` OU bridge extension
    Chrome `bridge`, selon le bookmaker) et finalise le trace avec l'erreur. Retourne
    le chemin de la screenshot (ou None si indisponible/échouée).
    """
    if not trace_dir:
        return None

    screenshot_path = None
    ts = int(time.time() * 1000)
    png_path = os.path.join(trace_dir, f"screenshot_{tag}_{ts}.png")

    try:
        if driver is not None:
            driver.save_screenshot(png_path)
            screenshot_path = png_path
        elif bridge is not None:
            screenshot_path = bridge.capture_screenshot(save_path=png_path)
    except Exception as e:
        print(f"[BetTrace] capture_failure screenshot échouée: {e}")

    step(trace_dir, "failure", {"error": str(error), "screenshot": screenshot_path}, level="error")
    return screenshot_path
