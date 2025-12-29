# Importations de base
import tkinter as tk
from tkinter import ttk
# Importation de composants
from preferences import Preferences

class SettingsTab(ttk.Frame):

    # Constructeur
    def __init__(self, parent, lang, prefs):

        super().__init__(parent)

        # --------------------------------
        # Partie "GamePath" de l'interface
        # --------------------------------

        

        # ------------------------------
        # Partie "Langue" de l'interface
        # ------------------------------

        # Propriétés et variables liées à la partie Langue des paramétrages
        self.lang = lang
        self.prefs = prefs
        self.selected = tk.StringVar()

        # Label avant la liste déroulante des langues
        self.label = ttk.Label(self)
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Liste déroulante du choix de la langue
        self.combo = ttk.Combobox(
            self,
            state="readonly",
            textvariable=self.selected
        )
        self.combo.grid(row=0, column=1, padx=10, pady=10)

        # Bouton "Appliquer" du choix de la langue
        self.button = ttk.Button(self, command=self.apply)
        self.button.grid(row=1, column=0, columnspan=2, pady=10)

        def refresh():
            self.label.config(text=lang.translate("app_data.tabs.settings.chooseLang_label"))
            self.button.config(text=lang.translate("app_data.widgets_terms.apply_btn"))

            values = [
                lang.language_name(code)
                for code in lang.available_languages()
            ]
            self.combo["values"] = values
            self.selected.set(lang.language_name(lang.current_lang))

        lang.register(refresh)
        refresh()

    def apply(self):
        for code in self.lang.available_languages():
            if self.lang.language_name(code) == self.selected.get():
                self.lang.set_language(code)
                self.prefs.set("language", code)
                break