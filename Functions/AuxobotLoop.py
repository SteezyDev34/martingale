# -*- coding: utf-8 -*-
"""
Boucle de placement automatique des paris non traités (API telegram_bets) via
Selenium/Playwright (Lollybet/Stake), avec suivi sur AuxoTracker.

Usage: ./venv/Scripts/python.exe -m Functions.AuxobotLoop
"""
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
config.localhost = 43151

import requests

from Functions.TelegramBetsAPI import telegram_bets_api
from Functions.GetMise import get_recommended_stake
from Functions.Bookmakers.router import place_best_bet, place_combined_bet
from Functions.PlacerPari import placer_pari
from ChromeDriver.SetDriver import get_script_driver

POLL_INTERVAL = 15
BETWEEN_BETS = 2
XBET_WINDOW = 8
XBET_ENABLED = False


def try_1xbet(matches, tipster, mise):
    """
    Tente le placement sur 1xBet (script legacy réutilisé) avant tout
    bookmaker Playwright/Selenium. En cas d'échec (site, sélecteur, données
    manquantes), retourne success=False pour laisser la loop retomber sur
    Lollybet.
    """
    today = time.strftime('%d/%m/%Y')
    xbet_matches = []
    for m in matches:
        xm = dict(m)
        xm.setdefault('date', today)
        xm.setdefault('categorie', 'Temps réglementaire')
        xm.setdefault('type_de_pari', xm.get('categorie', 'Temps réglementaire'))
        xbet_matches.append(xm)

    code_list = {"matches": xbet_matches, "tipster": tipster}

    try:
        config.mise = mise
        config.cote = float(xbet_matches[0].get("odds") or 0)
        driver = get_script_driver(XBET_WINDOW)
        result = placer_pari(driver, code_list)
    except Exception as e:
        config.log(f"[Loop] ⚠️ 1xBet indisponible: {e}", "warning")
        return {"success": False, "bookmaker": "1xBet", "error": str(e)}

    if isinstance(result, dict):
        success = bool(result.get("success"))
        error = result.get("message") or result.get("error")
    else:
        success = bool(result)
        error = None if success else "echec_1xbet"

    return {"success": success, "bookmaker": "1xBet", "odds": config.cote, "error": error}


def send_bet_to_tracker(bet_id, bookmaker, tipster, sport_id, global_odds, stake, event_list):
    base = getattr(config, 'AUXOTRACK_API_URL', 'https://api.auxotracker.p-com.studio')
    url = f"{base.rstrip('/')}/api/auxobot/bets"
    token = getattr(config, 'AUXOBOT_TOKEN', None)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    payload = {
        "bet_date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "global_odds": float(global_odds or 0),
        "bet_code": f"{bookmaker.lower()}-{bet_id}",
        "result": "pending",
        "stake": float(stake),
        "stake_type": "currency",
        "bankroll_id": 2,
        "tipster": tipster,
        "sport_id": int(sport_id or 1),
        "event_list": event_list,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        r.raise_for_status()
        config.log(f"[AuxoTracker] Pari {bet_id} envoyé au tracker", "info")
        return True
    except Exception as e:
        config.log(f"[AuxoTracker] Erreur envoi pari {bet_id}: {e}", "error")
        return False


def build_event_list(matches):
    return [{
        "equipe_1": m.get("equipe_1", ""),
        "equipe_2": m.get("equipe_2", ""),
        "selection": m.get("selection", ""),
        "odds": float(m.get("odds") or 0),
        "sport_id": int(m.get("sport") or 1),
    } for m in matches]


def process_one_bet(bet):
    bet_id = bet.get("id")

    try:
        sel = json.loads(bet.get("selection") or "{}")
    except (json.JSONDecodeError, TypeError):
        config.log(f"[Loop] Pari {bet_id}: selection JSON invalide", "error")
        telegram_bets_api.mark_bet_as_processed(bet_id, processed=2)
        return

    if not isinstance(sel, dict):
        config.log(f"[Loop] Pari {bet_id}: format selection inattendu", "error")
        telegram_bets_api.mark_bet_as_processed(bet_id, processed=2)
        return

    tipster = sel.get("tipster", "")
    matches = sel.get("matches", [])
    combined_events = sel.get("combined_events")
    ref_odds = matches[0].get("odds") if matches else sel.get("odds")

    try:
        stake_data = get_recommended_stake(cote=ref_odds, tipster=tipster, bankroll_id=2)
        mise = float(stake_data.get("recommended_stake") if stake_data.get("recommended_stake") is not None else 1.0)
    except Exception as e:
        mise = 1.0
        config.log(f"[Loop] ⚠️ Mise fallback 1€ pour pari {bet_id}: {e}", "warning")

    result = None
    try:
        if combined_events:
            # SGM : pas d'équivalent 1xBet, direct sur Stake/Lollybet via router
            match = dict(matches[0]) if matches else dict(sel)
            match["combined_events"] = combined_events
            match["tipster"] = tipster
            match["mise"] = mise
            config.log(f"[Loop] 🎯 SGM pari {bet_id} → Stake", "info")
            result = place_best_bet(match, xbet_driver=None)
        else:
            result = {"success": False}
            # 1. Tentative 1xBet en premier (désactivable via XBET_ENABLED)
            if XBET_ENABLED:
                xbet_matches = matches if matches else [sel]
                config.log(f"[Loop] 🌐 Tentative 1xBet pari {bet_id}", "info")
                result = try_1xbet(xbet_matches, tipster, mise)
                if not result.get("success"):
                    config.log(f"[Loop] ⏭ 1xBet échec ({result.get('error')}) → repli Lollybet", "warning")

            # 2. Lollybet (direct si 1xBet désactivé, ou en repli si échec)
            if not result.get("success"):
                if len(matches) > 1:
                    config.log(f"[Loop] 🎯 Combiné pari {bet_id}: {len(matches)} legs → Lollybet", "info")
                    result = place_combined_bet(matches, mise, xbet_driver=None)
                else:
                    match = dict(matches[0]) if matches else dict(sel)
                    match["tipster"] = tipster
                    match["mise"] = mise
                    config.log(f"[Loop] Pari simple {bet_id}: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info")
                    result = place_best_bet(match, xbet_driver=None)
    except Exception as e:
        config.log(f"[Loop] Exception placement pari {bet_id}: {e}", "error")
        result = {"success": False, "error": str(e)}

    if result and result.get("success"):
        bookmaker = result.get("bookmaker") or "?"
        global_odds = result.get("odds") or ref_odds or 0
        sport_id = (matches[0].get("sport") if matches else sel.get("sport")) or 1
        event_list = build_event_list(matches if matches else [sel])

        telegram_bets_api.mark_bet_as_processed(bet_id, processed=1)
        config.log(f"[Loop] ✅ Pari {bet_id} placé sur {bookmaker} @ {global_odds} (mise={mise}€)", "info")
        send_bet_to_tracker(bet_id, bookmaker, tipster, sport_id, global_odds, mise, event_list)
    else:
        err = result.get("error") if result else "unknown"
        config.log(f"[Loop] ❌ Échec placement pari {bet_id}: {err}", "error")
        telegram_bets_api.mark_bet_as_processed(bet_id, processed=2)


def run_forever():
    config.log("=== Démarrage boucle Auxobot (Lollybet/Stake) ===", "info")
    while True:
        try:
            bets = telegram_bets_api.get_unprocessed_bets(10)
            for bet in bets:
                if not bet:
                    continue
                try:
                    process_one_bet(dict(bet))
                except Exception as e:
                    config.log(f"[Loop] Exception non gérée pari {bet.get('id')}: {e}", "error")
                    try:
                        telegram_bets_api.mark_bet_as_processed(bet.get("id"), processed=2)
                    except Exception:
                        pass
                time.sleep(BETWEEN_BETS)
        except Exception as e:
            config.log(f"[Loop] Erreur boucle générale: {e}", "error")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_forever()
