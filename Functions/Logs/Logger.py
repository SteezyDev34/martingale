import datetime
import config
import time
def saveLog(txt):
    """
    Enregistre un message dans un fichier de log et l'affiche éventuellement dans la console.
    
    Args:
        txt: Le texte à enregistrer
        prntxt: 1 pour afficher le texte, 0 pour ne pas l'afficher
        matchname: Le nom du match concerné par le log
    """
    # Obtenir la date et l'heure actuelles
    date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
    heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")

    # Créer le nom de fichier avec la date
    nom_du_fichier = f"{config.projectPath}/Logs/logScript{config.scriptType}-{config.script_num}-{config.newmatch}-{date_actuelle}.log.log"

    # Créer le répertoire s'il n'existe pas
    nom_du_repertoire = os.path.dirname(nom_du_fichier)
    if nom_du_repertoire and not os.path.exists(nom_du_repertoire):
        os.makedirs(nom_du_repertoire)

    try:
        # Gestion robuste des interruptions clavier et des erreurs d'encodage
        try:
            # Vérifier d'abord si le fichier existe et s'il est lisible
            if os.path.exists(nom_du_fichier):
                try:
                    # Test de lecture pour détecter les problèmes d'encodage
                    with open(nom_du_fichier, 'r', encoding='utf-8') as test_file:
                        test_file.seek(0, 2)  # Aller à la fin pour tester
                except UnicodeDecodeError:
                    # Fichier corrompu, le sauvegarder et en créer un nouveau
                    backup_file = f"{nom_du_fichier}.corrupted.{int(time.time())}"
                    print(f"⚠️ Fichier de log corrompu, sauvegarde vers: {backup_file}")
                    try:
                        os.rename(nom_du_fichier, backup_file)
                    except:
                        # Si on ne peut pas renommer, supprimer le fichier corrompu
                        os.remove(nom_du_fichier)
                        print(f"❌ Fichier corrompu supprimé: {nom_du_fichier}")

            # Ouvrir le fichier en mode ajout avec gestion d'erreur renforcée
            with open(nom_du_fichier, 'a+', encoding='utf-8', buffering=1, errors='replace') as fichier:
                # Méthode plus efficace - éviter de lire tout le fichier
                fichier.seek(0, 2)  # Aller à la fin du fichier
                position = fichier.tell()

                # Ajouter un saut de ligne si le fichier n'est pas vide
                if position > 0:
                    try:
                        # Vérifier le dernier caractère pour éviter les doubles sauts de ligne
                        fichier.seek(position - 1)
                        dernier_char = fichier.read(1)
                        fichier.seek(0, 2)  # Retourner à la fin

                        if dernier_char and dernier_char != '\n':
                            fichier.write('\n')
                    except:
                        # En cas d'erreur de lecture, simplement ajouter une ligne
                        fichier.write('\n')

                # Nettoyer le texte pour éviter les caractères problématiques
                txt_clean = str(txt).encode('utf-8', errors='replace').decode('utf-8')

                # Écrire le texte à la fin du fichier
                fichier.write(f"{heure_actuelle} : {txt_clean}")
                fichier.flush()  # Forcer l'écriture immédiate

        except KeyboardInterrupt:
            # Gestion spécifique de Ctrl+C - essayer de sauvegarder quand même
            print(f"⚠️ Interruption détectée lors de l'écriture du log: {txt[:50]}...")
            try:
                # Tentative rapide de sauvegarde avec nettoyage du texte
                txt_clean = str(txt).encode('utf-8', errors='replace').decode('utf-8')
                with open(nom_du_fichier, 'a', encoding='utf-8', errors='replace') as fichier_urgence:
                    fichier_urgence.write(f"\n{heure_actuelle} : [INTERROMPU] {txt_clean}")
            except:
                # Si même ça échoue, au moins l'afficher
                print(f"❌ Impossible de sauvegarder: {txt}")
            raise  # Re-lancer l'interruption

    except Exception as e:
        error_msg = str(e)
        print(f'❌ Erreur de log: {error_msg}')

        # Essayer une sauvegarde d'urgence avec un nom de fichier alternatif
        try:
            emergency_file = f"{config.projectPath}/Logs/emergency_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            os.makedirs(os.path.dirname(emergency_file), exist_ok=True)

            txt_clean = str(txt).encode('ascii', errors='replace').decode('ascii')
            with open(emergency_file, 'w', encoding='ascii', errors='replace') as emergency:
                emergency.write(f"{heure_actuelle} : [ERREUR_LOG] {txt_clean}\n")
                emergency.write(f"Erreur originale: {error_msg}\n")

            print(f"💾 Log de secours créé: {emergency_file}")

        except Exception as emergency_error:
            print(f"❌ Impossible de créer un log de secours: {emergency_error}")
            # Dernière tentative: afficher dans la console seulement
            print(f"LOG PERDU: {heure_actuelle} - {txt}")


import colorama
import codecs
import sys
import os

# Forcer l'encodage en UTF-8 pour stdout
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="backslashreplace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="backslashreplace")

# Initialisation de colorama pour le support des couleurs sur Windows
# Le terminal natif de Windows ne prend pas en charge les codes ANSI par défaut
# Colorama permet d'activer cette fonctionnalité sur Windows
colorama.init()

# Définition des couleurs ANSI avec colorama pour la compatibilité Windows
RESET = colorama.Style.RESET_ALL  # Réinitialisation des styles
WHITE = colorama.Fore.WHITE
BOLD = colorama.Style.BRIGHT  # Texte en gras
YELLOW = colorama.Fore.YELLOW  # Texte jaune
GREEN = colorama.Fore.GREEN  # Texte vert
BLUE = colorama.Fore.BLUE  # Texte bleu
CYAN = colorama.Fore.CYAN  # Texte cyan
RED = colorama.Fore.RED  # Texte rouge
PURPLE = colorama.Fore.MAGENTA  # Texte magenta
BGPURPLE = colorama.Back.MAGENTA  # Fond magenta
BGCYAN = colorama.Back.CYAN  # Fond cyan
BGBLUE = colorama.Back.BLUE  # Fond bleu
BGRESET = colorama.Back.BLACK  # Fond noir (réinitialisation)


def log(message, type="", clear=True, indent=0, show_script_type=True):
    """
    Affiche un message dans le terminal tout en effaçant dynamiquement la ligne précédente si demandé.

    :param message: Le texte du nouveau message.
    :param clear: Booléen indiquant si la ligne précédente doit être effacée.
    :return: La longueur du message actuel, pour l'utiliser dans l'appel suivant.
    """
    global log_message
    # Détermination de la couleur en fonction du type de message
    if type == "info":
        color = WHITE
    elif type == "title":
        color = CYAN
    elif type == "success":
        color = GREEN
    elif type == "warning":
        color = YELLOW
    elif type == "error":
        color = RED
    elif type == "purple":
        color = PURPLE
    elif type == "bgpurple":
        color = BGPURPLE
    elif type == "bgcyan":
        color = BGCYAN
    elif type == "bgblue":
        color = BGBLUE
    elif type == "bgreset":
        color = BGRESET
    else:
        color = RESET  # Pas de couleur par défaut

    # Gestion de l'indentation
    indent = "    " * indent if indent > 0 else ""
    s = ''
    if show_script_type:
        s = config.scriptType
    sys.stdout.write(f"{color}{s} {indent}{message}{RESET}\n")

    if clear:
        # Effacement de la ligne précédente
        # Affichage du nouveau message sur la même ligne
        time.sleep(0.3)
        log_clear_line()

    # Force l'écriture du buffer
    sys.stdout.flush()
    # Mise à jour du message global
    log_message = message

    # Sauvegarde protégée contre les interruptions
    try:
        saveLog(message)
    except:
        pass  # Si même ça échoue, on abandonne silencieusement


def log_clear_line(line_number=1):
    """
    Efface un certain nombre de lignes dans le terminal.

    :param line_number: Nombre de lignes à effacer (par défaut 1)
    """
    if os.getenv('PYCHARM_HOSTED') == '1':  # Si exécuté dans PyCharm
        # Simple écriture de lignes vides pour PyCharm
        for _ in range(line_number):
            sys.stdout.write("clear\n")
            continue
    else:
        # Délai pour éviter les problèmes d'affichage
        for _ in range(line_number):
            if not config.devMode:
                sys.stdout.write("\x1b[1A\x1b[2K\r")
            # Monte d’une ligne et efface-la entièrement

        sys.stdout.flush()
