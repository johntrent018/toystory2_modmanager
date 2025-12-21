import json
import os

class Preferences:

    # Constructeur
    def __init__(self, path="preferences.json"):
        self.path = path
        self.data = {}
        self.load()

    # Charger les préférences (prise en charge des erreurs)
    def load(self):

        if not os.path.exists(self.path):
            self.data = {}
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.data = {}

    # Enregistrer les modifications dans le fichier de préférences
    def save(self):

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # Récupérer un élément des préférences
    def get(self, key, default=None):

        return self.data.get(key, default)

    # Modifier une préférence puis aller enregistrer le fichier
    def set(self, key, value):

        self.data[key] = value
        self.save()
