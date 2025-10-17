# 🎯 Automatisation Visuelle avec OCR pour Canvas

Cette solution permet d'automatiser les interactions avec des éléments `<canvas>` en utilisant la reconnaissance optique de caractères (OCR) avec Tesseract.

## 🚀 Installation

### 1. Installer Tesseract

#### Sur macOS (avec Homebrew)
```bash
brew install tesseract
```

#### Sur Windows
1. Télécharger Tesseract depuis : https://github.com/UB-Mannheim/tesseract/wiki
2. Installer et noter le chemin d'installation (généralement `C:\Program Files\Tesseract-OCR\`)

#### Sur Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

## 📋 Fonctionnalités

### Fonctions principales dans `CanvasOCR.py` :

1. **`capturer_canvas()`** - Capture le contenu d'un canvas en image
2. **`detecter_texte_ocr()`** - Utilise l'OCR pour détecter du texte dans une image
3. **`cliquer_sur_texte_canvas()`** - Clique automatiquement sur un texte détecté
4. **`automatisation_complete_canvas()`** - Fonction tout-en-un : capture + OCR + clic
5. **`lister_tout_le_texte_canvas()`** - Debug : liste tout le texte détectable

## 🔧 Utilisation

### Exemple simple
```python
from Functions.CanvasOCR import automatisation_complete_canvas
from selenium import webdriver
from selenium.webdriver.common.by import By

# Initialiser le driver
driver = webdriver.Chrome()
driver.get("https://votre-site.com")

# Trouver le canvas
canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')

# Automatisation complète : chercher "40:40" et cliquer dessus
succes = automatisation_complete_canvas(
    driver=driver,
    mot_cible="40:40",
    canvas_element=canvas
)

if succes:
    print("✅ Clic automatique réussi !")
else:
    print("❌ Texte non trouvé")
```

### Intégration dans GetBet copy.py

Remplacez la section de clic manuel (lignes 195+) par :

```python
from Functions.CanvasOCR import automatisation_complete_canvas

# Au lieu du clic manuel avec coordonnées fixes
canvas = driver.find_element(By.CLASS_NAME, 'market-grid-canvas__container')

# Rechercher et cliquer automatiquement sur le texte souhaité
if config.scriptType == "40A":
    texte_cible = "40:40"
elif config.scriptType == "30A":
    texte_cible = "30:30"
elif config.scriptType == "15A":
    texte_cible = "15:15"

succes = automatisation_complete_canvas(
    driver=driver,
    mot_cible=texte_cible,
    canvas_element=canvas
)

if not succes:
    # Fallback vers l'ancienne méthode si OCR échoue
    # ... code de clic manuel existant
```

## 🛠️ Debug et optimisation

### Voir tout le texte détectable
```python
from Functions.CanvasOCR import lister_tout_le_texte_canvas

textes = lister_tout_le_texte_canvas(driver, canvas_element=canvas)
for texte in textes:
    print(f"'{texte['texte']}' - Confiance: {texte['confiance']}%")
```

### Améliorer la détection OCR

Si la détection n'est pas optimale, vous pouvez :

1. **Ajuster la configuration Tesseract** :
```python
config_ocr = '--psm 8'  # Pour un seul mot
# ou
config_ocr = '--psm 6'  # Pour un bloc de texte uniforme
```

2. **Préprocesser l'image** (avec OpenCV) :
```python
import cv2
import numpy as np

def ameliorer_image_ocr(image_path):
    # Charger l'image
    img = cv2.imread(image_path)
    
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Augmenter le contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Sauvegarder l'image améliorée
    cv2.imwrite('image_amelioree.png', enhanced)
    return 'image_amelioree.png'
```

## ⚠️ Limitations et conseils

### Limitations
- L'OCR fonctionne mieux avec du texte net et contrasté
- Les polices stylisées ou les textes flous peuvent poser problème
- Plus lent que l'accès direct au DOM
- Dépendant de la résolution d'écran

### Conseils d'optimisation
1. **Utilisez cette méthode uniquement quand le DOM n'est pas accessible**
2. **Testez d'abord avec `lister_tout_le_texte_canvas()` pour voir ce qui est détectable**
3. **Gardez un fallback vers l'ancienne méthode en cas d'échec OCR**
4. **Ajustez le seuil de confiance selon vos besoins**

## 🔄 Intégration progressive

Pour une transition en douceur :

1. **Phase 1** : Testez avec `ExempleCanvasOCR.py`
2. **Phase 2** : Intégrez dans une copie de votre fonction existante
3. **Phase 3** : Ajoutez un système de fallback
4. **Phase 4** : Remplacez progressivement les clics manuels

## 📞 Support

En cas de problème :
1. Vérifiez que Tesseract est correctement installé
2. Testez avec `lister_tout_le_texte_canvas()` pour voir ce qui est détecté
3. Ajustez la configuration OCR selon le type de texte
4. Utilisez le preprocessing d'image si nécessaire