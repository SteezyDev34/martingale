# -*- coding: utf-8 -*-
"""
Utilitaires de chemin pour le projet.

Fonctions en français dans la docstring conformément aux consignes du projet.
"""
import os
import sys

def get_project_directory(file_path=None, levels=1, add_to_sys_path=False):
    """
    Retourne le chemin absolu du répertoire qui est `levels` niveaux au-dessus
    du fichier indiqué.

    Args:
        file_path (str): Chemin du fichier (par défaut : __file__ du module appelant)
        levels (int): Nombre de niveaux parents à remonter (1 = dossier contenant le fichier)
        add_to_sys_path (bool): Si True, ajoute le dossier résultant à `sys.path`

    Returns:
        str: Chemin absolu du répertoire trouvé
    """
    if file_path is None:
        file_path = __file__

    current_file_path = os.path.abspath(file_path)
    dir_path = current_file_path
    for _ in range(levels):
        dir_path = os.path.dirname(dir_path)

    if add_to_sys_path:
        if dir_path not in sys.path:
            sys.path.append(dir_path)

    return dir_path
