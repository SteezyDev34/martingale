# -*- coding: utf-8 -*-
"""
Test d'ouverture de Chrome sur le port 43151 avec 3 fenêtres différentes.
Ce script ouvre 3 fenêtres Chrome distinctes via Selenium sur le même port.
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import subprocess
import socket
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROME_DRIVER_PATH = os.path.join(os.path.dirname(__file__), 'chromedriver')
DEBUG_PORT = 43151



print("\n" + "="*60)
print("TEST : OUVERTURE DE 3 FENÊTRES CHROME")
print("="*60)

# Créer une nouvelle instance de Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Démarrer avec fenêtre maximisée
chrome_options.add_argument("--disable-infobars")  # Désactiver les infobars
chrome_options.add_argument("--disable-extensions")  # Désactiver les extensions
chrome_options.add_argument("--disable-popup-blocking")  # Autoriser les popups
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Cacher le message "Chrome est contrôlé par un logiciel..."
chrome_options.add_experimental_option("detach", True)  # Garder les fenêtres ouvertes après la fin du script

try:
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
    # Définir une taille initiale pour la première fenêtre
    driver.set_window_size(1000, 800)
    driver.set_window_position(0, 0)
except Exception as e:
    print(f"❌ Impossible de démarrer Chrome : {e}")
    exit(1)

# Ouvrir 3 fenêtres différentes
urls = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.duckduckgo.com/"
]

# Configuration de l'attente implicite
driver.implicitly_wait(10)

# Ouvrir la première URL dans la fenêtre actuelle
initial_handle = driver.current_window_handle
driver.get(urls[0])
print(f"✅ Fenêtre 1 ouverte sur {urls[0]}")

# Ouvrir les autres URLs dans de nouvelles fenêtres séparées
for i in range(1, len(urls)):
    try:
        # Ouvrir une nouvelle fenêtre vide
        driver.execute_script("window.open('about:blank', '_blank', 'width=1000,height=800')")
        time.sleep(1)
        
        # Passer à la nouvelle fenêtre
        driver.switch_to.window(driver.window_handles[-1])
        
        # Charger l'URL dans la nouvelle fenêtre
        driver.get(urls[i])
        
        # Positionner la fenêtre (en cascade)
        x_pos = i * 50
        y_pos = i * 50
        driver.set_window_position(x_pos, y_pos)
        driver.set_window_size(1000, 800)
        
        print(f"✅ Fenêtre {i+1} ouverte sur {urls[i]}")
        time.sleep(1)
    
    except Exception as e:
        print(f"❌ Impossible d'ouvrir la fenêtre {i+1} : {e}")
        
    except Exception as e:
        print(f"❌ Impossible d'ouvrir la fenêtre {i+1} : {e}")

print(f"\n🪟 Nombre total de fenêtres ouvertes : {len(driver.window_handles)}")

urls = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.duckduckgo.com/"
]

for i, handle in enumerate(driver.window_handles[:3]):
    driver.switch_to.window(handle)
    driver.get(urls[i])
    print(f"{i+1}. {driver.title} - {driver.current_url}")

print("\n" + "="*60)
print("✅ Test terminé avec succès")
print("="*60 + "\n")
