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


def main():
    log("🔁 Boucle de placement des paris démarrée", "info")
    while True:
        try:
            processed = process_api_bets(limit=10)
            if processed:
                log(f"✅ {processed} pari(s) traité(s) ce passage", "info")
        except Exception as e:
            log(f"⚠️ Erreur pendant process_api_bets: {e}", "error")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
