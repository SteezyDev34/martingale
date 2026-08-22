"""
Module de gestion de l'API Telegram Bets.
Envoie et récupère les paris détectés via Telegram et GPT.
"""
import base64
import json
import os
from typing import Dict, List, Optional

import requests

import config

# Cache des expéditeurs ignorés (chargé à la demande)
_IGNORED_SENDERS = None


def load_ignored_senders() -> set:
    """
    Charge la liste des expéditeurs à ignorer depuis `conf/ignored_senders.txt`.
    Format attendu: une valeur par ligne, commentaires possibles avec '#'.
    Les usernames peuvent commencer par '@' ou non. Les chat IDs sont traités comme des chaînes.
    Retourne un set de chaînes en minuscules.
    """
    global _IGNORED_SENDERS
    if _IGNORED_SENDERS is not None:
        return _IGNORED_SENDERS

    ignored = set()
    try:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        path = os.path.join(base, 'conf', 'ignored_senders.txt')
        if not os.path.exists(path):
            _IGNORED_SENDERS = ignored
            return ignored

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Normaliser username: enlever @ et forcer minuscule
                normalized = line.lstrip('@').lower()
                ignored.add(normalized)
    except Exception as e:
        config.log(f"Erreur chargement ignored_senders: {e}", 'error')

    _IGNORED_SENDERS = ignored
    return ignored


def is_ignored_sender(sender_username: str = None, chat_id: Optional[int] = None) -> bool:
    """
    Vérifie si `sender_username` ou `chat_id` figure dans la liste d'ignore.
    Retourne True si l'expéditeur doit être ignoré.
    """
    ignored = load_ignored_senders()
    if sender_username:
        if sender_username.lstrip('@').lower() in ignored:
            return True
    if chat_id is not None:
        if str(chat_id) in ignored:
            return True
    return False


class TelegramBetsAPI:
    """
    Classe pour gérer l'API des paris Telegram.
    Permet d'envoyer, récupérer et gérer les paris extraits des messages Telegram.
    """

    def __init__(self):
        """Initialise l'instance de l'API avec l'URL de base."""
        self.base_url = f"{config.api_url}/telegram_bets"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }

    def send_bet_to_api(self, bet_data: Dict, message_original: str = None, sender_username: str = None) -> bool:
        """
        Envoie un pari extrait par GPT vers l'API.
        
        Args:
            bet_data (Dict): Données du pari extraites par GPT
            message_original (str, optional): Message Telegram original
            sender_username (str, optional): Username de l'expéditeur
            
        Returns:
            bool: True si l'envoi est réussi, False sinon
        """
        try:
            print(f"Envoi à l'API: {bet_data}")
            
            url = f"{self.base_url}/insert.php"

            response = requests.post(url, headers=self.headers, data=json.dumps(bet_data), timeout=10)

            if response.status_code == 200:
                try:
                    json_resp = response.json()
                    if json_resp.get('success'):
                        config.log(f"Pari envoyé avec succès à l'API: ID {json_resp.get('id')}", 'info', True)
                        return True
                    else:
                        config.log(f"Erreur API: {json_resp.get('message')}", 'error', True)
                        return False
                except ValueError:
                    config.log("Réponse API invalide (pas de JSON)", 'warning', True)
                    return False
            else:
                config.log(f"Erreur HTTP lors de l'envoi du pari: {response.status_code} - {response.text}", 'error',
                           True)
                return False

        except Exception as e:
            config.log(f"Exception lors de l'envoi du pari à l'API: {str(e)}", 'error', True)
            return False

    def get_unprocessed_bets(self, limit: int = 50) -> List[Dict]:
        """
        Récupère les paris non traités depuis l'API.
        
        Args:
            limit (int): Nombre maximum de paris à récupérer
            
        Returns:
            List[Dict]: Liste des paris non traités
        """
        try:
            url = f"{self.base_url}/get.php"
            params = {
                "processed": "false",
                "limit": limit
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                json_resp = response.json()
                if json_resp.get('success'):
                    return json_resp.get('data', [])
                else:
                    config.log(f"Erreur API lors de la récupération: {json_resp.get('message')}", 'error')
                    return []
            else:
                config.log(f"Erreur HTTP lors de la récupération: {response.status_code}", 'error')
                return []

        except Exception as e:
            config.log(f"Exception lors de la récupération des paris: {str(e)}", 'error')
            return []

    def mark_bet_as_processed(self, bet_id: int, processed: int = 1) -> bool:
        """
        Marque un pari comme traité dans l'API.
        
        Args:
            bet_id (int): ID du pari à marquer comme traité
            processed (int): Statut à définir (1 pour traité, 0 pour non traité)
            
        Returns:
            bool: True si la mise à jour est réussie, False sinon
        """
        try:
            url = f"{self.base_url}/update.php"
            data = {
                "id": bet_id,
                "processed": processed
            }

            response = requests.post(url, headers=self.headers, data=json.dumps(data), timeout=10)

            if response.status_code == 200:
                json_resp = response.json()
                if json_resp.get('success'):
                    config.log(f"Pari {bet_id} marqué comme traité", 'info')
                    return True
                else:
                    config.log(f"Erreur lors du marquage du pari {bet_id}: {json_resp.get('message')}", 'error')
                    return False
            else:
                config.log(f"Erreur HTTP lors du marquage: {response.status_code}", 'error')
                return False

        except Exception as e:
            config.log(f"Exception lors du marquage du pari {bet_id}: {str(e)}", 'error')
            return False

    def get_bets_by_tipster(self, tipster: str, processed: Optional[bool] = None, limit: int = 50) -> List[Dict]:
        """
        Récupère les paris d'un tipster spécifique.
        
        Args:
            tipster (str): Nom du tipster
            processed (bool, optional): Filtrer par statut traité/non traité
            limit (int): Nombre maximum de paris à récupérer
            
        Returns:
            List[Dict]: Liste des paris du tipster
        """
        try:
            url = f"{self.base_url}/get.php"
            params = {
                "tipster": tipster,
                "limit": limit
            }

            if processed is not None:
                params["processed"] = "true" if processed else "false"

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                json_resp = response.json()
                if json_resp.get('success'):
                    return json_resp.get('data', [])
                else:
                    config.log(f"Erreur API: {json_resp.get('message')}", 'error')
                    return []
            else:
                config.log(f"Erreur HTTP: {response.status_code}", 'error')
                return []

        except Exception as e:
            config.log(f"Exception lors de la récupération pour {tipster}: {str(e)}", 'error')
            return []


# Instance globale de l'API
telegram_bets_api = TelegramBetsAPI()


def send_bet_data_to_api(bet_data: Dict, message_original: str = None, sender_username: str = None, image_path: str = None) -> bool:
    """
    Fonction utilitaire pour envoyer des données de pari à l'API.

    Args:
        bet_data (Dict): Données du pari extraites par GPT
        message_original (str, optional): Message Telegram original
        sender_username (str, optional): Username de l'expéditeur
        image_path (str, optional): Chemin vers l'image source — encodée en base64 et ajoutée sous la clé 'image_base64'

    Returns:
        bool: True si l'envoi est réussi, False sinon
    """
    if image_path:
        try:
            with open(image_path, 'rb') as f:
                bet_data['image_base64'] = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            config.log(f"Impossible d'encoder l'image en base64 ({image_path}): {e}", 'warning')
    return telegram_bets_api.send_bet_to_api(bet_data, message_original, sender_username)


def _auxotracker_headers() -> Dict:
    token = getattr(config, 'AUXOBOT_TOKEN', None)
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def send_bet_to_auxotracker(bet_dict: Dict) -> Optional[int]:
    """
    Envoie un pari à POST /api/auxobot/bets sur AuxoTracker.
    Retourne l'ID du pari créé, ou None en cas d'erreur.
    """
    try:
        base = getattr(config, 'AUXOTRACK_API_URL', 'https://api.auxotracker.p-com.studio')
        url = f"{base}/api/auxobot/bets"
        response = requests.post(url, headers=_auxotracker_headers(), json=bet_dict, timeout=15, verify=False)
        if response.ok:
            data = response.json()
            bet_id = data.get('data', {}).get('id') if isinstance(data.get('data'), dict) else data.get('id')
            config.log(f"Pari envoyé AuxoTracker ID={bet_id}", 'info', False)
            return bet_id
        else:
            config.log(f"Erreur AuxoTracker POST: {response.status_code} {response.text[:200]}", 'warning', False)
            return None
    except Exception as e:
        config.log(f"Exception send_bet_to_auxotracker: {e}", 'warning', False)
        return None


def update_bet_result_auxotracker(bet_id: int, result: str) -> bool:
    """
    Met à jour le résultat d'un pari via PATCH /api/auxobot/bets/{id}.
    result doit être 'win' ou 'lost'.
    """
    try:
        base = getattr(config, 'AUXOTRACK_API_URL', 'https://api.auxotracker.p-com.studio')
        url = f"{base}/api/auxobot/bets/{bet_id}"
        response = requests.patch(url, headers=_auxotracker_headers(), json={'result': result}, timeout=15, verify=False)
        if response.ok:
            config.log(f"Résultat AuxoTracker mis à jour: ID={bet_id} result={result}", 'info', False)
            return True
        else:
            config.log(f"Erreur AuxoTracker PATCH: {response.status_code} {response.text[:200]}", 'warning', False)
            return False
    except Exception as e:
        config.log(f"Exception update_bet_result_auxotracker: {e}", 'warning', False)
        return False


def flush_api_result_queue() -> None:
    """
    Envoie en batch tous les résultats en attente dans config._api_result_queue.
    Appelé en fin de match pour ne pas bloquer la boucle critique.
    """
    queue = getattr(config, '_api_result_queue', [])
    if not queue:
        return
    sent = []
    for entry in queue:
        try:
            if update_bet_result_auxotracker(entry['id'], entry['result']):
                sent.append(entry['id'])
        except Exception:
            pass
    config._api_result_queue = [e for e in queue if e['id'] not in sent]


def get_unprocessed_telegram_bets(limit: int = 50) -> List[Dict]:
    """
    Fonction utilitaire pour récupérer les paris non traités.
    
    Args:
        limit (int): Nombre maximum de paris à récupérer
        
    Returns:
        List[Dict]: Liste des paris non traités
    """
    return telegram_bets_api.get_unprocessed_bets(limit)


def mark_telegram_bet_processed(bet_id: int) -> bool:
    """
    Fonction utilitaire pour marquer un pari comme traité.
    
    Args:
        bet_id (int): ID du pari à marquer comme traité
        
    Returns:
        bool: True si la mise à jour est réussie, False sinon
    """
    return telegram_bets_api.mark_bet_as_processed(bet_id)
