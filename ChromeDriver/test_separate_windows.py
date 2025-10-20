# -*- coding: utf-8 -*-
"""
Test d'ouverture de véritables fenêtres Chrome séparées (pas des onglets)
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
import subprocess

# Chemin du chromedriver
CHROME_DRIVER_PATH = os.path.join(os.path.dirname(__file__), 'chromedriver')

def check_url_in_windows(driver, url):
    """
    Vérifie si une URL est déjà ouverte dans une des fenêtres ou onglets
    """
    current_handle = driver.current_window_handle
    for handle in driver.window_handles:
        try:
            driver.switch_to.window(handle)
            if url in driver.current_url:
                print(f"⚠️ URL déjà ouverte dans : {driver.title}")
                return True
        except:
            continue
    driver.switch_to.window(current_handle)
    return False

def create_chrome_debugger(port=43151):
    """
    Configure Chrome en mode debugger sur le port spécifié
    """
    print(f"\n🔍 Vérification de Chrome sur le port {port}...")
    
    # Vérifier si Chrome est déjà en cours d'exécution sur ce port
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:  # Le port est déjà ouvert
        try:
            # Tenter de se connecter au Chrome existant
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
            print(f"✅ Connexion établie au Chrome existant")
            print(f"   🪟 Fenêtres ouvertes : {len(driver.window_handles)}")
            return driver
        except Exception as e:
            print(f"❌ Erreur de connexion : {e}")
            result = -1  # Forcer la création d'une nouvelle instance
    
    if result != 0:  # Le port n'est pas ouvert ou la connexion a échoué
        print("🚀 Lancement d'une nouvelle instance Chrome...")
        # Lancer Chrome avec le port de débogage
        chrome_cmd = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            f'--remote-debugging-port={port}',
            '--no-first-run',
            '--no-default-browser-check',
            f'--user-data-dir=/tmp/chrome_debug_{port}'
        ]
        subprocess.Popen(chrome_cmd)
        time.sleep(2)  # Attendre que Chrome démarre
        
        # Se connecter à la nouvelle instance
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        print("✅ Nouvelle instance Chrome créée")
        return driver
    
    return None

def open_new_window(driver, url=None, position=None):
    """
    Ouvre une nouvelle fenêtre Chrome (pas un onglet)
    """
    # Sauvegarder le handle actuel
    original_handle = driver.current_window_handle
    
    # Créer une nouvelle fenêtre avec des paramètres spécifiques
    features = [
        "toolbar=yes",
        "menubar=yes",
        "location=yes",
        "status=yes",
        "scrollbars=yes",
        "resizable=yes",
        "width=1200",
        "height=800",
        f"left={position[0] if position else 100}",
        f"top={position[1] if position else 100}"
    ]
    
    driver.execute_script(
        f"window.open('about:blank', '_blank', '{','.join(features)}')"
    )
    
    # Attendre la nouvelle fenêtre
    time.sleep(1)
    
    # Passer à la nouvelle fenêtre
    new_handle = [h for h in driver.window_handles if h != original_handle][-1]
    driver.switch_to.window(new_handle)
    
    # Positionner la fenêtre
    if position:
        driver.set_window_position(position[0], position[1])
        driver.set_window_size(1200, 800)
    
    # Charger l'URL
    if url:
        driver.get(url)
        time.sleep(1)  # Attendre le chargement
    
    return driver.current_window_handle

def main():
    """Test d'ouverture de fenêtres séparées"""
    print("\n" + "="*60)
    print("TEST D'OUVERTURE DE FENÊTRES CHROME SÉPARÉES")
    print("="*60)
    
    try:
        # Initialiser ou se connecter à Chrome
        driver = create_chrome_debugger(43151)
        if not driver:
            print("❌ Impossible d'initialiser Chrome")
            return
        
        # Liste des sites à ouvrir
        sites = [
            {"url": "https://www.google.com", "name": "Google", "pos": (0, 0)},
            {"url": "https://www.youtube.com", "name": "YouTube", "pos": (300, 100)}
        ]
        
        # Traiter chaque site
        for i, site in enumerate(sites, 1):
            print(f"\n{i}️⃣ Vérification de {site['name']}...")
            
            # Vérifier si le site est déjà ouvert
            if check_url_in_windows(driver, site['url']):
                print(f"   ℹ️ {site['name']} est déjà ouvert")
                continue
            
            # Si c'est le premier site
            if i == 1:
                if len(driver.window_handles) == 1:
                    try:
                        current_url = driver.current_url
                        if current_url == "about:blank" or current_url == "data:," or "new-tab-page" in current_url:
                            print(f"   🔄 Utilisation de la fenêtre existante pour {site['name']}")
                            driver.get(site['url'])
                            driver.set_window_position(*site['pos'])
                            driver.set_window_size(1200, 800)
                            time.sleep(1)  # Attendre le chargement
                            continue
                    except:
                        pass
            
            # Sinon, ouvrir une nouvelle fenêtre
            print(f"   🆕 Ouverture d'une nouvelle fenêtre pour {site['name']}")
            open_new_window(driver, site['url'], position=site['pos'])
        
        # Afficher un résumé des fenêtres
        print("\n📊 Résumé des fenêtres :")
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            print(f"   - {driver.title}")
            print(f"     {driver.current_url}")
        
        print("\n✅ Configuration des fenêtres terminée")
        input("\nAppuyez sur Entrée pour terminer...")
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
    
    print("\n✨ Test terminé")

if __name__ == "__main__":
    main()