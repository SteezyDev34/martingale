"""
Module de gestion des matchs avec une instance unique globale.
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

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
            base_path = config.projectPath if isinstance(getattr(config, 'projectPath', None), str) and getattr(config,
                                                                                                                'projectPath',
                                                                                                                None) else os.getcwd()
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

    def add_match(self, match_id: str, url: str = None) -> None:
        """
        Ajoute un nouveau match à la base de données.

        Copie au passage les scriptTypes calculés au classement (matches_todo) et l'URL
        1xBet du match : le match est retiré de matches_todo juste après l'engagement,
        et ces infos sont nécessaires pour le reprendre si le bot redémarre en plein
        match (cf. get_match_script_config, get_match_url).

        Args:
            match_id (str): Identifiant unique du match
            url (str): URL 1xBet de la page du match
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO matches (match_id, strategy, created_at, status, script_types, total_gain_wanted, url) "
                    "VALUES (?, ?, ?, ?, "
                    "(SELECT script_types FROM matches_todo WHERE match_id = ?), "
                    "(SELECT total_gain_wanted FROM matches_todo WHERE match_id = ?), ?)",
                    (match_id, self.strategy_name, datetime.now(), "active", match_id, match_id, url)
                )
            except sqlite3.IntegrityError:
                pass

    def get_match_url(self, match_id: str) -> Optional[str]:
        """URL 1xBet mémorisée à l'engagement du match (None si inconnue)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT url FROM matches WHERE match_id = ? AND url IS NOT NULL AND url != '' "
                    "ORDER BY created_at DESC LIMIT 1",
                    (match_id,)
                ).fetchone()
                return row[0] if row else None
        except Exception as e:
            config.log(f"Erreur DB get_match_url: {e}", 'warning', True)
            return None

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
                raw_players = match.get("players", [])
                if isinstance(raw_players, str):
                    ps = raw_players.strip()
                    if ps.startswith('[') and ps.endswith(']'):
                        try:
                            parsed = json.loads(ps)
                            players_list = parsed if isinstance(parsed, list) else [str(parsed)]
                        except Exception:
                            if ' - ' in raw_players:
                                players_list = [p.strip().strip("[]'\"") for p in raw_players.split(' - ') if p.strip()]
                            elif ',' in raw_players:
                                players_list = [p.strip().strip("[]'\"") for p in raw_players.split(',') if p.strip()]
                            else:
                                cleaned = raw_players.strip().strip("[]'\"")
                                players_list = [cleaned] if cleaned else []
                    else:
                        if ' - ' in raw_players:
                            players_list = [p.strip().strip("[]'\"") for p in raw_players.split(' - ') if p.strip()]
                        elif ',' in raw_players:
                            players_list = [p.strip().strip("[]'\"") for p in raw_players.split(',') if p.strip()]
                        else:
                            cleaned = raw_players.strip().strip("[]'\"")
                            players_list = [cleaned] if cleaned else []
                elif isinstance(raw_players, list):
                    players_list = [str(p).strip().strip("[]'\"") for p in raw_players]
                else:
                    players_list = [str(raw_players).strip().strip("[]'\"")]

                match = [
                    players_list,
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
            print(response)
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

            # Migration : scriptTypes/objectif/URL conservés à l'engagement (cf. add_match)
            match_cols = [row[1] for row in conn.execute("PRAGMA table_info(matches)")]
            if 'script_types' not in match_cols:
                conn.execute("ALTER TABLE matches ADD COLUMN script_types TEXT")
            if 'total_gain_wanted' not in match_cols:
                conn.execute("ALTER TABLE matches ADD COLUMN total_gain_wanted FLOAT")
            if 'url' not in match_cols:
                conn.execute("ALTER TABLE matches ADD COLUMN url TEXT")

            # Table pour les matchs à faire
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches_todo (
                    match_id TEXT PRIMARY KEY,
                    players TEXT,
                    league TEXT,
                    match_date TIMESTAMP,
                    probability FLOAT,
                    link TEXT,
                    created_at TIMESTAMP
                )
            ''')
            # Migration : ajouter les colonnes manquantes (rétrocompatibilité)
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(matches_todo)")]
            if 'link' not in existing_cols:
                conn.execute("ALTER TABLE matches_todo ADD COLUMN link TEXT")
            if 'script_types' not in existing_cols:
                conn.execute("ALTER TABLE matches_todo ADD COLUMN script_types TEXT")
            if 'total_gain_wanted' not in existing_cols:
                conn.execute("ALTER TABLE matches_todo ADD COLUMN total_gain_wanted FLOAT")

            # Historique des gains par scriptType une fois un match terminé (plus en
            # cours de pari) — permet un récap après coup, ce que config.global_match_win
            # (en mémoire, remis à 0 à la fin de chaque match) ne permettait pas.
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches_history (
                    match_id TEXT,
                    script_type TEXT,
                    gain FLOAT,
                    finished_at TIMESTAMP,
                    PRIMARY KEY (match_id, script_type, finished_at)
                )
            ''')

    def record_match_history(self, match_id: str, gains_by_scripttype: dict) -> None:
        """
        Enregistre le gain final de chaque scriptType pour ce match, juste avant que
        Functions_431a.py ne remette config.global_match_win à zéro et supprime le
        match — sinon cette donnée est perdue définitivement.
        """
        if not gains_by_scripttype:
            return
        try:
            now = datetime.now()
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO matches_history (match_id, script_type, gain, finished_at) "
                    "VALUES (?, ?, ?, ?)",
                    [(match_id, st, float(gain), now) for st, gain in gains_by_scripttype.items()]
                )
        except Exception as e:
            config.log(f"Erreur lors de l'enregistrement de l'historique du match: {e}", 'warning', True)

    def get_remote_matches_todo(self) -> List[dict]:
        """
        Récupère la liste des matchs à faire depuis le serveur distant.
        
        Returns:
            List[dict]: Liste des matchs à faire au format [{"match_id": str, "players": str, ...}]
        """
        import requests
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

                    data = response.json()
                    return data.get('data', [])
                except ValueError:
                    config.log("Réponse 200 reçue mais le corps n'est pas du JSON valide", 'warning', True)
                    return []
            else:
                config.log(f"Erreur lors de la récupération des matchs : {response.status_code}", 'error', True)
                return []
        except Exception as e:
            config.log(f"Exception lors de la récupération des matchs : {str(e)}", 'error', True)
            return []

    def purge_remote_past_matches(self) -> int:
        """
        Supprime du serveur distant les matchs dont la date est passée (avant aujourd'hui).
        Seule la suppression d'un match engagé (remove_match_todo) touchait jusqu'ici le
        distant : les matchs classés mais jamais joués y restaient indéfiniment.
        Retourne le nombre de match_id distincts supprimés.
        """
        import requests

        today = datetime.now().strftime("%Y-%m-%d")
        past_ids = {
            m.get('match_id') for m in self.get_remote_matches_todo()
            if m.get('match_id') and (m.get('match_date') or '')[:10] < today
        }
        url = f"{config.api_url}/matchlist/delete.php"
        headers = {"User-Agent": "Mozilla/5.0"}
        removed = 0
        for match_id in past_ids:
            try:
                # delete.php renvoie toujours {"status":"error"} (warning PHP sur
                # affected_rows) alors que la suppression a bien lieu : seul le code
                # HTTP est fiable.
                resp = requests.get(url, params={"match_id": match_id}, headers=headers, timeout=10)
                if resp.status_code == 200:
                    removed += 1
            except Exception as e:
                config.log(f"Erreur suppression distante de {match_id} : {e}", 'warning', False)
        return removed

    def get_match_link(self, match_id: str) -> Optional[str]:
        """
        Récupère le lien Sofascore d'un match à partir de son `match_id` (local uniquement).

        Args:
            match_id (str): Identifiant du match à rechercher

        Returns:
            Optional[str]: URL Sofascore trouvée, ou `None` si non trouvée
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("SELECT link FROM matches_todo WHERE match_id = ?", (match_id,))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
        except Exception as e:
            config.log(f"Erreur DB lors de la recherche du link local: {e}", 'warning', True)

        return None

    def get_match_script_config(self, match_id: str) -> dict:
        """
        Retourne {'script_types': list, 'total_gain_wanted': float} pour un match.
        Retourne un dict vide si non trouvé.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "SELECT script_types, total_gain_wanted FROM matches_todo WHERE match_id = ?",
                    (match_id,)
                )
                row = cur.fetchone()
                if not row:
                    # Match déjà engagé (retiré de matches_todo) : scriptTypes copiés
                    # dans matches par add_match.
                    row = conn.execute(
                        "SELECT script_types, total_gain_wanted FROM matches "
                        "WHERE match_id = ? AND script_types IS NOT NULL "
                        "ORDER BY created_at DESC LIMIT 1",
                        (match_id,)
                    ).fetchone()
                if row:
                    import json as _json
                    script_types = _json.loads(row[0]) if row[0] else []
                    total_gain_wanted = float(row[1]) if row[1] else 0.0
                    return {'script_types': script_types, 'total_gain_wanted': total_gain_wanted}
        except Exception as e:
            config.log(f"Erreur DB get_match_script_config: {e}", 'warning', True)
        return {}

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
                "[player1, player2]|league|match-id|date|probability|link"
            
        Returns:
            bool: True si ajouté avec succès (local ou distant), False sinon
        """
        try:
            parts = match_info.split('|')
            players, league, match_id, date_str, prob = parts[0], parts[1], parts[2], parts[3], parts[4]
            link = parts[5] if len(parts) > 5 else ''
            script_types_json = parts[6] if len(parts) > 6 else '[]'
            total_gain_wanted = float(parts[7]) if len(parts) > 7 else 0.0
            # Ajout local
            added_locally = False
            with sqlite3.connect(self.db_path) as conn:
                try:
                    conn.execute(
                        """
                        INSERT INTO matches_todo
                        (match_id, players, league, match_date, probability, link, script_types, total_gain_wanted, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (match_id, players, league, date_str, float(prob), link, script_types_json, total_gain_wanted, datetime.now())
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
                                players_list = [p.strip().strip("[]'\"") for p in players.split(' - ') if p.strip()]
                            elif ',' in players:
                                players_list = [p.strip().strip("[]'\"") for p in players.split(',') if p.strip()]
                            else:
                                cleaned = players.strip().strip("[]'\"")
                                players_list = [cleaned] if cleaned else []
                    else:
                        # Découpage par séparateur connu ou fallback
                        if ' - ' in players:
                            players_list = [p.strip().strip("[]'\"") for p in players.split(' - ') if p.strip()]
                        elif ',' in players:
                            players_list = [p.strip().strip("[]'\"") for p in players.split(',') if p.strip()]
                        else:
                            cleaned = players.strip().strip("[]'\"")
                            players_list = [cleaned] if cleaned else []
                else:
                    players_list = [str(players).strip().strip("[]'\"")]
            except Exception:
                players_list = players if isinstance(players, list) else [str(players).strip().strip("[]'\"")]
            match_payload = [
                players_list,
                league,
                match_id,
                date_str,
                float(prob)
            ]

            # Envoi au serveur distant
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
