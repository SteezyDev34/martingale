# Tempete Betting - Gestionnaire de Dépendances

Ce projet inclut un système automatique de vérification et d'installation des dépendances Python.

## 🚀 Installation Rapide

### Option 1: Script d'installation automatique

```bash
python setup.py
```

### Option 2: Installation manuelle

```bash
pip install -r requirements.txt
```

## 📦 Gestion des Dépendances

### Vérification automatique

Le programme vérifie automatiquement les dépendances au démarrage. Si des packages manquent, il proposera de les installer.

### Vérification manuelle

```bash
python dependency_manager.py
```

### Installation forcée des dépendances

```python
from dependency_manager import check_and_install_dependencies
check_and_install_dependencies(auto_install=True)
```

## 📋 Dépendances Requises

- `requests` - Pour les requêtes HTTP
- `beautifulsoup4` - Pour le parsing HTML
- `opencv-python` - Pour le traitement d'images
- `pillow` - Pour la manipulation d'images
- `pytesseract` - Pour l'OCR (reconnaissance de texte)
- `telepot` - Pour l'intégration Telegram
- `numpy` - Pour les calculs numériques

## 🔧 Configuration Additionnelle

### Tesseract OCR

Ce programme utilise Tesseract pour la reconnaissance de texte. Installez-le selon votre OS :

**macOS:**

```bash
brew install tesseract
```

**Ubuntu/Debian:**

```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Téléchargez depuis [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Configuration Telegram

1. Modifiez le token du bot dans `tempeteBetting.py`
2. Configurez l'ID du groupe/chat cible

## 🧪 Test de l'Installation

Après l'installation, vous pouvez tester avec :

```bash
python test_installation.py
```

## 📁 Structure du Projet

```
tempete/
├── tempeteBetting.py      # Script principal
├── ImageTreatment.py      # Module de traitement d'images
├── dependency_manager.py  # Gestionnaire de dépendances
├── requirements.txt       # Liste des dépendances
├── setup.py              # Script d'installation
├── test_installation.py  # Script de test (généré)
└── README.md             # Ce fichier
```

## 🐛 Résolution de Problèmes

### Erreurs d'importation

Si vous rencontrez des erreurs d'importation :

1. Vérifiez que vous êtes dans le bon environnement virtuel
2. Relancez `python setup.py`
3. Installez manuellement les packages manquants

### Erreurs Tesseract

Si Tesseract n'est pas trouvé :

1. Vérifiez l'installation avec `tesseract --version`
2. Ajoutez Tesseract au PATH de votre système
3. Sur Windows, spécifiez le chemin dans le code

### Problèmes de permissions

Sur macOS/Linux, vous pourriez avoir besoin de :

```bash
chmod +x setup.py
```

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs d'erreur
2. Assurez-vous que toutes les dépendances sont installées
3. Vérifiez la configuration de votre environnement Python
