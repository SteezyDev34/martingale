"""
Boucle autonome de placement des paris Telegram en file d'attente — remplace les
appels manuels/répétés au skill Claude Code "/loop". Pur Python, aucun coût LLM :
appelle process_api_bets() en continu, avec une pause entre chaque passage.
"""
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from Functions.ProcessTelegramBets import process_api_bets
from Functions.Logs.Logger import log

POLL_INTERVAL = 30  # secondes entre deux passages de la file d'attente
HEARTBEAT_EVERY = 10  # passages silencieux avant un message "toujours en vie"


def main():
    log("🔁 Boucle de placement des paris démarrée", "info")
    silent_cycles = 0
    while True:
        try:
            processed = process_api_bets(limit=10)
            if processed:
                log(f"✅ {processed} pari(s) traité(s) ce passage", "info")
                silent_cycles = 0
            else:
                # process_api_bets() ne log rien si la file est vide -- sans ce
                # heartbeat, la boucle semble "bloquée" pendant les silences
                # (observé le 2026-10-16 : confusion de l'utilisateur en lancant
                # process_bets_loop.py avec aucun pari en attente).
                silent_cycles += 1
                if silent_cycles >= HEARTBEAT_EVERY:
                    log(f"😴 Toujours en vie, aucun pari en attente depuis {silent_cycles * POLL_INTERVAL}s", "info")
                    silent_cycles = 0
        except Exception as e:
            log(f"⚠️ Erreur pendant process_api_bets: {e}", "error")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
