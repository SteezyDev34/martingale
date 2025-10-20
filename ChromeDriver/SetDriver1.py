import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import config

# Importer le gestionnaire de fenêtres si disponible
try:
    from ChromeDriver.WindowManager import (
        interactive_window_selector,
        auto_select_window,
        print_windows_list,
        list_chrome_windows
    )
    from ChromeDriver.ConfigureWindow import load_window_preference
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False
    print("⚠️  WindowManager non disponible, fonctionnalité limitée")

Path = os.path.dirname(os.path.abspath(__file__))
opt = Options()
if config.systeme == 'Windows':
    Path = Path + '\\chromedriver.exe'
else:
    Path = Path + '/chromedriver'
try:
    # 7978
    # 43151
    # 1035
    opt.add_experimental_option("debuggerAddress", "localhost:43151")
    # Utilisation correcte du chemin pour macOS
    driver = webdriver.Chrome(executable_path=Path, options=opt)
    
    # Gestion des fenêtres multiples
    if len(driver.window_handles) > 1:
        print(f"\n{'='*60}")
        print(f"⚠️  {len(driver.window_handles)} fenêtres Chrome détectées")
        print(f"{'='*60}")
        
        if WINDOW_MANAGER_AVAILABLE:
            # Vérifier s'il y a une configuration sauvegardée
            window_config = load_window_preference()
            
            if window_config and any(window_config.values()):
                print("\n🔧 Configuration automatique trouvée")
                
                # Appliquer la configuration
                if window_config.get('url_pattern'):
                    print(f"   Recherche d'URL: {window_config['url_pattern']}")
                    if auto_select_window(driver, url_pattern=window_config['url_pattern']):
                        print(f"{'='*60}\n")
                        success = 1
                        # Continue avec le reste du script
                    else:
                        print("⚠️  Pattern d'URL non trouvé, sélection manuelle requise")
                        window_config = None
                        
                elif window_config.get('title_pattern'):
                    print(f"   Recherche de titre: {window_config['title_pattern']}")
                    if auto_select_window(driver, title_pattern=window_config['title_pattern']):
                        print(f"{'='*60}\n")
                        success = 1
                        # Continue avec le reste du script
                    else:
                        print("⚠️  Pattern de titre non trouvé, sélection manuelle requise")
                        window_config = None
                        
                elif window_config.get('window_index') is not None:
                    print(f"   Utilisation de la fenêtre #{window_config['window_index']}")
                    if auto_select_window(driver, index=window_config['window_index']):
                        print(f"{'='*60}\n")
                        success = 1
                        # Continue avec le reste du script
                    else:
                        print("⚠️  Index invalide, sélection manuelle requise")
                        window_config = None
            
            # Si pas de config ou config échouée, demander à l'utilisateur
            if not window_config or not any(window_config.values()):
                # Utiliser le gestionnaire de fenêtres avancé
                print("\n📋 MODE SÉLECTION DE FENÊTRE")
                print("Choisissez une méthode:")
                print("  1. Interface interactive complète")
                print("  2. Recherche automatique par URL (1xbet)")
                print("  3. Sélection manuelle rapide")
                print("  4. Utiliser la première fenêtre")
                
                mode = input("\nMode (1-4, défaut=3): ").strip() or "3"
                
                if mode == "1":
                    # Mode interactif complet
                    interactive_window_selector(driver)
                elif mode == "2":
                    # Recherche automatique de fenêtre 1xbet
                    if not auto_select_window(driver, url_pattern="1xbet"):
                        print("⚠️  Fenêtre 1xbet non trouvée, sélection manuelle")
                        windows = list_chrome_windows(driver)
                        print_windows_list(windows)
                        try:
                            idx = int(input(f"Numéro (1-{len(windows)}): ")) - 1
                            auto_select_window(driver, index=idx)
                        except:
                            driver.switch_to.window(driver.window_handles[0])
                elif mode == "3":
                    # Sélection rapide par numéro
                    windows = list_chrome_windows(driver)
                    print_windows_list(windows)
                    try:
                        choice = int(input(f"Fenêtre (1-{len(windows)}): ")) - 1
                        driver.switch_to.window(driver.window_handles[choice])
                        print(f"✅ Fenêtre {choice + 1} sélectionnée: {driver.title}")
                    except:
                        print("⚠️  Utilisation de la première fenêtre")
                        driver.switch_to.window(driver.window_handles[0])
                else:
                    # Utiliser la première fenêtre
                    driver.switch_to.window(driver.window_handles[0])
                    print(f"✅ Première fenêtre utilisée: {driver.title}")
        else:
            # Mode simple sans WindowManager
            print("\nFenêtres disponibles:")
            for i, handle in enumerate(driver.window_handles):
                driver.switch_to.window(handle)
                print(f"  {i+1}. {driver.title[:50]}")
            
            try:
                choice = int(input(f"\nFenêtre (1-{len(driver.window_handles)}): ")) - 1
                driver.switch_to.window(driver.window_handles[choice])
                print(f"✅ Sélectionnée: {driver.title}")
            except:
                driver.switch_to.window(driver.window_handles[0])
                print("⚠️  Première fenêtre utilisée")
    else:
        print(f"\nℹ️  Une seule fenêtre détectée")
        driver.switch_to.window(driver.window_handles[0])
        print(f"   Titre: {driver.title}")
        print(f"   URL: {driver.current_url}")
    
    print(f"{'='*60}\n")
    
except Exception as e:
    try:
        opt.add_experimental_option("debuggerAddress", "localhost:43151")
        service = Service(executable_path=Path)  # Modification du chemin
        driver = webdriver.Chrome(service=service, options=opt)
    except Exception as e:
        try:
            opt = webdriver.ChromeOptions()
            opt.add_experimental_option("debuggerAddress", "localhost:43151")
            opt.binary_location = Path  # Chemin binaire adapté pour macOS
            # Initialiser l'instance de WebDriver avec les options
            driver = webdriver.Chrome(options=opt)
        except Exception as e:
            sys.stdout.write(f'\rUne erreur est survenue : {e}\n')
            sys.stdout.write('Merci de réessayer.\n')
        else:
            success = 1
    else:
        success = 1
else:
    success = 1
