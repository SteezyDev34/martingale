"""
Exemple d'utilisation des fonctions d'automatisation visuelle avec OCR
Montre comment intégrer la solution dans GetBet copy.py
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# Import des fonctions OCR
from CanvasOCR import automatisation_complete_canvas, lister_tout_le_texte_canvas

# from ChromeDriver.SetDriver1 import driver


def exemple_integration_getbet(driver):
    """
    Exemple d'intégration dans la fonction GetBet
    Montre comment remplacer les clics manuels par de l'automatisation OCR
    """
    try:
        # Attendre que le canvas soit visible (comme dans GetBet copy.py ligne 37-42)
        canvas = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'market-grid-canvas__container'))
        )

        # Option 1: Rechercher et cliquer sur un texte spécifique
        # Par exemple, rechercher "40:40" dans le canvas
        texte_a_chercher = "40:40"
        succes = automatisation_complete_canvas(
            driver=driver,
            mot_cible=texte_a_chercher,
            canvas_element=canvas
        )

        if succes:
            print(f"✅ Clic automatique réussi sur '{texte_a_chercher}'")
            return True
        else:
            print(f"❌ Impossible de trouver ou cliquer sur '{texte_a_chercher}'")
            return False

    except Exception as e:
        print(f"❌ Erreur dans l'automatisation : {str(e)}")
        return False


def exemple_debug_canvas(driver):
    """
    Exemple pour déboguer et voir tout le texte disponible dans un canvas
    Utile pour identifier les textes disponibles avant d'automatiser
    """
    try:
        # Trouver le canvas
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')

        # Lister tout le texte détectable
        textes_detectes = lister_tout_le_texte_canvas(driver, canvas_element=canvas)

        print("\n📋 Résumé des textes détectés :")
        for i, texte_info in enumerate(textes_detectes, 1):
            print(f"{i}. '{texte_info['texte']}' - Confiance: {texte_info['confiance']}%")

        return textes_detectes

    except Exception as e:
        print(f"❌ Erreur lors du debug : {str(e)}")
        return []


def exemple_recherche_multiple(driver, liste_textes):
    """
    Exemple pour rechercher plusieurs textes et cliquer sur le premier trouvé
    
    Args:
        driver: Instance WebDriver
        liste_textes: Liste des textes à rechercher par ordre de priorité
    """
    try:
        canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')

        for texte in liste_textes:
            print(f"🔍 Recherche de '{texte}'...")
            succes = automatisation_complete_canvas(
                driver=driver,
                mot_cible=texte,
                canvas_element=canvas
            )

            if succes:
                print(f"✅ Trouvé et cliqué sur '{texte}'")
                return texte

        print("❌ Aucun des textes recherchés n'a été trouvé")
        return None

    except Exception as e:
        print(f"❌ Erreur lors de la recherche multiple : {str(e)}")
        return None


def exemple_integration_complete(driver):
    """
    Exemple complet montrant toute la séquence d'automatisation
    Utilise le driver déjà lancé passé en paramètre
    """
    print("🚀 Démarrage de l'exemple complet d'automatisation OCR")
    
    try:
 

        # Attendre le chargement
        time.sleep(3)

        # Exemple 1: Debug - voir tout le texte disponible
        print("=== PHASE DEBUG ===")
        textes_disponibles = exemple_debug_canvas(driver)

        # Exemple 2: Recherche et clic automatique
        print("\n=== PHASE AUTOMATISATION ===")
        # Utiliser les textes tels qu'ils sont réellement détectés par l'OCR
        textes_a_chercher = ["Jeu 4 : 40-40 - Oui", "Jeu 4", "Oui"]
        texte_trouve = exemple_recherche_multiple(driver, textes_a_chercher)

        if texte_trouve:
            print(f"🎯 Automatisation réussie avec le texte : '{texte_trouve}'")
        else:
            print("❌ Aucun texte cible trouvé")

        # Attendre avant de continuer
        time.sleep(2)

    except Exception as e:
        print(f"❌ Erreur dans l'exemple complet : {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    import sys
    import os
    
    # Ajouter le répertoire parent au chemin Python
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from ChromeDriver.SetDriver1 import driver
    
    # Exécuter l'exemple complet
    exemple_integration_complete(driver)
