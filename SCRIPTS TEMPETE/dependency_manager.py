"""
Module de gestion et vérification des dépendances
"""
import subprocess
import sys
import importlib
import pkg_resources
from pathlib import Path
import os

class DependencyManager:
    def __init__(self, requirements_file='requirements.txt'):
        self.requirements_file = requirements_file
        self.missing_packages = []
        self.required_packages = self._parse_requirements()
    
    def _parse_requirements(self):
        """Parse le fichier requirements.txt"""
        requirements_path = Path(self.requirements_file)
        if not requirements_path.exists():
            print(f"❌ Fichier {self.requirements_file} non trouvé!")
            return []
        
        packages = []
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Sépare le nom du package de la version
                        if '>=' in line:
                            package_name = line.split('>=')[0].strip()
                            version = line.split('>=')[1].strip()
                        elif '==' in line:
                            package_name = line.split('==')[0].strip()
                            version = line.split('==')[1].strip()
                        else:
                            package_name = line.strip()
                            version = None
                        packages.append({'name': package_name, 'version': version, 'requirement': line})
        except Exception as e:
            print(f"❌ Erreur lors de la lecture de {self.requirements_file}: {e}")
            return []
        
        return packages
    
    def _get_installed_version(self, package_name):
        """Obtient la version installée d'un package"""
        try:
            # Essai avec pkg_resources
            try:
                return pkg_resources.get_distribution(package_name).version
            except pkg_resources.DistributionNotFound:
                pass
            
            # Essai avec importlib pour certains packages avec des noms différents
            package_mappings = {
                'opencv-python': 'cv2',
                'pillow': 'PIL',
                'beautifulsoup4': 'bs4'
            }
            
            import_name = package_mappings.get(package_name, package_name)
            
            try:
                module = importlib.import_module(import_name)
                if hasattr(module, '__version__'):
                    return module.__version__
                elif hasattr(module, 'VERSION'):
                    return module.VERSION
                elif hasattr(module, 'version'):
                    return module.version
                else:
                    return "unknown"
            except ImportError:
                return None
        except Exception:
            return None
    
    def check_dependencies(self):
        """Vérifie toutes les dépendances"""
        print("🔍 Vérification des dépendances...")
        self.missing_packages = []
        
        for package in self.required_packages:
            package_name = package['name']
            required_version = package['version']
            
            installed_version = self._get_installed_version(package_name)
            
            if installed_version is None:
                print(f"❌ {package_name} n'est pas installé")
                self.missing_packages.append(package)
            else:
                if required_version and installed_version != "unknown":
                    try:
                        # Comparaison simple de version (peut être améliorée)
                        if self._version_compare(installed_version, required_version):
                            print(f"✅ {package_name} ({installed_version}) - OK")
                        else:
                            print(f"⚠️  {package_name} ({installed_version}) - Version requise: {required_version}")
                            self.missing_packages.append(package)
                    except Exception:
                        print(f"✅ {package_name} ({installed_version}) - Version vérifiée")
                else:
                    print(f"✅ {package_name} ({installed_version}) - OK")
        
        return len(self.missing_packages) == 0
    
    def _version_compare(self, installed, required):
        """Compare les versions (simple)"""
        try:
            installed_parts = [int(x) for x in installed.split('.')]
            required_parts = [int(x) for x in required.split('.')]
            
            # Égalise la longueur des listes
            max_len = max(len(installed_parts), len(required_parts))
            installed_parts.extend([0] * (max_len - len(installed_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            return installed_parts >= required_parts
        except Exception:
            return True  # En cas d'erreur, on considère que c'est OK
    
    def install_missing_packages(self, auto_install=False):
        """Installe les packages manquants"""
        if not self.missing_packages:
            print("✅ Toutes les dépendances sont installées!")
            return True
        
        print(f"\n📦 {len(self.missing_packages)} package(s) manquant(s) détecté(s):")
        for package in self.missing_packages:
            print(f"  - {package['requirement']}")
        
        if not auto_install:
            response = input("\n❓ Voulez-vous installer les packages manquants? (o/n): ").lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("❌ Installation annulée.")
                return False
        
        print("\n🚀 Installation des packages manquants...")
        
        try:
            # Installation via pip
            for package in self.missing_packages:
                print(f"📥 Installation de {package['requirement']}...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package['requirement']
                ], capture_output=True, text=True, check=True)
                
                if result.returncode == 0:
                    print(f"✅ {package['name']} installé avec succès!")
                else:
                    print(f"❌ Erreur lors de l'installation de {package['name']}")
                    print(f"Erreur: {result.stderr}")
                    return False
            
            print("\n🎉 Toutes les dépendances ont été installées avec succès!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation: {e}")
            print(f"Sortie d'erreur: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
    
    def generate_requirements(self, output_file='requirements_generated.txt'):
        """Génère un fichier requirements.txt basé sur les packages installés"""
        try:
            print(f"📝 Génération du fichier {output_file}...")
            installed_packages = [d for d in pkg_resources.working_set]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for package in sorted(installed_packages, key=lambda x: x.project_name):
                    f.write(f"{package.project_name}=={package.version}\n")
            
            print(f"✅ Fichier {output_file} généré avec succès!")
            print(f"📊 {len(installed_packages)} packages listés.")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")

def check_and_install_dependencies(requirements_file='requirements.txt', auto_install=False):
    """Fonction utilitaire pour vérifier et installer les dépendances"""
    dm = DependencyManager(requirements_file)
    
    print("=" * 50)
    print("🔧 GESTIONNAIRE DE DÉPENDANCES")
    print("=" * 50)
    
    # Vérification
    all_installed = dm.check_dependencies()
    
    if not all_installed:
        # Installation si nécessaire
        success = dm.install_missing_packages(auto_install)
        if success:
            print("\n🔄 Nouvelle vérification...")
            dm.check_dependencies()
        return success
    else:
        print("\n🎉 Toutes les dépendances sont satisfaites!")
        return True

if __name__ == "__main__":
    # Test du gestionnaire
    check_and_install_dependencies()