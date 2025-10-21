#!/usr/bin/env python3
"""
Utilitaire pour surveiller et gérer le rate limiting Telegram
"""
import time
from datetime import datetime, timedelta

class TelegramRateLimitManager:
    """Gestionnaire centralisé du rate limiting pour Telegram"""
    
    def __init__(self):
        self.message_history = []  # Historique des messages envoyés
        self.chat_last_message = {}  # Dernier message par chat
        
        # Limites Telegram
        self.GLOBAL_LIMIT = 30  # messages par seconde (théorique)
        self.SAFE_GLOBAL_LIMIT = 20  # limite sécurisée
        self.CHAT_LIMIT = 1  # seconde entre messages par chat
        self.MINUTE_LIMIT = 20  # messages par minute (limite conservative)
    
    def can_send_message(self, chat_id):
        """Vérifie si on peut envoyer un message maintenant"""
        current_time = datetime.now()
        
        # Nettoyer l'historique (garder seulement la dernière minute)
        self._clean_history(current_time)
        
        # Vérifier la limite par minute
        if len(self.message_history) >= self.MINUTE_LIMIT:
            return False, "Limite par minute atteinte"
        
        # Vérifier la limite par chat
        if str(chat_id) in self.chat_last_message:
            time_since_last = (current_time - self.chat_last_message[str(chat_id)]).total_seconds()
            if time_since_last < self.CHAT_LIMIT:
                return False, f"Trop rapide pour ce chat (attendez {self.CHAT_LIMIT - time_since_last:.1f}s)"
        
        return True, "OK"
    
    def get_wait_time(self, chat_id):
        """Calcule le temps d'attente nécessaire"""
        can_send, reason = self.can_send_message(chat_id)
        if can_send:
            return 0
        
        current_time = datetime.now()
        
        # Temps d'attente pour le chat
        chat_wait = 0
        if str(chat_id) in self.chat_last_message:
            time_since_last = (current_time - self.chat_last_message[str(chat_id)]).total_seconds()
            if time_since_last < self.CHAT_LIMIT:
                chat_wait = self.CHAT_LIMIT - time_since_last
        
        # Temps d'attente pour la limite globale
        global_wait = 0
        if len(self.message_history) >= self.MINUTE_LIMIT:
            oldest_message = min(self.message_history)
            time_until_oldest_expires = 60 - (current_time - oldest_message).total_seconds()
            if time_until_oldest_expires > 0:
                global_wait = time_until_oldest_expires
        
        return max(chat_wait, global_wait)
    
    def wait_if_needed(self, chat_id):
        """Attend si nécessaire avant d'envoyer"""
        wait_time = self.get_wait_time(chat_id)
        if wait_time > 0:
            print(f"⏳ Rate limiting: attente de {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    def register_message_sent(self, chat_id):
        """Enregistre qu'un message a été envoyé"""
        current_time = datetime.now()
        self.message_history.append(current_time)
        self.chat_last_message[str(chat_id)] = current_time
        
        # Nettoyer l'historique
        self._clean_history(current_time)
    
    def _clean_history(self, current_time):
        """Nettoie l'historique des messages anciens"""
        cutoff_time = current_time - timedelta(minutes=1)
        self.message_history = [msg_time for msg_time in self.message_history if msg_time > cutoff_time]
    
    def get_status(self):
        """Retourne le statut actuel du rate limiting"""
        current_time = datetime.now()
        self._clean_history(current_time)
        
        return {
            'messages_last_minute': len(self.message_history),
            'limit_per_minute': self.MINUTE_LIMIT,
            'percentage_used': (len(self.message_history) / self.MINUTE_LIMIT) * 100,
            'can_send_more': len(self.message_history) < self.MINUTE_LIMIT,
            'chats_tracked': len(self.chat_last_message)
        }
    
    def print_status(self):
        """Affiche le statut du rate limiting"""
        status = self.get_status()
        print(f"📊 Rate Limiting Status:")
        print(f"   Messages dernière minute: {status['messages_last_minute']}/{status['limit_per_minute']}")
        print(f"   Utilisation: {status['percentage_used']:.1f}%")
        print(f"   Peut envoyer: {'✅' if status['can_send_more'] else '❌'}")
        print(f"   Chats suivis: {status['chats_tracked']}")

# Instance globale pour utilisation dans les autres modules
rate_limiter = TelegramRateLimitManager()

def apply_smart_rate_limiting(send_function, chat_id, *args, **kwargs):
    """Wrapper pour appliquer le rate limiting à n'importe quelle fonction d'envoi"""
    rate_limiter.wait_if_needed(chat_id)
    
    try:
        result = send_function(chat_id, *args, **kwargs)
        rate_limiter.register_message_sent(chat_id)
        return result
    except Exception as e:
        if "429" in str(e):
            print("❌ Erreur 429 malgré le rate limiting - Ajustement des limites")
            # Réduire les limites pour être plus conservateur
            rate_limiter.MINUTE_LIMIT = max(10, rate_limiter.MINUTE_LIMIT - 5)
            rate_limiter.CHAT_LIMIT = min(3, rate_limiter.CHAT_LIMIT + 0.5)
            print(f"📉 Nouvelles limites: {rate_limiter.MINUTE_LIMIT}/min, {rate_limiter.CHAT_LIMIT}s/chat")
        raise

if __name__ == "__main__":
    # Test du rate limiter
    manager = TelegramRateLimitManager()
    
    print("🧪 Test du Rate Limiter")
    print("=" * 40)
    
    test_chat = "-1001315247334"
    
    # Simuler plusieurs envois
    for i in range(25):
        can_send, reason = manager.can_send_message(test_chat)
        wait_time = manager.get_wait_time(test_chat)
        
        print(f"Message {i+1}: {'✅' if can_send else '❌'} - {reason}")
        if wait_time > 0:
            print(f"   Attente nécessaire: {wait_time:.1f}s")
        
        if can_send:
            manager.register_message_sent(test_chat)
            time.sleep(0.1)  # Petit délai pour simuler l'envoi
        
        if i % 5 == 4:  # Afficher le statut tous les 5 messages
            manager.print_status()
            print()
        
        if not can_send and wait_time > 2:  # Arrêter si l'attente devient trop longue
            print("⏸️  Test arrêté - Attente trop longue")
            break