# Importations
import json
import os

class LanguageManager:

    # Constructeur
    def __init__(self, locales_path, default_lang="en-GB"):

        self.locales_path = locales_path
        self.default_lang = default_lang
        self.current_lang = default_lang

        self.translations = {}
        self.observers = []

        self._load_languages()

    # -----------------------
    # Chargement des langues
    # -----------------------

    def _load_languages(self):
        for file in os.listdir(self.locales_path):
            if file.endswith(".json"):
                lang_code = file.replace(".json", "")
                file_path = os.path.join(self.locales_path, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)

    # -----------------------
    # Design Pattern "Observeur"
    # -----------------------

    def register(self, callback):
        if callback not in self.observers:
            self.observers.append(callback)

    def notify(self):
        for callback in self.observers:
            callback()

    # -----------------------
    # Gestion de la langue
    # -----------------------

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code
            self.notify()

    def available_languages(self):
        return list(self.translations.keys())

    def language_name(self, lang_code, target_lang=None):
        if target_lang is None:
            target_lang = self.current_lang
        return self.translations[lang_code]["meta"]["name"].get(
            target_lang,
            lang_code
        )

    # -----------------------
    # Traduction (CLÉ DU SYSTÈME)
    # -----------------------

    def translate(self, key_path, default=None):
        
        # key_path : str avec notation par points (ex: "app_data.tabs.create_mod.sub_tabs.music_sfx.h1")
        # Retourne soit une string, soit une liste, soit un dict, ou 'default' (ou key_path) si introuvable
        data = self.translations.get(self.current_lang)
        if not data:
            return default if default is not None else key_path
        keys = key_path.split(".")
        value = data

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default if default is not None else key_path
