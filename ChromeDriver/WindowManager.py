# -*- coding: utf-8 -*-
"""
Module utilitaire pour gérer les fenêtres Chrome multiples.
Permet de lister, sélectionner et basculer entre les différentes fenêtres.
"""
import time


def list_chrome_windows(driver):
    """
    Liste toutes les fenêtres Chrome ouvertes.
    
    Args:
        driver: Instance du WebDriver Selenium
        
    Returns:
        list: Liste de dictionnaires avec les informations des fenêtres
    """
    windows = []
    current_handle = driver.current_window_handle
    
    for index, handle in enumerate(driver.window_handles):
        driver.switch_to.window(handle)
        time.sleep(0.5)  # Petite pause pour charger les infos
        
        window_info = {
            'index': index,
            'handle': handle,
            'title': driver.title,
            'url': driver.current_url,
            'is_current': handle == current_handle
        }
        windows.append(window_info)
    
    # Revenir à la fenêtre d'origine
    driver.switch_to.window(current_handle)
    
    return windows


def print_windows_list(windows):
    """
    Affiche la liste des fenêtres de manière formatée.
    
    Args:
        windows (list): Liste des fenêtres obtenue par list_chrome_windows()
    """
    print(f"\n{'='*80}")
    print(f"FENÊTRES CHROME DISPONIBLES ({len(windows)} fenêtres)")
    print(f"{'='*80}")
    
    for window in windows:
        marker = "👉" if window['is_current'] else "  "
        print(f"\n{marker} Fenêtre {window['index'] + 1}:")
        print(f"   Titre: {window['title'][:60]}{'...' if len(window['title']) > 60 else ''}")
        print(f"   URL:   {window['url'][:60]}{'...' if len(window['url']) > 60 else ''}")
        if window['is_current']:
            print(f"   Status: ✅ Fenêtre active")
    
    print(f"{'='*80}\n")


def select_window_by_index(driver, index):
    """
    Sélectionne une fenêtre par son index.
    
    Args:
        driver: Instance du WebDriver Selenium
        index (int): Index de la fenêtre (0-based)
        
    Returns:
        bool: True si la sélection a réussi, False sinon
    """
    try:
        if 0 <= index < len(driver.window_handles):
            driver.switch_to.window(driver.window_handles[index])
            print(f"✅ Fenêtre {index + 1} sélectionnée")
            print(f"   Titre: {driver.title}")
            print(f"   URL: {driver.current_url}")
            return True
        else:
            print(f"❌ Index {index} invalide (0-{len(driver.window_handles)-1} disponibles)")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la sélection de la fenêtre: {e}")
        return False


def select_window_by_url(driver, url_pattern):
    """
    Sélectionne une fenêtre contenant un pattern d'URL spécifique.
    
    Args:
        driver: Instance du WebDriver Selenium
        url_pattern (str): Pattern à rechercher dans l'URL
        
    Returns:
        bool: True si une fenêtre correspondante a été trouvée et sélectionnée
    """
    current_handle = driver.current_window_handle
    
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        time.sleep(0.5)
        
        if url_pattern.lower() in driver.current_url.lower():
            print(f"✅ Fenêtre trouvée par URL")
            print(f"   Titre: {driver.title}")
            print(f"   URL: {driver.current_url}")
            return True
    
    # Aucune fenêtre trouvée, revenir à l'originale
    driver.switch_to.window(current_handle)
    print(f"❌ Aucune fenêtre trouvée avec l'URL contenant: {url_pattern}")
    return False


def select_window_by_title(driver, title_pattern):
    """
    Sélectionne une fenêtre contenant un pattern de titre spécifique.
    
    Args:
        driver: Instance du WebDriver Selenium
        title_pattern (str): Pattern à rechercher dans le titre
        
    Returns:
        bool: True si une fenêtre correspondante a été trouvée et sélectionnée
    """
    current_handle = driver.current_window_handle
    
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        time.sleep(0.5)
        
        if title_pattern.lower() in driver.title.lower():
            print(f"✅ Fenêtre trouvée par titre")
            print(f"   Titre: {driver.title}")
            print(f"   URL: {driver.current_url}")
            return True
    
    # Aucune fenêtre trouvée, revenir à l'originale
    driver.switch_to.window(current_handle)
    print(f"❌ Aucune fenêtre trouvée avec le titre contenant: {title_pattern}")
    return False


def interactive_window_selector(driver):
    """
    Interface interactive pour sélectionner une fenêtre.
    
    Args:
        driver: Instance du WebDriver Selenium
        
    Returns:
        bool: True si une fenêtre a été sélectionnée
    """
    windows = list_chrome_windows(driver)
    
    if len(windows) == 1:
        print("ℹ️  Une seule fenêtre disponible, sélection automatique")
        return True
    
    print_windows_list(windows)
    
    print("OPTIONS:")
    print("  1. Sélectionner par numéro")
    print("  2. Rechercher par URL")
    print("  3. Rechercher par titre")
    print("  4. Utiliser la fenêtre actuelle")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == '1':
        try:
            index = int(input(f"Numéro de fenêtre (1-{len(windows)}): ")) - 1
            return select_window_by_index(driver, index)
        except ValueError:
            print("❌ Entrée invalide")
            return False
    
    elif choice == '2':
        url_pattern = input("Pattern d'URL à rechercher: ").strip()
        return select_window_by_url(driver, url_pattern)
    
    elif choice == '3':
        title_pattern = input("Pattern de titre à rechercher: ").strip()
        return select_window_by_title(driver, title_pattern)
    
    elif choice == '4':
        print("✅ Utilisation de la fenêtre actuelle")
        return True
    
    else:
        print("❌ Choix invalide")
        return False


def auto_select_window(driver, url_pattern=None, title_pattern=None, index=None):
    """
    Sélection automatique de fenêtre selon différents critères.
    
    Args:
        driver: Instance du WebDriver Selenium
        url_pattern (str, optional): Pattern d'URL à rechercher
        title_pattern (str, optional): Pattern de titre à rechercher
        index (int, optional): Index de la fenêtre
        
    Returns:
        bool: True si la sélection a réussi
    """
    if url_pattern:
        return select_window_by_url(driver, url_pattern)
    elif title_pattern:
        return select_window_by_title(driver, title_pattern)
    elif index is not None:
        return select_window_by_index(driver, index)
    else:
        print("⚠️  Aucun critère spécifié, utilisation de la fenêtre actuelle")
        return True


def get_window_control(driver, **criteria):
    """
    Obtient le contrôle d'une fenêtre spécifique selon plusieurs critères.
    
    Args:
        driver: Instance du WebDriver Selenium
        **criteria: Critères de sélection de la fenêtre
            - url (str): URL exacte ou partielle
            - title (str): Titre exact ou partiel
            - index (int): Index de la fenêtre (0-based)
            - contains_url (str): URL contient cette chaîne
            - contains_title (str): Titre contient cette chaîne
            - program_name (str): Nom du programme (pour la configuration)
    
    Returns:
        dict: Informations sur la fenêtre sélectionnée
            - success (bool): True si une fenêtre a été trouvée et sélectionnée
            - handle: Handle de la fenêtre
            - title: Titre de la fenêtre
            - url: URL de la fenêtre
            - index: Index de la fenêtre
            - message: Message descriptif du résultat
    """
    result = {
        'success': False,
        'handle': None,
        'title': None,
        'url': None,
        'index': None,
        'message': None
    }
    
    # Sauvegarder la fenêtre actuelle
    original_handle = driver.current_window_handle
    
    try:
        # Si un index est spécifié
        if 'index' in criteria:
            if 0 <= criteria['index'] < len(driver.window_handles):
                handle = driver.window_handles[criteria['index']]
                driver.switch_to.window(handle)
                result.update({
                    'success': True,
                    'handle': handle,
                    'title': driver.title,
                    'url': driver.current_url,
                    'index': criteria['index'],
                    'message': f"Fenêtre trouvée par index {criteria['index']}"
                })
                return result
        
        # Parcourir toutes les fenêtres
        for idx, handle in enumerate(driver.window_handles):
            driver.switch_to.window(handle)
            time.sleep(0.5)  # Petit délai pour le chargement
            
            # Vérification de l'URL exacte
            if 'url' in criteria and driver.current_url == criteria['url']:
                result.update({
                    'success': True,
                    'handle': handle,
                    'title': driver.title,
                    'url': driver.current_url,
                    'index': idx,
                    'message': "Fenêtre trouvée par URL exacte"
                })
                return result
            
            # Vérification du titre exact
            if 'title' in criteria and driver.title == criteria['title']:
                result.update({
                    'success': True,
                    'handle': handle,
                    'title': driver.title,
                    'url': driver.current_url,
                    'index': idx,
                    'message': "Fenêtre trouvée par titre exact"
                })
                return result
            
            # Vérification de l'URL partielle
            if 'contains_url' in criteria and criteria['contains_url'].lower() in driver.current_url.lower():
                result.update({
                    'success': True,
                    'handle': handle,
                    'title': driver.title,
                    'url': driver.current_url,
                    'index': idx,
                    'message': "Fenêtre trouvée par URL partielle"
                })
                return result
            
            # Vérification du titre partiel
            if 'contains_title' in criteria and criteria['contains_title'].lower() in driver.title.lower():
                result.update({
                    'success': True,
                    'handle': handle,
                    'title': driver.title,
                    'url': driver.current_url,
                    'index': idx,
                    'message': "Fenêtre trouvée par titre partiel"
                })
                return result
        
        # Si aucune fenêtre n'est trouvée, revenir à la fenêtre originale
        driver.switch_to.window(original_handle)
        result['message'] = "Aucune fenêtre ne correspond aux critères"
        
    except Exception as e:
        # En cas d'erreur, revenir à la fenêtre originale
        driver.switch_to.window(original_handle)
        result['message'] = f"Erreur lors de la recherche de fenêtre: {str(e)}"
    
    return result


if __name__ == "__main__":
    print("Module de gestion des fenêtres Chrome")
    print("Importez ce module dans vos scripts pour gérer les fenêtres multiples")
    print("\nExemples d'utilisation:")
    print("  from ChromeDriver.WindowManager import get_window_control")
    print("  # Contrôler une fenêtre par URL")
    print("  window = get_window_control(driver, contains_url='1xbet')")
    print("  if window['success']:")
    print("      print(f'Fenêtre contrôlée: {window[\"title\"]}')")
    print("\n  # Contrôler une fenêtre par index")
    print("  window = get_window_control(driver, index=1)")
    print("\n  # Contrôler une fenêtre par titre")
    print("  window = get_window_control(driver, contains_title='Paris')")
