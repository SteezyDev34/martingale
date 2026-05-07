import os

# Couleurs ANSI (texte)
RESET = "\033[0m"  # Réinitialisation du style
BOLD = "\033[1m"  # Texte en gras
YELLOW = "\033[33m"  # Texte jaune
GREEN = "\033[32m"  # Texte vert
BLUE = "\033[34m"  # Texte bleu
CYAN = "\033[36m"  # Texte cyan
RED = "\033[31m"  # Texte rouge


def is_venv_activated():
    """Vérifie si un environnement virtuel est activé."""
    return os.getenv("VIRTUAL_ENV") is not None


def create_venv(venv_path="venv"):
    """Crée un nouvel environnement virtuel."""
    print(f"Création d'un nouvel environnement virtuel dans : {venv_path}")
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])
    print("Environnement virtuel créé avec succès.")


def activate_venv(venv_path="venv"):
    """Active un environnement virtuel."""
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")

    # Charge le script d'activation
    activate_command = f'source {activate_script}' if sys.platform != "win32" else activate_script
    print(f"Activation de l'environnement virtuel : {venv_path}")
    os.system(activate_command)


import subprocess
import sys
from importlib.metadata import distribution, PackageNotFoundError
import shutil
import platform
import time


def install_requirements_if_needed(requirements_file):
    """Installe les dépendances manquantes listées dans le fichier requirements.txt."""
    try:
        print(f"Vérification des dépendances dans '{requirements_file}'...")

        # Lire les dépendances depuis requirements.txt
        with open(requirements_file, "r") as file:
            requirements = file.readlines()

        requirements = [r.strip() for r in requirements if r.strip() and not r.startswith('#')]

        # Vérifier chaque dépendance
        missing_packages = []
        for requirement in requirements:
            package_name, _, version_spec = requirement.partition("==")
            try:
                dist = distribution(package_name)  # Vérifie si le paquet est installé
                if version_spec and dist.version != version_spec:
                    print(
                        f"Le paquet {package_name} est installé mais a une version différente (installée : {dist.version}, requise : {version_spec}).")
                    missing_packages.append(requirement)
            except PackageNotFoundError:
                print(f"Package manquant : {requirement}")
                missing_packages.append(requirement)

        # Installer les dépendances manquantes
        if missing_packages:
            print(f"Les dépendances manquantes seront installées : {', '.join(missing_packages)}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            print("Toutes les dépendances manquantes ont été installées avec succès.")
        else:
            print("Toutes les dépendances sont déjà satisfaites.")
    except Exception as e:
        print(f"Erreur lors de la vérification/installation des dépendances : {e}")
        sys.exit(1)


def is_command_available(cmd: str) -> bool:
    """Retourne True si la commande est trouvable dans le PATH."""
    return shutil.which(cmd) is not None


def _run(cmd, check=False, capture_output=True, shell=False):
    """Lance une commande shell et retourne (code, stdout, stderr)."""
    try:
        res = subprocess.run(cmd, check=check, stdout=subprocess.PIPE if capture_output else None,
                             stderr=subprocess.PIPE if capture_output else None, shell=shell)
        out = res.stdout.decode('utf-8').strip() if res.stdout is not None else ''
        err = res.stderr.decode('utf-8').strip() if res.stderr is not None else ''
        return res.returncode, out, err
    except Exception as e:
        return 1, '', str(e)


def ensure_redis_installed(auto_install: bool = True, use_docker: bool = True) -> bool:
    """
    Vérifie que Redis est installé et démarré. Si absent et `auto_install` est True,
    tente une installation automatique selon l'OS (macOS Homebrew, Debian/Ubuntu apt, Docker, Chocolatey/WSL).

    Retourne True si Redis répond à `redis-cli ping`.
    """
    print("Vérification de la disponibilité de Redis...")

    # Vérifier redis-cli / redis-server
    if is_command_available('redis-cli'):
        code, out, err = _run(['redis-cli', 'ping'])
        if out.strip().upper() == 'PONG':
            print('Redis répond (redis-cli ping -> PONG)')
            return True

    # Si redis-cli non disponible, essayer de voir si redis-server existe
    if is_command_available('redis-server'):
        # tenter de démarrer en background si possible
        print('redis-server trouvé mais service non joignable, tentative de démarrage...')
        if platform.system() == 'Darwin':
            if is_command_available('brew') and auto_install:
                print('Démarrage via Homebrew service...')
                _run(['brew', 'services', 'start', 'redis'])
                time.sleep(1)
        elif platform.system() == 'Linux':
            # tenter service start
            _run(['sudo', 'service', 'redis-server', 'start'])
            time.sleep(1)

    # Si on arrive ici et qu'on ne répond toujours pas
    if not auto_install:
        print('Redis non trouvé ou non joignable et l\'installation automatique est désactivée.')
        return False

    system = platform.system()
    print(f"Système détecté: {system}. Tentative d'installation automatique de Redis...")

    # macOS (Homebrew)
    if system == 'Darwin':
        if is_command_available('brew'):
            print('Utilisation de Homebrew pour installer Redis...')
            _run(['brew', 'update'])
            code, out, err = _run(['brew', 'install', 'redis'])
            if code == 0:
                _run(['brew', 'services', 'start', 'redis'])
                time.sleep(1)
        else:
            print('Homebrew introuvable — installez Homebrew manuellement: https://brew.sh')
            return False

    # Linux (Debian/Ubuntu)
    elif system == 'Linux':
        # Si WSL sur Windows l'utilisateur peut préférer apt dans la distribution
        print('Tentative d\'installation via apt (sudo requis)...')
        _run(['sudo', 'apt-get', 'update'])
        code, out, err = _run(['sudo', 'apt-get', 'install', '-y', 'redis-server'])
        if code == 0:
            _run(['sudo', 'service', 'redis-server', 'start'])
            time.sleep(1)
        else:
            print('Échec apt, tentative via Docker si disponible...')
            if use_docker and is_command_available('docker'):
                _run(['docker', 'run', '-d', '--name', 'redis', '-p', '6379:6379', 'redis:7'])
                time.sleep(2)

    # Windows
    elif system == 'Windows':
        # Préférer Docker ou WSL
        if is_command_available('docker') and use_docker:
            print('Utilisation de Docker pour lancer Redis...')
            _run(['docker', 'run', '-d', '--name', 'redis', '-p', '6379:6379', 'redis:7'])
            time.sleep(2)
        elif is_command_available('choco'):
            print('Utilisation de Chocolatey pour installer Redis...')
            code, out, err = _run(['choco', 'install', 'redis-64', '-y'], shell=True)
            if code == 0:
                _run(['sc', 'start', 'Redis'])
                time.sleep(1)
        else:
            # Si WSL est installé on peut tenter l'installation dans la distro
            if is_command_available('wsl'):
                print('WSL détecté — tentative d\'installation dans la distribution via apt...')
                _run(['wsl', 'sudo', 'apt-get', 'update'])
                _run(['wsl', 'sudo', 'apt-get', 'install', '-y', 'redis-server'])
                _run(['wsl', 'sudo', 'service', 'redis-server', 'start'])
                time.sleep(1)
            else:
                print('Aucune méthode d\'installation automatique disponible sur Windows. Installez WSL ou Docker.')
                return False

    # Vérifier si redis répond maintenant
    if is_command_available('redis-cli'):
        code, out, err = _run(['redis-cli', 'ping'])
        if out.strip().upper() == 'PONG':
            print('Redis installé et répond (PONG).')
            return True

    # dernier essai via connexion TCP
    try:
        import socket

        s = socket.socket()
        s.settimeout(1.0)
        s.connect(('127.0.0.1', 6379))
        s.close()
        print('Connexion TCP à 127.0.0.1:6379 réussie (probablement Redis en cours).')
        return True
    except Exception:
        print('Impossible de joindre Redis sur localhost:6379.')
        return False


def main():
    # Chemin de l'environnement virtuel
    venv_path = "venv"

    # Étape 1 : Vérifier si un venv est activé
    if not is_venv_activated():
        print("Aucun environnement virtuel n'est activé.")
        # Activer l'environnement virtuel
        activate_venv(venv_path)
        print("Veuillez activer l'environnement virtuel en exécutant :")
        print("  source venv/bin/activate (Linux/Mac)")
        print("  venv\\Scripts\\activate (Windows)")
        # Vérifier si un venv existe dans le répertoire courant
        if not os.path.isdir(venv_path):
            print(f"Aucun environnement virtuel trouvé dans {venv_path}.")
            create_venv(venv_path)  # Créer un nouvel environnement virtuel
            sys.exit(1)
        else:
            print(f"Environnement virtuel trouvé dans {venv_path}.")

    # Étape 2 : Installer les dépendances
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(
            f"Erreur : Le fichier '{requirements_file}' est introuvable. Assurez-vous qu'il existe avant de continuer.")
        sys.exit(1)

    install_requirements_if_needed(requirements_file)

    # Étape 1 : Vérifier si un venv est activé
    if not is_venv_activated():
        # Activer l'environnement virtuel
        activate_venv(venv_path)
        print("Veuillez activer l'environnement virtuel en exécutant :")
        print("  source venv/bin/activate (Linux/Mac)")
        print("  venv\\Scripts\\activate (Windows)")
        sys.exit(0)

    print(f"{GREEN}Tout est prêt !\n{RESET}")


if __name__ == "__main__":
    main()
