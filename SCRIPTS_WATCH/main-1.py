# Import des modules personnalises
# Import des modules standards
import base64
import datetime
import json
import os
import re
import sys
import threading

from art import *

# Recuperer le chemin absolu du fichier actuel
current_file_path = os.path.abspath(__file__)

# Recuperer le dossier parent du fichier actuel
parent_directory = os.path.dirname(current_file_path)

# ajouter un autre niveau parent si necessaire
project_directory = os.path.dirname(parent_directory)

sys.path.append(project_directory)

# Sauvegarder le repertoire de travail actuel
original_cwd = os.getcwd()

if os.getenv('PYCHARM_HOSTED') != '1':  # Si execute dans PyCharm
    # Simple ecriture de lignes vides pour PyChar
    # Verification de l'environnement
    # Changer vers le repertoire racine du projet pour VenvDependencyManager
    os.chdir(project_directory)

    import VenvDependencyManager

    VenvDependencyManager.main()

    # Revenir au repertoire original
    os.chdir(original_cwd)

# Port dédié au bridge Stake de CE process (pas le 10101 par défaut) -- DOIT être
# fixé avant tout import qui charge Functions.Bookmakers.router, dont le code au
# niveau module démarre déjà le bridge Stake sur le port par défaut dès l'import
# (avant même que session_init.py ait la main) : passer port=10103 seulement à
# l'appel dans session_init.py arrive trop tard, start_stake_bridge() est déjà
# idempotent sur le premier port utilisé (constaté le 2026-11-01). Même principe
# que le port 10102 dédié au bridge 1xBet de process_bets_loop.py (router.py) vs
# le 9999 par défaut de ce process -- process_bets_loop.py tourne déjà sur 10101
# en parallèle, même port = collision au bind.
os.environ.setdefault('STAKE_BRIDGE_PORT', '10103')

# Lance process_bets_loop.py en sous-processus au démarrage -- jusqu'ici il
# fallait le lancer séparément à la main en plus de main-1.py (demande
# explicite de l'utilisateur le 2026-11-02 : un seul script à lancer pour les
# deux). Idempotent : si le port 10101 (bridge Stake de process_bets_loop.py)
# répond déjà, un autre process_bets_loop.py tourne déjà ailleurs -- ne pas en
# relancer un second (collision de bind sinon). Non bloquant et non fatal : si
# ce lancement échoue, main-1.py continue quand même (le watcher reste la
# fonction principale de ce script). start_new_session=True détache le
# sous-processus du groupe de ce script : il continue de tourner même si
# main-1.py est arrêté (Ctrl+C), comme quand les deux étaient lancés à la main
# dans des terminaux séparés.
def _start_process_bets_loop():
    import socket
    try:
        with socket.create_connection(('127.0.0.1', 10101), timeout=0.5):
            print("[main-1] process_bets_loop.py déjà actif (port 10101 répond), pas de relance.")
            return
    except OSError:
        pass
    try:
        import subprocess
        log_dir = os.path.join(project_directory, 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'process_bets_loop.log')
        script_path = os.path.join(parent_directory, 'process_bets_loop.py')
        # Le sous-processus hérite par défaut de TOUT os.environ, y compris le
        # STAKE_BRIDGE_PORT=10103 fixé en haut de ce fichier pour CE process --
        # sans l'override ci-dessous, process_bets_loop.py essaierait de bind
        # 10103 au lieu de son port dédié 10101 (StakeBridge.py ne lit cette
        # var qu'une fois à l'import, avec '10101' comme défaut), collision
        # avec le bridge de main-1.py (constaté le 2026-11-06 au premier lancement
        # réel depuis un redémarrage de la machine, où aucun process_bets_loop.py
        # ne tournait déjà pour masquer le bug via l'idempotence ci-dessus).
        child_env = dict(os.environ)
        child_env['STAKE_BRIDGE_PORT'] = '10101'
        with open(log_path, 'ab') as log_file:
            subprocess.Popen(
                [sys.executable, script_path],
                cwd=project_directory,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env=child_env,
            )
        print(f"[main-1] process_bets_loop.py lancé en arrière-plan (log: {log_path})")
    except Exception as e:
        print(f"[main-1] ⚠️ Échec lancement process_bets_loop.py: {e}")


_start_process_bets_loop()

# Chargement des variables globales
import Functions.Functions_telegram
from Functions.Functions_telegram import send_telegram, send_telegram_photo
from Functions.PlacerCode import PlacerCode
from Functions.PlacerPari import placer_pari
from Functions.Logs.Logger import log, log_clear_line

import config

# Recuperer le nom du script
# Nom du fichier
file_name = os.path.basename(__file__)  # ou directement '40-1.py' pour l'exemple
# Separer le nom du fichier et l'extension
name_part = os.path.splitext(file_name)[0]
# Separer les parties du nom
parts = name_part.split('-')
if len(parts) > 1:
    config.scriptType = parts[0]  # Suppose que le type est avant le tiret
    config.script_num = int(parts[1])  # Suppose que le numero est avant le tiret
    localhost = str(config.scriptType) + str(config.script_num)
    config.localhost = ''.join(caractere for caractere in localhost if caractere.isdigit())
    if int(config.localhost) < 1024:
        config.localhost = 1024 + int(config.localhost)
    # Demander confirmation a l'utilisateur
    # Le lancement de Chrome est maintenant gere dans SetDriver.py
    log_clear_line(3)
else:
    log("Le format du nom du fichier est incorrect.", "error")
    exit()

# Chargement des functions
config.localhost = 43151
config.site_type = 'new_site'

from websocket_server import start_bridge, bridge
start_bridge()

# Vérification instance unique — tuer toute instance précédente du même script
import psutil as _psutil
_current_pid = os.getpid()
_parent_pid = os.getppid()
_script_name = os.path.basename(__file__)
for _proc in _psutil.process_iter(['pid', 'cmdline']):
    try:
        if _proc.pid == _current_pid or _proc.pid == _parent_pid:
            continue
        cmdline = ' '.join(_proc.info['cmdline'] or [])
        if _script_name in cmdline and 'python' in cmdline.lower():
            log(f"Instance précédente détectée (PID {_proc.pid}), arrêt...", "warning", clear=False)
            _proc.terminate()
            try:
                _proc.wait(timeout=5)
            except Exception:
                _proc.kill()
    except Exception:
        pass

# First install telethon using: pip install telethon
import ssl
import urllib3
from telethon import TelegramClient, events

# Configuration SSL pour eviter les erreurs de certificat
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'False'
os.environ['AIOHTTP_NO_EXTENSIONS'] = '1'

# Configurer SSL pour ignorer les certificats
ssl._create_default_https_context = ssl._create_unverified_context

# Desactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration specifique pour aiohttp (utilise par Telethon)

# Configuration supplementaire pour les requêtes

# Configuration globale pour requests
import requests.adapters
import sqlite3
from bs4 import BeautifulSoup

requests.adapters.DEFAULT_RETRIES = 3

from Functions import Functions_telegram
from Functions.getTextFromImageGPT import extraire_pari_depuis_image, extraire_pari_depuis_texte
from Functions.TelegramBetsAPI import send_bet_data_to_api, is_ignored_sender, get_pending_and_failed_bets
from Functions.AdrBettingScraper import scrape_adrbetting_coupons
from Functions.FrancePronosScraper import scrape_francepronos
from Functions.Bookmakers.session_init import init_bookmaker_sessions
from Functions.Bookmakers.router import place_best_bet, place_combined_bet
import Functions.Bookmakers.router as bookmaker_router
from Functions.GetMise import get_recommended_stake
from Functions.ProcessTelegramBets import preview_bet, place_bet_now, place_bet_manually
from Functions import RedisIPC

# Connexion manuelle aux bookmakers au démarrage
init_bookmaker_sessions()

# Declaration d'une variable globale qui va stocker les codes de paris
global codeList, betList
codeList = []
betList = []

# Informations d'identification pour l'API de Telegram
api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

# Identifiants de l'auxo bot et du groupe de notifications
auxo_bot_id = "820171667"
alertGroup = "-1001848207367"

# Configuration SSL specifique pour Telethon
import aiohttp


def filter_txt(txt):
    try:
        fichier = open(f"{config.projectPath}/conf/excluded_words.txt", "r")
        words = fichier.read()
        fichier.close()
        words = words.split('\n')
        for word in words:
            txt = txt.replace(word.strip().upper(), "")
        return txt
    except Exception as e:
        send_telegram(Functions.Functions_telegram.alertGroup, f"#E0007\nUne erreur est survenue : {e}")
        log(f"#E0007\nUne erreur est survenue : {e}", "error", clear=False)
        return txt


def bot_msg_handler(txt):
    # Gestion des commandes specifiques via regex
    if len(re.findall("/echecs", txt)) == 1:
        send_failed_bets_list()
    elif len(re.findall("/relance_scraping", txt)) == 1:
        relance_scraping()
    elif len(re.findall("/perte_globale", txt)) == 1:
        send_global_perte()


# ---- Commande /perte_globale : affichage en LECTURE SEULE de la perte globale -------
# GetJsonData.getGlobalPerte() interroge le même endpoint mais a des effets de bord
# (consomme la perte via SendGlobalPerte(), basé sur config.scriptType/mtt_recup du
# script APPELANT -- non définis dans ce process main-1.py, qui n'est pas un script
# martingale numéroté) -- inadapté pour une simple commande d'affichage. On refait ici
# juste le GET, sans toucher à rien côté serveur.
def fetch_global_perte():
    try:
        r = requests.get(f"{config.api_url}/strategy40A/get_global_perte.php", timeout=10)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        log(f"[PerteGlobale] Erreur récupération: {e}", "error", clear=False)
        return None


def send_global_perte():
    pertes = fetch_global_perte()
    if pertes is None:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "❌ Impossible de récupérer la perte globale (voir logs).")
        return
    msg = f"📉 Perte globale actuelle: {pertes.get('perte', '?')}€"

    # Pertes en cours par script martingale (015/150/15A/30A/300/5P/6P/etc.) -- lues
    # dans redis_fallback.sqlite (table `perte`, alimentée par RedisIPC.set_loss à
    # chaque jeu perdu). Affichées seulement si au moins un script a une perte non
    # nulle actuellement (séquence pas encore rattrapée).
    try:
        active_losses = RedisIPC.list_active_losses()
    except Exception as e:
        active_losses = []
        log(f"[PerteGlobale] Erreur lecture pertes scripts: {e}", "error", clear=False)
    if active_losses:
        msg += "\n\n🎾 Pertes en cours par script:"
        for script_type, loss, matchname, is_active in active_losses:
            suffixe = f" ({matchname})" if matchname else ""
            # Perte dont le process propriétaire n'est plus actif sur CE match : personne
            # ne la recouvrira (process reparti ailleurs ou arrêté) -- distingué pour ne
            # pas laisser croire qu'elle est encore "en cours" (signalé le 2026-11-08).
            if not is_active:
                suffixe += " ⚠️ abandonnée"
            msg += f"\n• {script_type}: {loss:.2f}€{suffixe}"

    Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, msg)


# ---- Commande /echecs : revue + relance manuelle des paris en erreur/non traités ----
# Flux par boutons inline (callback_query, cf. _poll_callback_queries plus bas -- ancien
# flux "répondre avec l'ID en texte" remplacé le 2026-11-07 à la demande utilisateur) :
#   1) /echecs -> liste des paris (#id + match + statut) + 1 bouton "🔄 #id" par pari
#   2) Clic sur un bouton -> callback "preview:<id>" -> nouveau message avec l'aperçu
#      (match + mise suggérée + mode simulation/réel) et 3 boutons Auto/Manuel/Annuler
#   3) Clic "🤖 Auto" -> callback "confirm:<id>:<mise>" -> placement automatisé réel (ou
#      simulé si SIMULATE_MODE) via le bookmaker, cf. place_bet_now
#      Clic "📝 Manuel" -> callback "manual:<id>:<mise>" -> AUCUN placement automatisé :
#      c'est l'utilisateur qui place lui-même chez le bookmaker, le bot se contente de
#      reporter le pari à AuxoTracker pour le suivi, cf. place_bet_manually
#      Clic "❌ Annuler" -> callback "cancel:<id>" -> rien n'est fait
#      Dans tous les cas le message est édité en place avec le résultat (boutons
#      retirés, pour empêcher un second clic de repasser le même pari)
_ECHECS_LIST_HEADER = "📋 PARIS EN ERREUR / NON TRAITÉS"


def _bet_display_text(match: dict) -> str:
    """
    Texte lisible généré par l'IA pour CE match -- priorité à `combined_label` (texte
    qui décrit TOUTES les jambes d'un combiné sur le même match, ex: "Double chance X2
    et Total Plus de 1.5"), puis `intitule` (ne décrit que la 1ère jambe pour un combiné
    -- insuffisant seul, cf. retour utilisateur du 2026-11-07 sur un Bet Builder AZ
    Alkmaar/Juventus où `intitule` omettait la jambe "Total Plus de 1.5"), puis repli sur
    `selection` (code technique, dernier recours). Les paris "plusieurs paris sur le même
    match empilés l'un en dessous de l'autre" (Bet Builder) sont fréquents -- toujours
    vérifier `combined_label` avant d'afficher quoi que ce soit à l'utilisateur.
    """
    return (match.get('combined_label') or '').strip() \
        or (match.get('intitule') or '').strip() \
        or match.get('selection', '?')


def _format_bet_line(bet):
    try:
        sel = json.loads(bet.get('selection') or '{}')
        matches = sel.get('matches', [])
        if matches:
            m = matches[0]
            desc = f"{m.get('equipe_1', '?')} vs {m.get('equipe_2', '?')} | {_bet_display_text(m)}"
            if len(matches) > 1:
                desc += f" (+{len(matches) - 1} jambes)"
        else:
            desc = "? vs ?"
    except Exception:
        desc = "(données illisibles)"
    if int(bet.get('processed') or 0) == 0:
        status = "⏳ non traité"
    else:
        status = f"❌ {bet.get('error') or 'échec'}"
    return f"#{bet.get('id')} {desc}\n   {status}"


def send_failed_bets_list():
    bets = get_pending_and_failed_bets(limit_each=20)
    if not bets:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, f"{_ECHECS_LIST_HEADER}\n\nAucun pari en attente ou en échec actuellement.")
        return
    # Un clavier inline Telegram reste lisible avec ~25 boutons (1 par ligne ici), même
    # limite d'affichage que l'ancienne liste texte -- pas besoin de la revoir à la baisse.
    shown = bets[:25]
    lines = [_format_bet_line(b) for b in shown]
    msg = f"{_ECHECS_LIST_HEADER}\n\n" + "\n\n".join(lines)
    if len(bets) > len(shown):
        msg += f"\n\n({len(bets) - len(shown)} de plus non affichés)"
    buttons = [[(f"🔄 Relancer #{b.get('id')}", f"preview:{b.get('id')}")] for b in shown]
    Functions_telegram.send_telegram_buttons(Functions_telegram.auxo_bot_id, msg, buttons)


_MANUAL_ENTRY_HEADER = "📝 SAISIE MANUELLE #"


def _remove_list_button(cq: dict, bet_id: int):
    """
    Retire le bouton "🔄 Relancer #<bet_id>" de la liste /echecs dès qu'il est cliqué
    (demande utilisateur du 2026-11-07 : éviter qu'un bouton déjà pris en charge reste
    cliquable dans la liste). Reconstruit le clavier à partir de celui que Telegram
    renvoie dans le callback_query lui-même (cq['message']['reply_markup']) -- pas besoin
    de connaître la liste complète par ailleurs.
    """
    msg = cq.get('message', {})
    chat_id = msg.get('chat', {}).get('id')
    message_id = msg.get('message_id')
    current_rows = msg.get('reply_markup', {}).get('inline_keyboard', [])
    target_cb = f"preview:{bet_id}"
    remaining_rows = [row for row in current_rows if not any(btn.get('callback_data') == target_cb for btn in row)]
    new_buttons = [[(btn['text'], btn['callback_data']) for btn in row] for row in remaining_rows]
    Functions_telegram.edit_telegram_reply_markup(chat_id, message_id, new_buttons)


def _is_photo_message(message: dict) -> bool:
    return bool(message.get('photo'))


def _edit_bet_message(chat_id, message_id, is_photo: bool, text: str, buttons=None):
    """
    Édite le texte/légende d'un message de pari -- dispatch vers editMessageCaption si
    le message est une photo (aperçu envoyé avec l'image du ticket) ou editMessageText
    sinon, Telegram n'acceptant pas editMessageText sur un message photo.

    Si l'édition échoue pour n'importe quelle raison (ex: Telegram rejette avec "message
    is not modified" si contenu+boutons sont identiques à l'existant, message trop
    ancien, etc.), envoie un NOUVEAU message à la place -- sans ce repli, un échec
    d'édition est totalement invisible pour l'utilisateur ("rien ne se passe" au clic,
    constaté le 2026-11-08 sur le bouton Manuel).
    """
    if is_photo:
        ok = Functions_telegram.edit_telegram_caption(chat_id, message_id, text, buttons)
    else:
        ok = Functions_telegram.edit_telegram_message(chat_id, message_id, text, buttons)
    if not ok:
        if buttons:
            Functions_telegram.send_telegram_buttons(chat_id, text, buttons)
        else:
            Functions_telegram.send_telegram(chat_id, text)


def handle_echecs_callback(action: str, parts: list, cq: dict):
    """
    Traite un clic sur bouton inline émis par /echecs (cf. _poll_callback_queries) :
    'preview' (choix d'un pari dans la liste) -> retire ce bouton de la liste puis
    affiche l'aperçu Auto/Manuel/Annuler, avec l'image source du ticket quand
    disponible (bet_data['image_base64'], stockée par l'API nichée dans la colonne
    `selection` -- cf. preview_bet) ; 'confirm' (Auto) -> placement automatisé ;
    'manual' -> demande la mise et la cote RÉELLES avant de valider (cf.
    _MANUAL_ENTRY_HEADER, suite gérée en texte dans my_event_handler car un bouton ne
    peut pas capturer une saisie libre) ; 'manual_confirm' -> enregistrement AuxoTracker
    avec les valeurs saisies ; 'cancel' -> rien. Toujours répondu via
    answer_callback_query pour retirer le spinner côté client Telegram.
    """
    message = cq.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    message_id = message.get('message_id')
    callback_id = cq.get('id')
    is_photo = _is_photo_message(message)

    if action == 'preview':
        bet_id = int(parts[1])
        Functions_telegram.answer_callback_query(callback_id)

        def _worker():
            try:
                preview = preview_bet(bet_id)
                if not preview:
                    Functions_telegram.send_telegram(chat_id, f"Pari #{bet_id} introuvable ou données corrompues.")
                    return
                matches = preview['matches']
                if matches:
                    m = matches[0]
                    texte = _bet_display_text(m)
                    desc = f"{m.get('equipe_1', '?')} vs {m.get('equipe_2', '?')}\n{texte}"
                    if len(matches) > 1:
                        desc += f"\n(+{len(matches) - 1} autres jambes du combiné)"
                else:
                    desc = "?"
                mode = "🧪 SIMULATION (aucun argent risqué)" if bookmaker_router.SIMULATE_MODE else "⚠️ ARGENT RÉEL"
                msg = (f"🎯 Pari #{bet_id}\n{desc}\n\n💰 Mise suggérée: {preview['mise']:.2f}€\n{mode}\n\n"
                       f"🤖 Auto : le bot cherche et place le pari lui-même\n"
                       f"📝 Manuel : tu le places toi-même chez le bookmaker (mise et cote RÉELLES demandées), "
                       f"le bot se contente de l'enregistrer dans AuxoTracker")
                mise_str = f"{preview['mise']:.2f}"
                buttons = [
                    [("🤖 Auto", f"confirm:{bet_id}:{mise_str}"), ("📝 Manuel", f"manual:{bet_id}:{mise_str}")],
                    [("❌ Annuler", f"cancel:{bet_id}")],
                ]
                # Image du ticket source si disponible (cf. docstring) -- repli texte
                # seul sinon (ticket ancien envoyé avant que l'IA n'attache l'image, ou
                # décodage échoué).
                image_b64 = preview['bet_data'].get('image_base64')
                sent_as_photo = False
                if image_b64:
                    try:
                        photo_bytes = base64.b64decode(image_b64)
                        sent_as_photo = Functions_telegram.send_telegram_photo_bytes(chat_id, photo_bytes, msg, buttons) is not None
                    except Exception as e:
                        log(f"[echecs] Décodage image échoué pour pari #{bet_id}: {e}", "warning", clear=False)
                sent_ok = sent_as_photo
                if not sent_as_photo:
                    sent_ok = Functions_telegram.send_telegram_buttons(chat_id, msg, buttons) is not None
                # Ne retire le bouton "🔄 Relancer #id" de la liste QU'APRÈS que l'aperçu
                # a bien été affiché -- demande utilisateur du 2026-11-08 : le bouton
                # doit disparaître une fois le pari et ses boutons affichés, pas avant
                # (sinon un échec d'envoi de l'aperçu laisserait l'utilisateur sans rien
                # à cliquer pour ce pari).
                if sent_ok:
                    _remove_list_button(cq, bet_id)
            except Exception as e:
                Functions_telegram.send_telegram(chat_id, f"Erreur lors de la préparation du pari #{bet_id}: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    elif action == 'confirm':
        bet_id = int(parts[1])
        mise = float(parts[2])
        Functions_telegram.answer_callback_query(callback_id, "⏳ Placement en cours...")
        _edit_bet_message(chat_id, message_id, is_photo, f"⏳ Placement du pari #{bet_id} en cours...", buttons=[])

        def _worker():
            try:
                result = place_bet_now(bet_id, mise)
                if result.get('success') and result.get('simulated'):
                    txt_res = f"🧪 [SIMULATION] Pari #{bet_id} serait placé sur {result.get('bookmaker')} @ {result.get('odds', '?')} (mise={mise:.2f}€) — non confirmé réellement."
                elif result.get('success'):
                    txt_res = f"✅ Pari #{bet_id} placé sur {result.get('bookmaker')} @ {result.get('odds', '?')} (mise={mise:.2f}€)"
                else:
                    txt_res = f"❌ Échec placement #{bet_id}: {result.get('error', 'erreur inconnue')}"
            except Exception as e:
                txt_res = f"Erreur lors du placement du pari #{bet_id}: {e}"
            _edit_bet_message(chat_id, message_id, is_photo, txt_res, buttons=[])

        threading.Thread(target=_worker, daemon=True).start()

    elif action == 'manual':
        # Ne place/n'enregistre RIEN ici -- demande d'abord la mise et la cote RÉELLES
        # utilisées par l'utilisateur chez le bookmaker (demande explicite du
        # 2026-11-07 : la mise suggérée et la cote du ticket peuvent différer de ce que
        # l'utilisateur a réellement obtenu). La suite (parsing de la réponse texte) est
        # gérée dans my_event_handler, repérée via _MANUAL_ENTRY_HEADER.
        bet_id = int(parts[1])
        # Conserve le texte/légende de l'aperçu (match + mise suggérée + mode, + l'image
        # si présente) au lieu de l'écraser -- demande utilisateur du 2026-11-08 : il
        # faut garder le pari sous les yeux pendant la saisie de la mise/cote réelles.
        existing_text = (message.get('caption') if is_photo else message.get('text')) or f"🎯 Pari #{bet_id}"
        Functions_telegram.answer_callback_query(callback_id)
        _edit_bet_message(
            chat_id, message_id, is_photo,
            f"{existing_text}\n\n"
            f"{_MANUAL_ENTRY_HEADER}{bet_id}\n"
            f"Réponds à CE message avec la mise réelle et la cote réelle utilisées, "
            f"séparées par un ESPACE (la virgule est gardée pour les décimales).\n"
            f"Ex: 12 1.75 ou 12,50 1.75",
            buttons=[]
        )

    elif action == 'manual_confirm':
        bet_id = int(parts[1])
        mise = float(parts[2])
        cote = float(parts[3])
        Functions_telegram.answer_callback_query(callback_id, "📝 Enregistrement...")
        _edit_bet_message(chat_id, message_id, is_photo, f"📝 Enregistrement manuel du pari #{bet_id}...", buttons=[])

        def _worker():
            try:
                result = place_bet_manually(bet_id, mise, odds_override=cote)
                if result.get('success'):
                    txt_res = (f"📝 Pari #{bet_id} enregistré en MANUEL @ {result.get('odds', '?')} "
                               f"(mise={mise:.2f}€) — reporté à AuxoTracker.")
                else:
                    txt_res = f"❌ Échec enregistrement manuel #{bet_id}: {result.get('error', 'erreur inconnue')}"
            except Exception as e:
                txt_res = f"Erreur lors de l'enregistrement manuel du pari #{bet_id}: {e}"
            _edit_bet_message(chat_id, message_id, is_photo, txt_res, buttons=[])

        threading.Thread(target=_worker, daemon=True).start()

    elif action == 'cancel':
        bet_id = parts[1] if len(parts) > 1 else '?'
        Functions_telegram.answer_callback_query(callback_id)
        _edit_bet_message(chat_id, message_id, is_photo, f"Annulé — pari #{bet_id} laissé en l'état (toujours visible dans /echecs).", buttons=[])


def handle_manual_entry_reply(reply_raw_text: str, user_txt: str):
    """
    Traite la réponse texte à l'invite "📝 SAISIE MANUELLE #<id>" (cf. action 'manual'
    de handle_echecs_callback) : extrait mise et cote réelles de la réponse libre de
    l'utilisateur, puis affiche un message de confirmation avant tout enregistrement
    (aucun appel à AuxoTracker ici).
    """
    id_match = re.search(rf'{re.escape(_MANUAL_ENTRY_HEADER)}(\d+)', reply_raw_text)
    if not id_match:
        return
    bet_id = int(id_match.group(1))

    # La virgule sert de décimale (convention FR, ex: "12,50") -- normalisée en point
    # AVANT de découper par nombre, donc jamais ambiguë avec un séparateur (qui est un
    # ESPACE, pas une virgule -- cf. retour utilisateur du 2026-11-08 : "12,1.75" avec
    # virgule-séparateur était mal interprété comme mise=12.1, cote=75).
    numbers = re.findall(r'\d+\.?\d*', user_txt.replace(',', '.'))
    if len(numbers) < 2:
        Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id,
                                          "Format non reconnu — réponds avec 2 nombres séparés par un espace (mise cote), ex: 12 1.75")
        return
    mise = float(numbers[0])
    cote = float(numbers[1])

    msg = f"📝 Confirme pour le pari #{bet_id} :\nMise réelle: {mise:.2f}€\nCote réelle: {cote:.2f}"
    buttons = [[("✅ Confirmer", f"manual_confirm:{bet_id}:{mise:.2f}:{cote:.2f}"), ("❌ Annuler", f"cancel:{bet_id}")]]
    Functions_telegram.send_telegram_buttons(Functions_telegram.auxo_bot_id, msg, buttons)


def _poll_callback_queries():
    """
    Poller getUpdates dédié aux clics de bouton inline (callback_query) -- infra ajoutée
    le 2026-11-07 pour remplacer le flux texte "répondre avec l'ID" de /echecs par des
    boutons cliquables (callback_query n'est délivré QUE via l'API Bot/getUpdates, jamais
    au client Telethon qui gère le reste du bot avec un compte UTILISATEUR -- cf.
    Functions_telegram.get_updates). Tourne dans son propre thread, indépendant du client
    Telethon : pas de conflit puisque chacun écoute un type d'update et un compte
    Telegram différents.
    """
    import time
    offset = None
    log("[CallbackPoller] Démarré (écoute des boutons /echecs)", "info", clear=False)
    while True:
        try:
            updates = Functions_telegram.get_updates(offset=offset, timeout=30)
            for upd in updates:
                offset = upd['update_id'] + 1
                cq = upd.get('callback_query')
                if not cq:
                    continue
                try:
                    data = cq.get('data', '') or ''
                    parts = data.split(':')
                    action = parts[0] if parts else ''
                    if action in ('preview', 'confirm', 'manual', 'manual_confirm', 'cancel'):
                        handle_echecs_callback(action, parts, cq)
                    else:
                        Functions_telegram.answer_callback_query(cq.get('id'))
                except Exception as e:
                    log(f"[CallbackPoller] Erreur traitement callback: {e}", "error", clear=False)
        except Exception as e:
            log(f"[CallbackPoller] Erreur boucle: {e}", "error", clear=False)
            time.sleep(5)
# ---------------------------------------------------------------------------------


# ---- Notification Telegram (canal alertGroup) d'un pari envoyé à l'API --------
def _format_pari_caption(label, match):
    """
    Texte lisible pour la notification Telegram d'un pari envoyé à l'API -- cf.
    _bet_display_text pour la logique de choix du texte (combined_label > intitule >
    selection). Retour utilisateur du 2026-11-07 : le texte affiché n'était pas le bon
    (manquait une jambe d'un Bet Builder/combiné sur le même match).
    """
    texte = _bet_display_text(match)
    return f"{label}\n{match.get('equipe_1')} vs {match.get('equipe_2')}\n🎯 {texte} @ {match.get('odds')}"


def _send_pari_notification(label, match, image=None):
    """
    Envoie la notification Telegram d'un pari envoyé à l'API, avec l'image source
    analysée en pièce jointe quand disponible (chemin local ou URL, cf.
    send_telegram_photo qui gère les deux) -- repli texte seul sinon.
    """
    caption = _format_pari_caption(label, match)
    if image:
        send_telegram_photo(Functions_telegram.alertGroup, image, caption)
    else:
        send_telegram(Functions_telegram.alertGroup, caption)
# ---------------------------------------------------------------------------------


# ---- Commande /relance_scraping : relance à la demande des 3 sources de scraping ----
# (AdrBetting VIP, France Pronos, Tempête) au lieu d'attendre leur déclenchement normal
# (message Telegram reçu pour les 2 premiers, polling toutes les 10 min pour Tempête).
# Les 3 fonctions réutilisées (run_adrbetting_scrape/run_francepronos_scrape/
# _tempete_check_once) sont définies plus bas dans ce fichier (étaient des closures
# imbriquées dans my_event_handler, factorisées le 2026-11-07 pour être appelables ici).
def relance_scraping():
    send_telegram(Functions_telegram.auxo_bot_id, "⏳ Relance du scraping (AdrBetting VIP, France Pronos, Tempête)...")

    def _worker():
        results = {}
        for nom, fn in (("AdrBetting VIP", lambda: run_adrbetting_scrape("Relance manuelle /relance_scraping")),
                         ("France Pronos", lambda: run_francepronos_scrape("Relance manuelle /relance_scraping")),
                         ("Tempête", _tempete_check_once)):
            try:
                results[nom] = fn()
            except Exception as e:
                log(f"[Relance scraping] Erreur {nom}: {e}", "error", clear=False)
                results[nom] = None

        def _fmt(n):
            return f"{n} pari(s) envoyé(s)" if n is not None else "❌ erreur (voir logs)"

        msg = (
            "✅ Relance terminée\n"
            f"🎰 AdrBetting VIP: {_fmt(results['AdrBetting VIP'])}\n"
            f"🇫🇷 France Pronos: {_fmt(results['France Pronos'])}\n"
            f"🌪️ Tempête: {_fmt(results['Tempête'])}"
        )
        send_telegram(Functions_telegram.auxo_bot_id, msg)

    threading.Thread(target=_worker, daemon=True).start()
# ---------------------------------------------------------------------------------


def add_word_to_replace(word):
    try:
        words = word.split('\n')
        for word in words:
            word = word.strip().upper()
            codes = open(f"{config.projectPath}/conf/excluded_words.txt", "a")
            codes.write('\n' + word)
            codes.close()
            log("word ADDED  : " + word, "info", clear=False)
        return True
    except Exception as e:
        send_telegram(Functions.Functions_telegram.alertGroup, f"#E00017\nUne erreur est survenue : {e}")
        log(f"#E00017\nUne erreur est survenue : {e}", "error", clear=False)
        return False


def delete_word_to_replace(word):
    try:
        words = word.split('\n')
        used_codes = ""
        codes = open(f"{config.projectPath}/conf/excluded_words.txt", "r")
        used_codes = codes.read()
        codes.close()
        updates_used_codes = used_codes  # Initialiser la variable
        for word in words:
            word = word.strip().upper()
            updates_used_codes = updates_used_codes.replace('\n' + word, '')
        codes = open(f"{config.projectPath}/conf/excluded_words.txt", "w")
        codes.write(updates_used_codes)
        codes.close()
        log("CODES UPDATED : " + updates_used_codes, "info", clear=False)
        return True
    except Exception as e:
        send_telegram(Functions_telegram.alertGroup, f"#E00018\nUne erreur est survenue : {e}")
        log(f"#E00018\nUne erreur est survenue : {e}", "error", clear=False)
        return False


def extract_code_1XBET(txt):
    """
    Extrait un code 1XBET de 5 caractères alphanumeriques en majuscules depuis un texte.
    
    Args:
        txt (str): Le texte a analyser
        
    Returns:
        list: Liste contenant le code trouve si exactement un code est detecte
        bool: False si aucun code ou plusieurs codes sont trouves
    """
    txt = filter_txt(txt)

    # Recherche de codes de 5 caractères alphanumeriques en majuscules uniquement
    # Le pattern \b[A-Z0-9]{5}\b recherche exactement 5 caractères consecutifs
    # composes uniquement de lettres majuscules (A-Z) et de chiffres (0-9)
    # entoures de delimiteurs de mots (\b)
    codes = re.findall(r"\b[A-Z0-9]{5}\b", txt)
    # Retourne le code uniquement si exactement un code est trouve
    if len(codes) == 1:
        log(f"Codes trouves : {codes}", "info")
        return codes
    else:
        return False


# --- Vérification périodique des images publiées sur tempetebetting.com ---
TEMPETE_BASE_URL = "https://tempetebetting.com/wp-content/uploads/{year}/{month:02d}/"
TEMPETE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tempete_images.db")
TEMPETE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _tempete_create_db():
    conn = sqlite3.connect(TEMPETE_DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_url TEXT UNIQUE,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def _tempete_get_image_links(url):
    try:
        r = requests.get(url, headers=TEMPETE_HEADERS, timeout=15, verify=False)
        if r.status_code != 200:
            log(f"[Tempête] Accès échoué {url} ({r.status_code})", "warning", clear=False)
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
        return [l for l in links if re.match(r'.*\.(jpg|jpeg|png)$', l, re.IGNORECASE)]
    except Exception as e:
        log(f"[Tempête] Erreur récupération liens: {e}", "error", clear=False)
        return []


def _tempete_filter_originals(image_links):
    pattern = re.compile(r'(-\d+x\d+)?\.(jpg|jpeg|png)$', re.IGNORECASE)
    originals = set()
    for link in image_links:
        originals.add(pattern.sub(r'.\2', link))
    return list(originals)


def _tempete_filter_new(image_urls):
    """Retourne les URLs pas encore en base, SANS les y insérer — l'insertion
    n'a lieu qu'après un traitement réussi (cf. _tempete_mark_seen), pour
    qu'une image dont le traitement échoue/bloque soit retentée au prochain
    cycle au lieu d'être perdue silencieusement."""
    conn = sqlite3.connect(TEMPETE_DB_PATH)
    seen = {row[0] for row in conn.execute("SELECT image_url FROM images")}
    conn.close()
    return [u for u in image_urls if u not in seen]


def _tempete_mark_seen(url):
    conn = sqlite3.connect(TEMPETE_DB_PATH)
    try:
        conn.execute("INSERT INTO images (image_url) VALUES (?)", (url,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def _tempete_check_once() -> int:
    """
    Un passage de vérification des nouvelles images Tempête (tempetebetting.com) --
    factorisée depuis check_tempete_images() (qui ne fait plus que boucler dessus) pour
    être réutilisable depuis la commande Telegram /relance_scraping (cf. bot_msg_handler).
    Retourne le nombre de paris effectivement envoyés à l'API.
    """
    import time
    sent_count = 0
    try:
        now = datetime.datetime.now()
        url = TEMPETE_BASE_URL.format(year=now.year, month=now.month)
        links = _tempete_get_image_links(url)
        originals = _tempete_filter_originals(links)
        new_images = _tempete_filter_new(originals)
        if new_images:
            log(f"[Tempête] {len(new_images)} nouvelle(s) image(s) détectée(s)", "info", clear=False)
            for i, img_name in enumerate(new_images):
                if i > 0:
                    time.sleep(3)
                full_url = img_name if img_name.startswith('http') else url + img_name
                try:
                    r = requests.get(full_url, headers=TEMPETE_HEADERS, timeout=15, verify=False)
                    if r.status_code != 200:
                        log(f"[Tempête] Téléchargement échoué: {img_name} ({r.status_code})", "warning", clear=False)
                        continue
                    # parent_directory (calculé une fois au niveau module, pas __file__
                    # ré-évalué ici) -- ce thread dédié (threading.Thread, pas asyncio)
                    # a vu __file__ devenir NameError de façon répétée et non reproductible
                    # en isolation (constaté plusieurs fois, dont le 2026-11-04 : échec
                    # systématique sur chaque image Tempête). parent_directory est une
                    # simple variable Python déjà résolue, insensible à ce problème.
                    temp_dir = os.path.join(parent_directory, 'media')
                    os.makedirs(temp_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_path = os.path.join(temp_dir, f"tempete_{timestamp}.jpg")
                    with open(img_path, 'wb') as f:
                        f.write(r.content)
                    log(f"[Tempête] Image téléchargée: {img_name}", "info", clear=False)
                    result = extraire_pari_depuis_image(img_path, "Tempête Betting")
                    try:
                        pari_dict = json.loads(result)
                        pari_dict["tipster"] = "TEMPÊTE BETTING"
                        matches = pari_dict.get("matches", [])
                        if matches:
                            api_success = send_bet_data_to_api(pari_dict, message_original=full_url, sender_username="TEMPÊTE BETTING", image_path=img_path)
                            if api_success:
                                sent_count += 1
                                for match in matches:
                                    log(f"[Tempête] ✅ Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                                    _send_pari_notification("🌪️ TEMPÊTE BETTING", match, img_path)
                            else:
                                log(f"[Tempête] ❌ Échec envoi ({len(matches)} match(s))", "error", clear=False)
                        else:
                            log(f"[Tempête] Aucun match extrait de {img_name}", "warning", clear=False)
                        # Traitement réussi (avec ou sans match détecté) : marquer vue
                        # seulement maintenant, pour qu'un échec plus haut (timeout OCR,
                        # JSON invalide) soit retenté au prochain cycle au lieu d'être
                        # perdu silencieusement pour toujours.
                        _tempete_mark_seen(img_name)
                    except json.JSONDecodeError as e:
                        log(f"[Tempête] Erreur JSON OCR: {e}", "error", clear=False)
                    finally:
                        if os.path.exists(img_path):
                            os.remove(img_path)
                except Exception as e:
                    log(f"[Tempête] Erreur traitement image {img_name}: {e}", "error", clear=False)
        else:
            log("[Tempête] Aucune nouvelle image", "info", clear=False)
    except Exception as e:
        log(f"[Tempête] Erreur boucle principale: {e}", "error", clear=False)
    return sent_count


def run_adrbetting_scrape(txt: str = "Relance manuelle") -> int:
    """
    Scrape AdrBetting VIP (coupons "PRONOS EN LIGNE") et traite chaque coupon trouvé --
    factorisée depuis une closure imbriquée dans my_event_handler pour être réutilisable
    depuis la commande Telegram /relance_scraping. `txt` accompagne l'OCR/l'envoi API
    comme le ferait le message Telegram déclencheur normalement.
    Retourne le nombre de paris effectivement envoyés à l'API.
    """
    sent_count = 0
    try:
        coupons = scrape_adrbetting_coupons()  # List[tuple(filepath, tipster)]
        if not coupons:
            log("[AdrBetting] Aucun coupon récupéré", "warning", clear=False)
            return 0
        log(f"[AdrBetting] {len(coupons)} coupon(s) récupéré(s), lancement OCR...", "info", clear=False)
        for img_path, tipster in coupons:
            try:
                log(f"[AdrBetting] OCR [{tipster}]: {os.path.basename(img_path)}", "info", clear=False)
                result = extraire_pari_depuis_image(img_path, txt)
                pari_dict = json.loads(result)
                pari_dict["tipster"] = tipster
                matches = pari_dict.get("matches", [])
                if matches:
                    api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username=tipster, image_path=img_path)
                    if api_success:
                        sent_count += 1
                        for match in matches:
                            log(f"[AdrBetting] ✅ [{tipster}] Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                            _send_pari_notification(f"🎰 {tipster}", match, img_path)
                    else:
                        log(f"[AdrBetting] ❌ [{tipster}] Échec envoi pari ({len(matches)} match(s))", "error", clear=False)
                if os.path.exists(img_path):
                    os.remove(img_path)
            except json.JSONDecodeError as e:
                log(f"[AdrBetting] Erreur JSON OCR [{tipster}]: {e}", "error", clear=False)
            except Exception as e:
                log(f"[AdrBetting] Erreur traitement coupon {img_path}: {e}", "error", clear=False)
    except Exception as e:
        log(f"[AdrBetting] Erreur scraping: {e}", "error", clear=False)
    return sent_count


def run_francepronos_scrape(txt: str = "Relance manuelle") -> int:
    """
    Scrape FrancePronos et traite chaque pronostic trouvé -- factorisée depuis une
    closure imbriquée dans my_event_handler pour être réutilisable depuis la commande
    Telegram /relance_scraping. Retourne le nombre de paris effectivement envoyés à l'API.
    """
    sent_count = 0
    try:
        pronos = scrape_francepronos()
        if not pronos:
            log("[FrancePronos] Aucun pronostic récupéré", "warning", clear=False)
            return 0
        log(f"[FrancePronos] {len(pronos)} pronostic(s) récupéré(s), passage à l'IA...", "info", clear=False)
        for raw in pronos:
            try:
                # Formatter le texte brut pour l'IA
                texte = (
                    f"Sport: {raw.get('sport', '')}\n"
                    f"Date: {raw.get('date', '')}\n"
                    f"Match: {raw.get('intitule', raw.get('equipe_1','') + ' vs ' + raw.get('equipe_2',''))}\n"
                    f"Équipe 1: {raw.get('equipe_1', '')}\n"
                    f"Équipe 2: {raw.get('equipe_2', '')}\n"
                    f"Sélection: {raw.get('selection', '')}\n"
                    f"Cote: {raw.get('odds', '')}\n"
                    f"Tipster: FrancePronos"
                )
                result = extraire_pari_depuis_texte(texte, txt)
                pari_dict = json.loads(result)
                pari_dict["tipster"] = "FrancePronos"
                matches = pari_dict.get("matches", [])
                if matches:
                    api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username="FrancePronos")
                    if api_success:
                        sent_count += 1
                        for match in matches:
                            log(f"[FrancePronos] ✅ Pari envoyé: {match.get('equipe_1')} vs {match.get('equipe_2')}", "info", clear=False)
                            _send_pari_notification("🇫🇷 France Pronos", match, raw.get('image'))
                    else:
                        log(f"[FrancePronos] ❌ Échec envoi ({len(matches)} match(s))", "error", clear=False)
            except json.JSONDecodeError as e:
                log(f"[FrancePronos] Erreur JSON IA: {e}", "error", clear=False)
            except Exception as e:
                log(f"[FrancePronos] Erreur traitement prono: {e}", "error", clear=False)
    except Exception as e:
        log(f"[FrancePronos] Erreur scraping: {e}", "error", clear=False)
    return sent_count


def process_channel_image(chat_title: str, txt: str, image_path: str) -> int:
    """
    Pipeline OCR + envoi API + notification pour une image reçue d'un canal "public"
    (AdrBetting, Tennistiqueur, TEMPÊTE BETTING, France Pronos Live, Auxo1XBOT) --
    factorisée depuis le bloc `elif has_media:` de my_event_handler (qui l'appelle pour
    chaque NOUVEAU message) pour être réutilisée aussi par relance_canaux_backlog()
    (relecture de l'historique récent, cf. commande Telegram /relance_canaux).
    Ne supprime PAS `image_path` -- laissé à l'appelant, qui gère le cycle de vie du
    fichier différemment selon le cas (répertoire temp partagé vs fichier dédié).
    Retourne le nombre de paris effectivement envoyés à l'API.
    """
    sent_count = 0
    result = extraire_pari_depuis_image(image_path, txt)
    try:
        pari_dict = json.loads(result)
        pari_dict["tipster"] = chat_title
        matches = pari_dict.get("matches", [])
        if not matches:
            return 0
        if chat_title == "France Pronos Live":
            # Live : placement direct, pas de queue API (réactivité) --
            # _place_live_bet_direct gère aussi la notification Telegram
            # et le dédoublonnage avec le texte explicatif qui suit souvent.
            _place_live_bet_direct(pari_dict, "image")
            sent_count = 1
        elif chat_title == "TEMPÊTE BETTING ®️" and len(matches) > 1:
            # TEMPÊTE BETTING combine souvent plusieurs picks dans un même
            # ticket/message (ex: "PALIER X MONTANTE" = plusieurs victoires
            # combinées). On envoie un pari séparé par match au lieu d'un seul
            # pari multi-matchs, pour que chacun soit évalué/parié
            # individuellement côté router (sinon len(matches)>1 le fait
            # traiter comme un seul pari combiné, cf. place_combined_bet).
            api_success = True
            for match in matches:
                single_pari = {**pari_dict, "matches": [match]}
                if not send_bet_data_to_api(single_pari, message_original=txt, sender_username=chat_title, image_path=image_path):
                    api_success = False
            if api_success:
                sent_count = len(matches)
                for match in matches:
                    _send_pari_notification(f"📩 {chat_title}", match, image_path)
        else:
            api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username=chat_title, image_path=image_path)
            if api_success:
                sent_count = len(matches)
                for match in matches:
                    _send_pari_notification(f"📩 {chat_title}", match, image_path)
    except Exception as _e:
        log(f"[Image] [{chat_title}] Erreur traitement OCR: {_e}", "error", clear=False)
    return sent_count


# ---- Commande /relance_canaux : relecture de l'historique récent des canaux PUBLICS --
# (AdrBetting public -- pas VIP, Tennistiqueur, TEMPÊTE BETTING) pour rattraper un
# message de prono manqué (ex: bot hors-ligne au moment de l'envoi) -- contrairement
# au flux normal (my_event_handler), qui ne réagit qu'aux NOUVEAUX messages reçus en
# direct et ne revient jamais sur l'historique.
BACKLOG_CHANNELS = {
    "AdrBetting":          "TICKET SAFE PUBLIC",
    "Tennistiqueur 🎾":    "CONFIANCE",
    "TEMPÊTE BETTING ®️":  ("PRONO DU JOUR", "PALIER"),
}

# chat_id par titre de canal, peuplé au fil des messages live reçus par my_event_handler
# -- cf. commentaire sur chat_title dans my_event_handler pour pourquoi ceci est plus
# fiable que client.iter_dialogs() pour relance_canaux_backlog().
_known_channel_entities: dict = {}

CHANNEL_BACKLOG_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channel_backlog_seen.db")


def _backlog_create_db():
    conn = sqlite3.connect(CHANNEL_BACKLOG_DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS seen_messages (
        channel TEXT,
        message_id INTEGER,
        seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (channel, message_id)
    )''')
    conn.commit()
    conn.close()


def _backlog_is_seen(channel, message_id) -> bool:
    conn = sqlite3.connect(CHANNEL_BACKLOG_DB_PATH)
    row = conn.execute('SELECT 1 FROM seen_messages WHERE channel=? AND message_id=?', (channel, message_id)).fetchone()
    conn.close()
    return row is not None


def _backlog_mark_seen(channel, message_id):
    conn = sqlite3.connect(CHANNEL_BACKLOG_DB_PATH)
    conn.execute('INSERT OR IGNORE INTO seen_messages (channel, message_id) VALUES (?, ?)', (channel, message_id))
    conn.commit()
    conn.close()


def _backlog_message_matches(chat_title: str, msg_text: str) -> bool:
    """Même logique de condition textuelle que IMAGE_CHANNELS dans my_event_handler."""
    required_text = BACKLOG_CHANNELS.get(chat_title)
    if required_text is None:
        return True
    conditions = required_text if isinstance(required_text, (list, tuple)) else (required_text,)
    return any(c.upper() in (msg_text or "").upper() for c in conditions)


async def relance_canaux_backlog(limit_per_channel: int = 20):
    """
    Parcourt les `limit_per_channel` derniers messages des canaux PUBLICS AdrBetting,
    Tennistiqueur et TEMPÊTE BETTING et retraite toute image de prono pas encore vue
    (dédoublonnage persistant via channel_backlog_seen.db -- un message déjà vu n'est
    jamais retraité, même après plusieurs appels de /relance_canaux).
    """
    from telethon.tl.types import MessageMediaDocument
    _backlog_create_db()
    Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "⏳ Vérification de l'historique récent (AdrBetting, Tennistiqueur, TEMPÊTE BETTING)...")

    results = {}
    for chat_title in BACKLOG_CHANNELS:
        scanned = 0
        found = 0
        sent = 0
        try:
            # Priorité au chat_id déjà vu en live (fiable) -- repli sur iter_dialogs()
            # seulement si aucun message de ce canal n'est encore arrivé depuis le
            # dernier redémarrage (cf. _known_channel_entities).
            entity = _known_channel_entities.get(chat_title)
            if entity is None:
                async for dialog in client.iter_dialogs():
                    if dialog.title == chat_title:
                        entity = dialog.entity
                        break
            if entity is None:
                log(f"[Backlog] Canal '{chat_title}' introuvable (ni vu en live, ni dans les dialogues)", "warning", clear=False)
                results[chat_title] = None
                continue

            messages = await client.get_messages(entity, limit=limit_per_channel)
            scanned = len(messages)
            for msg in messages:
                if not msg.media or _backlog_is_seen(chat_title, msg.id):
                    continue
                msg_text = msg.raw_text or ""
                if not _backlog_message_matches(chat_title, msg_text):
                    _backlog_mark_seen(chat_title, msg.id)
                    continue
                if isinstance(msg.media, MessageMediaDocument):
                    doc = msg.media.document
                    if any(getattr(attr, 'mime_type', '') == 'image/gif' or str(type(attr).__name__) == 'DocumentAttributeAnimated' for attr in (doc.attributes or [])):
                        _backlog_mark_seen(chat_title, msg.id)
                        continue

                found += 1
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = os.path.join(parent_directory, 'media')
                os.makedirs(temp_dir, exist_ok=True)
                image_path = os.path.join(temp_dir, f"backlog_{chat_title.replace(' ', '_')}_{msg.id}_{timestamp}.jpg")
                try:
                    await msg.download_media(file=image_path)
                    sent += process_channel_image(chat_title, msg_text, image_path)
                except Exception as e:
                    log(f"[Backlog] [{chat_title}] Erreur traitement message {msg.id}: {e}", "error", clear=False)
                finally:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    _backlog_mark_seen(chat_title, msg.id)
            results[chat_title] = (scanned, found, sent)
        except Exception as e:
            log(f"[Backlog] Erreur canal '{chat_title}': {e}", "error", clear=False)
            results[chat_title] = None

    lines = ["✅ Vérification terminée"]
    for chat_title, r in results.items():
        if r is None:
            lines.append(f"❌ {chat_title}: canal introuvable ou erreur (voir logs)")
        else:
            sc, f, s = r
            lines.append(f"📩 {chat_title}: {sc} message(s) scanné(s), {f} image(s) nouvelle(s), {s} pari(s) envoyé(s)")
    Functions_telegram.send_telegram(Functions_telegram.auxo_bot_id, "\n".join(lines))
# ---------------------------------------------------------------------------------


def check_tempete_images():
    import time
    _tempete_create_db()
    log("[Tempête] Thread de vérification des images démarré", "info", clear=False)
    while True:
        _tempete_check_once()
        time.sleep(600)  # Vérification toutes les 10 minutes


# Patch pour aiohttp afin de desactiver la verification SSL
original_create_connection = aiohttp.TCPConnector._create_connection


async def patched_create_connection(self, req, traces, timeout):
    return await original_create_connection(self, req, traces, timeout)


# Appliquer le patch
aiohttp.TCPConnector._create_connection = patched_create_connection

# Initialisation du client Telegram avec paramètres robustes
try:
    client = TelegramClient(
        '2',
        api_id,
        api_hash,
        connection_retries=5,
        retry_delay=1,
        timeout=30,
        request_retries=5,
        auto_reconnect=True,
        device_model="Desktop",
        system_version="Windows 10",
        app_version="1.0",
        lang_code="fr",
        system_lang_code="fr"
    )
    log("Client Telegram initialise avec succès", "success", clear=False)
except Exception as e:
    log(f"Erreur lors de l'initialisation du client Telegram : {e}", "error", clear=False)
    # Fallback vers une configuration simple
    client = TelegramClient('2', api_id, api_hash)


# --- Placement direct pour le canal live "France Pronos Live" -------------------
# Demande utilisateur du 2026-10-17 : contrairement aux autres canaux (stockés via
# send_bet_data_to_api puis traités par le poll de 30s de process_bets_loop.py),
# les tips de ce canal doivent être placés IMMÉDIATEMENT -- un pari live perd de sa
# valeur (cote qui bouge, marché qui se ferme) à chaque seconde d'attente.
# Les tips y arrivent parfois en image, parfois en texte seul, et une image est
# généralement suivie d'un texte explicatif pour LE MÊME pari -- sans dédoublonnage
# il serait placé deux fois. _is_duplicate_live_bet() filtre sur (equipe_1, equipe_2,
# selection) avec une fenêtre de 5 minutes.
_LIVE_BET_DEDUP_TTL = datetime.timedelta(minutes=5)
_live_bet_seen = {}


def _live_bet_key(match):
    e1 = (match.get('equipe_1') or '').strip().lower()
    e2 = (match.get('equipe_2') or '').strip().lower()
    sel = (match.get('selection') or '').strip().lower()
    return f"{e1}|{e2}|{sel}"


def _is_duplicate_live_bet(matches):
    now = datetime.datetime.now()
    for k in list(_live_bet_seen.keys()):
        if now - _live_bet_seen[k] > _LIVE_BET_DEDUP_TTL:
            del _live_bet_seen[k]
    combo_key = "||".join(sorted(_live_bet_key(m) for m in matches))
    if combo_key in _live_bet_seen:
        return True
    _live_bet_seen[combo_key] = now
    return False


def _format_live_matches(matches):
    return " + ".join(f"{m.get('equipe_1')} vs {m.get('equipe_2')} | {m.get('selection')}" for m in matches)


def _place_live_bet_direct(pari_dict, source_label):
    """
    Placement DIRECT (sans passer par la queue API telegram_bets) pour "France
    Pronos Live". Lancé dans un thread séparé car place_best_bet/place_combined_bet
    sont bloquants (pilotage Selenium/extension Chrome) -- sinon ça gèlerait la
    réception des autres messages Telegram pendant tout le placement.
    """
    matches = pari_dict.get("matches", [])
    if not matches:
        return
    tipster = pari_dict.get("tipster", "France Pronos Live")
    if _is_duplicate_live_bet(matches):
        log(f"[FrancePronosLive] Doublon ignoré ({source_label}) : {_format_live_matches(matches)}", "warning", clear=False)
        return

    def _run():
        try:
            ref_odds = matches[0].get("odds")
            try:
                stake_data = get_recommended_stake(cote=ref_odds, tipster=tipster)
                mise = float(stake_data.get("recommended_stake") or 1.0)
            except Exception:
                mise = 1.0
            log(f"[FrancePronosLive] 🎯 Placement direct ({source_label}, mise={mise}€) : {_format_live_matches(matches)}", "info", clear=False)
            if len(matches) > 1:
                result = place_combined_bet(matches, mise)
            else:
                match = dict(matches[0])
                match["tipster"] = tipster
                match["mise"] = mise
                result = place_best_bet(match)
            if result.get("success"):
                log(f"[FrancePronosLive] ✅ Pari placé sur {result.get('bookmaker')} @ {result.get('odds', '?')}", "info", clear=False)
                for m in matches:
                    msg = f"⚡ France Pronos Live (direct)\n{m.get('equipe_1')} vs {m.get('equipe_2')}\n🎯 {m.get('selection')} @ {result.get('odds', '?')}"
                    send_telegram(Functions_telegram.alertGroup, msg)
            else:
                log(f"[FrancePronosLive] ❌ Échec placement direct : {result.get('error', '')}", "error", clear=False)
        except Exception as e:
            log(f"[FrancePronosLive] Erreur placement direct : {e}", "error", clear=False)

    threading.Thread(target=_run, daemon=True).start()
# ----------------------------------------------------------------------------------


# Gestionnaire d'evenements pour detecter les nouveaux messages Telegram
@client.on(events.NewMessage())
async def my_event_handler(event):
    try:
        e = event
    except Exception as e:
        pass

    success = 0  # Indicateur pour contrôler le succès du traitement
    if success == 0:
        while success == 0:
            print('test')
            success = 1  # Passe a 1 une fois que le traitement est reussi
            # Recuperation et affichage du pseudo de l'expediteur
            sender = await event.get_sender()
            txt = event.raw_text  # Convertit le texte en majuscules pour faciliter le traitement
            
            # Filtre pour ignorer les messages contenant certains mots/phrases
            try:
                with open(f"{config.projectPath}/conf/ignored_messages.txt", "r", encoding='utf-8') as fichier:
                    ignored_phrases = [line.strip().lower() for line in fichier.read().split('\n') if line.strip() and not line.strip().startswith('#')]
                    
                # Vérifier si le message contient une phrase à ignorer
                txt_lower = txt.lower()
                for phrase in ignored_phrases:
                    if phrase in txt_lower:
                        log(f"Message ignoré car contient '{phrase}': {txt[:50]}...", "info", clear=False)
                        return  # Ignorer ce message
                        
            except FileNotFoundError:
                # Si le fichier n'existe pas, continuer normalement
                log(f"Fichier ignored_messages.txt non trouvé, aucun filtrage appliqué", "warning", clear=False)

            if str(event.chat_id) == '1910869556':
                bot_msg_handler(txt)
                if len(re.findall("/relance_canaux", txt)) == 1:
                    await relance_canaux_backlog()
                reply = await event.get_reply_message()  # Recupère le message auquel il est repondu
                if reply:
                    reply_raw_text = reply.raw_text  # Texte du message de reponse
                    # Cas où on répond à l'invite "📝 SAISIE MANUELLE #<id>" avec la
                    # mise et la cote réelles -- suite de l'action 'manual' de
                    # handle_echecs_callback (un bouton ne peut pas capturer une saisie
                    # libre, cf. _MANUAL_ENTRY_HEADER).
                    if _MANUAL_ENTRY_HEADER in reply_raw_text:
                        handle_manual_entry_reply(reply_raw_text, txt)

            if event.chat and hasattr(event.chat, 'title') and event.chat.title == 'AdrBetting VIP':
                txt_upper = txt.upper()

                # Ticket Jackpot : pari combiné (parfois plusieurs événements sur le même
                # match) posté directement en image dans le canal, hors du flux de
                # scraping website "PRONOS EN LIGNE". On le garde comme UN SEUL pari
                # combiné (pas de split par jambe comme pour Tempête/PALIER) — le JSON
                # combined_events/matches multi-matchs existant route déjà correctement
                # côté router (SGM Stake si même match, combiné Lollybet si multi-matchs).
                if "TICKET JACKPOT" in txt_upper and event.message.media is not None:
                    log("[AdrBetting] Ticket Jackpot détecté — OCR direct de l'image", "info", clear=False)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_dir = os.path.join(parent_directory, 'media')
                    os.makedirs(temp_dir, exist_ok=True)
                    image_path = os.path.join(temp_dir, f"jackpot_{timestamp}.jpg")
                    await event.message.download_media(file=image_path)
                    try:
                        result = extraire_pari_depuis_image(image_path, txt)
                        pari_dict = json.loads(result)
                        pari_dict["tipster"] = "AdrBetting VIP"
                        matches = pari_dict.get("matches", [])
                        if matches:
                            api_success = send_bet_data_to_api(pari_dict, message_original=txt, sender_username="AdrBetting VIP", image_path=image_path)
                            if api_success:
                                for match in matches:
                                    _send_pari_notification("🎰 AdrBetting VIP Jackpot", match, image_path)
                            else:
                                log("[AdrBetting] ❌ Échec envoi pari Jackpot", "error", clear=False)
                    except json.JSONDecodeError as e:
                        log(f"[AdrBetting] Erreur JSON OCR Jackpot: {e}", "error", clear=False)
                    except Exception as e:
                        log(f"[AdrBetting] Erreur traitement Jackpot: {e}", "error", clear=False)
                    finally:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    return

                if "PRONOS EN LIGNE" not in txt_upper:
                    log(f"[AdrBetting] Message ignoré (pas de 'PRONOS EN LIGNE' ni 'TICKET JACKPOT')", "info", clear=False)
                    return
                log(f"[AdrBetting] Message reçu du canal VIP — lancement du scraping", "info", clear=False)
                # Lancer le scraping dans un thread séparé pour ne pas bloquer l'event loop Telegram
                threading.Thread(target=run_adrbetting_scrape, args=(txt,), daemon=True).start()
                return  # Ne pas traiter le message Telegram normalement

            if event.chat and hasattr(event.chat, 'title') and event.chat.title == 'France Pronos':
                if "www.france-pronos.com/?source=telegram" not in txt.lower():
                    log("[FrancePronos] Message ignoré (pas de lien france-pronos.com)", "info", clear=False)
                    return
                log("[FrancePronos] Message reçu — lancement du scraping", "info", clear=False)
                threading.Thread(target=run_francepronos_scrape, args=(txt,), daemon=True).start()
                return  # Ne pas traiter le message Telegram normalement
            if sender or event.chat_id:
                if is_ignored_sender(sender.username if sender else None, event.chat_id):
                    log("Expediteur ignore, message ignore", "warning", clear=True)
                    return  # Ignorer le message si l'expediteur est dans la liste d'ignorés
                # Affiche le nom d'utilisateur s'il existe, sinon le nom complet
                if sender.username:
                    log(f'Pseudo de l\'expediteur: {sender.username}', "info", clear=False)
                else:
                    log(f'Channel ID: {event.chat_id} - {event.chat.title if event.chat and hasattr(event.chat, "title") else "N/A"}',
                        "info", clear=False)
                # Chaque fois qu'un nouveau message est reçu, cette fonction est declenchee
                log('Nouvel evenement detecte')
                log(event.raw_text, "info", clear=False)  # Affiche le texte brut du message
                log(f'chat id {event.chat_id}', "info", clear=False)  # Affiche l'ID du chat d'où vient le message
                # Check if message contains media/image
                has_media = event.message.media is not None
                log(f'Message contains media: {has_media}', "info", clear=False)

                # Canaux autorisés à envoyer des images de pronos + condition textuelle éventuelle.
                # None = pas de condition. Une condition peut être un tuple de plusieurs textes
                # alternatifs (OR) — ex: TEMPÊTE BETTING poste soit un "PRONO DU JOUR" classique,
                # soit une mise à jour de "PALIER X MONTANTE", les deux sont des paris valides.
                IMAGE_CHANNELS = {
                    "AdrBetting":          "TICKET SAFE PUBLIC",
                    "Tennistiqueur 🎾":    "CONFIANCE",
                    "TEMPÊTE BETTING ®️":  ("PRONO DU JOUR", "PALIER"),
                    "France Pronos Live": None,
                    "Auxo1XBOT": None
                }

                chat_title = event.chat.title if event.chat and hasattr(event.chat, "title") else ""
                if chat_title:
                    # Mémorise le chat_id réel par titre de canal -- relance_canaux_backlog()
                    # en a besoin pour relire l'historique (client.get_messages), mais
                    # client.iter_dialogs() s'est révélé peu fiable pour retrouver certains
                    # canaux par titre (constaté le 2026-11-07 : "TEMPÊTE BETTING" jamais
                    # trouvé alors que ce canal reçoit des messages live sans problème) --
                    # capturer le chat_id directement depuis les events live est bien plus
                    # fiable, au prix de devoir avoir déjà vu au moins un message du canal
                    # depuis le dernier redémarrage (fallback iter_dialogs() sinon).
                    _known_channel_entities[chat_title] = event.chat_id

                # Détection de code 1XBET restreinte aux canaux censés en envoyer --
                # sans ce filtre, n'importe quel mot de 5 caractères majuscules/chiffres
                # dans N'IMPORTE QUEL canal (ex: "PRONO DU JOUR" matche involontairement)
                # était traité comme un code potentiel, ce qui pouvait déclencher une
                # tentative de placement vouée à l'échec (cf. bug boucle infinie dans
                # check(), corrigé le 2026-10-28 : del codeList[0] même en cas d'échec).
                CODE_1XBET_CHANNELS = {"France Pronos Live", "Auxo1XBOT"}
                is_code_channel = (
                    chat_title in CODE_1XBET_CHANNELS
                    or str(event.chat_id) == str(auxo_bot_id)
                )
                codes = extract_code_1XBET(event.raw_text) if is_code_channel else False
                if codes and isinstance(codes, list):
                    for code in codes:
                        codeList.append(code)
                # Download media if present and canal autorisé
                elif has_media:
                    # Vérifier si le canal est dans la whitelist
                    required_text = IMAGE_CHANNELS.get(chat_title, "NOT_ALLOWED")
                    if required_text == "NOT_ALLOWED":
                        log(f"[Image] Canal '{chat_title}' non autorisé, image ignorée", "info", clear=False)
                        return
                    # Vérifier la condition textuelle si elle existe (texte unique, ou tuple = OR)
                    if required_text is not None:
                        conditions = required_text if isinstance(required_text, (list, tuple)) else (required_text,)
                        if not any(c.upper() in txt.upper() for c in conditions):
                            log(f"[Image] [{chat_title}] Image ignorée (condition '{required_text}' absente du message)", "info", clear=False)
                            return
                    # Ignorer les GIFs
                    from telethon.tl.types import MessageMediaDocument
                    if isinstance(event.message.media, MessageMediaDocument):
                        doc = event.message.media.document
                        if any(getattr(attr, 'mime_type', '') == 'image/gif' or str(type(attr).__name__) == 'DocumentAttributeAnimated' for attr in (doc.attributes or [])):
                            log(f"[Image] [{chat_title}] GIF ignoré", "info", clear=False)
                            return
                    log(f"[Image] [{chat_title}] Traitement image autorisé", "info", clear=False)
                    if has_media:
                        # Create unique filename using timestamp
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"media_{timestamp}.jpg"
                        # Create temp directory in the script directory
                        temp_dir = os.path.join(parent_directory, 'media')
                        os.makedirs(temp_dir, exist_ok=True)
                        # Set full path for the image in temp directory
                        image_path = os.path.join(temp_dir, filename)
                        log(f"Repertoire temp cree: {temp_dir}", "info", clear=False)
                        log(f"Chemin de l'image: {image_path}", "info", clear=False)
                        # Download the media directly to temp directory
                        await event.message.download_media(file=image_path)
                        log(f"Media downloaded successfully as {image_path}", "info", clear=False)
                        # Process the image
                        process_channel_image(chat_title, txt, image_path)
                        # Delete the downloaded image file
                        print("Attempting to delete the image file...")
                        # try:
                        if image_path:
                            # Verifier que le fichier existe avant de le supprimer
                            if os.path.exists(image_path):
                                # Verifier les permissions de lecture/ecriture
                                if os.access(image_path, os.W_OK):
                                    os.remove(image_path)
                                    log(f"Fichier image supprime avec succès: {filename}", "info", clear=False)
                                else:
                                    log(f"Erreur: Pas de permission d'ecriture pour {image_path}", "error", clear=False)
                                    # Essayer de changer les permissions
                                    try:
                                        os.chmod(image_path, 0o666)
                                        os.remove(image_path)
                                        log(f"Fichier image supprime après changement de permissions: {filename}",
                                            "info", clear=False)
                                    except OSError as chmod_error:
                                        log(f"Impossible de changer les permissions: {chmod_error}", "error",
                                            clear=False)
                            else:
                                log(f"Erreur: Le fichier {image_path} n'existe pas", "error", clear=False)
                        # except OSError as e:
                        # log(f"Erreur lors de la suppression du fichier image: {e}", "error", clear=False)
                        # log(f"Chemin du fichier: {image_path}", "info", clear=False)
                        # log(f"Repertoire courant: {os.getcwd()}", "info", clear=False)
                        # log(f"Le fichier existe: {os.path.exists(image_path)}", "info", clear=False)
                        # Clean up empty temp directory
                        try:
                            # Verifier que le repertoire existe et est vide
                            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                os.rmdir(temp_dir)
                                log(f"Repertoire temporaire supprime: {temp_dir}", "info", clear=False)
                        except OSError as e:
                            log(f"Impossible de supprimer le repertoire temporaire: {e}", "error", clear=False)
                        # Revenir au repertoire original
                        os.chdir(original_cwd)
                    # except Exception as e:
                    # log(f"Error downloading media: {e}", "error", clear=False)

                elif chat_title == "France Pronos Live" and txt and txt.strip():
                    # Tip texte seul (sans image) sur le canal live -- généralement
                    # une image est suivie d'un texte explicatif pour le MÊME pari ;
                    # _place_live_bet_direct s'occupe du dédoublonnage.
                    log("[FrancePronosLive] Tip texte reçu — extraction + placement direct", "info", clear=False)

                    def _run_text_live(txt=txt, chat_title=chat_title):
                        try:
                            result = extraire_pari_depuis_texte(txt, txt)
                            pari_dict = json.loads(result)
                            pari_dict["tipster"] = chat_title
                            matches = pari_dict.get("matches", [])
                            if matches:
                                _place_live_bet_direct(pari_dict, "texte")
                            else:
                                log("[FrancePronosLive] Aucun match extrait du texte", "warning", clear=False)
                        except Exception as e:
                            log(f"[FrancePronosLive] Erreur traitement texte: {e}", "error", clear=False)

                    threading.Thread(target=_run_text_live, daemon=True).start()

            else:
                log("Expediteur introuvable", "warning", clear=False)
    # except Exception as e:
    # log('Erreur dans le traitement du message', e, "error", clear=False)


# Demarrage du client Telegram
import time as _time
for _attempt in range(5):
    try:
        client.start()
        break
    except Exception as _e:
        if "database is locked" in str(_e).lower() and _attempt < 4:
            log(f"Session SQLite verrouillée, attente... ({_attempt+1}/5)", "warning", clear=False)
            _time.sleep(3)
        else:
            raise

config.scriptType = 'LIVE'


# Fonction de verification des nouveaux codes et envoi
def check():
    import time

    last_api_check = 0
    api_check_interval = 1  # Verifier l'API toutes les 5 minutes

    while True:
        # Traitement des codes directs
        if codeList != []:
            bridge.navigate(config.site_line_url)
            code = codeList[0]
            try:
                PlacerCode(code)
            except Exception as e:
                log(f"Erreur lors du placement du code: {e}", "error", clear=False)
            else:
                log(f"Code place avec succès: {code}", "info", clear=False)
            finally:
                # Toujours retirer le code tenté (succès OU échec) -- sinon un code
                # invalide (faux positif, déjà utilisé, expiré) reste en tête de
                # codeList pour toujours : la boucle while True ci-dessus le retente
                # à chaque passage, sans fin (bug "boucle infinie" constaté le
                # 2026-10-28). Une tentative par code suffit ; pas de retry voulu ici.
                del codeList[0]

        # Traitement des paris en temps reel
        if betList != []:
            try:
                log('Gestion du pari en temps reel', "info", clear=False)
                placer_pari(betList)
            except Exception as e:
                log(f"Erreur lors du placement du pari: {e}", "error", clear=False)
            else:
                log(f"Pari place avec succès: {betList[0]}", "info", clear=False)
                del betList[0]

        # Verification periodique de l'API pour les paris non traites
        current_time = time.time()
        if current_time - last_api_check > api_check_interval:
            #try:
            if current_time:
                #log("Verification des paris non traites dans l'API...", "info", clear=False)
                #processed_count = process_api_bets(limit=5)
                #if processed_count > 0:
                    #log(f"Traite {processed_count} paris depuis l'API", "info", clear=False)
                #else:
                    #log_clear_line()
                last_api_check = current_time
            #except Exception as e:
            #    log(f"Erreur lors du traitement des paris API: {e}", "error", clear=False)

        # Petite pause pour eviter une boucle trop intensive
        time.sleep(10)


# Lancement d'un thread pour verifier les messages en continu
confirmThread = threading.Thread(target=check)
confirmThread.start()

# Thread de vérification des images publiées sur tempetebetting.com
tempeteThread = threading.Thread(target=check_tempete_images, daemon=True)
tempeteThread.start()

callbackPollerThread = threading.Thread(target=_poll_callback_queries, daemon=True)
callbackPollerThread.start()

# Indique que le bot est demarre
Functions_telegram.send_telegram(auxo_bot_id, "Bot 1XBET Demarre")

# Le bot continue a tourner tant qu'il n'est pas deconnecte
client.run_until_disconnected()
