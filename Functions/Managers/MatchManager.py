"""
Module de gestion des matchs avec une instance unique globale.
"""
import os
import sqlite3
from typing import List, Optional
from datetime import datetime
import config

class MatchManager:
    """
    Gestionnaire de matchs utilisant le pattern Singleton pour assurer une instance unique par stratégie.
    Utilise SQLite pour le stockage local et une API distante pour la synchronisation.
    """
    _instance = None
    _db_path = None

    def __new__(cls):
        """
        Crée ou retourne l'instance unique du gestionnaire de matchs.

        Returns:
            MatchManager: L'instance unique du gestionnaire
        """
        if cls._instance is None:
            cls._instance = super(MatchManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialise l'instance unique si ce n'est pas déjà fait.
        Configure la connexion à la base de données centrale.
        """
        if not hasattr(self, '_initialized') or not self._initialized:
            base_path = config.projectPath if isinstance(getattr(config, 'projectPath', None), str) and getattr(config, 'projectPath', None) else os.getcwd()
            self.db_path = os.path.join(base_path, 'DataFiles', 'matches.db')
            self.strategy_name: Optional[str] = None
            self._init_db()
            self._initialized = True

    @classmethod
    def get_instance(cls, strategy_name: Optional[str] = None) -> 'MatchManager':
        """
        Méthode de classe pour obtenir l'instance unique du gestionnaire.
        
        Args:
            strategy_name (str, optional): Nom de la stratégie. Si fourni, 
                                         définit la stratégie courante.
        
        Returns:
            MatchManager: L'instance unique du gestionnaire
        """
        instance = cls()
        if strategy_name is not None:
            instance.strategy_name = strategy_name
        return instance

    # (supprimé: version dupliquée de _init_db)

    def add_match(self, match_id: str) -> None:
        """
        Ajoute un nouveau match à la base de données.
        
        Args:
            match_id (str): Identifiant unique du match
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO matches (match_id, strategy, created_at, status) VALUES (?, ?, ?, ?)",
                    (match_id, self.strategy_name, datetime.now(), "active")
                )
            except sqlite3.IntegrityError:
                pass

    def send_matchlist_to_remote(self, match) -> bool:
        """
        Envoie la liste des matchs à l'URL distante via une requête GET.
        
        Args:
            match: Informations du match à envoyer. Accepte:
                  - une liste au format [players_list, league, match_id, date, probability]
                  - ou un dict avec les clés {players, league, match_id, match_date, probability}
            
        Returns:
            bool: True si l'envoi est réussi, False sinon.
        """
        import requests
        import json

        url = f"{config.api_url}/matchlist/insert.php"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
        }
        # Normaliser le format si 'match' est un dict
        if isinstance(match, dict):
            try:
                match = [
                    match.get("players", []),
                    match.get("league", ""),
                    match.get("match_id", ""),
                    match.get("match_date", ""),
                    float(match.get("probability", 0))
                ]
            except Exception as e:
                config.log(f"Erreur de normalisation des données de match: {str(e)}", 'error', True)
                return False
        # Format attendu par l'API : [players_list, league, match_id, date, probability]
        params = {"matches": json.dumps(match)}

        try:
            # Envoyer les données en GET
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    json_resp = response.json()
                    status_val = str(json_resp.get("status", "")).lower()
                    # Considérer les doublons comme succès côté client
                    return status_val in ("success", "exists", "duplicate")
                except ValueError:
                    config.log("Réponse 200 reçue mais le corps n'est pas du JSON valide", 'warning', True)
                    return False
            else:
                config.log(
                    f"Échec de l'envoi de la matchlist – code HTTP {response.status_code} | "
                    f"URL : {response.url} | ",
                    'error',
                    True
                )
                return False
        except Exception as e:
            config.log(f"Exception lors de l'envoi de la matchlist : {str(e)}", 'error', True)
            return False

    def remove_match(self, match_id: str) -> None:
        """
        Supprime un match de la base de données.
        
        Args:
            match_id (str): Identifiant du match à supprimer
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM matches WHERE match_id = ? AND strategy = ?",
                (match_id, self.strategy_name)
            )

    def get_all_matches(self) -> List[tuple]:
        """
        Récupère tous les matchs pour la stratégie courante.
        
        Returns:
            List[tuple]: Liste de tuples contenant (match_id, created_at, status)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT match_id, created_at, status FROM matches WHERE strategy = ?",
                (self.strategy_name,)
            )
            return cursor.fetchall()

    def match_exists(self, match_id: str) -> bool:
        """
        Vérifie si un match existe pour la stratégie courante.
        
        Args:
            match_id (str): Identifiant du match à vérifier
            
        Returns:
            bool: True si le match existe, False sinon
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM matches WHERE match_id = ? AND strategy = ?",
                (match_id, self.strategy_name)
            )
            return cursor.fetchone() is not None

    def update_match(self, action: str, match_id: str) -> None:
        """
        Met à jour le statut du match selon l'action.
        
        Args:
            action (str): Action à effectuer ("add" pour ajouter ou "del" pour supprimer)
            match_id (str): Identifiant du match
        """
        if action == "add":
            self.add_match(match_id)
        elif action == "del":
            self.remove_match(match_id)
        else:
            raise ValueError("Action invalide. Utilisez 'add' ou 'del'")

    def get_match_status(self, match_id: str) -> Optional[str]:
        """
        Récupère le statut actuel d'un match.
        
        Args:
            match_id (str): Identifiant du match à vérifier
            
        Returns:
            Optional[str]: Statut du match s'il est trouvé, None sinon
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT status FROM matches WHERE match_id = ? AND strategy = ?",
                (match_id, self.strategy_name)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _init_db(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Table pour les matchs en cours
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT,
                    strategy TEXT,
                    created_at TIMESTAMP,
                    status TEXT,
                    PRIMARY KEY (match_id, strategy)
                )
            ''')
            
            # Table pour les matchs à faire
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches_todo (
                    match_id TEXT PRIMARY KEY,
                    players TEXT,
                    league TEXT,
                    match_date TIMESTAMP,
                    probability FLOAT,
                    created_at TIMESTAMP
                )
            ''')

    def get_remote_matches_todo(self) -> List[dict]:
        """
        Récupère la liste des matchs à faire depuis le serveur distant.
        
        Returns:
            List[dict]: Liste des matchs à faire au format [{"match_id": str, "players": str, ...}]
        """
        import requests
        import json
        import config

        url = f"{config.api_url}/matchlist/get.php"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    config.log("Réponse 200 reçue mais le corps n'est pas du JSON valide", 'warning', True)
                    return []
            else:
                config.log(f"Erreur lors de la récupération des matchs : {response.status_code}", 'error', True)
                return []
        except Exception as e:
            config.log(f"Exception lors de la récupération des matchs : {str(e)}", 'error', True)
            return []

    def is_match_todo(self, match_id: str) -> bool:
        """
        Vérifie si un match est dans la liste des matchs à faire (locale ou distante).
        
        Args:
            match_id (str): Identifiant du match à vérifier
            
        Returns:
            bool: True si le match est dans la liste des matchs à faire, False sinon
        """
        # Vérification locale
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM matches_todo WHERE match_id = ?",
                (match_id,)
            )
            if cursor.fetchone() is not None:
                return True

        # Vérification distante
        remote_matches = self.get_remote_matches_todo()
        return any(match.get('match_id') == match_id for match in remote_matches)

    def add_match_todo(self, match_info: str) -> bool:
        """
        Ajoute un match à la liste des matchs à faire (locale et distante).
        
        Args:
            match_info (str): Information du match au format:
                "[player1, player2]|league|match-id|date|probability"
            
        Returns:
            bool: True si ajouté avec succès (local ou distant), False sinon
        """
        try:
            players, league, match_id, date_str, prob = match_info.split('|')
            # Ajout local
            added_locally = False
            with sqlite3.connect(self.db_path) as conn:
                try:
                    conn.execute(
                        """
                        INSERT INTO matches_todo 
                        (match_id, players, league, match_date, probability, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (match_id, players, league, date_str, float(prob), datetime.now())
                    )
                    added_locally = True
                except sqlite3.IntegrityError:
                    pass

            # Création du dictionnaire pour l'envoi distant
            # Construire la payload au format attendu par l'API PHP
            # Normalisation robuste des joueurs pour garantir un tableau
            try:
                import json
                if isinstance(players, list):
                    players_list = players
                elif isinstance(players, str):
                    ps = players.strip()
                    # Si la chaîne ressemble à un tableau JSON, tenter de la parser
                    if ps.startswith('[') and ps.endswith(']'):
                        try:
                            parsed = json.loads(ps)
                            players_list = parsed if isinstance(parsed, list) else [str(parsed)]
                        except Exception:
                            # Repli sur un découpage simple
                            if ' - ' in players:
                                players_list = [p.strip() for p in players.split(' - ') if p.strip()]
                            elif ',' in players:
                                players_list = [p.strip() for p in players.split(',') if p.strip()]
                            else:
                                players_list = [players.strip()] if players.strip() else []
                    else:
                        # Découpage par séparateur connu ou fallback
                        if ' - ' in players:
                            players_list = [p.strip() for p in players.split(' - ') if p.strip()]
                        elif ',' in players:
                            players_list = [p.strip() for p in players.split(',') if p.strip()]
                        else:
                            players_list = [players.strip()] if players.strip() else []
                else:
                    players_list = [str(players)]
            except Exception:
                players_list = players if isinstance(players, list) else [str(players)]
            match_payload = [
                players_list,
                league,
                match_id,
                date_str,
                float(prob)
            ]

            # Envoi au serveur distant
            print('Envoi au serveur distant')
            added_remotely = self.send_matchlist_to_remote(match_payload)
            
            # Si l'ajout a réussi soit localement soit à distance, on considère que c'est un succès
            return added_locally or added_remotely

        except Exception as e:
            config.log(f"Erreur lors de l'ajout du match : {str(e)}", 'error')
            return False

    def remove_match_todo(self, match_id: str) -> bool:
        """
        Supprime un match de la liste des matchs à faire (locale et distante).
        
        Args:
            match_id (str): Identifiant du match à supprimer
            
        Returns:
            bool: True si supprimé avec succès (local ou distant), False si non trouvé
        """
        # Suppression locale
        removed_locally = False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM matches_todo WHERE match_id = ?",
                (match_id,)
            )
            removed_locally = cursor.rowcount > 0

        # Suppression distante
        try:
            import requests

            url = f"{config.api_url}/matchlist/delete.php"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/122.0.0.0 Safari/537.36"
            }
            data = {
                "match_id": match_id
            }

            response = requests.get(url, params=data, headers=headers, timeout=10)
            removed_remotely = response.status_code == 200

            # Si la suppression a réussi soit localement soit à distance, on considère que c'est un succès
            return removed_locally or removed_remotely

        except Exception as e:
            config.log(f"Erreur lors de la suppression distante du match : {str(e)}", 'error')
            return removed_locally

    def get_matches_todo(self, min_probability: float = 0.0) -> list:
        """
        Récupère la liste des matchs à faire, triés par probabilité.
        
        Args:
            min_probability (float): Probabilité minimum à considérer
            
        Returns:
            list: Liste des matchs à faire [(match_id, players, league, date, probability)]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT match_id, players, league, match_date, probability 
                FROM matches_todo 
                WHERE probability >= ?
                ORDER BY probability DESC
                """,
                (min_probability,)
            )
            return cursor.fetchall()

    def cleanup_old_matches(self, days: int = 7) -> int:
        """
        Supprime les matchs plus vieux que le nombre de jours spécifié.
        
        Args:
            days (int): Nombre de jours de conservation des matchs
            
        Returns:
            int: Nombre de matchs supprimés
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM matches 
                WHERE strategy = ? 
                AND datetime(created_at) < datetime('now', ?)
                """,
                (self.strategy_name, f'-{days} days')
            )
            deleted_count = cursor.rowcount
            
            # Nettoyer aussi les matchs_todo
            cursor = conn.execute(
                """
                DELETE FROM matches_todo 
                WHERE datetime(match_date) < datetime('now', ?)
                """,
                (f'-{days} days',)
            )
            deleted_count += cursor.rowcount
            
            return deleted_count

    def clear_all_matches(self, strategy_only: bool = True) -> int:
        """
        Supprime tous les matchs de la base de données.
        
        Args:
            strategy_only (bool): Si True, supprime uniquement les matchs de la stratégie courante.
                                Si False, supprime tous les matchs toutes stratégies confondues.
            
        Returns:
            int: Nombre de matchs supprimés
            
        Example:
            >>> manager = MatchManager.get_instance("40A")
            >>> # Supprimer uniquement les matchs de la stratégie 40A
            >>> manager.clear_all_matches()
            >>> # Supprimer tous les matchs de toutes les stratégies
            >>> manager.clear_all_matches(strategy_only=False)
        
        Raises:
            ValueError: Si strategy_only est True mais qu'aucune stratégie n'est définie
        """
        if strategy_only and not self.strategy_name:
            raise ValueError("Une stratégie doit être définie pour supprimer les matchs par stratégie")
            
        with sqlite3.connect(self.db_path) as conn:
            if strategy_only:
                cursor = conn.execute(
                    "DELETE FROM matches WHERE strategy = ?",
                    (self.strategy_name,)
                )
            else:
                cursor = conn.execute("DELETE FROM matches")
                cursor.execute("DELETE FROM matches_todo")
            
            return cursor.rowcount

# Instance globale et helper pour récupérer l'instance configurée
def get_match_manager(strategy_name: Optional[str] = None) -> MatchManager:
    """
    Retourne l'instance unique de MatchManager et optionnellement
    définit la stratégie courante.

    Args:
        strategy_name: Nom de la stratégie à définir

    Returns:
        MatchManager: L'instance unique du gestionnaire de matchs
    """
    instance = MatchManager.get_instance(strategy_name)
    return instance

# Expose une instance globale par défaut pour compatibilité
try:
    default_strategy = getattr(config, 'scriptType', None) or None
except Exception:
    default_strategy = None
match_manager = MatchManager.get_instance(default_strategy)