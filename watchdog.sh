#!/bin/bash
# Watchdog du bot Telegram (main-1-server.py) — relance le process s'il n'est
# pas actif. Conçu pour tourner via cron toutes les 5 minutes :
#   */5 * * * * bash /home2/sc2vagr6376/api.auxotracker/bot-telegram/watchdog.sh
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$PROJECT_DIR/main-1-server.py"
PYTHON="$PROJECT_DIR/venv/bin/python3"
LOG="$PROJECT_DIR/bot.log"
LOCK="$PROJECT_DIR/.watchdog.lock"

# Évite les lancements concurrents si le watchdog précédent tourne encore
if ! mkdir "$LOCK" 2>/dev/null; then
    exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

if pgrep -f "$SCRIPT" > /dev/null 2>&1; then
    exit 0
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') : ⚠️  Bot Telegram absent, redémarrage..." >> "$LOG"
cd "$PROJECT_DIR" || exit 1
nohup "$PYTHON" "$SCRIPT" >> "$LOG" 2>&1 &
disown
echo "$(date '+%Y-%m-%d %H:%M:%S') : ✅ Bot Telegram relancé (PID $!)" >> "$LOG"
