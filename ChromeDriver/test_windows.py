# -*- coding: utf-8 -*-
"""
Script de test pour la gestion des fenêtres Chrome multiples.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ChromeDriver.SetDriver1 import driver

print("\n" + "="*60)
print("TEST DU SYSTÈME DE GESTION DES FENÊTRES")
print("="*60)

print(f"\n✅ Driver initialisé avec succès")
print(f"📊 Fenêtre active: {driver.title}")
print(f"🌐 URL: {driver.current_url}")
print(f"🪟 Nombre total de fenêtres: {len(driver.window_handles)}")

if len(driver.window_handles) > 1:
    print(f"\n📋 Liste des fenêtres disponibles:")
    for i, handle in enumerate(driver.window_handles):
        current_handle = driver.current_window_handle
        driver.switch_to.window(handle)
        marker = "👉" if handle == current_handle else "  "
        print(f"{marker} {i+1}. {driver.title[:50]} - {driver.current_url[:40]}")
        driver.switch_to.window(current_handle)
else:
    print(f"\nℹ️  Une seule fenêtre détectée")
    print(f"💡 Pour tester avec plusieurs fenêtres:")
    print(f"   1. Ouvrez plusieurs onglets dans Chrome (port 43151)")
    print(f"   2. Relancez ce script")

print("\n" + "="*60)
print("✅ Test terminé avec succès")
print("="*60 + "\n")
