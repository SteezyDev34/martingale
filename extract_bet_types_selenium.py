import json
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Fonction pour extraire les types de paris et leurs sélections
def extract_bet_types_and_selections(browser):
    """
    Extrait les types de paris et leurs sélections depuis une URL 1xBet.
    
    Args:
        browser (webdriver.Chrome): Instance du navigateur
        url (str): URL de la page à analyser
        
    Returns:
        dict: Dictionnaire des types de paris et leurs sélections
    """
    
    # Attendre que la page se charge    
    # Attendre que les éléments de paris soient chargés
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".game-markets-group-header-title"))
        )
    except Exception as e:
        print(f"Erreur lors de l'attente des éléments: {e}")
        return {}

    # Extraire tous les types de paris
    bet_types = {}
    # Chercher les conteneurs principaux de groupes de paris
    bet_containers = browser.find_elements(By.CSS_SELECTOR, ".game-markets-group.game-markets-content__item")

    for container in bet_containers:
        try:
            # Extraire le nom du type de pari depuis le titre
            title_element = container.find_element(By.CSS_SELECTOR, ".game-markets-group-header-title .ui-caption")
            bet_type_name = title_element.text.strip()
            print('type de paris :', bet_type_name)
            
            # Le conteneur parent est déjà l'élément actuel
            parent_container = container

            # Extraire les sélections depuis la liste des marchés
            selections = []
            bet_markets = parent_container.find_elements(By.CSS_SELECTOR, ".game-markets-group__market")

            for market in bet_markets[:20]:  # Augmenter la limite pour récupérer plus d'options
                try:
                    # Extraire le nom de la sélection depuis le span avec la classe ui-market__name
                    market_name_element = market.find_element(By.CSS_SELECTOR, ".ui-market__name")
                    market_name = market_name_element.text.strip()
                    
                    
                    # Combiner nom et cote
                    selection = f"{market_name}"
                    print('selection :', selection)
                    selections.append(selection)
                except Exception as e:
                    print(f"Erreur extraction sélection: {e}")
                    continue

            if selections:
                bet_types[bet_type_name] = selections
                print(f"✅ {len(selections)} sélections trouvées pour '{bet_type_name}'")
            print('')
            print('')
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction du type de pari: {e}")
            continue

    return bet_types


# Fonction pour mettre à jour les fichiers JSON
def update_json_files(category, bet_types):
    """
    Met à jour les fichiers JSON avec les nouveaux types de paris et sélections.
    Complète les données existantes en évitant les doublons.
    
    Args:
        category (str): La catégorie de paris (ex: "Temps réglementaire")
        bet_types (dict): Dictionnaire des types de paris et leurs sélections
    """
    # Chemins des fichiers JSON
    types_file = 'xbet_types.json'
    selections_file = 'xbet_selections.json'

    # Charger ou créer les fichiers JSON
    if os.path.exists(types_file):
        with open(types_file, 'r', encoding='utf-8') as f:
            types_data = json.load(f)
    else:
        types_data = {}

    if os.path.exists(selections_file):
        with open(selections_file, 'r', encoding='utf-8') as f:
            selections_data = json.load(f)
    else:
        selections_data = {}

    # Initialiser la catégorie si elle n'existe pas
    if category not in types_data:
        types_data[category] = []
    
    if category not in selections_data:
        selections_data[category] = {}

    # Mettre à jour les types de paris et sélections
    for bet_type, new_selections in bet_types.items():
        # Ajouter le type de pari s'il n'existe pas déjà (éviter les doublons)
        if bet_type not in types_data[category]:
            types_data[category].append(bet_type)

        # Initialiser le type de pari dans selections_data s'il n'existe pas
        if bet_type not in selections_data[category]:
            selections_data[category][bet_type] = []

        # Fusionner les nouvelles sélections avec les existantes en évitant les doublons
        existing_selections = selections_data[category][bet_type]
        
        # Convertir en set pour éviter les doublons, puis reconvertir en liste
        combined_selections = list(set(existing_selections + new_selections))
        
        # Trier pour maintenir un ordre cohérent
        combined_selections.sort()
        
        selections_data[category][bet_type] = combined_selections

    # Enregistrer les fichiers JSON
    with open(types_file, 'w', encoding='utf-8') as f:
        json.dump(types_data, f, ensure_ascii=False, indent=4)

    with open(selections_file, 'w', encoding='utf-8') as f:
        json.dump(selections_data, f, ensure_ascii=False, indent=4)

    print(f"Fichiers {types_file} et {selections_file} mis à jour avec succès (doublons évités).")


# Fonction principale
def main():
    """
    Fonction principale qui gère l'extraction des types de paris et sélections.
    """
    print("Extraction des types de paris et sélections de 1xBet")
    print("==================================================")

    # Demander la catégorie
    category = input("Entrez la catégorie (ex: 'Temps réglementaire', '1 Set', etc.): ")

    # Demander l'URL

    # Configurer le navigateur
    from ChromeDriver.SetDriver1 import driver
    browser = driver

    try:
        # Extraire les types de paris et sélections
        bet_types = extract_bet_types_and_selections(browser)

        if bet_types:
            print(f"\nNombre de types de paris extraits: {len(bet_types)}")
            for bet_type, selections in bet_types.items():
                print(f"\nType de pari: {bet_type}")
                print(f"Nombre de sélections: {len(selections)}")
                print("Sélections:")
                for selection in selections:
                    print(f"- {selection}")

            # Mettre à jour les fichiers JSON
            update_json_files(category, bet_types)
        else:
            print("Aucun type de pari trouvé sur la page.")
    finally:
        # Fermer le navigateur
        browser.quit()


if __name__ == "__main__":
    main()
