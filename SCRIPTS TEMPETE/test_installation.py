#!/usr/bin/env python3
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
