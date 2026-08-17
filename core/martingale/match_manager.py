# PROTOTYPE ABANDONNÉ — jamais importé par aucun code actif (le gestionnaire
# de matchs réellement utilisé est Functions/Managers/MatchManager.py, un
# module distinct). Conservé pour référence uniquement, cf. base.py du même
# dossier pour le contexte complet.

import os
import json
from typing import Optional, List

class MatchManager:
    """
    Manages match tracking and status updates across different strategy files.
    Handles operations like adding/removing matches and checking match status.
    """
    
    def __init__(self, matchlist_file_path: str):
        """
        Initialize the Match Manager with a matchlist file path.
        
        Args:
            matchlist_file_path (str): Path to the matchlist file (without .txt extension)
        """
        self.matchlist_file = f"{matchlist_file_path}.txt"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the matchlist file exists, create if not."""
        if not os.path.exists(self.matchlist_file):
            with open(self.matchlist_file, 'w') as f:
                f.write("")

    def add_match(self, match_id: str) -> None:
        """
        Add a new match to the matchlist.
        
        Args:
            match_id (str): Unique identifier for the match
        """
        with open(self.matchlist_file, "a") as f:
            f.write(f"\n{match_id}")

    def remove_match(self, match_id: str) -> None:
        """
        Remove a match from the matchlist.
        
        Args:
            match_id (str): Match identifier to remove
        """
        with open(self.matchlist_file, "r") as f:
            content = f.read()
        
        updated_content = content.replace(f"\n{match_id}", "")
        
        with open(self.matchlist_file, "w") as f:
            f.write(updated_content)

    def get_all_matches(self) -> List[str]:
        """
        Get all matches from the matchlist.
        
        Returns:
            List[str]: List of all match IDs
        """
        with open(self.matchlist_file, "r") as f:
            content = f.read()
        return [match for match in content.split('\n') if match]

    def match_exists(self, match_id: str) -> bool:
        """
        Check if a match exists in the matchlist.
        
        Args:
            match_id (str): Match identifier to check
            
        Returns:
            bool: True if match exists, False otherwise
        """
        return match_id in self.get_all_matches()

    def update_match(self, action: str, match_id: str) -> None:
        """
        Update match status based on action.
        
        Args:
            action (str): Action to perform ("add" or "del")
            match_id (str): Match identifier
        """
        if action == "add":
            self.add_match(match_id)
        elif action == "del":
            self.remove_match(match_id)
        else:
            raise ValueError("Invalid action. Use 'add' or 'del'")