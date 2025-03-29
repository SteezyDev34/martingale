import sys


def log_with_clear(message, previous_message_length=0):
    """
    Affiche un message dans le terminal tout en effaçant dynamiquement la ligne précédente.
    
    :param message: Le texte du nouveau message.
    :param previous_message_length: La longueur de la ligne précédente (0 par défaut si rien à effacer).
    :return: La longueur du message actuel, pour l'utiliser dans l'appel suivant.
    """
    # Effacer la ligne précédente avec des espaces
    sys.stdout.write(f"\r{' ' * previous_message_length}\r")
    # Écrire le nouveau message
    sys.stdout.write(message)
    sys.stdout.flush()
    # Retourner la longueur du message actuel pour le prochain appel
    return len(message)