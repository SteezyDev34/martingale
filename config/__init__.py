# -*- coding: utf-8 -*-
"""
Module de configuration pour le projet martingale-40A1.
Ce module regroupe tous les éléments de configuration dans des fichiers séparés
pour une meilleure organisation et maintenabilité du code.
"""

# Import des configurations principales
from .classes import classes
from .scores import score_to_start
from .betting_config import total_want_win, total_want_winset1

# Rendre les configurations disponibles au niveau du module
__all__ = ['classes', 'score_to_start', 'total_want_win', 'total_want_winset1']