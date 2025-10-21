"""
Module pour résoudre les problèmes SSL avec les API externes
"""
import ssl
import certifi
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SSLContextManager:
    """Gestionnaire de contexte SSL pour résoudre les problèmes de certificats"""
    
    def __init__(self):
        self.original_ssl_context = None
        
    def create_ssl_context(self, verify_ssl=True):
        """Crée un contexte SSL approprié"""
        if verify_ssl:
            # Utilise les certificats de certifi
            context = ssl.create_default_context(cafile=certifi.where())
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            # Contexte SSL moins strict (à utiliser avec précaution)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        return context
    
    def get_requests_session(self, verify_ssl=True, retries=3):
        """Crée une session requests avec gestion SSL appropriée"""
        session = requests.Session()
        
        if verify_ssl:
            # Utilise les certificats de certifi
            session.verify = certifi.where()
        else:
            # Désactive la vérification SSL (non recommandé en production)
            session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configuration des retry
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

def fix_ssl_for_telegram():
    """Configure SSL spécifiquement pour l'API Telegram"""
    try:
        # Test de connexion à l'API Telegram
        ssl_manager = SSLContextManager()
        
        # D'abord, essayons avec SSL vérifié
        session = ssl_manager.get_requests_session(verify_ssl=True)
        
        try:
            response = session.get("https://api.telegram.org", timeout=10)
            print("✅ Connexion SSL sécurisée à Telegram réussie")
            return session, True
        except requests.exceptions.SSLError:
            print("⚠️  Échec de la connexion SSL sécurisée, tentative avec SSL détendu...")
            
            # Si ça échoue, utilisons une approche moins stricte
            session = ssl_manager.get_requests_session(verify_ssl=False)
            response = session.get("https://api.telegram.org", timeout=10)
            print("⚠️  Connexion SSL non-vérifiée à Telegram réussie (moins sécurisé)")
            return session, False
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration SSL: {e}")
        return None, False

def create_telegram_bot_with_ssl_fix():
    """Crée un bot Telegram avec correction SSL"""
    try:
        import telepot
        from telepot.api import set_proxy
        
        # Configuration SSL pour telepot
        session, is_secure = fix_ssl_for_telegram()
        
        if session:
            # Monkey patch pour telepot si nécessaire
            original_request = telepot.api._requests.request
            
            def patched_request(*args, **kwargs):
                kwargs['verify'] = session.verify
                return original_request(*args, **kwargs)
            
            telepot.api._requests.request = patched_request
            print("✅ Correction SSL appliquée à telepot")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration de telepot: {e}")
        return False

def update_certificates():
    """Met à jour les certificats du système"""
    try:
        import subprocess
        import sys
        
        print("🔄 Mise à jour des certificats...")
        
        # Sur macOS, mise à jour des certificats
        try:
            subprocess.run([
                sys.executable, '-c',
                'import ssl; ssl.create_default_context().load_verify_locations()'
            ], check=True, capture_output=True)
            print("✅ Certificats Python vérifiés")
        except subprocess.CalledProcessError:
            print("⚠️  Problème avec les certificats Python")
        
        # Installation/mise à jour de certifi
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'certifi'
            ], check=True, capture_output=True)
            print("✅ Package certifi mis à jour")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Impossible de mettre à jour certifi: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour des certificats: {e}")
        return False

def diagnose_ssl_issues():
    """Diagnostique les problèmes SSL"""
    print("🔍 Diagnostic des problèmes SSL...")
    
    # Vérification de certifi
    try:
        import certifi
        cert_path = certifi.where()
        print(f"✅ Certificats certifi trouvés: {cert_path}")
    except ImportError:
        print("❌ Package certifi non installé")
        return False
    
    # Test de connexion basique
    try:
        import requests
        response = requests.get("https://httpbin.org/get", timeout=10)
        print("✅ Connexion HTTPS basique réussie")
    except Exception as e:
        print(f"❌ Échec connexion HTTPS basique: {e}")
    
    # Test spécifique à Telegram
    try:
        response = requests.get("https://api.telegram.org", timeout=10)
        print("✅ Connexion à l'API Telegram réussie")
        return True
    except Exception as e:
        print(f"❌ Échec connexion API Telegram: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 DIAGNOSTIC ET CORRECTION SSL")
    print("=" * 50)
    
    # Diagnostic
    ssl_ok = diagnose_ssl_issues()
    
    if not ssl_ok:
        print("\n🛠️  Tentative de correction...")
        update_certificates()
        create_telegram_bot_with_ssl_fix()
        
        print("\n🔄 Nouveau test après correction...")
        diagnose_ssl_issues()