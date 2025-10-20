# -*- coding: utf-8 -*-
"""
Script pour sélectionner la fenêtre 2 et naviguer vers Google.
"""
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ChromeDriver.SetDriver1 import driver

print("\n" + "="*60)
print("UTILISATION DE LA FENÊTRE 2 ET NAVIGATION VERS GOOGLE")
print("="*60)

window_handles = driver.window_handles
if len(window_handles) < 2:
    print("❌ Moins de 2 fenêtres détectées. Veuillez ouvrir au moins deux fenêtres Chrome (pas juste des onglets) sur le port 43151 et relancer le script.")
    exit(1)

# Sélection de la fenêtre 2 (index 1)
driver.switch_to.window(window_handles[1])
print(f"✅ Fenêtre 2 sélectionnée : {driver.title} - {driver.current_url}")

# Aller sur Google
driver.get("https://www.google.com/")
print(f"🌐 Navigué vers Google : {driver.title} - {driver.current_url}")

print("\n" + "="*60)
print("✅ Script terminé avec succès")
print("="*60 + "\n")
