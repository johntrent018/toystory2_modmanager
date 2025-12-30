# Importations de base
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
# Importation de composants
from app.core.preferences import Preferences

class SettingsTab(ttk.Frame):

    # Constructeur
    def __init__(self, parent, lang, prefs):

        super().__init__(parent)
        
        self.lang = lang
        self.prefs = prefs

        # --------------------------------
        # Partie "GamePath" de l'interface
        # --------------------------------

        # Variable Tkinter pour l'input de texte du gamepath
        self.game_path_var = tk.StringVar()

        # On charge la valeur de gamepath si elle existe déjà dans les préférences
        saved_path = self.prefs.get("game_path")
        if saved_path:
            self.game_path_var.set(saved_path)

        # self.columnconfigure(1, weight=1)

        self.label = ttk.Label(self)
        self.label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))

        self.browse_gamepath_btn = ttk.Button(self, command=self.browse_game_exe)
        self.browse_gamepath_btn.grid(row=1, column=0, padx=10)

        self.entry = ttk.Entry(self, textvariable=self.game_path_var)
        self.entry.grid(row=1, column=1, columnspan=10, sticky="ew", padx=10)

        self.apply_gamepath_btn = ttk.Button(self, command=self.apply_game_path)
        self.apply_gamepath_btn.grid(row=1, column=11, padx=10, pady=10, sticky="w")




        # ------------------------------
        # Partie "Langue" de l'interface
        # ------------------------------

        # Propriétés et variables liées à la partie Langue des paramétrages
        self.selected = tk.StringVar()

        # Label avant la liste déroulante des langues
        self.labelChooseLanguage = ttk.Label(self)
        self.labelChooseLanguage.grid(row=6, column=0, padx=10, pady=10, sticky="w")

        # Liste déroulante du choix de la langue
        self.combo = ttk.Combobox(
            self,
            state="readonly",
            textvariable=self.selected
        )
        self.combo.grid(row=6, column=1, padx=10, pady=10)

        # Bouton "Appliquer" du choix de la langue
        self.button = ttk.Button(self, command=self.apply)
        self.button.grid(row=6, column=3, columnspan=2, pady=10)

        def refresh():

            # Rafraîchissement visuel des chaînes de caractères liées au gamepath
            self.browse_gamepath_btn.config(text=lang.translate("app_data.tabs.settings.selectGamePath_btn"))
            self.apply_gamepath_btn.config(text=lang.translate("app_data.widgets_terms.apply_btn"))
            
            # Rafraîchissement visuel des chaînes de caractères liées aux langues 
            self.labelChooseLanguage.config(text=lang.translate("app_data.tabs.settings.chooseLang_label"))
            self.button.config(text=lang.translate("app_data.widgets_terms.apply_btn"))

            values = [
                lang.language_name(code)
                for code in lang.available_languages()
            ]
            self.combo["values"] = values
            self.selected.set(lang.language_name(lang.current_lang))

        lang.register(refresh)
        refresh()

    # Méthode d'action pour la sélection d'une langue
    def apply(self):
        for code in self.lang.available_languages():
            if self.lang.language_name(code) == self.selected.get():
                self.lang.set_language(code)
                self.prefs.set("language", code)
                break

    # Méthodes d'action pour la sélection du gamepath
    def browse_game_exe(self):
        path = filedialog.askopenfilename(
            title=self.lang.translate("app_data.tabs.settings.selectGamePath_modal.modal_title"),
            filetypes=[("Executable", "*.exe")]
        )
        if path:
            self.game_path_var.set(path)

    def apply_game_path(self):
        exe_path = self.game_path_var.get()

        if not exe_path or not os.path.isfile(exe_path):
            messagebox.showerror(
                self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.titles.error"),
                self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.descriptions.select_exe")
            )
            return

        game_root = os.path.dirname(exe_path)

        audio_dir = os.path.join(game_root, "audio")
        data_dir = os.path.join(game_root, "data")
        sfx_dir = os.path.join(data_dir, "sfx")

        if not os.path.isdir(audio_dir):
            self._error(self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.descriptions.audio_missing"))
            return

        if not os.path.isdir(data_dir):
            self._error(self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.descriptions.data_missing"))
            return

        if not os.path.isdir(sfx_dir):
            self._error(self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.descriptions.sfx_missing"))
            return

        # Tout est OK → on sauvegarde
        self.prefs.set("game_path", game_root)

        messagebox.showinfo(
            self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.titles.success"),
            self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.success.game_path_saved")
        )

    def _error(self, msg):
        messagebox.showerror(self.lang.translate("app_data.tabs.settings.selectGamePath_modal.messages_on_opening.titles.error"), msg)