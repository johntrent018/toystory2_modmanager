"""Point d'entrée du gestionnaire de mods. / Mod manager entry point.

Lancement : python main.py
"""
from __future__ import annotations

import tkinter as tk

from app.app_paths import get_app_dir
from app.controllers.create_mod_controller import CreateModController
from app.controllers.mod_list_controller import ModListController
from app.controllers.settings_controller import SettingsController
from app.event_bus import EventBus
from app.game_path_manager import GamePath_Manager
from app.language_manager import LanguageManager
from app.models.mod_activator import ModActivator
from app.models.mod_repository import ModRepository
from app.preferences import Preferences
from app.views.app_icon import apply_app_icon
from app.views.main_window import MainWindow

def main() -> None:
    """Assemble les composants (modèles → contrôleurs → vues). / Wire everything together."""
    app_dir = get_app_dir()
    logging.debug(app_dir)

    # --- Services partagés
    bus = EventBus()
    preferences = Preferences(app_dir / "preferences.json")
    lang = LanguageManager(preferences, bus)
    game_path_manager = GamePath_Manager(preferences, bus)

    # --- Modèles
    repository = ModRepository(app_dir / "mods")
    activator = ModActivator(repository, game_path_manager, bus)

    # --- Contrôleurs
    list_controller = ModListController(repository, activator, game_path_manager, bus, lang)
    create_controller = CreateModController(repository, activator, bus, lang)
    settings_controller = SettingsController(game_path_manager, lang)

    # --- Vues
    root = tk.Tk()
    apply_app_icon(root)  # icône de l'appli (repli : plume Tk par défaut)
    MainWindow(root, lang, bus, list_controller, create_controller, settings_controller)
    root.mainloop()


if __name__ == "__main__":
    main()
