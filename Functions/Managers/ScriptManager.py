import sqlite3
import time
from datetime import datetime
import os
import sys

def adapt_datetime(dt):
    """Convertit un datetime en texte ISO format pour SQLite"""
    return dt.isoformat()

def convert_datetime(text):
    """Convertit un texte ISO format en datetime"""
    return datetime.fromisoformat(text)

class ScriptManager:
    # Instance globale unique
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Récupère l'instance unique de ScriptManager (pattern Singleton)
        
        Returns:
            ScriptManager: L'instance unique de ScriptManager
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, db_path="scripts.db"):
        """Initialise le gestionnaire de scripts"""
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "..", "DataFiles", db_path)
        
        # Enregistrer les adaptateurs datetime personnalisés
        sqlite3.register_adapter(datetime, adapt_datetime)
        sqlite3.register_converter("TIMESTAMP", convert_datetime)
        
        self._init_db()

    def _init_db(self):
        """Initialise la base de données SQLite"""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS running_scripts (
                    script_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP,
                    last_heartbeat TIMESTAMP,
                    status TEXT,
                    pid INTEGER
                )
            ''')

    def start_script(self, script_type: str, script_num: int) -> bool:
        """Démarre un nouveau script s'il n'est pas déjà en cours"""
        script_id = f"{script_type}-{script_num}"
        current_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            # Nettoyer les scripts inactifs
            self._cleanup_inactive_scripts(conn)
            
            # Vérifier si le script est déjà en cours
            if self._is_script_running(conn, script_id):
                return False
                
            # Enregistrer le nouveau script
            conn.execute(
                "INSERT INTO running_scripts VALUES (?, ?, ?, ?, ?)",
                (script_id, current_time, current_time, "RUNNING", os.getpid())
            )
            return True

    def stop_script(self, script_type: str, script_num: int):
        """Arrête un script en cours"""
        script_id = f"{script_type}-{script_num}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM running_scripts WHERE script_id = ?",
                (script_id,)
            )

    def heartbeat(self, script_type: str, script_num: int):
        """Met à jour le timestamp de dernière activité"""
        script_id = f"{script_type}-{script_num}"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE running_scripts SET last_heartbeat = ? WHERE script_id = ?",
                (datetime.now(), script_id)
            )

    def _cleanup_inactive_scripts(self, conn, timeout_minutes=5):
        """Nettoie les scripts inactifs"""
        timeout = datetime.now().timestamp() - (timeout_minutes * 60)
        conn.execute(
            "DELETE FROM running_scripts WHERE strftime('%s', last_heartbeat) < ?",
            (timeout,)
        )

    def _is_script_running(self, conn, script_id: str) -> bool:
        """Vérifie si un script est en cours d'exécution"""
        cursor = conn.execute(
            "SELECT pid FROM running_scripts WHERE script_id = ?",
            (script_id,)
        )
        result = cursor.fetchone()
        if not result:
            return False
            
        # Vérifier si le processus existe toujours
        pid = result[0]
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # Le processus n'existe plus
            conn.execute("DELETE FROM running_scripts WHERE script_id = ?", (script_id,))
            return False

    def get_running_scripts(self) -> list:
        """Retourne la liste des scripts en cours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM running_scripts")
            return cursor.fetchall()

    def are_previous_scripts_running(self, script_type: str, current_script_num: int) -> bool:
        """
        Vérifie si tous les scripts précédents DE LA MÊME FAMILLE sont en cours d'exécution.

        Args:
            script_type: Famille de script (ex: '1530A', '4P6P') — sans ça, "%-{num}"
                matchait n'importe quelle famille ayant ce numéro (ex: '4P6P-1' validait
                le script '1530A-2' par erreur dès que plusieurs familles tournent en
                même temps, cf. migration multi-instance).
            current_script_num: Numéro du script actuel

        Returns:
            bool: True si tous les scripts précédents sont en cours, False sinon
        """
        with sqlite3.connect(self.db_path) as conn:
            # Nettoyer d'abord les scripts inactifs
            self._cleanup_inactive_scripts(conn)

            # Vérifier chaque script précédent de la même famille
            for script_num in range(1, current_script_num):
                cursor = conn.execute(
                    "SELECT pid FROM running_scripts WHERE script_id = ?",
                    (f"{script_type}-{script_num}",)
                )
                result = cursor.fetchone()

                # Si un script précédent n'est pas trouvé ou n'est plus en cours
                if not result or not self._is_process_running(result[0]):
                    return False

            return True

    def _is_process_running(self, pid: int) -> bool:
        """Vérifie si un processus est toujours en cours"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def check_previous_scripts(self, script_type: str, script_num: int) -> bool:
        """
        Vérifie si tous les scripts précédents DE LA MÊME FAMILLE sont en cours d'exécution.

        Args:
            script_type: Famille de script (ex: '1530A', '4P6P') — la table running_scripts
                est partagée par toutes les familles ; sans ce filtre, un '4P6P-1' en cours
                validait à tort le "script précédent" d'un '1530A-2' (et inversement) dès que
                plusieurs familles tournent en parallèle (cf. migration multi-instance bridge).
            script_num: Numéro du script actuel

        Returns:
            bool: True si le script peut démarrer, False s'il doit attendre
        """
        if script_num <= 1:
            return True

        dot_count = 0
        while True:
            # Récupérer tous les scripts en cours, filtrés sur la même famille
            running_scripts = self.get_running_scripts()
            running_nums = set()
            for script_id, start, last_beat, status, pid in running_scripts:
                prefix, _, num = script_id.rpartition("-")
                if prefix == script_type:
                    try:
                        running_nums.add(int(num))
                    except ValueError:
                        continue

            # Vérifier que tous les scripts précédents de la même famille sont en cours
            all_previous_running = all(prev_num in running_nums for prev_num in range(1, script_num))

            if all_previous_running:
                return True

            # Affichage du message d'attente
            message = f"Script {script_num} en attente des scripts précédents"
            sys.stdout.write(f"\r{message}{'.' * dot_count}")
            sys.stdout.flush()

            dot_count = (dot_count + 1) % 4
            time.sleep(1)
            
            # Nettoyer la ligne pour le prochain affichage
            sys.stdout.write('\r' + ' ' * (len(message) + 4))
            sys.stdout.flush()

# Création de l'instance globale unique
script_manager = ScriptManager.get_instance()