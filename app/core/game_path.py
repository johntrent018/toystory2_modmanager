# Importations de base
import os

# Service gérant les actions sur le chemin du jeu modifiable depuis l'onglet "Settings" de l'application
# et stocké dans le fichier des préférences "preferences.json" à la racine du projet
class GamePath_Manager:
    
    # Constructeur
    def __init__(self, preferences):
        self.preferences = preferences
        self._subscribers = []

    # --------------------------
    # Design Pattern "Observeur"
    # --------------------------

    def register(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def notify(self):
        for callback in self._subscribers:
            callback()

    # ----------------------------------------
    # Méthodes logiques liées au chemin du jeu
    # ----------------------------------------

    def is_set(self):
        path = self.get_game_path()
        return path is not None and os.path.isdir(path)

    def get_game_path(self):
        return self.preferences.get("game_path")

    def set_game_path(self, path):
        self.preferences.set("game_path", path)
        self.notify()