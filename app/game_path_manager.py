"""Chemin d'installation du jeu. / Game installation path."""
from __future__ import annotations

from pathlib import Path

from app.event_bus import EventBus, Events
from app.preferences import Preferences


class GamePath_Manager:
    """Valide et mémorise le dossier d'installation du jeu.
    Validates and stores the game installation folder.

    Le dossier attendu est le PARENT DIRECT du sous-dossier « data ».
    """

    PREF_KEY = "game_path"

    def __init__(self, preferences: Preferences, bus: EventBus) -> None:
        self._prefs = preferences
        self._bus = bus

    @staticmethod
    def is_valid_game_folder(path: Path) -> bool:
        """Un dossier de jeu valide contient un sous-dossier « data ».
        A valid game folder contains a "data" subfolder.
        """
        return path.is_dir() and (path / "data").is_dir()

    def get_stored_text(self) -> str:
        """Chemin tel qu'enregistré (même s'il n'est plus valide). / Stored path as text."""
        return str(self._prefs.get(self.PREF_KEY, ""))

    def get_path(self) -> Path | None:
        """Chemin du jeu s'il est renseigné ET encore valide, sinon None.
        Game path if set AND still valid, otherwise None.

        La validité est revérifiée à chaque appel : le dossier a pu être
        supprimé ou déplacé depuis le dernier lancement.
        """
        text = self.get_stored_text()
        if not text:
            return None
        path = Path(text)
        return path if self.is_valid_game_folder(path) else None

    def is_valid(self) -> bool:
        """Le chemin du jeu est-il utilisable ? / Is the game path usable?"""
        return self.get_path() is not None

    def set_path(self, text: str) -> bool:
        """Enregistre un nouveau chemin s'il est valide. / Store a new path if valid.

        Returns:
            True si accepté (événement GAME_PATH_CHANGED publié), False sinon.
        """
        path = Path(text.strip())
        if not self.is_valid_game_folder(path):
            return False
        self._prefs.set(self.PREF_KEY, str(path))
        self._bus.publish(Events.GAME_PATH_CHANGED)
        return True
