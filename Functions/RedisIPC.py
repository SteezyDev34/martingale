import json
import os
from typing import Any, Optional, Iterable, Tuple
import sqlite3

try:
    import redis
except Exception:
    redis = None

# ---------------------------------------------------------------------------
# Schéma de clé Redis : ETAT_<SCRIPT_TYPE> (Hash)
#
# Écriture : set_data('mise', 0.5, '15A')    → HSET ETAT_15A mise 0.5
# Lecture  : get_data('mise', '15A')         → HGET ETAT_15A mise → 0.5
#
# Les valeurs dict/list sont sérialisées en JSON automatiquement.
# ---------------------------------------------------------------------------


_client = None


# ---------------------------------------------------------------------------
# API publique simplifiée
# ---------------------------------------------------------------------------

def set_data(champ: str, valeur: Any, script_type: str) -> bool:
    """
    Écrit un champ dans le Hash Redis ETAT_<SCRIPT_TYPE>.

    Les valeurs dict/list sont sérialisées en JSON automatiquement.
    Pour supprimer un champ, passer valeur=None.

    Args:
        champ (str): Nom du champ (ex: 'mise', 'perte')
        valeur (Any): Valeur à stocker
        script_type (str): Type de script (ex: '15A', '30A')

    Returns:
        bool: True si succès, False si Redis indisponible
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        key = f"ETAT_{script_type.upper()}"
        if valeur is None:
            client.hdel(key, champ)
            return True
        if isinstance(valeur, (dict, list)):
            raw = json.dumps(valeur)
        else:
            raw = str(valeur)
        client.hset(key, champ, raw)
        return True
    except Exception:
        return False


def get_data(champ: str, script_type: str, default: Any = None) -> Any:
    """
    Lit un champ depuis le Hash Redis ETAT_<SCRIPT_TYPE>.

    Cast automatique :
    - JSON si la valeur commence par '{' ou '['
    - int si la valeur est un entier pur
    - float si la valeur est un nombre décimal
    - str sinon

    Args:
        champ (str): Nom du champ (ex: 'mise', 'perte')
        script_type (str): Type de script (ex: '15A', '30A')
        default (Any): Valeur retournée si le champ est absent ou Redis indisponible

    Returns:
        Any: Valeur castée, ou default
    """
    client = get_redis_client()
    if client is None:
        return default
    try:
        key = f"ETAT_{script_type.upper()}"
        raw = client.hget(key, champ)
        if raw is None:
            return default
        # Désérialisation JSON
        if raw.startswith(('{', '[')):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        # Cast numérique
        try:
            if '.' in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw
    except Exception:
        return default


def get_redis_client():
    """Retourne un client Redis singleton. Ne crée pas le client si le package n'est pas installé.

    Configuration via variables d'environnement : REDIS_UNIX_SOCKET (optionnel), REDIS_HOST, REDIS_PORT, REDIS_DB
    """
    # Redis désactivé — forcer utilisation du fallback SQLite uniquement.
    # Cette fonction retourne toujours None pour empêcher tout accès à Redis.
    return None


def bkp_set_loss(script_type: str, loss_value: float, publish: bool = True) -> bool:
    """Stocke la perte pour `script_type` dans Redis (clé PERTE_<SCRIPT>) et optionnellement publie une notification.

    Retourne True si succès.
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        try:
            import config
        except Exception:
            config = None

        key = f"PERTE_{str(script_type).upper()}"
        # Logging diagnostic
        config.log(f"[RedisIPC] set_loss key={key} value={loss_value}", 'debug')
        # utiliser pipeline pour rapidité si on publie
        if publish:
            pipe = client.pipeline()
            pipe.set(key, float(loss_value))
            pipe.publish('perte_updates', f"{key}:{loss_value}")
            pipe.execute()
        else:
            client.set(key, float(loss_value))
        # Log success
        config.log(f"[RedisIPC] set_loss success key={key}", 'debug')
        return True
    except Exception:
        try:
            import traceback
            err = traceback.format_exc()
            config.log(f"[RedisIPC] set_loss error for key={key}: {err}", 'error')
        except Exception:
            pass
        return False


def bkp_get_loss(script_type: str, default: float = 0.0) -> float:
    """Lit la perte depuis Redis. Retourne `default` en cas d'erreur ou d'absence."""
    client = get_redis_client()
    if client is None:
        return float(default)
    try:
        try:
            import config
        except Exception:
            config = None

        key = f"PERTE_{str(script_type).upper()}"
        val = client.get(key)
        # Logging diagnostic
        config.log(f"[RedisIPC] get_loss key={key} raw={val}", 'debug')
        if val is None:
            return float(default)
        return float(val)
    except Exception:
        try:
            import traceback
            err = traceback.format_exc()
            config.log(f"[RedisIPC] get_loss error for key={key}: {err}", 'error')
        except Exception:
            pass
        return float(default)


def publish_update(channel: str, message: str) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.publish(channel, message)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# État complet d'un script — lecture / écriture / chargement dans config
# ---------------------------------------------------------------------------

def sauvegarder_etat(script_type: str) -> bool:
    """
    Sauvegarde l'état courant du script depuis le module config vers Redis.
    Remplace config.save_variables() + config.switchScript() pour un script donné.

    Clé Redis : Hash ETAT_<SCRIPT_TYPE>

    Args:
        script_type (str): Type de script (ex: '15A', '30A', '300')

    Returns:
        bool: True si la sauvegarde a réussi
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        import config
        key = f"ETAT_{script_type.upper()}"
        validated_bet_json = json.dumps(
            config.validated_bet if isinstance(config.validated_bet, dict) else {}
        )
        champs = {
            "mise":           str(config.mise),
            "perte":          str(config.perte),
            "wantwin":        str(config.wantwin),
            "increment":      str(config.increment),
            "gain":           str(config.gain),
            "netprofit":      str(config.netprofit),
            "cote":           str(config.cote),
            "rattrape_perte": str(config.rattrape_perte),
            "looking_game":   str(config.looking_game if config.looking_game else 0),
            "placed_game":    str(config.placed_game if config.placed_game else 0),
            "saved_score":    str(config.saved_score if config.saved_score else ""),
            "win_type":       str(config.win_type),
            "result":         str(config.result if config.result else ""),
            "error":          "true" if config.error else "false",
            "validated_bet":  validated_bet_json,
            # Rétrocompatibilité : PERTE_<SCRIPT> mis à jour en même temps
        }
        pipe = client.pipeline()
        pipe.hset(key, mapping=champs)
        # Mise à jour de la clé PERTE_<SCRIPT> pour rétrocompatibilité
        pipe.set(f"PERTE_{script_type.upper()}", str(config.perte))
        pipe.execute()
        return True
    except Exception:
        return False


def charger_etat(script_type: str) -> bool:
    """
    Charge l'état d'un script depuis Redis vers le module config.
    Remplace config.switchScript() + config.init_variable() pour un script donné.

    Si la clé Redis n'existe pas (premier lancement), ne touche pas config.

    Args:
        script_type (str): Type de script (ex: '15A', '30A', '300')

    Returns:
        bool: True si un état a été trouvé et chargé, False si absent de Redis
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        import config
        key = f"ETAT_{script_type.upper()}"
        champs = client.hgetall(key)
        if not champs:
            return False

        # Application des valeurs dans config avec cast automatique
        _appliquer_champ(champs, "mise",           float, lambda v: setattr(config, "mise", v))
        _appliquer_champ(champs, "perte",          float, lambda v: setattr(config, "perte", v))
        _appliquer_champ(champs, "wantwin",        float, lambda v: setattr(config, "wantwin", v))
        _appliquer_champ(champs, "increment",      float, lambda v: setattr(config, "increment", v))
        _appliquer_champ(champs, "gain",           float, lambda v: setattr(config, "gain", v))
        _appliquer_champ(champs, "netprofit",      float, lambda v: setattr(config, "netprofit", v))
        _appliquer_champ(champs, "cote",           float, lambda v: setattr(config, "cote", v))
        _appliquer_champ(champs, "rattrape_perte", int,   lambda v: setattr(config, "rattrape_perte", v))
        _appliquer_champ(champs, "looking_game",   int,   lambda v: setattr(config, "looking_game", v))
        _appliquer_champ(champs, "placed_game",    int,   lambda v: setattr(config, "placed_game", v))
        _appliquer_champ(champs, "saved_score",    str,   lambda v: setattr(config, "saved_score", v or False))
        _appliquer_champ(champs, "win_type",       str,   lambda v: setattr(config, "win_type", v))
        _appliquer_champ(champs, "result",         str,   lambda v: setattr(config, "result", v or False))

        if "error" in champs:
            config.error = champs["error"].lower() == "true"

        if "validated_bet" in champs:
            try:
                config.validated_bet = json.loads(champs["validated_bet"])
            except (json.JSONDecodeError, TypeError):
                config.validated_bet = {}

        # Mise à jour du scriptType actif
        config.scriptType = script_type
        return True
    except Exception:
        return False


def lire_etat(script_type: str) -> dict[str, Any]:
    """
    Lit l'état d'un script depuis Redis sans l'appliquer dans config.
    Utile pour inspecter l'état d'un script sans changer le contexte global.

    Args:
        script_type (str): Type de script

    Returns:
        dict: État du script avec les valeurs castées, ou {} si absent
    """
    client = get_redis_client()
    if client is None:
        return {}
    try:
        key = f"ETAT_{script_type.upper()}"
        champs = client.hgetall(key)
        if not champs:
            return {}

        # Cast automatique via get_data() pour chaque champ présent
        etat: dict[str, Any] = {}
        for champ in champs:
            etat[champ] = get_data(champ, script_type, default=champs[champ])
        return etat
    except Exception:
        return {}


def reinitialiser_etat(script_type: str) -> bool:
    """
    Supprime l'état d'un script dans Redis (équivalent d'un reset complet).

    Args:
        script_type (str): Type de script

    Returns:
        bool: True si suppression réussie
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        pipe = client.pipeline()
        pipe.delete(f"ETAT_{script_type.upper()}")
        pipe.delete(f"PERTE_{script_type.upper()}")
        pipe.execute()
        return True
    except Exception:
        return False


def _appliquer_champ(
    champs: dict,
    nom: str,
    cast: type,
    setter,
) -> None:
    """
    Applique un champ Redis dans config via le setter fourni, avec gestion d'erreur silencieuse.

    Args:
        champs (dict): Résultat de hgetall Redis
        nom (str): Nom du champ
        cast (type): Type de cast (float, int, str)
        setter: Fonction lambda qui écrit dans config
    """
    if nom in champs:
        try:
            setter(cast(champs[nom]))
        except (ValueError, TypeError):
            pass  # Valeur invalide — on garde la valeur actuelle de config





# ---------------------------------------------------------------------------
# Fallback SQLite implementations (utilitaire temporaire quand Redis est HS)
# Ces fonctions écrivent/lecturent dans une petite BDD SQLite locale pour
# ne pas perturber le reste du code pendant le dépannage de Redis.
# ---------------------------------------------------------------------------


def _get_sqlite_conn() -> sqlite3.Connection:
    """
    Retourne une connexion SQLite vers le fichier de fallback.

    Le fichier se trouve au niveau du projet (un dossier au-dessus de ce module)
    pour être facilement accessible par les autres scripts.
    """
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'redis_fallback.sqlite'))
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA foreign_keys = ON")
    # Créer la table si nécessaire
    conn.execute(
        "CREATE TABLE IF NOT EXISTS perte (script_type TEXT PRIMARY KEY, loss REAL NOT NULL DEFAULT 0.0)"
    )
    # Table pour état de running (1 = running, 0 = stopped) avec matchname
    conn.execute(
        "CREATE TABLE IF NOT EXISTS running (script_type TEXT PRIMARY KEY, is_running INTEGER NOT NULL DEFAULT 0, matchname TEXT DEFAULT '')"
    )
    # S'assurer que la colonne matchname existe (ALTER si base existante plus ancienne)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(running)").fetchall()]
        if 'matchname' not in cols:
            conn.execute("ALTER TABLE running ADD COLUMN matchname TEXT DEFAULT ''")
    except Exception:
        pass
    return conn


def set_loss(script_type: str, loss_value: float, publish: bool = True) -> bool:
    """
    Sauvegarde la perte pour `script_type` dans la BDD SQLite de secours.

    Si Redis est disponible, la valeur est également propagée via `bkp_set_loss`.
    """
    try:
        try:
            import config
        except Exception:
            config = None

        st = str(script_type).upper()
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("REPLACE INTO perte (script_type, loss) VALUES (?, ?)", (st, float(loss_value)))
        conn.commit()
        conn.close()

        if config:
            config.log(f"[RedisIPC] sqlite set_loss {st}={loss_value}", 'debug')
        return True
    except Exception:
        try:
            import traceback
            err = traceback.format_exc()
            if 'config' in locals() and config:
                config.log(f"[RedisIPC] sqlite set_loss error for {script_type}: {err}", 'error')
        except Exception:
            pass
        return False


def get_loss(script_type: str, default: float = 0.0) -> float:
    """
    Lit la perte pour `script_type` depuis Redis si disponible, sinon depuis SQLite.
    """
    import config
    try:
        st = str(script_type).upper()
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT loss FROM perte WHERE script_type = ?", (st,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return float(default)
        config.log(f"[RedisIPC] sqlite get_loss {st}={row[0]}", 'debug')
        return float(row[0])
    except Exception:
        return float(default)
    
def any_loss_exists(script_type: str) -> bool:
    """
    Vérifie si une perte existe sauf pour `script_type` dans SQLite.

    Retourne True si une perte est trouvée (même 0.0), False si aucune entrée.
    """
    try:
        st = str(script_type).upper()
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM perte")
        row = cur.fetchone()
        conn.close()
        return bool(row)
    except Exception:
        return False


def deduct_amount_from_largest() -> Optional[tuple]:
    """
    Retourne la perte la plus grande stockée dans SQLite sans la modifier.

    Returns:
        tuple: `(script_type, perte)` de l'entrée avec la plus grande perte,
               ou None si aucune perte positive n'existe.
    """
    try:
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT script_type, loss FROM perte ORDER BY loss DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if not row:
            return 0

        script_type, val = row
        try:
            valf = float(val)
        except Exception:
            valf = 0.0

        if valf <= 0:
            return 0

        try:
            import config
            config.log(f"[RedisIPC] sqlite deduct_amount_from_largest {script_type}={valf}", 'debug')
        except Exception:
            pass
        set_loss(script_type, 0.0)
        return valf
    except Exception:
        return 0


def list_running(exclude_script_types: Optional[Iterable[str]] = None, matchname: str = "") -> list:
    """
    Retourne la liste des `script_type` actuellement marqués comme running (1).

    Args:
        exclude_script_types (Optional[Iterable[str]]): script(s) à exclure (optionnel)

    Returns:
        list: liste des script_type en cours
    """
    excludes = set()
    if exclude_script_types is not None:
        if isinstance(exclude_script_types, str):
            excludes.add(exclude_script_types.upper())
        else:
            for s in exclude_script_types:
                try:
                    excludes.add(str(s).upper())
                except Exception:
                    continue

    results: list[Tuple[str, str]] = []
   

    # Fallback SQLite
    import config
    try:
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        if not excludes:
            cur.execute("SELECT script_type, matchname FROM running WHERE is_running = 1")
            rows = cur.fetchall()
        else:
            placeholders = ','.join('?' for _ in excludes)
            sql = f"SELECT script_type, matchname FROM running WHERE is_running = 1 AND script_type NOT IN ({placeholders}) AND (matchname = '' OR matchname = ?)"
            cur.execute(sql, tuple(excludes) + (matchname,))
            rows = cur.fetchall()
        conn.close()
        config.log(f"[RedisIPC] sqlite list_running exclude={excludes} matchname='{matchname}' results: {rows}", 'debug')
        return [(r[0], r[1] or '') for r in rows]
    except Exception:
        config.log(f"[RedisIPC] sqlite list_running error with exclude={excludes} matchname='{matchname}'", 'error')
        return False


def count_running(exclude_script_types: Optional[Iterable[str]] = None) -> int:
    """
    Retourne le nombre de scripts en cours, optionnellement en excluant un ou plusieurs scripts donnés.
    """
    try:
        return len(list_running(exclude_script_types))
    except Exception:
        return 0


def set_running(script_type: str, running: bool, matchname: str = "") -> bool:
    """
    Définit l'état d'exécution pour `script_type`.

    - Écrit dans Redis sur la clé `RUN_<SCRIPT>` si disponible (valeur '1' ou '0').
    - Écrit également dans la BDD SQLite de secours pour assurer la persistance.

    Args:
        script_type (str): identifiant du script
        running (bool): True si le script tourne, False sinon

    Returns:
        bool: True si opération réussie
    """
    try:
        st = str(script_type).upper()
        val = 1 if running else 0
        import config


        # Toujours écrire dans SQLite de secours
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("REPLACE INTO running (script_type, is_running, matchname) VALUES (?, ?, ?)", (st, int(val), str(matchname)))
        conn.commit()
        conn.close()

        try:
            config.log(f"[RedisIPC] set_running {st}={val}", 'debug')
        except Exception:
            config.log(f"[RedisIPC] set_running {st}={val}", 'debug')
            pass
        return True
    except Exception:
        config.log(f"[RedisIPC] set_running error for {script_type} with running={running} matchname='{matchname}'", 'error')
        return False


def get_running(script_type: str, default: int = 0) -> int:
    """
    Récupère l'état d'exécution pour `script_type`.

    Priorité à Redis si disponible, sinon lecture depuis SQLite.
    Retourne 1 si running, 0 sinon.
    """
    st = str(script_type).upper()
    # Vérifier Redis
    try:
        client = get_redis_client()
        if client is not None:
            val = client.get(f"RUN_{st}")
            if val is not None:
                try:
                    return int(val)
                except Exception:
                    return int(default)
    except Exception:
        pass

    # Fallback SQLite
    try:
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("SELECT is_running FROM running WHERE script_type = ?", (st,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return int(default)
        return int(row[0])
    except Exception:
        return int(default)


def any_other_running(exclude_script_types: Optional[Iterable[str]] = None) -> bool:
    """
    Retourne True s'il existe au moins un autre script marqué comme "running"
    (valeur 1) dans Redis ou dans la BDD SQLite de secours, en excluant un
    ou plusieurs `exclude_script_types`.

    Args:
        exclude_script_types (Optional[Iterable[str]]): script(s) à exclure de la vérification

    Returns:
        bool: True s'il existe un autre script en cours, False sinon
    """
    excludes = set()
    if exclude_script_types is not None:
        # accepter une chaîne unique ou un itérable
        if isinstance(exclude_script_types, str):
            excludes.add(exclude_script_types.upper())
        else:
            for s in exclude_script_types:
                try:
                    excludes.add(str(s).upper())
                except Exception:
                    continue

    # Vérifier Redis en priorité
    try:
        client = get_redis_client()
        if client is not None:
            keys = client.keys('RUN_*')
            if keys:
                for k in keys:
                    try:
                        st = k.replace('RUN_', '', 1)
                        if st in excludes:
                            continue
                        v = client.get(k)
                        if v is None:
                            continue
                        if int(v) == 1:
                            return True
                    except Exception:
                        continue
            return False
    except Exception:
        pass

    # Fallback SQLite
    try:
        conn = _get_sqlite_conn()
        cur = conn.cursor()
        if excludes:
            # construire clause dynamique
            placeholders = ','.join('?' for _ in excludes)
            sql = f"SELECT 1 FROM running WHERE is_running = 1 AND script_type NOT IN ({placeholders}) LIMIT 1"
            cur.execute(sql, tuple(excludes))
        else:
            cur.execute("SELECT 1 FROM running WHERE is_running = 1 LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return bool(row)
    except Exception:
        return False
def bkp_deduct_amount_from_largest(amount: float):
    """
    Déduit un montant donné des clés PERTE_<SCRIPT> en commençant par la perte la plus élevée.

    Comportement:
    - Récupère toutes les clés `PERTE_*` et trie par valeur décroissante.
    - Déduit l'`amount` de la plus grande perte; si `amount` > valeur, met la perte à 0
      et continue sur la suivante avec le reliquat.
    - Écrit les nouvelles valeurs dans Redis via pipeline.

    Args:
        amount (float): montant à déduire (positif)

    Returns:
        list of tuple: liste d'éléments (script_type, nouvelle_perte) pour chaque clé modifiée,
                       dans l'ordre d'application.
    """
    client = get_redis_client()
    if client is None:
        return []
    
    import config
    try:
        keys = client.keys('PERTE_*')
        if not keys:
            return []
        # Obtenir toutes les valeurs
        vals = client.mget(keys)
        # Construire liste (key, float_val)
        pairs = []
        for k, v in zip(keys, vals):
            try:
                fv = float(v) if v is not None else 0.0
            except Exception:
                fv = 0.0
            pairs.append((k, fv))

        # Trier par valeur décroissante
        pairs.sort(key=lambda x: x[1], reverse=True)

        remaining = float(amount)
        modifications = []
        pipe = client.pipeline()
        for key, val in pairs:
            if remaining <= 0:
                break
            if val <= 0:
                continue
            if remaining >= val:
                # Consommer toute cette perte
                new_val = 0.0
                remaining -= val
            else:
                new_val = round(val - remaining, 8)
                remaining = 0.0

            pipe.set(key, new_val)
            # extraire script type du key PERTE_<SCRIPT>
            script_type = key.replace('PERTE_', '', 1)
            modifications.append((script_type, float(new_val)))

        if modifications:
            pipe.execute()
        config.log(f"[RedisIPC] deduct_amount_from_largest modifications: {modifications}", 'debug')
        return modifications
    except Exception:
        return []
