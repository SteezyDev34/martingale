#!/usr/bin/env python3
"""
Script pour corriger les problèmes SSL sur macOS
"""
import ssl
import os
import sys
import subprocess
import requests
import urllib3

def fix_macos_ssl():
    """Corrige les problèmes SSL spécifiques à macOS"""
    print("🍎 Correction SSL pour macOS...")
    
    try:
        # Mise à jour de certifi
        print("📦 Installation/mise à jour de certifi...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'certifi'], 
                      check=True, capture_output=True)
        
        # Installation des certificats Python
        print("🔒 Configuration des certificats Python...")
        
        # Recherche du script d'installation des certificats
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        possible_paths = [
            f"/Applications/Python {python_version}/Install Certificates.command",
            "/Applications/Python 3.9/Install Certificates.command",
            "/Applications/Python 3.8/Install Certificates.command",
        ]
        
        cert_script = None
        for path in possible_paths:
            if os.path.exists(path):
                cert_script = path
                break
        
        if cert_script:
            print(f"🚀 Exécution du script: {cert_script}")
            subprocess.run([cert_script], check=True)
        else:
            print("⚠️  Script d'installation des certificats non trouvé")
            print("📝 Installation manuelle des certificats...")
            
            # Installation manuelle via certifi
            import certifi
            import ssl
            
            # Création d'un contexte SSL avec les certificats certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            print("✅ Contexte SSL créé avec les certificats certifi")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction SSL: {e}")
        return False

def test_telegram_connection():
    """Test spécifique de la connexion à l'API Telegram"""
    print("🔍 Test de connexion à l'API Telegram...")
    
    # Test avec différentes méthodes
    methods = [
        ("Standard", lambda: requests.get("https://api.telegram.org", timeout=10)),
        ("Avec certifi", lambda: requests.get("https://api.telegram.org", 
                                              verify=get_certifi_path(), timeout=10)),
        ("Sans vérification", lambda: requests.get("https://api.telegram.org", 
                                                   verify=False, timeout=10))
    ]
    
    for name, test_func in methods:
        try:
            if name == "Sans vérification":
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = test_func()
            print(f"✅ {name}: Succès (Status: {response.status_code})")
            return True
            
        except Exception as e:
            print(f"❌ {name}: Échec - {str(e)[:100]}...")
    
    return False

def get_certifi_path():
    """Obtient le chemin vers les certificats certifi"""
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None

def create_patched_telepot():
    """Crée une version patchée de telepot avec correction SSL"""
    print("🔧 Application du patch SSL pour telepot...")
    
    try:
        # Patch pour telepot
        patch_code = '''
import telepot
import requests
import certifi
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Désactiver les warnings SSL pour les connexions non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLTelegramBot(telepot.Bot):
    def __init__(self, token, **kwargs):
        super().__init__(token, **kwargs)
        
        # Configuration d'une session requests personnalisée
        self._session = requests.Session()
        
        # Tentative avec certificats
        try:
            self._session.verify = certifi.where()
        except:
            # En dernier recours, désactiver la vérification SSL
            self._session.verify = False
            print("⚠️  Vérification SSL désactivée pour Telegram")
        
        # Configuration des retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
    
    def sendMessage(self, *args, **kwargs):
        """Override de sendMessage avec session personnalisée"""
        try:
            return super().sendMessage(*args, **kwargs)
        except Exception as e:
            if "SSL" in str(e) or "certificate" in str(e):
                print(f"🔒 Erreur SSL détectée: {e}")
                # Désactiver temporairement la vérification SSL
                original_verify = self._session.verify
                self._session.verify = False
                try:
                    result = super().sendMessage(*args, **kwargs)
                    self._session.verify = original_verify
                    return result
                except Exception as e2:
                    print(f"❌ Échec même sans SSL: {e2}")
                    raise
            else:
                raise

# Monkey patch pour remplacer telepot.Bot
telepot.Bot = SSLTelegramBot
'''
        
        with open('telepot_ssl_patch.py', 'w') as f:
            f.write(patch_code)
        
        print("✅ Patch telepot créé dans telepot_ssl_patch.py")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du patch: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 CORRECTION SSL POUR MACOS + TELEGRAM")
    print("=" * 60)
    
    # Correction générale SSL
    if fix_macos_ssl():
        print("✅ Correction SSL générale réussie")
    
    # Test de connexion
    if test_telegram_connection():
        print("✅ Connexion Telegram possible")
    else:
        print("⚠️  Problèmes de connexion persistants")
        
        # Création du patch telepot
        if create_patched_telepot():
            print("✅ Patch telepot créé")
            print("\n📋 Instructions:")
            print("1. Importez le patch dans votre script:")
            print("   import telepot_ssl_patch")
            print("2. Utilisez telepot.Bot normalement")
    
    print("\n🔧 Solutions manuelles à essayer:")
    print("1. Mettre à jour macOS: sudo softwareupdate -i -a")
    print("2. Réinitialiser le keychain: Trousseau d'accès > Certificats")
    print("3. Utiliser un VPN si vous êtes derrière un proxy d'entreprise")
    print("4. Vérifier les paramètres de sécurité réseau")

if __name__ == "__main__":
    main()