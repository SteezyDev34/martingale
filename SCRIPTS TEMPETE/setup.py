#!/usr/bin/env python3
"""
Script d'installation et de vérification des dépendances pour tempeteBetting
Usage: python setup.py
"""
import subprocess
import sys
import os
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🚀 SETUP TEMPETE BETTING")
    print("=" * 60)
    print("Ce script va installer toutes les dépendances nécessaires.")
    print()

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    print(f"🐍 Version Python détectée: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 ou supérieur est requis!")
        return False
    
    print("✅ Version Python compatible")
    return True

def check_pip():
    """Vérifie que pip est disponible"""
    try:
        import pip
        print("✅ pip est disponible")
        return True
    except ImportError:
        print("❌ pip n'est pas installé!")
        return False

def install_requirements():
    """Installe les requirements"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ Fichier requirements.txt non trouvé!")
        return False
    
    print("📦 Installation des dépendances...")
    try:
        # Mise à jour de pip
        print("⬆️  Mise à jour de pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Installation des requirements
        print("📥 Installation des packages...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Toutes les dépendances ont été installées!")
            return True
        else:
            print("❌ Erreur lors de l'installation:")
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False

def check_tesseract():
    """Vérifie que Tesseract OCR est installé"""
    try:
        subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
        print("✅ Tesseract OCR est installé")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Tesseract OCR n'est pas installé ou pas dans le PATH")
        print("Sur macOS: brew install tesseract")
        print("Sur Ubuntu: sudo apt-get install tesseract-ocr")
        print("Sur Windows: Téléchargez depuis https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def test_imports():
    """Test l'import de tous les modules requis"""
    print("🧪 Test des imports...")
    
    modules_to_test = [
        'requests',
        'bs4',
        'sqlite3',
        're',
        'io',
        'time',
        'datetime',
        'PIL',
        'telepot',
        'pytesseract',
        'cv2',
        'numpy'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  {len(failed_imports)} module(s) échoué(s): {', '.join(failed_imports)}")
        return False
    else:
        print("\n🎉 Tous les modules sont importables!")
        return True

def create_test_script():
    """Crée un script de test rapide"""
    test_content = '''#!/usr/bin/env python3
"""
Script de test rapide pour vérifier l'installation
"""
import sys
sys.path.append('.')

try:
    from dependency_manager import check_and_install_dependencies
    print("✅ Module dependency_manager importé avec succès")
    
    # Test de la vérification des dépendances
    result = check_and_install_dependencies(auto_install=False)
    if result:
        print("✅ Test de vérification des dépendances réussi")
    else:
        print("⚠️  Certaines dépendances pourraient manquer")
        
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    sys.exit(1)

print("🎉 Installation vérifiée avec succès!")
'''
    
    with open('test_installation.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("📝 Script de test créé: test_installation.py")

def main():
    print_banner()
    
    # Vérifications préliminaires
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # Installation
    if not install_requirements():
        sys.exit(1)
    
    # Vérifications post-installation
    check_tesseract()
    
    if test_imports():
        print("\n🎉 Installation terminée avec succès!")
        
        # Création du script de test
        create_test_script()
        
        print("\n📋 Prochaines étapes:")
        print("1. Configurez votre token Telegram dans tempeteBetting.py")
        print("2. Vérifiez que Tesseract OCR est installé si vous en avez besoin")
        print("3. Lancez le programme: python tempeteBetting.py")
        print("4. Testez l'installation: python test_installation.py")
        
    else:
        print("\n⚠️  Installation partiellement réussie.")
        print("Certains modules pourraient nécessiter une installation manuelle.")
        sys.exit(1)

if __name__ == "__main__":
    main()