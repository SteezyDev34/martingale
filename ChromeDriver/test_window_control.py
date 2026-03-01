# -*- coding: utf-8 -*-
"""
Test de gestion des fenêtres multiples pour le système de paris.
Ce script montre comment utiliser le nouveau système de contrôle des fenêtres
dans un contexte de paris sportifs.
"""
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ChromeDriver.WindowManager import get_window_control
from ChromeDriver.SetDriver1 import driver

# URLs des sites de test
SITE_1 = "https://www.google.com"
SITE_2 = "https://www.youtube.com"

def setup_test_windows():
    """Configure les fenêtres de test"""
    try:
        # Ouvrir Google dans la fenêtre actuelle
        print("\n1️⃣ Ouverture de Google...")
        driver.get(SITE_1)
        time.sleep(2)
        
        # Ouvrir une nouvelle fenêtre pour YouTube
        print("\n2️⃣ Ouverture de YouTube...")
        # Créer une nouvelle fenêtre Chrome avec un handle différent
        driver.execute_script("""
            window.open('', '_blank', 'width=1200,height=800,toolbar=yes,location=yes,menubar=yes,status=yes');
        """)
        
        # Passer à la nouvelle fenêtre
        driver.switch_to.window(driver.window_handles[-1])
        # Charger YouTube dans la nouvelle fenêtre
        driver.get(SITE_2)
        
        # Positionner la nouvelle fenêtre
        driver.set_window_position(50, 50)
        driver.set_window_size(1200, 800)
        
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration des fenêtres : {e}")
        return False

def demo_window_control():
    """Démontre l'utilisation du contrôle des fenêtres"""
    print("\n" + "="*60)
    print("DÉMONSTRATION DU CONTRÔLE DES FENÊTRES")
    print("="*60)
    
    # 1. Contrôler la fenêtre Google
    print("\n🎯 Recherche de la fenêtre Google...")
    window = get_window_control(driver, contains_url='google')
    if window['success']:
        print(f"✅ Fenêtre Google trouvée")
        print(f"   Titre: {window['title']}")
        print(f"   Index: {window['index']}")
        
        # Simuler une action sur Google
        print("   💫 Simulation de recherche sur Google...")
        time.sleep(1)
    
    # 2. Basculer vers la fenêtre YouTube
    print("\n🎯 Recherche de la fenêtre YouTube...")
    window = get_window_control(driver, contains_url='youtube')
    if window['success']:
        print(f"✅ Fenêtre YouTube trouvée")
        print(f"   Titre: {window['title']}")
        print(f"   Index: {window['index']}")
        
        # Simuler une action sur YouTube
        print("   🎵 Simulation de navigation sur YouTube...")
        time.sleep(1)
    
    # 3. Retour à Google par index
    print("\n🎯 Retour à la première fenêtre...")
    window = get_window_control(driver, index=0)
    if window['success']:
        print(f"✅ Retour à la fenêtre principale")
        print(f"   Titre: {window['title']}")
    
    print("\n" + "="*60)
    print("✅ Démonstration terminée")
    print("="*60 + "\n")

def demo_window_control():
    """Démontre l'utilisation du contrôle des fenêtres"""
    print("\n" + "="*60)
    print("DÉMONSTRATION DU CONTRÔLE DES FENÊTRES")
    print("="*60)
    
    # 1. Contrôler la fenêtre 1xBet
    print("\n🎯 Recherche de la fenêtre Google...")
    window = get_window_control(driver, contains_url='1xbet')
    if window['success']:
        print(f"✅ Fenêtre 1xBet trouvée")
        print(f"   Titre: {window['title']}")
        print(f"   Index: {window['index']}")
        
        # Simuler une action sur 1xBet
        print("   💫 Simulation d'actions sur 1xBet...")
        time.sleep(1)
    
    # 2. Basculer vers la fenêtre d'analyse
    print("\n🎯 Recherche de la fenêtre YouTube...")
    window = get_window_control(driver, contains_url='tennisinsight')
    if window['success']:
        print(f"✅ Fenêtre d'analyse trouvée")
        print(f"   Titre: {window['title']}")
        print(f"   Index: {window['index']}")
        
        # Simuler une analyse
        print("   📊 Simulation d'analyse...")
        time.sleep(1)
    
    # 3. Retour à 1xBet par index
    print("\n🎯 Retour à la première fenêtre...")
    window = get_window_control(driver, index=0)
    if window['success']:
        print(f"✅ Retour à la fenêtre principale")
        print(f"   Titre: {window['title']}")
    
    print("\n" + "="*60)
    print("✅ Démonstration terminée")
    print("="*60 + "\n")

def main():
    """Fonction principale de test"""
    try:
        if not setup_test_windows():
            print("❌ Échec de la configuration des fenêtres")
            return
        
        # Attendre que les fenêtres soient bien chargées
        time.sleep(2)
        
        # Démontrer le contrôle des fenêtres
        demo_window_control()
        
        input("\nAppuyez sur Entrée pour terminer...")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")
    
    print("\n✨ Test terminé")

if __name__ == "__main__":
    main()