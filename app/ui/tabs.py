import tkinter as tk
from tkinter import ttk
from preferences import Preferences

class ModListTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        def refresh():
            self.label.config(text=lang.translate("modlist.label"))

        lang.register(refresh)
        refresh()


class TutorialTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        def refresh():
            self.label.config(text=lang.translate("tutorial.label"))

        lang.register(refresh)
        refresh()


class SettingsTab(ttk.Frame):
    def __init__(self, parent, lang, prefs):
        super().__init__(parent)

        self.lang = lang
        self.prefs = prefs
        self.selected = tk.StringVar()

        self.label = ttk.Label(self)
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.combo = ttk.Combobox(
            self,
            state="readonly",
            textvariable=self.selected
        )
        self.combo.grid(row=0, column=1, padx=10, pady=10)

        self.button = ttk.Button(self, command=self.apply)
        self.button.grid(row=1, column=0, columnspan=2, pady=10)

        def refresh():
            self.label.config(text=lang.translate("settings.language"))
            self.button.config(text=lang.translate("settings.apply"))

            values = [
                lang.language_name(code)
                for code in lang.available_languages()
            ]
            self.combo["values"] = values
            self.selected.set(lang.language_name(lang.lang))

        lang.register(refresh)
        refresh()

    def apply(self):
        for code in self.lang.available_languages():
            if self.lang.language_name(code) == self.selected.get():
                self.lang.set_language(code)
                self.prefs.set("language", code)
                break

class AboutTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.labelCreatedBy_text = ttk.Label(self)
        self.labelCreatedBy_text.pack(padx=20, pady=20)

        def refresh():
            self.labelCreatedBy_text.config(text=lang.translate("tab.about.createdby_text"))

        lang.register(refresh)
        refresh()