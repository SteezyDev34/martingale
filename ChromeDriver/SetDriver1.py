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
# Activer le mode headless si défini dans la configuration
HEADLESS = False  # getattr(config, 'headless', False)
if HEADLESS:
    opt.add_argument('--headless=new')
    opt.add_argument('--no-sandbox')
    opt.add_argument('--disable-dev-shm-usage')
    opt.add_argument('--disable-gpu')
    opt.add_argument('--window-size=1920,1080')
if config.systeme == 'Windows':
    Path = Path + '\\chromedriver.exe'
else:
    Path = Path + '/chromedriver'
try:
    # 7978
    # 43151
    # 1035
    # Si on n'est pas en headless, tenter de se connecter à une instance chrome existante
    if not HEADLESS:
        opt.add_experimental_option("debuggerAddress", "localhost:43151")
        service = Service(executable_path=Path)
        driver = webdriver.Chrome(service=service, options=opt)
    else:
        # En headless, lancer une nouvelle instance via chromedriver
        service = Service(executable_path=Path)
        driver = webdriver.Chrome(service=service, options=opt)
    # Appliquer un niveau de zoom si configuré (ex: 25 pour 25%)
    ZOOM = getattr(config, 'zoom_percent', None)
    ZOOM_MAX = getattr(config, 'zoom_max', False)
    MIN_ZOOM_FACTOR = 1  # 0.1
    if ZOOM or ZOOM_MAX:
        try:
            if ZOOM_MAX:
                zoom_factor = MIN_ZOOM_FACTOR
                applied_percent = int(zoom_factor * 100)
            else:
                zoom_delta = float(ZOOM)
                zoom_factor = 1.0 + (zoom_delta / 100.0)
                if zoom_factor < MIN_ZOOM_FACTOR:
                    zoom_factor = MIN_ZOOM_FACTOR
                applied_percent = int(zoom_factor * 100)

            try:
                driver.execute_cdp_cmd("Page.setZoomFactor", {"zoomFactor": zoom_factor})
                print(f"✅ Zoom appliqué via CDP : {applied_percent}%")
            except Exception:
                # Fallback: appliquer via JS sur chaque fenêtre
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.execute_script(f"document.body.style.zoom='{applied_percent}%';")
                    print(f"✅ Zoom appliqué via JS {applied_percent}% sur la fenêtre {handle[:8]}...")
        except Exception as e:
            print(f"⚠️ Impossible d'appliquer le zoom: {e}")


    # Helper pour appliquer le zoom sur un driver donné
    def _apply_zoom_to_driver(drv):
        if not drv:
            return
        try:
            if ZOOM_MAX:
                zoom_factor_local = MIN_ZOOM_FACTOR
                applied_percent_local = int(zoom_factor_local * 100)
            else:
                zoom_delta_local = float(ZOOM)
                zoom_factor_local = 1.0 + (zoom_delta_local / 100.0)
                if zoom_factor_local < MIN_ZOOM_FACTOR:
                    zoom_factor_local = MIN_ZOOM_FACTOR
                applied_percent_local = int(zoom_factor_local * 100)

            try:
                drv.execute_cdp_cmd("Page.setZoomFactor", {"zoomFactor": zoom_factor_local})
            except Exception:
                for handle_local in drv.window_handles:
                    try:
                        drv.switch_to.window(handle_local)
                        drv.execute_script(f"document.body.style.zoom='{applied_percent_local}%';")
                    except Exception:
                        pass
        except Exception:
            pass


    # Wrap driver.get to reapply zoom after navigation
    try:
        if 'driver' in locals() and driver:
            _orig_get = driver.get


            def _wrapped_get(url, *a, **k):
                res = _orig_get(url, *a, **k)
                try:
                    _apply_zoom_to_driver(driver)
                except Exception:
                    pass
                return res


            driver.get = _wrapped_get
    except Exception:
        pass

    # Gestion des fenêtres multiples
    if len(driver.window_handles) > 1:
        print(f"\n{'=' * 60}")
        print(f"⚠️  {len(driver.window_handles)} fenêtres Chrome détectées")
        print(f"{'=' * 60}")

        if WINDOW_MANAGER_AVAILABLE:
            # Vérifier s'il y a une configuration sauvegardée
            window_config = load_window_preference()

            if window_config and any(window_config.values()):
                print("\n🔧 Configuration automatique trouvée")

                # Appliquer la configuration
                if window_config.get('url_pattern'):
                    print(f"   Recherche d'URL: {window_config['url_pattern']}")
                    if auto_select_window(driver, url_pattern=window_config['url_pattern']):
                        print(f"{'=' * 60}\n")
                        success = 1
                        # Continue avec le reste du script
                    else:
                        print("⚠️  Pattern d'URL non trouvé, sélection manuelle requise")
                        window_config = None

                elif window_config.get('title_pattern'):
                    print(f"   Recherche de titre: {window_config['title_pattern']}")
                    if auto_select_window(driver, title_pattern=window_config['title_pattern']):
                        print(f"{'=' * 60}\n")
                        success = 1
                        # Continue avec le reste du script
                    else:
                        print("⚠️  Pattern de titre non trouvé, sélection manuelle requise")
                        window_config = None

                elif window_config.get('window_index') is not None:
                    print(f"   Utilisation de la fenêtre #{window_config['window_index']}")
                    if auto_select_window(driver, index=window_config['window_index']):
                        print(f"{'=' * 60}\n")
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
                print(f"  {i + 1}. {driver.title[:50]}")

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

    print(f"{'=' * 60}\n")

except Exception as e:
    try:
        if not HEADLESS:
            opt.add_experimental_option("debuggerAddress", "localhost:43151")
            service = Service(executable_path=Path)  # Modification du chemin
            driver = webdriver.Chrome(service=service, options=opt)
        else:
            service = Service(executable_path=Path)
            driver = webdriver.Chrome(service=service, options=opt)
    except Exception as e:
        try:
            opt = webdriver.ChromeOptions()
            if not HEADLESS:
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
