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
