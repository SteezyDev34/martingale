"""
Module AddRunning - Gestion des scripts en cours d'exécution

Ce module permet de garder une trace des scripts qui sont actuellement en cours 
d'exécution en les enregistrant dans un fichier texte. Cela évite que plusieurs 
instances du même script ne s'exécutent simultanément.

Utilisation typique:
    from Functions.AddRunning import main
    main(1, "/path/to/running_file")
"""

def main(script_num: int, running_file_name: str) -> None:
    """
    Ajoute le numéro d'un script au fichier des scripts en cours d'exécution.
    
    Args:
        script_num: Le numéro du script à ajouter (entier ou '#1#')
        running_file_name: Chemin du fichier où enregistrer les scripts en cours
                         (sans l'extension .txt)
    
    Note:
        Si script_num est '#1#', il sera converti en 1 pour standardisation
    """
    # Conversion de la valeur spéciale '#1#' en entier 1
    if script_num == '#1#':
        script_num = 1
    
    # Ouverture du fichier en mode append (ajout à la fin)
    get_running_file = open(running_file_name + ".txt", "a")
    
    # Écriture du numéro du script
    get_running_file.write(str(script_num))
    
    # Fermeture du fichier pour libérer les ressources
    get_running_file.close()
