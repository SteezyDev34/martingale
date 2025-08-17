# Function_GetIfMatchPage

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


# RECHERCHER UN MATCH SPÉCIFIQUE
def SearchMatch(driver, match_data):
    """
    Fonction pour rechercher un match spécifique en cliquant sur la loupe de recherche
    et en tapant le nom d'un des joueurs dans la zone de recherche.
    
    Args:
        driver: Instance du driver Selenium
        match_data: Dictionnaire contenant les données du match avec les clés:
                   - date: Date du match
                   - equipe_1: Nom du premier joueur/équipe
                   - equipe_2: Nom du deuxième joueur/équipe
                   - type_de_pari: Type de pari
                   - selection: Sélection du pari
                   - odds: Cotes du pari
    
    Returns:
        bool: True si la recherche s'est bien déroulée, False sinon
    """
    try:
        # Attendre et cliquer sur la loupe de recherche
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='search-button'], .search-icon, .fa-search, button[aria-label*='search'], button[title*='search']"))
        )
        search_button.click()
        config.log("Clic sur la loupe de recherche effectué", 'info', True)
        
        # Attendre l'ouverture de la modal de recherche
        search_modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal, .search-modal, [role='dialog'], .popup, .overlay"))
        )
        config.log("Modal de recherche ouverte", 'info', True)
        
        # Trouver la zone de saisie de recherche
        search_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='search'], input[placeholder*='search'], input[name*='search'], .search-input, input[data-testid*='search']"))
        )
        
        # Effacer le contenu existant et taper le nom du premier joueur
        search_input.clear()
        player_name = match_data.get('equipe_1', '')
        search_input.send_keys(player_name)
        config.log(f"Recherche du joueur: {player_name}", 'info', True)
        
        # Attendre un moment pour que les résultats de recherche apparaissent
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results, .results, .suggestions, .dropdown"))
        )
        config.log("Résultats de recherche affichés", 'info', True)
        
        return True
        
    except Exception as e:
        config.log(f"Erreur lors de la recherche de match: {str(e)}", 'error', True)
        return False


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    
    # Données d'exemple pour tester la fonction
    match_data_exemple = {
        "date": "05/10/2023",
        "equipe_1": "Ugo Humbert",
        "equipe_2": "Frances Tiafoe",
        "type_de_pari": "Total jeux",
        "selection": "Plus De 20.5",
        "odds": "1.57"
    }
    
    print(SearchMatch(driver, match_data_exemple))
