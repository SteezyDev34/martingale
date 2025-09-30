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
            EC.presence_of_element_located((By.CSS_SELECTOR, ".bet-title"))
        )
    except Exception as e:
        print(f"Erreur lors de l'attente des éléments: {e}")
        return {}

    # Extraire tous les types de paris
    bet_types = {}
    bet_titles = browser.find_elements(By.CLASS_NAME, "bet-title")

    for bet_title in bet_titles:
        try:
            # Extraire le nom du type de pari
            # Faire défiler jusqu'à l'élément pour s'assurer qu'il est visible
            # browser.execute_script("arguments[0].scrollIntoView(true);", bet_title)
            bet_type_name = bet_title.find_element(By.CLASS_NAME, "bet-title__label").get_attribute(
                "textContent").strip()
            print('type de paris ', bet_type_name)
            # Trouver le conteneur parent pour accéder aux sélections
            parent_container = bet_title.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'bets')]")

            # Extraire les sélections
            selections = []
            bet_inners = parent_container.find_elements(By.CLASS_NAME, "bet-inner")

            for bet_inner in bet_inners[:10]:  # Limiter à 10 sélections
                try:
                    # Faire défiler jusqu'à l'élément de sélection pour s'assurer qu'il est visible
                    selection = bet_inner.find_element(By.CLASS_NAME, "bet_type").get_attribute("textContent").strip()
                    print('selection ', selection)
                    selections.append(selection)
                except Exception:
                    continue

            if selections:
                bet_types[bet_type_name] = selections
            print('')
            print('')
        except Exception as e:
            print(f"Erreur lors de l'extraction du type de pari: {e}")
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
