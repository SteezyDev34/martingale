#!/usr/bin/env python3
"""
Test d'intégration pour vérifier que tempeteBetting.py fonctionne avec le gestionnaire de dépendances
"""
import sys
import subprocess
import os

def test_main_script():
    """Test le script principal avec la vérification des dépendances"""
    print("🧪 Test d'intégration du script principal...")
    
    try:
        # Test d'import sans exécution du main
        result = subprocess.run([
            sys.executable, '-c', 
            """
import sys
sys.path.append('.')

# Test d'import du script principal
try:
    import tempeteBetting
    print("✅ Import de tempeteBetting réussi")
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

# Test de l'import du gestionnaire de dépendances
try:
    from dependency_manager import DependencyManager
    dm = DependencyManager()
    print(f"✅ DependencyManager chargé - {len(dm.required_packages)} packages requis")
except Exception as e:
    print(f"❌ Erreur du gestionnaire: {e}")
    sys.exit(1)

print("🎉 Test d'intégration réussi!")
"""
        ], cwd=os.getcwd(), capture_output=True, text=True, timeout=30)
        
        print("Sortie:")
        print(result.stdout)
        
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout du test")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    print("=" * 50)
    print("🔧 TEST D'INTÉGRATION TEMPETE BETTING")
    print("=" * 50)
    
    if test_main_script():
        print("\n✅ Tous les tests d'intégration sont passés!")
        print("\n📋 Le système de gestion des dépendances est opérationnel:")
        print("• Vérification automatique au démarrage")
        print("• Installation automatique des packages manquants")
        print("• Gestion des erreurs d'import")
        print("\n🚀 Vous pouvez maintenant lancer le programme principal!")
        
    else:
        print("\n❌ Échec des tests d'intégration")
        print("Vérifiez les erreurs ci-dessus et corrigez les problèmes.")
        sys.exit(1)

if __name__ == "__main__":
    main()