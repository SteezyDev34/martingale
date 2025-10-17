"""
Module d'automatisation visuelle pour canvas avec OCR
Permet de capturer un canvas, détecter du texte avec Tesseract et cliquer automatiquement
"""

import time
import os
import sys
from typing import Optional, Dict, List, Tuple, Union, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Gestion des imports optionnels avec vérifications
PIL_AVAILABLE = False
PYTESSERACT_AVAILABLE = False

# Variables pour stocker les modules importés
Image = None
pytesseract = None

def _importer_dependances():
    """Importe les dépendances optionnelles de manière sécurisée"""
    global PIL_AVAILABLE, PYTESSERACT_AVAILABLE, Image, pytesseract
    
    # Import de PIL
    try:
        import importlib
        pil_module = importlib.import_module('PIL.Image')
        Image = pil_module
        PIL_AVAILABLE = True
    except ImportError:
        print("❌ PIL (Pillow) n'est pas installé. Exécutez: pip install Pillow")
        PIL_AVAILABLE = False
    
    # Import de pytesseract
    try:
        import importlib
        pytesseract = importlib.import_module('pytesseract')
        PYTESSERACT_AVAILABLE = True
        
        # Configuration de Tesseract (ajustez le chemin selon votre installation)
        if os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        else:  # macOS/Linux
            # Essayer plusieurs chemins possibles pour Tesseract
            chemins_possibles = [
                '/usr/local/bin/tesseract',  # Installation Homebrew classique
                '/opt/homebrew/bin/tesseract',  # Installation Homebrew M1/M2
                '/usr/bin/tesseract'  # Installation système
            ]
            for chemin in chemins_possibles:
                if os.path.exists(chemin):
                    pytesseract.pytesseract.tesseract_cmd = chemin
                    break
    except ImportError:
        print("❌ pytesseract n'est pas installé. Exécutez: pip install pytesseract")
        PYTESSERACT_AVAILABLE = False

# Initialiser les dépendances au chargement du module
_importer_dependances()


def capturer_canvas(driver: Any, canvas_selector: Optional[str] = None, canvas_element: Any = None, nom_fichier: str = "canvas_capture.png") -> Tuple[Any, Optional[str]]:
    """
    Capture le contenu d'un canvas en image
    
    Args:
        driver: Instance du WebDriver Selenium
        canvas_selector: Sélecteur CSS/XPath pour trouver le canvas (optionnel si canvas_element fourni)
        canvas_element: Élément canvas déjà trouvé (optionnel si canvas_selector fourni)
        nom_fichier: Nom du fichier de sortie pour l'image du canvas
        
    Returns:
        tuple: (canvas_element, canvas_image_path) ou (None, None) en cas d'erreur
    """
    if not PIL_AVAILABLE or Image is None:
        print("❌ PIL (Pillow) n'est pas disponible. Impossible de capturer le canvas.")
        return None, None
        
    try:
        # Trouver l'élément canvas
        if canvas_element is None:
            if canvas_selector is None:
                canvas_selector = "canvas"  # Sélecteur par défaut
            
            if canvas_selector.startswith("//"):
                canvas = driver.find_element(By.XPATH, canvas_selector)
            elif "." in canvas_selector:
                canvas = driver.find_element(By.CLASS_NAME, canvas_selector.replace(".", ""))
            elif "#" in canvas_selector:
                canvas = driver.find_element(By.ID, canvas_selector.replace("#", ""))
            else:
                canvas = driver.find_element(By.TAG_NAME, canvas_selector)
        else:
            canvas = canvas_element
        
        # Attendre que le canvas soit chargé
        time.sleep(1)
        
        # Obtenir la position et la taille du canvas
        location = canvas.location
        size = canvas.size
        
        # Capture de la page entière
        driver.save_screenshot("page_complete.png")
        
        # Ouvrir l'image et découper la partie du canvas
        image = Image.open("page_complete.png")
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']
        
        # Découper l'image du canvas
        canvas_image = image.crop((left, top, right, bottom))
        canvas_image.save(nom_fichier)
        
        # Nettoyer le fichier temporaire
        os.remove("page_complete.png")
        
        print(f"✅ Canvas capturé avec succès : {nom_fichier}")
        print(f"📐 Dimensions : {size['width']}x{size['height']} pixels")
        
        return canvas, nom_fichier
        
    except Exception as e:
        print(f"❌ Erreur lors de la capture du canvas : {str(e)}")
        return None, None


def detecter_texte_ocr(image_path: str, mot_cible: str, config_ocr: Optional[str] = None) -> Optional[Dict[str, Union[int, str]]]:
    """
    Utilise l'OCR pour détecter un texte spécifique dans une image
    
    Args:
        image_path: Chemin vers l'image à analyser
        mot_cible: Texte à rechercher
        config_ocr: Configuration personnalisée pour Tesseract (optionnel)
        
    Returns:
        dict: Informations sur le texte trouvé (x, y, width, height) ou None si non trouvé
    """
    if not PIL_AVAILABLE or not PYTESSERACT_AVAILABLE or Image is None or pytesseract is None:
        print("❌ PIL ou pytesseract n'est pas disponible. Impossible d'effectuer l'OCR.")
        return None
        
    try:
        # Charger l'image
        image = Image.open(image_path)
        
        # Configuration par défaut pour Tesseract
        if config_ocr is None:
            config_ocr = '--psm 6'  # Assume a single uniform block of text
        
        # Extraire les données OCR
        data = pytesseract.image_to_data(image, config=config_ocr, output_type=pytesseract.Output.DICT)
        
        # Rechercher le mot cible
        for i in range(len(data['text'])):
            texte_detecte = data['text'][i].strip()
            if texte_detecte and mot_cible.lower() in texte_detecte.lower():
                resultat = {
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'texte': texte_detecte,
                    'confiance': data['conf'][i]
                }
                
                print(f"🎯 Texte '{mot_cible}' trouvé : '{texte_detecte}'")
                print(f"📍 Position : x={resultat['x']}, y={resultat['y']}")
                print(f"📏 Taille : {resultat['width']}x{resultat['height']}")
                print(f"🎯 Confiance : {resultat['confiance']}%")
                
                return resultat
        
        print(f"❌ Texte '{mot_cible}' non trouvé dans l'image")
        return None
        
    except Exception as e:
        print(f"❌ Erreur lors de l'OCR : {str(e)}")
        return None


def cliquer_sur_texte_canvas(driver: Any, canvas_element: Any, coordonnees_texte: Dict[str, Union[int, str]]) -> bool:
    """
    Clique sur un texte détecté dans un canvas avec plusieurs méthodes de fallback
    
    Args:
        driver: Instance du WebDriver Selenium
        canvas_element: Élément canvas
        coordonnees_texte: Dictionnaire avec les coordonnées du texte (x, y, width, height)
        
    Returns:
        bool: True si le clic a réussi, False sinon
    """
    try:
        # Calculer le centre du texte détecté
        x_center = int(coordonnees_texte['x']) + int(coordonnees_texte['width']) // 2
        y_center = int(coordonnees_texte['y']) + int(coordonnees_texte['height']) // 2
        
        # Obtenir les dimensions du canvas pour ajuster les coordonnées
        canvas_size = canvas_element.size
        canvas_width = canvas_size['width']
        canvas_height = canvas_size['height']
        
        # Ajuster les coordonnées : move_to_element_with_offset utilise le centre du canvas comme référence (0,0)
        # Donc nous devons soustraire la moitié des dimensions pour convertir depuis le coin supérieur gauche
        x_offset = x_center - (canvas_width // 2)
        y_offset = y_center - (canvas_height // 2)
        
        print(f"🖱️ Coordonnées OCR : ({x_center}, {y_center})")
        print(f"📐 Dimensions canvas : {canvas_width}x{canvas_height}")
        print(f"🎯 Offset ajusté : ({x_offset}, {y_offset})")
        
        # Méthode 1: ActionChains avec move_to_element_with_offset (coordonnées ajustées)
        try:
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(canvas_element, x_offset, y_offset).click().perform()
            print(f"✅ Clic réussi avec ActionChains (méthode 1)")
            time.sleep(0.5)  # Petit délai pour laisser le temps au clic de s'enregistrer
            return True
        except Exception as e1:
            print(f"⚠️ Méthode 1 échouée : {str(e1)}")
        
        # Méthode 2: ActionChains avec pause (coordonnées ajustées)
        try:
            actions = ActionChains(driver)
            actions.move_to_element(canvas_element).pause(0.1)
            actions.move_by_offset(x_offset, y_offset).pause(0.1)
            actions.click().perform()
            print(f"✅ Clic réussi avec ActionChains + pause (méthode 2)")
            time.sleep(0.5)
            return True
        except Exception as e2:
            print(f"⚠️ Méthode 2 échouée : {str(e2)}")
        
        # Méthode 3: JavaScript click
        try:
            # Obtenir les coordonnées absolues du canvas
            canvas_rect = driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {x: rect.left, y: rect.top, width: rect.width, height: rect.height};
            """, canvas_element)
            
            # Calculer les coordonnées absolues
            abs_x = canvas_rect['x'] + x_center
            abs_y = canvas_rect['y'] + y_center
            
            # Simuler un clic JavaScript
            driver.execute_script("""
                var canvas = arguments[0];
                var x = arguments[1];
                var y = arguments[2];
                var event = new MouseEvent('click', {
                    clientX: x,
                    clientY: y,
                    bubbles: true,
                    cancelable: true
                });
                canvas.dispatchEvent(event);
            """, canvas_element, abs_x, abs_y)
            
            print(f"✅ Clic réussi avec JavaScript (méthode 3)")
            time.sleep(0.5)
            return True
        except Exception as e3:
            print(f"⚠️ Méthode 3 échouée : {str(e3)}")
        
        print(f"❌ Toutes les méthodes de clic ont échoué")
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale lors du clic : {str(e)}")
        return False


def automatisation_complete_canvas(driver: Any, mot_cible: str, canvas_selector: Optional[str] = None, canvas_element: Any = None, config_ocr: Optional[str] = None) -> bool:
    """
    Fonction complète d'automatisation : capture + OCR + clic
    
    Args:
        driver: Instance du WebDriver Selenium
        mot_cible: Texte à rechercher et sur lequel cliquer
        canvas_selector: Sélecteur pour trouver le canvas (optionnel)
        canvas_element: Élément canvas déjà trouvé (optionnel)
        config_ocr: Configuration Tesseract (optionnel)
        
    Returns:
        bool: True si toute la séquence a réussi, False sinon
    """
    print(f"🚀 Début de l'automatisation pour le texte : '{mot_cible}'")
    
    # Étape 1 : Capturer le canvas
    canvas, image_path = capturer_canvas(driver, canvas_selector, canvas_element)
    if canvas is None or image_path is None:
        return False
    
    # Étape 2 : Détecter le texte avec OCR
    coordonnees = detecter_texte_ocr(image_path, mot_cible, config_ocr)
    if coordonnees is None:
        # Nettoyer le fichier temporaire
        if os.path.exists(image_path):
            os.remove(image_path)
        return False
    
    # Étape 3 : Cliquer sur le texte
    succes_clic = cliquer_sur_texte_canvas(driver, canvas, coordonnees)
    
    # Nettoyer le fichier temporaire
    if os.path.exists(image_path):
        os.remove(image_path)
    
    if succes_clic:
        print("✅ Automatisation terminée avec succès !")
    else:
        print("❌ Échec de l'automatisation")
    
    return succes_clic


def lister_tout_le_texte_canvas(driver: Any, canvas_selector: Optional[str] = None, canvas_element: Any = None) -> List[Dict[str, Union[int, str]]]:
    """
    Fonction utilitaire pour lister tout le texte détecté dans un canvas
    Utile pour déboguer et voir ce que l'OCR peut détecter
    
    Args:
        driver: Instance du WebDriver Selenium
        canvas_selector: Sélecteur pour trouver le canvas (optionnel)
        canvas_element: Élément canvas déjà trouvé (optionnel)
        
    Returns:
        list: Liste de tous les textes détectés avec leurs coordonnées
    """
    print("🔍 Analyse complète du texte dans le canvas...")
    
    # Capturer le canvas
    canvas, image_path = capturer_canvas(driver, canvas_selector, canvas_element, "debug_canvas.png")
    if canvas is None or image_path is None:
        return []
    
    if not PIL_AVAILABLE or not PYTESSERACT_AVAILABLE or Image is None or pytesseract is None:
        print("❌ PIL ou pytesseract n'est pas disponible. Impossible d'effectuer l'analyse.")
        if os.path.exists(image_path):
            os.remove(image_path)
        return []
    
    try:
        # Charger l'image
        image = Image.open(image_path)
        
        # Extraire toutes les données OCR
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        textes_detectes = []
        for i in range(len(data['text'])):
            texte = data['text'][i].strip()
            if texte and data['conf'][i] > 30:  # Seuil de confiance minimum
                texte_info = {
                    'texte': texte,
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'confiance': data['conf'][i]
                }
                textes_detectes.append(texte_info)
                print(f"📝 '{texte}' à ({texte_info['x']}, {texte_info['y']}) - Confiance: {texte_info['confiance']}%")
        
        print(f"📊 Total de {len(textes_detectes)} textes détectés")
        
        # Nettoyer le fichier temporaire
        if os.path.exists(image_path):
            os.remove(image_path)
        
        return textes_detectes
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse : {str(e)}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return []