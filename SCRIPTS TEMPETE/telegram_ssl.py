"""
Alternative à telepot avec gestion SSL améliorée et rate limiting
"""
import requests
import json
import certifi
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import time
from datetime import datetime, timedelta

class TelegramBotSSL:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Configuration de la session avec SSL
        self.session = self._create_session()
        
        # Rate limiting - stockage des derniers envois par chat
        self.last_message_time = {}
        self.message_count = 0
        self.start_time = datetime.now()
        
        # Limites Telegram
        self.GLOBAL_LIMIT = 30  # messages per second
        self.CHAT_LIMIT = 1     # second between messages per chat
        self.BOT_LIMIT = 20     # messages per minute
    
    def _create_session(self):
        """Crée une session requests avec gestion SSL robuste"""
        session = requests.Session()
        
        # Configuration SSL
        try:
            # Utilise les certificats de certifi
            session.verify = certifi.where()
            print("✅ SSL configuré avec certifi")
        except Exception:
            # Fallback: désactiver SSL (non recommandé en production)
            session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            print("⚠️  SSL désactivé en fallback")
        
        # Configuration des retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _wait_for_rate_limit(self, chat_id):
        """Gère le rate limiting pour éviter l'erreur 429"""
        current_time = datetime.now()
        
        # Vérification du rate limiting par chat (1 message/seconde)
        if str(chat_id) in self.last_message_time:
            time_since_last = (current_time - self.last_message_time[str(chat_id)]).total_seconds()
            if time_since_last < self.CHAT_LIMIT:
                wait_time = self.CHAT_LIMIT - time_since_last
                print(f"⏳ Rate limiting: attente de {wait_time:.2f}s pour le chat {chat_id}")
                time.sleep(wait_time)
        
        # Vérification du rate limiting global (20 messages/minute)
        elapsed_minutes = (current_time - self.start_time).total_seconds() / 60
        if elapsed_minutes > 0:
            current_rate = self.message_count / elapsed_minutes
            if current_rate > self.BOT_LIMIT:
                wait_time = 60 / self.BOT_LIMIT  # Attendre pour respecter la limite
                print(f"⏳ Rate limiting global: attente de {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Mise à jour des compteurs
        self.last_message_time[str(chat_id)] = datetime.now()
        self.message_count += 1
    
    def _handle_429_error(self, response):
        """Gère l'erreur 429 avec retry-after"""
        retry_after = 1  # Par défaut 1 seconde
        
        try:
            # Essayer d'extraire retry-after des headers
            if 'retry-after' in response.headers:
                retry_after = int(response.headers['retry-after'])
            elif response.status_code == 429:
                # Extraire retry-after du JSON si disponible
                try:
                    error_data = response.json()
                    if 'parameters' in error_data and 'retry_after' in error_data['parameters']:
                        retry_after = error_data['parameters']['retry_after']
                except:
                    pass
        except:
            pass
        
        print(f"⏳ Erreur 429 détectée - Attente de {retry_after}s...")
        time.sleep(retry_after + 1)  # +1 seconde de sécurité
        return retry_after
    
    def send_message(self, chat_id, text, parse_mode=None, max_retries=3):
        """Envoie un message texte avec gestion du rate limiting"""
        
        for attempt in range(max_retries):
            try:
                # Appliquer le rate limiting avant l'envoi
                self._wait_for_rate_limit(chat_id)
                
                url = f"{self.base_url}/sendMessage"
                
                data = {
                    'chat_id': chat_id,
                    'text': text
                }
                
                if parse_mode:
                    data['parse_mode'] = parse_mode
                
                response = self.session.post(url, data=data, timeout=30)
                
                # Gestion spécifique de l'erreur 429
                if response.status_code == 429:
                    if attempt < max_retries - 1:  # Si ce n'est pas la dernière tentative
                        self._handle_429_error(response)
                        continue
                    else:
                        raise requests.exceptions.HTTPError(f"429 Client Error: Too Many Requests après {max_retries} tentatives")
                
                response.raise_for_status()
                
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    raise Exception(f"API Error: {result.get('description', 'Unknown error')}")
                    
            except requests.exceptions.SSLError as e:
                print(f"🔒 Erreur SSL: {e}")
                # Tentative sans vérification SSL
                original_verify = self.session.verify
                self.session.verify = False
                
                try:
                    self._wait_for_rate_limit(chat_id)  # Rate limiting même en SSL fallback
                    response = self.session.post(url, data=data, timeout=30)
                    
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            self.session.verify = original_verify
                            self._handle_429_error(response)
                            continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Restaurer la vérification SSL
                    self.session.verify = original_verify
                    
                    if result.get('ok'):
                        print("✅ Message envoyé avec SSL détendu")
                        return result
                    else:
                        raise Exception(f"API Error: {result.get('description', 'Unknown error')}")
                        
                except Exception as e2:
                    self.session.verify = original_verify
                    if attempt == max_retries - 1:  # Dernière tentative
                        raise Exception(f"Échec complet: {e2}")
                    else:
                        print(f"⚠️  Tentative {attempt + 1} échouée: {e2}")
                        time.sleep(2 ** attempt)  # Backoff exponentiel
            
            except requests.exceptions.HTTPError as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # Gestion générale du 429
                    print(f"⚠️  Erreur 429 - Tentative {attempt + 1}/{max_retries}")
                    time.sleep(5 * (attempt + 1))  # Attente progressive
                    continue
                else:
                    raise Exception(f"Erreur HTTP: {e}")
            
            except Exception as e:
                if attempt == max_retries - 1:  # Dernière tentative
                    raise Exception(f"Erreur d'envoi: {e}")
                else:
                    print(f"⚠️  Tentative {attempt + 1} échouée: {e}")
                    time.sleep(2 ** attempt)  # Backoff exponentiel
        
        # Si on arrive ici, toutes les tentatives ont échoué
        raise Exception(f"Échec après {max_retries} tentatives")
    
    def send_photo(self, chat_id, photo_url, caption=None, max_retries=3):
        """Envoie une photo via URL avec gestion du rate limiting"""
        
        for attempt in range(max_retries):
            try:
                # Appliquer le rate limiting avant l'envoi
                self._wait_for_rate_limit(chat_id)
                
                url = f"{self.base_url}/sendPhoto"
                
                data = {
                    'chat_id': chat_id,
                    'photo': photo_url
                }
                
                if caption:
                    data['caption'] = caption
                
                response = self.session.post(url, data=data, timeout=30)
                
                # Gestion spécifique de l'erreur 429
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        self._handle_429_error(response)
                        continue
                    else:
                        raise requests.exceptions.HTTPError(f"429 Client Error: Too Many Requests après {max_retries} tentatives")
                
                response.raise_for_status()
                
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    raise Exception(f"API Error: {result.get('description', 'Unknown error')}")
                    
            except requests.exceptions.HTTPError as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Erreur 429 photo - Tentative {attempt + 1}/{max_retries}")
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    raise Exception(f"Erreur HTTP photo: {e}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Erreur d'envoi photo: {e}")
                else:
                    print(f"⚠️  Tentative photo {attempt + 1} échouée: {e}")
                    time.sleep(2 ** attempt)
        
        raise Exception(f"Échec envoi photo après {max_retries} tentatives")
    
    def get_me(self):
        """Obtient les informations du bot"""
        url = f"{self.base_url}/getMe"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                return result['result']
            else:
                raise Exception(f"API Error: {result.get('description', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Erreur de récupération: {e}")

def test_telegram_bot_ssl():
    """Test du bot Telegram avec SSL"""
    print("🧪 Test du bot Telegram SSL...")
    
    # Remplacez par votre vrai token
    token = '1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc'
    chat_id = "-1001315247334"
    
    try:
        bot = TelegramBotSSL(token)
        
        # Test de connexion
        bot_info = bot.get_me()
        print(f"✅ Bot connecté: {bot_info.get('first_name', 'N/A')}")
        
        # Test d'envoi de message
        result = bot.send_message(chat_id, "🧪 Test de connexion SSL réussi!")
        print("✅ Message de test envoyé avec succès")
        
        return bot
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return None

if __name__ == "__main__":
    test_telegram_bot_ssl()