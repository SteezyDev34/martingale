"""
Dashboard de monitoring (+ contrôle) pour les bots martingale — outil séparé, lecture
seule sur l'état (ne modifie rien), sauf les boutons Play/Stop de l'onglet Scripts qui
lancent/arrêtent explicitement un process à la demande de l'utilisateur.

Sources de données :
  - redis_fallback.sqlite (tables running/perte/gain/match_score)
  - DataFiles/matches.db (table matches_todo)
  - stdout/stderr en direct des scripts lancés depuis ce dashboard (tout script doit
    être lancé d'ici pour apparaître dans les logs), copié aussi dans
    Logs/dashboard_<script>.log
  - SCRIPTS_*/*-N.py (scripts de lancement des bots)

Lancement : python dashboard.py
Raccourcis : o = vue d'ensemble, s = scripts, r = rafraîchir, ctrl+q = quitter
"""
import json
import os
import pty
import queue
import re
import signal
import sqlite3
import subprocess
import threading

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Header, Footer, Static, DataTable, RichLog, Button, Input,
    TabbedContent, TabPane,
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_DB = os.path.join(PROJECT_DIR, "DataFiles", "matches.db")
REDIS_DB = os.path.join(PROJECT_DIR, "redis_fallback.sqlite")
LOGS_DIR = os.path.join(PROJECT_DIR, "Logs")
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "bin", "python")
if not os.path.exists(VENV_PYTHON):
    # venv Windows (créé via Scripts/, sans bin/) : on bascule sur le venv WSL à côté
    VENV_PYTHON = os.path.join(PROJECT_DIR, "venv_wsl", "bin", "python")

# Pour l'instant on ne pilote que ces trois process depuis le dashboard (pas les
# 36 scripts de lancement) : 1530A (bridge 1xBet), 456P (représenté par 4P6P-1,
# cf. choix utilisateur — il n'y a pas de fichier "456P-1.py" unique, la famille
# 456P étant répartie sur plusieurs dossiers SCRIPTS_*) et le Watcher Telegram
# (SCRIPTS_WATCH/main-1.py — pas une famille de scriptType martingale, n'a donc
# pas d'entrée dans FAMILY_SCRIPTTYPES ci-dessous : son statut n'affiche que le
# pid, pas d'infos de match en cours).
FIXED_LAUNCHERS = [
    (os.path.join(PROJECT_DIR, "SCRIPTS_1530A", "1530A-1.py"), "1530A"),
    (os.path.join(PROJECT_DIR, "SCRIPTS_4P6P", "4P6P-1.py"), "456P"),
    (os.path.join(PROJECT_DIR, "SCRIPTS_WATCH", "main-1.py"), "Watcher"),
    (os.path.join(PROJECT_DIR, "SCRIPTS_WATCH", "process_bets_loop.py"), "Placement paris"),
]

# ScriptTypes gérés par chaque famille de bot (cf. config.VALID_SCRIPTTYPES_1530A/456P
# dans le bot lui-même) — dupliqué ici pour ne pas importer tout le module config.py
# (effets de bord au chargement) juste pour ces deux constantes.
FAMILY_SCRIPTTYPES = {
    "1530A": {"150", "015", "030", "300", "15A", "30A"},
    "456P": {"40A", "4015", "4030", "400", "4P", "5P", "6P", "BREAK", "HOLD"},
}

# API distante de la liste des matchs (= config.api_url, dupliqué pour la même raison).
API_URL = "http://auxobetbot.sc2vagr6376.universe.wf"

MAX_LOG_LINES = 2000


def _connect(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1)


def _sanitize_id(text):
    """Rend une chaîne compatible avec les id de widgets Textual (lettres/chiffres/_/-)."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", text)


def get_running_matches():
    """
    Retourne {matchname: [scriptTypes actifs]} pour TOUS les matchs actuellement en
    cours (is_running=1) — plusieurs bots (1530A, 456P, ...) peuvent tourner en
    parallèle sur des matchs différents en même temps.
    """
    result = {}
    try:
        conn = _connect(REDIS_DB)
        rows = conn.execute(
            "SELECT script_type, matchname FROM running WHERE is_running=1 AND matchname != ''"
        ).fetchall()
        conn.close()
        for st, matchname in rows:
            result.setdefault(matchname, []).append(st)
    except Exception:
        pass
    return result


def get_match_info(matchname, bot_family=None):
    """
    bot_family (optionnel) : 1530A et 456P ont chacun leur propre ligne pour le
    même match_id depuis la correction du bug de partage de matches_todo (une
    famille qui engageait un match supprimait la ligne de l'autre) -- sans ce
    filtre, la ligne retournée est arbitraire quand les deux existent.
    """
    try:
        conn = _connect(MATCHES_DB)
        if bot_family:
            row = conn.execute(
                "SELECT players, league, script_types FROM matches_todo WHERE match_id = ? AND bot_family = ?",
                (matchname, bot_family)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT players, league, script_types FROM matches_todo WHERE match_id = ?",
                (matchname,)
            ).fetchone()
        conn.close()
        return row
    except Exception:
        return None


def _infer_bot_family(scripttypes):
    """Déduit 1530A/456P à partir d'une liste de scriptTypes actifs (None si mixte/inconnu)."""
    families = {fam for fam, sts in FAMILY_SCRIPTTYPES.items() if sts & set(scripttypes or [])}
    return families.pop() if len(families) == 1 else None


def get_live_score(matchname):
    try:
        conn = _connect(REDIS_DB)
        row = conn.execute(
            "SELECT score, set_actuel, jeu_actuel FROM match_score WHERE matchname = ?",
            (matchname,)
        ).fetchone()
        conn.close()
        return row
    except Exception:
        return None


def get_perte_gain(matchname, scripttypes):
    perte = {}
    gain = 0.0
    try:
        conn = _connect(REDIS_DB)
        for st in scripttypes:
            row = conn.execute(
                "SELECT loss FROM perte WHERE script_type=? AND matchname=?", (st, matchname)
            ).fetchone()
            perte[st] = row[0] if row else 0.0
        # La table 'gain' est en réalité indexée par matchname malgré le nom de colonne.
        row = conn.execute("SELECT gain FROM gain WHERE script_type=?", (matchname,)).fetchone()
        gain = row[0] if row else 0.0
        conn.close()
    except Exception:
        pass
    return perte, gain


def get_last_validated_bet(scripttypes):
    """
    Dernière mise placée, la plus récente parmi les fichiers <scriptType>_validated_bets.json
    des scriptTypes actifs donnés (écrits par ValidationDuParis.py à chaque pari placé).
    """
    last_bet = None
    last_ts = ""
    for st in scripttypes:
        json_path = os.path.join(PROJECT_DIR, f"{st}_validated_bets.json")
        if not os.path.isfile(json_path):
            continue
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                bets = json.load(f)
        except Exception:
            continue
        if not bets:
            continue
        b = bets[-1]
        ts = b.get("timestamp") or ""
        if ts >= last_ts:
            last_ts = ts
            last_bet = {**b, "scriptType": st}
    return last_bet


def get_family_live_info(label):
    """
    Infos en direct pour la famille de bot (1530A/456P) : match en cours, set/jeu,
    perte totale et gain total cumulés sur les scriptTypes actifs, dernière mise
    (via get_last_validated_bet). Retourne None si rien n'est en cours pour cette
    famille.
    """
    scripttypes_family = FAMILY_SCRIPTTYPES.get(label, set())
    if not scripttypes_family:
        return None
    try:
        conn = _connect(REDIS_DB)
        rows = conn.execute(
            "SELECT script_type, matchname FROM running WHERE is_running=1 AND matchname != ''"
        ).fetchall()
        active = [(st, mn) for st, mn in rows if st in scripttypes_family]
        if not active:
            conn.close()
            return None
        matchname = active[0][1]
        active_sts = [st for st, mn in active if mn == matchname]
        perte_total = 0.0
        for st in active_sts:
            row = conn.execute(
                "SELECT loss FROM perte WHERE script_type=? AND matchname=?", (st, matchname)
            ).fetchone()
            if row:
                perte_total += row[0]
        gain_row = conn.execute("SELECT gain FROM gain WHERE script_type=?", (matchname,)).fetchone()
        gain = gain_row[0] if gain_row else 0.0
        score_row = conn.execute(
            "SELECT score, set_actuel, jeu_actuel FROM match_score WHERE matchname=?", (matchname,)
        ).fetchone()
        conn.close()
    except Exception:
        return None
    return {
        "matchname": matchname,
        "scripttypes": active_sts,
        "score": score_row[0] if score_row else "-",
        "set": score_row[1] if score_row else "-",
        "jeu": score_row[2] if score_row else "-",
        "perte": perte_total,
        "gain": gain,
        "last_bet": get_last_validated_bet(active_sts),
    }


def get_matches_todo(limit=20):
    try:
        conn = _connect(MATCHES_DB)
        rows = conn.execute(
            "SELECT match_id, players, league, script_types, match_date FROM matches_todo "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def get_matches_todo_count():
    """
    Total réel de matches_todo, sans la limite d'affichage (get_matches_todo
    plafonne à limit=20 pour la table -- depuis la suppression du plafond
    max_matches=30 côté classement, ScriptRechercheDeMatch.py, il peut y avoir
    bien plus de 20 matchs en attente et la table n'en montrerait qu'une partie
    sans ce compteur séparé).
    """
    try:
        conn = _connect(MATCHES_DB)
        count = conn.execute("SELECT COUNT(*) FROM matches_todo").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def get_match_history(limit=200):
    """
    Récap des gains par scriptType pour les matchs terminés (cf.
    Functions_431a.py::record_match_history, appelé juste avant la remise à zéro de
    config.global_match_win). Une ligne par (match, scriptType).
    """
    try:
        conn = _connect(MATCHES_DB)
        rows = conn.execute(
            "SELECT match_id, script_type, gain, finished_at FROM matches_history "
            "ORDER BY finished_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def clear_matches_todo():
    """
    Vide entièrement la table matches_todo locale et retourne les match_id supprimés
    (action destructive, appelée après confirmation). None en cas d'erreur.
    """
    try:
        conn = sqlite3.connect(MATCHES_DB)
        ids = [r[0] for r in conn.execute("SELECT match_id FROM matches_todo").fetchall()]
        conn.execute("DELETE FROM matches_todo")
        conn.commit()
        conn.close()
        return ids
    except Exception:
        return None


def purge_remote_matches_todo(local_ids):
    """
    Supprime côté distant (API matchlist, cf. MatchManager.remove_match_todo) les matchs
    locaux qu'on vient de vider + tous les matchs distants dont la date est passée.
    Sans ça, le bouton "Vider matches_todo" ne vidait que le local et la liste distante
    grossissait indéfiniment. Retourne (nb supprimés, nb échecs).
    """
    import requests
    from datetime import datetime

    headers = {"User-Agent": "Mozilla/5.0"}
    ids = set(local_ids or [])
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        resp = requests.get(f"{API_URL}/matchlist/get.php", headers=headers, timeout=10)
        for m in resp.json().get("data", []):
            if m.get("match_id") and (m.get("match_date") or "")[:10] < today:
                ids.add(m["match_id"])
    except Exception:
        pass
    ok = ko = 0
    for match_id in ids:
        try:
            # delete.php répond toujours {"status":"error"} (warning PHP) alors que la
            # suppression a lieu : seul le code HTTP est fiable.
            r = requests.get(
                f"{API_URL}/matchlist/delete.php", params={"match_id": match_id},
                headers=headers, timeout=10,
            )
            if r.status_code == 200:
                ok += 1
            else:
                ko += 1
        except Exception:
            ko += 1
    return ok, ko


def _settings_conn():
    conn = sqlite3.connect(REDIS_DB, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return conn


def get_dev_mode(default=True):
    """Lit config.devMode (table settings) — même mécanisme que Functions/RedisIPC.get_dev_mode."""
    try:
        conn = _settings_conn()
        row = conn.execute("SELECT value FROM settings WHERE key='devMode'").fetchone()
        conn.close()
        if row is None:
            return default
        return row[0] == "1"
    except Exception:
        return default


def set_dev_mode(value):
    """
    Écrit devMode dans redis_fallback.sqlite. Les bots déjà lancés (1530A/456P) le
    relisent sous 2s (cf. config.refresh_dev_mode, appelé à chaque config.log()) —
    pas besoin de les redémarrer pour que le changement prenne effet.
    """
    try:
        conn = _settings_conn()
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('devMode', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("1" if value else "0",)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def clear_running_table():
    """
    Remet à 0 tous les 'is_running' de la table running (redis_fallback.sqlite). Sert
    à débloquer un état incohérent après un crash/kill du bot : la table reste à 1
    alors qu'aucun match n'est réellement en cours, ce qui fait croire au dashboard
    (et au bot au redémarrage) qu'un match est encore actif.
    """
    try:
        conn = sqlite3.connect(REDIS_DB)
        conn.execute("UPDATE running SET is_running = 0")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_running_matchnames():
    """
    Liste les matchs distincts actuellement marqués 'en cours' (is_running=1) dans la
    table running, tous scriptTypes/familles confondus — sert à cibler l'annulation
    d'une reprise sur UN match précis plutôt que de vider toute la table.
    """
    try:
        conn = sqlite3.connect(REDIS_DB)
        rows = conn.execute(
            "SELECT DISTINCT matchname FROM running WHERE is_running = 1 AND matchname != '' ORDER BY matchname"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []


def clear_running_match(matchname):
    """
    Remet à 0 'is_running' uniquement pour les lignes de la table running portant ce
    matchname précis — au prochain cycle de recherche, RedisIPC.get_interrupted_match()
    ne trouve plus ce match et le script repart sur une recherche normale au lieu de
    le reprendre, sans affecter les autres matchs/familles éventuellement en cours.
    """
    try:
        conn = sqlite3.connect(REDIS_DB)
        conn.execute("UPDATE running SET is_running = 0 WHERE matchname = ?", (matchname,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False




# Process lancés PAR ce dashboard : path -> {"proc": Popen, "queue": Queue, "name": str}.
# Pour ceux-là on capture le vrai stdout/stderr en direct (pipe), pas besoin de relire
# un fichier. Un script lancé en dehors du dashboard (terminal de l'utilisateur) ne peut
# pas être intercepté ainsi : son stdout appartient à un autre terminal, inaccessible
# depuis l'extérieur — pour ceux-là on retombe sur la lecture des fichiers de log.
_process_registry = {}



# Séquence brute écrite par config.log_clear_line() (config.py) pour remonter d'une
# ligne et l'effacer — utilisée par le système d'affichage dynamique de la recherche
# de match dans ScriptRechercheDeMatch.py (efface une ligue/un match/tout le bloc de
# recherche une fois "traité", pour ne pas laisser un historique de terminal infini).
# Elle est écrite SANS retour à la ligne : elle peut donc atterrir n'importe où dans
# le flux, entre deux lignes complètes — d'où un parsing en octets bruts plutôt qu'un
# simple split sur b"\n".
_CLEAR_SEQ = b"\x1b[1A\x1b[2K\r"
_CLEAR_RE = re.compile(b"(?:" + re.escape(_CLEAR_SEQ) + b")+")


def _reader_thread(master_fd, q, log_path=None):
    """
    Lit le stdout/stderr du process via le côté maître du pseudo-terminal. On utilise
    un pty (pas un simple pipe) car colorama (utilisé par config.log dans le bot)
    désactive automatiquement les couleurs quand la sortie n'est pas un vrai terminal
    — un pipe classique aurait donc fait perdre les couleurs à la source.

    En plus des lignes de texte, on reconnaît la séquence d'effacement _CLEAR_SEQ
    (émise par config.log_clear_line) et on la traduit en événement ("erase", n) —
    n = nombre de lignes à retirer du buffer affiché — pour que le dashboard reproduise
    le même effacement dynamique qu'un vrai terminal (cf. _drain_process_queues).
    """
    buf = b""
    # Copie brute du flux dans Logs/dashboard_<script>.log (ANSI compris) : permet de
    # relire après coup ce que le bot a affiché, y compris les lignes effacées.
    try:
        log_file = open(log_path, "ab") if log_path else None
    except Exception:
        log_file = None
    try:
        while True:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            if log_file:
                try:
                    log_file.write(chunk)
                    log_file.flush()
                except Exception:
                    pass
            buf += chunk
            while True:
                nl_idx = buf.find(b"\n")
                m = _CLEAR_RE.match(buf)
                if m:
                    count = len(m.group(0)) // len(_CLEAR_SEQ)
                    q.put(("erase", count))
                    buf = buf[m.end():]
                    continue
                # Une séquence d'effacement peut aussi apparaître plus loin dans le
                # buffer (précédée d'une ligne complète) : on ne traite alors que la
                # ligne complète d'abord, la prochaine itération retombera sur le cas
                # ci-dessus une fois le préfixe consommé.
                m2 = _CLEAR_RE.search(buf)
                if nl_idx == -1:
                    break
                if m2 and m2.start() < nl_idx:
                    break  # laisse le cas "match" ci-dessus gérer une fois raccourci
                line, buf = buf.split(b"\n", 1)
                q.put(("line", line.decode("utf-8", errors="ignore").rstrip("\r")))
            # Reliquat sans retour à la ligne (ex: un input() qui affiche son prompt
            # et attend la réponse sur la même ligne) : on l'affiche quand même tout
            # de suite en "aperçu", sinon il resterait invisible indéfiniment alors
            # que le script attend une réponse dans la zone stdin du dashboard. buf
            # n'est PAS consommé ici — la ligne complète sera émise normalement au
            # \n final (après la frappe de l'utilisateur).
            if buf and not _CLEAR_SEQ.startswith(buf) and not _CLEAR_RE.search(buf):
                q.put(("partial", buf.decode("utf-8", errors="ignore").rstrip("\r")))
        if buf:
            m = _CLEAR_RE.fullmatch(buf)
            if m:
                q.put(("erase", len(m.group(0)) // len(_CLEAR_SEQ)))
            else:
                q.put(("line", buf.decode("utf-8", errors="ignore")))
    except Exception:
        pass
    finally:
        if log_file:
            try:
                log_file.close()
            except Exception:
                pass
        try:
            os.close(master_fd)
        except Exception:
            pass
        q.put(("eof", None))  # marqueur de fin de process


def launcher_pid(path):
    """Retourne le PID (str) si ce script tourne actuellement, sinon None."""
    entry = _process_registry.get(path)
    if entry and entry["proc"].poll() is None:
        return str(entry["proc"].pid)
    try:
        out = subprocess.run(["pgrep", "-f", path], capture_output=True, text=True)
        pids = [p for p in out.stdout.split() if p.strip()]
        return pids[0] if pids else None
    except Exception:
        return None


def start_launcher(path):
    """
    Lance le script en arrière-plan et capture son stdout/stderr/stdin en direct via un
    pseudo-terminal (vrais messages terminal, couleurs comprises — cf. _reader_thread).
    stdin est branché sur le même pty (pas juste un 'echo N' figé) pour pouvoir répondre
    à n'importe quel prompt interactif du script depuis le dashboard (cf. send_input).
    """
    if path in _process_registry and _process_registry[path]["proc"].poll() is None:
        return False  # déjà suivi
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            [VENV_PYTHON, path],
            cwd=PROJECT_DIR,
            stdout=slave_fd, stderr=slave_fd, stdin=slave_fd,
            start_new_session=True,
            close_fds=True,
        )
        os.close(slave_fd)  # seul le process enfant garde ce côté du pty
    except Exception:
        return False
    q = queue.Queue()
    log_path = os.path.join(LOGS_DIR, f"dashboard_{name}.log")
    threading.Thread(target=_reader_thread, args=(master_fd, q, log_path), daemon=True).start()
    _process_registry[path] = {"proc": proc, "queue": q, "name": name, "master_fd": master_fd}
    return True


def send_input(path, text):
    """Envoie une ligne de texte au stdin (via le pty) du script en cours, s'il tourne."""
    entry = _process_registry.get(path)
    if not entry:
        return False
    try:
        os.write(entry["master_fd"], (text + "\n").encode("utf-8"))
        return True
    except Exception:
        return False


def stop_launcher(path):
    """
    Arrête le script s'il tourne (SIGTERM). Le process suivi est lancé via
    "bash -c 'echo N | python ...'" (start_new_session=True) : terminer seulement ce
    bash ne tue pas le vrai bot Python de la pipeline (processus frère, pas enfant
    direct) — il faut cibler tout le groupe de process (pgid = pid du bash, car chef
    de session).
    """
    entry = _process_registry.get(path)
    if entry:
        try:
            os.killpg(os.getpgid(entry["proc"].pid), signal.SIGTERM)
            return True
        except Exception:
            return False
    pid = launcher_pid(path)
    if not pid:
        return False
    try:
        os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
        return True
    except Exception:
        try:
            os.kill(int(pid), signal.SIGTERM)
            return True
        except Exception:
            return False


def _render_match_block(matchname, scripttypes):
    """Construit le texte (avec markup Rich) d'un panneau de match, couleur selon le gain."""
    info = get_match_info(matchname, bot_family=_infer_bot_family(scripttypes))
    score_row = get_live_score(matchname)
    perte, gain = get_perte_gain(matchname, scripttypes)
    gain_color = "green" if gain >= 0 else "red"

    lines = [f"[b]{matchname}[/b]"]
    if info:
        players, league, all_st = info
        lines.append(f"{players} — {league}")
        lines.append(f"ScriptTypes classés : {all_st}")
    else:
        # Normal : un match engagé est retiré de matches_todo (cf. Functions_431a/456P,
        # remove_match_todo juste après add_match).
        lines.append("[dim](match engagé : retiré de matches_todo)[/dim]")
    if score_row:
        score, set_a, jeu_a = score_row
        lines.append(f"Score : [b]{score}[/b]  (set {set_a}, jeu {jeu_a})")
    lines.append("")
    lines.append(f"ScriptTypes actifs : {', '.join(scripttypes) or '-'}")
    for st in scripttypes:
        p = perte.get(st, 0.0)
        p_color = "yellow" if p > 0 else "dim"
        lines.append(f"  {st} — perte en cours : [{p_color}]{p:.2f}€[/{p_color}]")
    lines.append("")
    lines.append(f"[b {gain_color}]Gain net cumulé (match) : {gain:.2f}€[/b {gain_color}]")
    return "\n".join(lines)


class ConfirmScreen(ModalScreen[bool]):
    """Boîte de dialogue de confirmation générique pour une action destructive."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: thick $error 80%;
        background: $surface;
        padding: 1 2;
    }
    #dialog Static {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #dialog Horizontal {
        align: center middle;
        height: auto;
    }
    #dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._message)
            with Horizontal():
                yield Button("Oui, confirmer", id="confirm_yes", variant="error")
                yield Button("Annuler", id="confirm_no", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm_yes")


class SelectMatchScreen(ModalScreen):
    """Liste les matchs actuellement 'en cours' pour en choisir un à annuler (reprise)."""

    CSS = """
    SelectMatchScreen {
        align: center middle;
    }
    #dialog {
        width: 70;
        height: auto;
        max-height: 20;
        border: thick $warning 80%;
        background: $surface;
        padding: 1 2;
    }
    #dialog Static {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #dialog Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self, matchnames):
        super().__init__()
        self._matchnames = matchnames

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Annuler la reprise de quel match ?")
            for matchname in self._matchnames:
                yield Button(matchname, id=f"pick_{self._matchnames.index(matchname)}", variant="warning")
            yield Button("Annuler", id="pick_cancel", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "pick_cancel" or not button_id.startswith("pick_"):
            self.dismiss(None)
            return
        try:
            idx = int(button_id.split("_", 1)[1])
        except ValueError:
            self.dismiss(None)
            return
        self.dismiss(self._matchnames[idx])


class Dashboard(App):
    BINDINGS = [
        ("o", "goto_tab('tab_overview')", "Vue d'ensemble"),
        ("h", "goto_tab('tab_history')", "Historique"),
        ("r", "manual_refresh", "Rafraîchir"),
        ("ctrl+q", "quit", "Quitter"),
    ]

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        height: 1fr;
    }
    #top {
        height: 1fr;
    }
    #queue_panel {
        width: 1fr;
        border: round cyan;
    }
    #log_filter {
        height: 3;
        border: round yellow;
    }
    #logs_tabs {
        height: 3fr;
        border: round white;
    }
    #scripts_panel {
        height: 1fr;
    }
    .match_content {
        padding: 1;
        border: round green;
    }
    .script_row {
        height: 1;
        align: left middle;
        margin-bottom: 1;
    }
    .button_row {
        height: 3;
    }
    .button_row Button {
        margin-right: 1;
    }
    #toggle_devmode {
        /* Largeur fixe : "devMode: ON"/"devMode: OFF" ont une longueur différente --
           sans ça le bouton change de taille au toggle et décale les autres boutons
           de la rangée, faisant rater le clic suivant au même endroit à l'écran
           (bug rapporté le 2026-10-17, reproduit via Pilot.click : 2e clic sans effet). */
        width: 16;
    }
    RichLog {
        height: 1fr;
        /* wrap=False -> une barre de scroll horizontale apparaît en bas dès qu'une
           ligne dépasse la largeur, et cachait la toute dernière ligne de logs sans
           cette marge de respiration. */
        padding-bottom: 1;
    }
    #logs_tabs Input {
        height: 3;
        dock: bottom;
    }
    .log_end_marker {
        height: 1;
        color: $text-muted;
        content-align: center middle;
    }
    .toggle_icon {
        width: 3;
        min-width: 3;
        height: 1;
        border: none;
        background: transparent;
        padding: 0;
        content-align: center middle;
        text-style: bold;
    }
    .toggle_icon:hover {
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Vue d'ensemble", id="tab_overview"):
                yield Static("", id="queue_count")
                with Horizontal(id="top"):
                    yield DataTable(id="queue_panel")
                with Horizontal(classes="button_row"):
                    yield Button("🗑 Vider matches_todo", id="clear_queue", variant="warning")
                    yield Button("🗑 Vider matchs en cours (running)", id="clear_running", variant="warning")
                    yield Button("⛔ Annuler reprise d'un match", id="cancel_resume", variant="warning")
                    yield Button("devMode: ...", id="toggle_devmode", variant="default")
                    yield Button("📋 Copier matches_todo", id="copy_queue", variant="default")
                yield Input(placeholder="Filtrer les logs (ex: 300, WIN, error...)", id="log_filter")
                with TabbedContent(id="logs_tabs"):
                    for i, (_path, label) in enumerate(FIXED_LAUNCHERS):
                        with TabPane(label, id=f"logtab_{i}"):
                            with Horizontal(classes="script_row"):
                                yield Button("▶", id=f"logtoggle_{i}", classes="toggle_icon", variant="success")
                                yield Static(label, id=f"logstatus_{i}")
                                yield Button("📋", id=f"logcopy_{i}", classes="toggle_icon", variant="default")
                            yield RichLog(id=f"logrich_{i}", wrap=False, highlight=False, markup=True)
                            # Repère fixe (ne scrolle pas avec le log) confirmant qu'on est
                            # bien arrivé à la toute dernière ligne affichée — la barre de
                            # scroll horizontale du RichLog pouvait sinon donner l'impression
                            # qu'il manque du texte en bas.
                            yield Static("─" * 60, id=f"logend_{i}", classes="log_end_marker")
                            yield Input(placeholder="Répondre au script (ex: Y, N, 1, 2...)", id=f"stdin_{i}")
            with TabPane("Historique", id="tab_history"):
                yield DataTable(id="history_panel")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#queue_panel", DataTable)
        table.add_columns("Match", "Ligue", "ScriptTypes", "Date/heure prévue")
        history_table = self.query_one("#history_panel", DataTable)
        history_table.add_columns("Match", "ScriptType", "Gain", "Terminé le")
        self._log_lines_by_idx = {i: [] for i in range(len(FIXED_LAUNCHERS))}
        self._partial_by_idx = {i: "" for i in range(len(FIXED_LAUNCHERS))}
        self._log_filter = ""
        self._match_tab_ids = set()
        self.set_interval(2.0, self.refresh_data)
        self.set_interval(3.0, self.refresh_fixed_log_headers)
        self.set_interval(0.5, self._drain_process_queues)
        self.call_later(self.refresh_data)
        self.refresh_fixed_log_headers()
        self._refresh_devmode_button()

    def _copy_text(self, text: str, export_name: str) -> None:
        """
        Copie `text` dans le presse-papier du terminal (OSC 52, cf. Textual
        App.copy_to_clipboard) -- ne fonctionne pas sur macOS Terminal.app
        (limite documentée de Textual), fonctionne sur la plupart des autres
        terminaux (iTerm2 avec l'option presse-papier activée, etc.). Écrit
        aussi systématiquement le texte dans DataFiles/exports/ comme filet de
        secours fiable quel que soit le terminal, demandé le 2026-10-17 car les
        tableaux (DataTable) n'implémentent pas la sélection de texte native de
        Textual (ALLOW_SELECT=False côté librairie).
        """
        self.copy_to_clipboard(text)
        try:
            export_dir = os.path.join(PROJECT_DIR, "DataFiles", "exports")
            os.makedirs(export_dir, exist_ok=True)
            path = os.path.join(export_dir, export_name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.notify(f"Copié (si le terminal le permet) + exporté vers {path}")
        except Exception as e:
            self.notify(f"Échec de l'export fichier : {e}", severity="error")

    def _refresh_devmode_button(self) -> None:
        try:
            button = self.query_one("#toggle_devmode", Button)
        except Exception:
            return
        on = get_dev_mode()
        button.label = f"devMode: {'ON' if on else 'OFF'}"
        button.variant = "warning" if on else "success"

    def refresh_fixed_log_headers(self) -> None:
        """Met à jour l'icône ▶/⏸ (verte/rouge) et le libellé au-dessus de chaque fenêtre de logs."""
        for i, (path, label) in enumerate(FIXED_LAUNCHERS):
            pid = launcher_pid(path)
            try:
                status = self.query_one(f"#logstatus_{i}", Static)
                button = self.query_one(f"#logtoggle_{i}", Button)
            except Exception:
                continue
            if pid:
                info = get_family_live_info(label) if label in FAMILY_SCRIPTTYPES else None
                if info:
                    gain_color = "green" if info["gain"] >= 0 else "red"
                    bet = info.get("last_bet")
                    bet_txt = (
                        f"mise {bet.get('montant')}€ @ {bet.get('cote')} ({bet.get('scriptType')})"
                        if bet else "aucune mise"
                    )
                    details = (
                        f" | match {info['matchname']} | set {info['set']} jeu {info['jeu']} "
                        f"({info['score']}) | perte en cours [yellow]{info['perte']:.2f}€[/yellow] | "
                        f"gain total [{gain_color}]{info['gain']:.2f}€[/{gain_color}] | {bet_txt}"
                    )
                elif label in FAMILY_SCRIPTTYPES:
                    details = " | en attente d'un match"
                else:
                    details = ""
                status.update(f"{label} — [b green]en cours[/b green] (pid {pid}){details}")
                button.label = "⏸"
                button.variant = "error"
            else:
                status.update(f"{label} — [dim]arrêté[/dim]")
                button.label = "▶"
                button.variant = "success"

    def _drain_process_queues(self) -> None:
        """
        Affiche en direct le stdout/stderr de chaque bot, dans sa fenêtre de logs dédiée.
        Reproduit aussi l'effacement dynamique du bot (cf. config.log_clear_line /
        ScriptRechercheDeMatch.py) : un événement ("erase", n) retire les n dernières
        lignes du buffer stocké, puis on réécrit intégralement le RichLog concerné
        (celui-ci ne sait pas "remonter" et effacer une ligne comme un vrai terminal).
        """
        if not _process_registry:
            return
        filt = self._log_filter
        for i, (path, _label) in enumerate(FIXED_LAUNCHERS):
            entry = _process_registry.get(path)
            if not entry:
                continue
            q = entry["queue"]
            lines = self._log_lines_by_idx.setdefault(i, [])
            appended = []
            erased = False
            finished = False
            partial_changed = False
            while True:
                try:
                    kind, payload = q.get_nowait()
                except queue.Empty:
                    break
                if kind == "eof":
                    finished = True
                    break
                if kind == "erase":
                    # Désactivé à la demande de l'utilisateur (2026-10-17) : on ne
                    # reproduit plus l'effacement dynamique du bot (config.log_clear_line)
                    # dans le dashboard -- tous les logs restent affichés et défilent
                    # normalement, même ceux que le bot efface dans un vrai terminal.
                    continue
                if kind == "partial":
                    # Reliquat sans \n (ex: prompt input() en attente d'une réponse) —
                    # affiché tout de suite comme dernière ligne provisoire, remplacée
                    # par la vraie ligne complète une fois le \n reçu (cf. plus bas).
                    self._partial_by_idx[i] = payload
                    partial_changed = True
                    continue
                # kind == "line" : Text.from_ansi restitue les vraies couleurs du stdout
                # (colorama, cf. config.PURPLE/config.log dans le bot) au lieu d'afficher
                # les codes d'échappement bruts. Une ligne complète remplace le "partial"
                # en attente (le \n qui vient d'arriver la termine).
                self._partial_by_idx[i] = ""
                entry_line = (payload, Text.from_ansi(payload))
                lines.append(entry_line)
                appended.append(entry_line)
            self._log_lines_by_idx[i] = lines[-MAX_LOG_LINES:]
            if erased or partial_changed:
                self._rerender_log(i)
            elif appended:
                try:
                    log_widget = self.query_one(f"#logrich_{i}", RichLog)
                except Exception:
                    log_widget = None
                if log_widget is not None:
                    for plain, rendered in appended:
                        if not filt or filt in plain.lower():
                            log_widget.write(rendered)
            if finished:
                del _process_registry[path]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "clear_queue":
            self.push_screen(
                ConfirmScreen(
                    "Vider entièrement la table matches_todo ?\n"
                    "Tous les matchs classés (non encore pariés) seront supprimés, en local "
                    "et sur la liste distante (ainsi que les matchs distants déjà passés)."
                ),
                self._on_clear_queue_confirmed,
            )
            return
        if button_id == "clear_running":
            self.push_screen(
                ConfirmScreen(
                    "Réinitialiser la table 'running' ?\n"
                    "À utiliser si un match reste marqué 'en cours' après un crash/kill "
                    "du bot alors qu'aucun match n'est réellement actif."
                ),
                self._on_clear_running_confirmed,
            )
            return
        if button_id == "cancel_resume":
            matchnames = get_running_matchnames()
            if not matchnames:
                self.notify("Aucun match 'en cours' à annuler.", severity="information")
            elif len(matchnames) == 1:
                self.push_screen(
                    ConfirmScreen(
                        f"Annuler la reprise de '{matchnames[0]}' ?\n"
                        "Le bot ne rouvrira plus ce match au prochain démarrage/cycle "
                        "de recherche ; il repartira sur une recherche normale."
                    ),
                    lambda confirmed: self._on_cancel_resume_confirmed(confirmed, matchnames[0]),
                )
            else:
                self.push_screen(SelectMatchScreen(matchnames), self._on_match_picked)
            return
        if button_id == "toggle_devmode":
            set_dev_mode(not get_dev_mode())
            self._refresh_devmode_button()
            return
        if button_id == "copy_queue":
            rows = get_matches_todo(limit=1_000_000)
            lines = ["Match\tLigue\tScriptTypes\tDate/heure prévue"]
            for match_id, players, league, script_types, match_date in rows:
                lines.append(f"{players or match_id}\t{league or ''}\t{script_types or '[]'}\t{match_date or '-'}")
            self._copy_text("\n".join(lines), "matches_todo.txt")
            return
        if button_id.startswith("logcopy_"):
            try:
                idx = int(button_id.split("_", 1)[1])
            except ValueError:
                return
            lines = self._log_lines_by_idx.get(idx, [])
            text = "\n".join(plain for plain, _rendered in lines)
            label = FIXED_LAUNCHERS[idx][1] if 0 <= idx < len(FIXED_LAUNCHERS) else f"log_{idx}"
            safe_label = re.sub(r"[^A-Za-z0-9_-]+", "_", label)
            self._copy_text(text, f"log_{safe_label}.txt")
            return
        if not button_id.startswith("logtoggle_"):
            return
        try:
            idx = int(button_id.split("_", 1)[1])
        except ValueError:
            return
        if idx < 0 or idx >= len(FIXED_LAUNCHERS):
            return
        path = FIXED_LAUNCHERS[idx][0]
        label = FIXED_LAUNCHERS[idx][1]
        if launcher_pid(path):
            self.push_screen(
                ConfirmScreen(
                    f"Arrêter le bot {label} ?\n"
                    "Le script en cours sera interrompu immédiatement (SIGTERM)."
                ),
                lambda confirmed: self._on_stop_confirmed(confirmed, path),
            )
        else:
            start_launcher(path)
            self.refresh_fixed_log_headers()

    def _on_stop_confirmed(self, confirmed: bool, path: str) -> None:
        if not confirmed:
            return
        stop_launcher(path)
        self.refresh_fixed_log_headers()

    def _on_clear_queue_confirmed(self, confirmed: bool) -> None:
        if not confirmed:
            return
        local_ids = clear_matches_todo()
        table = self.query_one("#queue_panel", DataTable)
        table.clear()
        if local_ids is None:
            self.notify("Échec du vidage local de matches_todo", severity="error")
            return

        def _purge():
            ok, ko = purge_remote_matches_todo(local_ids)
            msg = f"Liste distante : {ok} match(s) supprimé(s)" + (f", {ko} échec(s)" if ko else "")
            self.call_from_thread(self.notify, msg, severity="warning" if ko else "information")

        self.notify("Local vidé, purge de la liste distante en cours...")
        threading.Thread(target=_purge, daemon=True).start()

    def _on_clear_running_confirmed(self, confirmed: bool) -> None:
        if not confirmed:
            return
        clear_running_table()
        self.refresh_fixed_log_headers()

    def _on_match_picked(self, matchname) -> None:
        if not matchname:
            return
        self.push_screen(
            ConfirmScreen(
                f"Annuler la reprise de '{matchname}' ?\n"
                "Le bot ne rouvrira plus ce match au prochain démarrage/cycle de "
                "recherche ; il repartira sur une recherche normale."
            ),
            lambda confirmed: self._on_cancel_resume_confirmed(confirmed, matchname),
        )

    def _on_cancel_resume_confirmed(self, confirmed: bool, matchname: str) -> None:
        if not confirmed:
            return
        clear_running_match(matchname)
        self.refresh_fixed_log_headers()

    # ─── Raccourcis clavier ────────────────────────────────────────────────

    def action_goto_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    async def action_manual_refresh(self) -> None:
        await self.refresh_data()
        self.refresh_fixed_log_headers()

    # ─── Filtre de logs ────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "log_filter":
            self._log_filter = event.value.strip().lower()
            self._rerender_logs()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        input_id = event.input.id or ""
        if not input_id.startswith("stdin_"):
            return
        try:
            idx = int(input_id.split("_", 1)[1])
        except ValueError:
            return
        if idx < 0 or idx >= len(FIXED_LAUNCHERS):
            return
        path = FIXED_LAUNCHERS[idx][0]
        if send_input(path, event.value):
            event.input.value = ""

    def _rerender_logs(self) -> None:
        for i in range(len(FIXED_LAUNCHERS)):
            self._rerender_log(i)

    def _rerender_log(self, i: int) -> None:
        """Réécrit entièrement le RichLog #i à partir du buffer stocké (filtre appliqué)."""
        filt = self._log_filter
        try:
            log_widget = self.query_one(f"#logrich_{i}", RichLog)
        except Exception:
            return
        log_widget.clear()
        for plain, rendered in self._log_lines_by_idx.get(i, []):
            if not filt or filt in plain.lower():
                log_widget.write(rendered)
        partial = self._partial_by_idx.get(i, "")
        if partial and (not filt or filt in partial.lower()):
            log_widget.write(Text.from_ansi(partial))

    # ─── Rafraîchissement principal ───────────────────────────────────────

    async def refresh_data(self) -> None:
        running = get_running_matches()
        tabbed = self.query_one(TabbedContent)

        new_tab_ids = set()
        for matchname, scripttypes in running.items():
            tab_id = f"tab_match_{_sanitize_id(matchname)}"
            new_tab_ids.add(tab_id)
            content_id = f"content_{tab_id}"
            block = _render_match_block(matchname, scripttypes)
            if tab_id in self._match_tab_ids:
                try:
                    self.query_one(f"#{content_id}", Static).update(block)
                except Exception:
                    pass
            else:
                pane = TabPane(
                    matchname[:20],
                    Static(block, id=content_id, classes="match_content"),
                    id=tab_id,
                )
                await tabbed.add_pane(pane)
                self._match_tab_ids.add(tab_id)

        for tab_id in list(self._match_tab_ids - new_tab_ids):
            try:
                await tabbed.remove_pane(tab_id)
            except Exception:
                pass
            self._match_tab_ids.discard(tab_id)

        # table.clear() remet le scroll en haut -- on le restaure juste après pour ne
        # pas interrompre une lecture en cours (refresh_data tourne toutes les 2s,
        # cf. set_interval dans on_mount).
        queue_count = get_matches_todo_count()
        self.query_one("#queue_count", Static).update(f"{queue_count} match(s) dans matches_todo")
        table = self.query_one("#queue_panel", DataTable)
        _queue_scroll_y = table.scroll_y
        table.clear()
        for match_id, players, league, script_types, match_date in get_matches_todo():
            table.add_row(players or match_id, league or "", script_types or "[]", match_date or "-")
        table.scroll_to(y=_queue_scroll_y, animate=False)

        history_table = self.query_one("#history_panel", DataTable)
        _history_scroll_y = history_table.scroll_y
        history_table.clear()
        for match_id, script_type, gain, finished_at in get_match_history():
            gain_color = "green" if gain >= 0 else "red"
            history_table.add_row(
                match_id, script_type, Text(f"{gain:.2f}€", style=gain_color), finished_at
            )
        history_table.scroll_to(y=_history_scroll_y, animate=False)

        # Le flux de logs est alimenté exclusivement par _drain_process_queues (stdout
        # en direct des scripts lancés depuis ce dashboard) — pas de fallback fichier :
        # tout doit être lancé depuis l'onglet Scripts pour apparaître ici.


if __name__ == "__main__":
    Dashboard().run()
