import json
import os
from bs4 import BeautifulSoup

# Exemple HTML pour les tests
EXAMPLE_HTML = """
<div class="bet-title">
    <span class="bet-title__label">Total. Corners</span>
</div>
<div class="bets">
    <div class="bet-inner">
        <span class="bet_type">Over 8.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Under 8.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Over 9.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Under 9.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Over 10.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Under 10.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Over 11.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Under 11.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Over 12.5</span>
    </div>
    <div class="bet-inner">
        <span class="bet_type">Under 12.5</span>
    </div>
</div>
"""

# Fonction pour extraire les types de paris et leurs sélections
def extract_bet_types_and_selections(html_content):
    """
    Extrait les types de paris et leurs sélections à partir du contenu HTML.
    
    Args:
        html_content (str): Le contenu HTML à analyser
        
    Returns:
        tuple: (type de pari, liste des sélections)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraire le type de pari
    bet_title_element = soup.select_one('span.bet-title__label')
    if not bet_title_element:
        return None, []
    
    bet_type = bet_title_element.text.strip()
    
    # Extraire les sélections
    selections = []
    bet_inner_elements = soup.select('div.bet-inner')
    
    for bet_inner in bet_inner_elements:
        bet_type_element = bet_inner.select_one('span.bet_type')
        if bet_type_element:
            selection = bet_type_element.text.strip()
            selections.append(selection)
    
    return bet_type, selections

# Fonction pour mettre à jour les fichiers JSON
def update_json_files(category, bet_type, selections):
    """
    Met à jour les fichiers JSON avec les nouveaux types de paris et sélections.
    
    Args:
        category (str): La catégorie de paris (ex: "Temps réglementaire")
        bet_type (str): Le type de pari (ex: "Total. Corners")
        selections (list): Liste des sélections pour ce type de pari
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
    
    # Mettre à jour les types de paris
    if category not in types_data:
        types_data[category] = []
    
    if bet_type not in types_data[category]:
        types_data[category].append(bet_type)
    
    # Mettre à jour les sélections
    key = f"{category}:{bet_type}"
    selections_data[key] = selections
    
    # Enregistrer les fichiers JSON
    with open(types_file, 'w', encoding='utf-8') as f:
        json.dump(types_data, f, ensure_ascii=False, indent=4)
    
    with open(selections_file, 'w', encoding='utf-8') as f:
        json.dump(selections_data, f, ensure_ascii=False, indent=4)
    
    print(f"Fichiers {types_file} et {selections_file} mis à jour avec succès.")

# Fonction principale
def main():
    """
    Fonction principale qui gère l'extraction des types de paris et sélections.
    """
    print("Extraction des types de paris et sélections de 1xBet")
    print("==================================================")
    
    # Demander la catégorie
    category = input("Entrez la catégorie (ex: 'Temps réglementaire', '1 Set', etc.): ")
    
    # Demander si l'utilisateur veut utiliser l'exemple HTML
    use_example = input("Voulez-vous utiliser l'exemple HTML? (o/n): ").lower() == 'o'
    
    if use_example:
        html_content = EXAMPLE_HTML
    else:
        print("Collez le HTML à analyser (terminez par une ligne vide):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        html_content = '\n'.join(lines)
    
    # Extraire les types de paris et sélections
    bet_type, selections = extract_bet_types_and_selections(html_content)
    
    if bet_type:
        print(f"\nType de pari extrait: {bet_type}")
        print(f"Nombre de sélections: {len(selections)}")
        print("Sélections:")
        for selection in selections:
            print(f"- {selection}")
        
        # Mettre à jour les fichiers JSON
        update_json_files(category, bet_type, selections)
    else:
        print("Aucun type de pari trouvé dans le HTML fourni.")

if __name__ == "__main__":
    main()