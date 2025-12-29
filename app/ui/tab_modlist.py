import tkinter as tk
from tkinter import ttk
from preferences import Preferences

class ModListTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        def refresh():
            self.label.config(text="Texte en dur : aucune chaîne de caractère associée n'existe pour le moment car les deux-sous onglets n'existent pas encore et existeront à l'avenir dans une branche git 'mods_list'.", wraplength=400)

        lang.register(refresh)
        refresh()