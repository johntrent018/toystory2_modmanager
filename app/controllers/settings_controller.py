"""Contrôleur de l'onglet « Paramètres ». / Controller for the settings tab."""
from __future__ import annotations

from app.game_path_manager import GamePath_Manager
from app.language_manager import LanguageManager


class SettingsController:
    """Expose les réglages à la vue. / Exposes the settings to the view."""

    def __init__(self, game_path_manager: GamePath_Manager, lang: LanguageManager) -> None:
        self._game_path_manager = game_path_manager
        self._lang = lang

    def game_path_text(self) -> str:
        """Chemin du jeu enregistré (peut être vide). / Stored game path (may be empty)."""
        return self._game_path_manager.get_stored_text()

    def is_game_path_valid(self) -> bool:
        """Le chemin enregistré est-il valide ? / Is the stored path valid?"""
        return self._game_path_manager.is_valid()

    def set_game_path(self, folder: str) -> str | None:
        """Enregistre le dossier du jeu. / Store the game folder.

        Returns:
            None si accepté, sinon le message d'erreur traduit.
        """
        if self._game_path_manager.set_path(folder):
            return None
        return self._lang.t("settings.game_path.invalid_selection")

    # ------------------------------------------------------------------ langue

    def language_choices(self) -> list[tuple[str, str]]:
        """Langues disponibles : [(code, nom affiché), …]. / Available languages."""
        return self._lang.available_languages()

    def preferred_language(self) -> str:
        """Code de la langue préférée. / Preferred language code."""
        return self._lang.preferred_language

    def set_preferred_language(self, code: str) -> None:
        """Change la langue : interface (immédiat) + langue par défaut des nouveaux mods."""
        self._lang.set_preferred_language(code)
