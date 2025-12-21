import json
import os

class LanguageManager:
    
    # Constructeur
    def __init__(self, locales_path, default_lang):

        self.locales = {}
        self.lang = default_lang
        self._observers = []

        for file in os.listdir(locales_path):
            if file.endswith(".json"):
                with open(os.path.join(locales_path, file), encoding="utf-8") as f:
                    data = json.load(f)
                    self.locales[data["meta"]["code"]] = data

    def available_languages(self):
        return list(self.locales.keys())

    def language_name(self, lang_code, target_lang=None):
        if target_lang is None:
            target_lang = self.lang
        return self.locales[lang_code]["meta"]["name"].get(
            target_lang,
            lang_code
        )

    def translate(self, key):
        return self.locales[self.lang].get(key, key)

    def set_language(self, lang):
        if lang in self.locales and lang != self.lang:
            self.lang = lang
            self._notify()

    def register(self, callback):
        self._observers.append(callback)

    # Méthode pour envoyer une notification aux observers
    def _notify(self):
        for cb in self._observers:
            cb()
