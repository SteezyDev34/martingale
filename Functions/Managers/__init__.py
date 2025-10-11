"""
Package de gestion des ressources du système de paris.

Ce package contient les différents gestionnaires qui assurent:
- La gestion des matchs (MatchManager)
- La gestion des scripts (ScriptManager)
- La gestion des ressources système (SystemManager)
"""

from .MatchManager import MatchManager, match_manager, get_match_manager

__all__ = ['MatchManager', 'match_manager', 'get_match_manager']