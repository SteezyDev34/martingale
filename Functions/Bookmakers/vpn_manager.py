# -*- coding: utf-8 -*-
"""
Gestionnaire VPN CyberGhost pour macOS.
Active/désactive le VPN selon le bookmaker (Stake.bet et 1xBet nécessitent Toronto).
"""
import subprocess
import time
import os
from Functions.Logs.Logger import log

# Chemins possibles du binaire CyberGhost sur macOS
_CYBERGHOST_BINS = [
    "/usr/local/bin/cyberghostvpn",
    "/usr/bin/cyberghostvpn",
    os.path.expanduser("~/Applications/CyberGhost VPN.app/Contents/MacOS/CyberGhost VPN"),
    "/Applications/CyberGhost VPN.app/Contents/MacOS/CyberGhost VPN",
]

VPN_COUNTRY = "CA"      # Canada
VPN_CITY    = "Toronto"


def _find_bin():
    for path in _CYBERGHOST_BINS:
        if os.path.isfile(path):
            return path
    # Tentative via `which`
    try:
        result = subprocess.run(["which", "cyberghostvpn"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _run(args, timeout=30):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def is_connected() -> bool:
    """Vérifie si le VPN est actif."""
    bin_path = _find_bin()
    if not bin_path:
        return False
    code, output = _run([bin_path, "--status"])
    return "connected" in output.lower() or "actif" in output.lower()


def connect(country: str = VPN_COUNTRY, city: str = VPN_CITY) -> bool:
    """Active le VPN CyberGhost sur Toronto."""
    if is_connected():
        log("[VPN] Déjà connecté", "info")
        return True

    bin_path = _find_bin()
    if not bin_path:
        log("[VPN] ❌ Binaire CyberGhost introuvable", "error")
        _notify_vpn_error("Binaire CyberGhost introuvable — VPN non activé")
        return False

    log(f"[VPN] Connexion à {city} ({country})...", "info")
    code, output = _run([bin_path, "--connect", "--country-code", country, "--city", city], timeout=60)
    if code != 0:
        # Certaines versions n'acceptent pas --city, réessayer sans
        code, output = _run([bin_path, "--connect", "--country-code", country], timeout=60)

    if code == 0 or is_connected():
        log(f"[VPN] ✅ VPN activé ({city})", "info")
        time.sleep(3)  # laisser le réseau se stabiliser
        return True

    log(f"[VPN] ❌ Échec connexion VPN: {output}", "error")
    _notify_vpn_error(f"Impossible d'activer le VPN ({output[:100]})")
    return False


def disconnect() -> bool:
    """Désactive le VPN CyberGhost."""
    bin_path = _find_bin()
    if not bin_path:
        return True  # pas de CyberGhost installé = pas de VPN à couper

    if not is_connected():
        return True

    log("[VPN] Déconnexion...", "info")
    code, output = _run([bin_path, "--disconnect"], timeout=30)
    if code == 0 or not is_connected():
        log("[VPN] ✅ VPN désactivé", "info")
        time.sleep(2)
        return True

    log(f"[VPN] ❌ Échec déconnexion VPN: {output}", "error")
    return False


def _notify_vpn_error(message: str):
    try:
        from Functions.Functions_telegram import send_telegram, alertGroup
        send_telegram(alertGroup, f"⚠️ #VPN_ERREUR\n{message}")
    except Exception:
        pass
