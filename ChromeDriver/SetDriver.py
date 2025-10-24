
import os
import sys
import time
import json
import socket
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

def calculate_window_position(num_fenetre, screen_width, screen_height):
    """
    Calcule la position et la taille d'une fenêtre selon une grille de 4 colonnes
    Args:
        num_fenetre (int): Numéro de la fenêtre (1, 2, 3, etc.)
        screen_width (int): Largeur de l'écran
        screen_height (int): Hauteur de l'écran
    Returns:
        tuple: (x_pos, y_pos, width, height) Position et taille de la fenêtre
    """
    # Calcul de la taille de chaque fenêtre (grille 4 colonnes)
    fenetre_width = int(screen_width / 6)
    fenetre_height = 375  # Hauteur fixe ou calculée selon vos besoins
    
    # Calcul de la position dans la grille (base 0)
    grid_position = num_fenetre - 1
    
    # Calcul de la colonne (0 à 5)
    colonne = grid_position % 6
    
    # Calcul de la ligne (0, 1, 2, etc.)
    ligne = grid_position // 6
    
    # Position finale
    x_pos = int(colonne * fenetre_width)
    y_pos = int(ligne * fenetre_height)
    
    return x_pos, y_pos, fenetre_width, fenetre_height

def is_port_open(port):
    """Vérifie si un port est ouvert sur localhost"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', int(port)))
    sock.close()
    return result == 0

def wait_for_port(port, timeout=10):
    """Attend que le port soit disponible"""
    for _ in range(timeout):
        if is_port_open(port):
            return True
        time.sleep(1)
    return False

def launch_chrome_windows(port, profile_dir):
    """Lance Chrome sous Windows"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]

    chrome_path = None
    for path in possible_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if chrome_path is None:
        raise FileNotFoundError("Chrome executable not found.")

    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
    ]

    # Rediriger la sortie et détacher le processus sur Windows
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                          start_new_session=True)  # Détache le processus

def launch_chrome_mac(port, profile_dir):
    """Lance Chrome sous macOS"""
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    if not os.path.exists(chrome_path):
        raise FileNotFoundError("Chrome n'est pas installé dans l'emplacement standard")
    
    args = [
        chrome_path,
        f'--remote-debugging-port={port}',
        f'--user-data-dir={profile_dir}',

    ]
    
    # Rediriger la sortie et détacher le processus sur Mac
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          start_new_session=True)  # Détache le processus

def ensure_chrome_running(port, project_dir):
    """S'assure que Chrome est lancé avec les bons paramètres"""
    if not is_port_open(port):
        print(f"🚀 Lancement de Chrome sur le port {port}...")
        
        try:
            if config.systeme == 'Windows':
                profile_dir = os.path.join(project_dir, f'ChromeDebugProfile{port}')
                process = launch_chrome_windows(port, profile_dir)
            else:
                profile_dir = os.path.expanduser(f"~/ChromeDebugProfile{port}")
                process = launch_chrome_mac(port, profile_dir)
            
            if wait_for_port(port):
                print(f"✅ Chrome lancé avec succès sur le port {port}")
                return True
            else:
                print(f"❌ Timeout lors du lancement de Chrome sur le port {port}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du lancement de Chrome : {e}")
            return False
    else:
        print(f"✅ Chrome est déjà lancé sur le port {port}")
        return True

# Initialisation du driver
def init_driver(port, window_handle=None):
    """Initialise le driver Selenium avec une fenêtre spécifique en option"""
    Path = os.path.dirname(os.path.abspath(__file__))
    Path = Path + ('\\chromedriver.exe' if config.systeme == 'Windows' else '/chromedriver')
    print('win', window_handle)
    opt = Options()
    opt.add_experimental_option("debuggerAddress", f"localhost:{port}")
    
    try:
        # Première tentative avec executable_path
        driver = webdriver.Chrome(executable_path=Path, options=opt)
    except Exception as e1:
        try:
            # Deuxième tentative avec service
            service = Service(executable_path=Path)
            driver = webdriver.Chrome(service=service, options=opt)
        except Exception as e2:
            try:
                # Dernière tentative avec binary_location
                opt.binary_location = Path
                driver = webdriver.Chrome(options=opt)
            except Exception as e3:
                print(f"❌ Impossible d'initialiser le driver Chrome :")
                print(f"   Tentative 1 : {e1}")
                print(f"   Tentative 2 : {e2}")
                print(f"   Tentative 3 : {e3}")
                return None
    
    if window_handle:
        # Si un handle de fenêtre est spécifié, on switch dessus
        try:
            driver.switch_to.window(window_handle)
        except:
            print("❌ Impossible de switcher sur la fenêtre spécifiée")
    return driver

def create_new_window(port, num_fenetre, url=config.site_url):
    """
    Crée une nouvelle fenêtre Chrome et retourne son handle
    Args:
        port (int): Port de débogage Chrome
        url (str): URL à ouvrir dans la nouvelle fenêtre (par défaut: about:blank)
    """
    try:
        temp_driver = init_driver(port)
        if not temp_driver:
            return None
            
        # Récupère l'état initial
        initial_handles = temp_driver.window_handles
        initial_handle = temp_driver.current_window_handle
        # Configure la position et la taille de la fenêtre selon la grille
        screen_size = temp_driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
        screen_width = screen_size[0]
        screen_height = screen_size[1]

        x_pos, y_pos, width, height = calculate_window_position(num_fenetre, screen_width, screen_height)

        # Ouvre une nouvelle fenêtre avec l'URL spécifiée
        temp_driver.execute_script(f"window.open('{url}', '_blank', 'width={width},height={height}')")
        time.sleep(1)
        
        # Récupère les nouveaux handles et trouve le nouveau
        new_handles = [h for h in temp_driver.window_handles if h not in initial_handles]
        if not new_handles:
            raise Exception("Aucune nouvelle fenêtre détectée")
            
        # Passe à la nouvelle fenêtre
        new_handle = new_handles[0]
        temp_driver.switch_to.window(new_handle)
        
        # Configure la position et la taille de la fenêtre selon la grille
        screen_size = temp_driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
        screen_width = screen_size[0]
        screen_height = screen_size[1]
        
        # Utilise la nouvelle fonction de calcul de position et taille
        x_pos, y_pos, width, height = calculate_window_position(num_fenetre, screen_width, screen_height)
        
        temp_driver.set_window_position(x_pos, y_pos)
        temp_driver.set_window_size(width, height)
        
        print(f"✅ Nouvelle fenêtre {num_fenetre} créée à ({x_pos}, {y_pos}) taille {width}x{height} (handle: {new_handle[:8]}...)")
        return new_handle
            
    except Exception as e:
        print(f"❌ Erreur lors de la création d'une nouvelle fenêtre : {e}")
        # Retour à la fenêtre initiale en cas d'erreur
        try:
            temp_driver.switch_to.window(initial_handle)
        except:
            pass
        return None
        time.sleep(2)  # Attente un peu plus longue pour la création
        
        # Récupère les nouveaux handles
        new_handles = [h for h in temp_driver.window_handles if h not in initial_handles]
        if not new_handles:
            raise Exception("Aucune nouvelle fenêtre détectée")
            
        # Sélectionne la nouvelle fenêtre
        new_handle = new_handles[0]
        temp_driver.switch_to.window(new_handle)
        
        # Configure la nouvelle fenêtre
        temp_driver.set_window_position(200, 200)
        temp_driver.set_window_size(1000, 800)
        
        
        print(f"✅ Nouvelle fenêtre créée et configurée (handle: {new_handle[:8]}...)")
        return new_handle
            
    except Exception as e:
        print(f"❌ Erreur lors de la création d'une nouvelle fenêtre : {e}")
        # Retour à la fenêtre initiale en cas d'erreur si possible
        try:
            if 'initial_handle' in locals():
                temp_driver.switch_to.window(initial_handle)
        except:
            pass
        return None

# Variable pour stocker les handles des fenêtres
window_handles = {}

def save_window_handles():
    """Sauvegarde les handles des fenêtres dans un fichier JSON"""
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'window_handles.json')
    try:
        with open(save_path, 'w') as f:
            json.dump(window_handles, f, indent=4)
        print("💾 Handles des fenêtres sauvegardés")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des handles : {e}")

def load_window_handles():
    """Charge les handles des fenêtres depuis le fichier JSON"""
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'window_handles.json')
    try:
        if os.path.exists(save_path):
            with open(save_path, 'r') as f:
                loaded_handles = json.load(f)
            print("📂 Handles des fenêtres chargés")
            return loaded_handles
        return {}
    except Exception as e:
        print(f"❌ Erreur lors du chargement des handles : {e}")
        return {}

def verify_handles(driver, handles):
    """Vérifie si les handles sont toujours valides"""
    valid_handles = {}
    try:
        current_handles = set(driver.window_handles)
        for num, handle in handles.items():
            if handle in current_handles:
                valid_handles[num] = handle
                print(f"✅ Fenêtre {num} existante validée")
            else:
                print(f"❌ Fenêtre {num} invalide (handle expiré)")
        return valid_handles
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des handles : {e}")
        return {}

def get_script_driver(num_fenetre):
    """
    Retourne un driver configuré pour la fenêtre spécifiée
    Args:
        num_fenetre (int): Numéro de la fenêtre (1, 2, 3, etc.)
    """
    num_str = str(num_fenetre)

    global window_handles
    
    # Première initialisation
    if not window_handles:
        if not ensure_chrome_running(config.localhost, os.path.dirname(os.path.dirname(__file__))):
            return None
            
        # Initialise la première fenêtre
        driver = init_driver(config.localhost)
        if not driver:
            return None
            
        # Essaie de charger les handles sauvegardés
        saved_handles = load_window_handles()
        if saved_handles:
            print("🔄 Vérification des fenêtres sauvegardées...")
            window_handles = verify_handles(driver, saved_handles)
        
        # Si aucun handle valide n'a été chargé
        if not window_handles:
            print("🆕 Initialisation d'une nouvelle session...")
            window_handles['1'] = driver.current_window_handle
            
            # Configure la fenêtre principale avec la nouvelle méthode
            screen_size = driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
            screen_width = screen_size[0]
            screen_height = screen_size[1]
            x_pos, y_pos, width, height = calculate_window_position(1, screen_width, screen_height)
            
            driver.set_window_position(x_pos, y_pos)
            driver.set_window_size(width, height)
            print(f"✅ Fenêtre 1 (principale) initialisée à ({x_pos}, {y_pos}) taille {width}x{height}")
            save_window_handles()  # Sauvegarde la configuration initiale
            
        # Configure les fenêtres existantes avec les nouvelles positions et tailles
        for num, handle in window_handles.items():
            try:
                driver.switch_to.window(handle)
                screen_size = driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
                screen_width = screen_size[0]
                screen_height = screen_size[1]
                
                # Utilise la nouvelle fonction de calcul avec taille
                x_pos, y_pos, width, height = calculate_window_position(int(num), screen_width, screen_height)
                
                driver.set_window_position(x_pos, y_pos)
                driver.set_window_size(width, height)
                print(f"✅ Fenêtre {num} repositionnée à ({x_pos}, {y_pos}) taille {width}x{height}")
            except Exception as e:
                print(f"❌ Erreur lors de la configuration de la fenêtre {num}: {e}")
                
        # Revient à la première fenêtre si elle existe
        if '1' in window_handles:
            driver.switch_to.window(window_handles['1'])

    # Si la fenêtre demandée n'existe pas encore, la créer
    if num_str not in window_handles:
        print(f"🔄 Création de la fenêtre {num_fenetre}...")
        new_handle = create_new_window(config.localhost,num_fenetre)
        if new_handle:
            window_handles[num_str] = new_handle
            save_window_handles()  # Sauvegarde la nouvelle configuration
            print(f"✅ Fenêtre {num_fenetre} créée et sauvegardée avec succès")
        else:
            print(f"❌ Échec de la création de la fenêtre {num_fenetre}")
            return None

    # Vérifie si le handle est toujours valide
    try:
        driver = init_driver(config.localhost)
        if not driver:
            return None
        # Vérifie si le handle existe encore dans la liste des fenêtres
        if window_handles[num_str] not in driver.window_handles:
            print(f"🔄 Le handle de la fenêtre {num_fenetre} n'est plus valide, création d'une nouvelle fenêtre...")
            new_handle = create_new_window(config.localhost, num_fenetre)
            if new_handle:
                window_handles[num_str] = new_handle
                print(f"✅ Fenêtre {num_fenetre} recréée avec succès")
            else:
                print(f"❌ Échec de la recréation de la fenêtre {num_fenetre}")
                return None
        # Connexion à la fenêtre
        driver = init_driver(config.localhost, window_handles[num_str])
        if driver:
            # Forcer le redimensionnement de la fenêtre 1 à chaque appel
            if num_fenetre == 1:
                screen_size = driver.execute_script("return [window.screen.availWidth, window.screen.availHeight];")
                screen_width = screen_size[0]
                screen_height = screen_size[1]
                x_pos, y_pos, width, height = calculate_window_position(1, screen_width, screen_height)
                driver.set_window_position(x_pos, y_pos)
                driver.set_window_size(width, height)
                print(f"✅ Fenêtre 1 forcée à ({x_pos}, {y_pos}) taille {width}x{height}")
            print(f"✅ Connecté à la fenêtre {num_fenetre}")
            return driver

    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la fenêtre {num_fenetre}: {e}")

    print(f"❌ Impossible de se connecter à la fenêtre {num_fenetre}")
    return None

# Cette partie n'est plus nécessaire car l'initialisation est gérée par get_script_driver
success = 1
