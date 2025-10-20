# -*- coding: utf-8 -*-
"""
Configuration de la sélection automatique de fenêtre Chrome.
Permet de définir des règles pour sélectionner automatiquement 
la bonne fenêtre lors des prochaines connexions.
"""
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'window_config.json')


def save_window_preference(url_pattern=None, title_pattern=None, window_index=None):
    """
    Sauvegarde les préférences de sélection de fenêtre.
    
    Args:
        url_pattern (str): Pattern d'URL à rechercher
        title_pattern (str): Pattern de titre à rechercher
        window_index (int): Index de fenêtre préféré
    """
    config = {
        'url_pattern': url_pattern,
        'title_pattern': title_pattern,
        'window_index': window_index
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Préférences sauvegardées dans {CONFIG_FILE}")


def load_window_preference():
    """
    Charge les préférences de sélection de fenêtre.
    
    Returns:
        dict: Configuration sauvegardée ou None
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"ℹ️  Préférences chargées depuis {CONFIG_FILE}")
            return config
        except:
            return None
    return None


def configure_window_selection():
    """
    Interface interactive pour configurer la sélection automatique.
    """
    print("=" * 60)
    print("CONFIGURATION DE SÉLECTION AUTOMATIQUE DE FENÊTRE")
    print("=" * 60)
    
    print("\nComment voulez-vous sélectionner la fenêtre?")
    print("  1. Par pattern d'URL (ex: '1xbet', 'line', etc.)")
    print("  2. Par pattern de titre (ex: '1xBet', 'Paris', etc.)")
    print("  3. Par index fixe (ex: toujours la 2ème fenêtre)")
    print("  4. Supprimer la configuration (demander à chaque fois)")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == '1':
        url_pattern = input("Pattern d'URL: ").strip()
        save_window_preference(url_pattern=url_pattern)
        print(f"\n✅ Configuration sauvegardée: recherche d'URL contenant '{url_pattern}'")
        
    elif choice == '2':
        title_pattern = input("Pattern de titre: ").strip()
        save_window_preference(title_pattern=title_pattern)
        print(f"\n✅ Configuration sauvegardée: recherche de titre contenant '{title_pattern}'")
        
    elif choice == '3':
        try:
            window_index = int(input("Index de fenêtre (commence à 0): "))
            save_window_preference(window_index=window_index)
            print(f"\n✅ Configuration sauvegardée: utilisation de la fenêtre #{window_index}")
        except ValueError:
            print("❌ Index invalide")
            
    elif choice == '4':
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("\n✅ Configuration supprimée")
        else:
            print("\n ℹ️  Aucune configuration à supprimer")
    else:
        print("❌ Choix invalide")


if __name__ == "__main__":
    configure_window_selection()
