import os
import sys
import time

# Ajouter le répertoire parent au PYTHONPATH
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from ChromeDriver.SetDriver import get_script_driver

print("\n" + "="*60)
print("TEST DE CRÉATION DE FENÊTRES MULTIPLES")
print("="*60 + "\n")

try:
    # Tentative d'obtenir la première fenêtre
    print("1️⃣ Test de la fenêtre 1...")
    driver1 = get_script_driver(1)
    if driver1:
        print("   ✅ Fenêtre 1 obtenue avec succès")
        driver1.get("https://www.google.com")
        print("   ✅ Page Google chargée dans la fenêtre 1")
        time.sleep(2)
    else:
        print("   ❌ Échec de l'obtention de la fenêtre 1")
        sys.exit(1)

    # Tentative d'obtenir la deuxième fenêtre
    print("\n2️⃣ Test de la fenêtre 2...")
    driver2 = get_script_driver(2)
    if driver2:
        print("   ✅ Fenêtre 2 obtenue avec succès")
        driver2.get("https://www.github.com")
        print("   ✅ Page GitHub chargée dans la fenêtre 2")
        time.sleep(2)
    else:
        print("   ❌ Échec de l'obtention de la fenêtre 2")

    # Tentative d'obtenir la troisième fenêtre
    print("\n3️⃣ Test de la fenêtre 3...")
    driver3 = get_script_driver(3)
    if driver3:
        print("   ✅ Fenêtre 3 obtenue avec succès")
        driver3.get("https://www.python.org")
        print("   ✅ Page Python.org chargée dans la fenêtre 3")
        time.sleep(2)
    else:
        print("   ❌ Échec de l'obtention de la fenêtre 3")

    # Test de basculement entre les fenêtres
    print("\n🔄 Test de basculement entre les fenêtres...")
    
    # Retour à la fenêtre 1
    driver1 = get_script_driver(1)
    if driver1:
        print("   ✅ Retour à la fenêtre 1 réussi")
        print(f"   📍 URL actuelle: {driver1.current_url}")
    
    # Basculement vers la fenêtre 2
    driver2 = get_script_driver(2)
    if driver2:
        print("   ✅ Basculement vers la fenêtre 2 réussi")
        print(f"   📍 URL actuelle: {driver2.current_url}")

    print("\n✨ Test terminé avec succès")

except Exception as e:
    print(f"\n❌ Erreur lors du test : {e}")

print("\n" + "="*60)
input("Appuyez sur Entrée pour terminer...")
print("="*60 + "\n")