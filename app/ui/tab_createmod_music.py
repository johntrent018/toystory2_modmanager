# Importations de base
import tkinter as tk
from tkinter import ttk

class CreateMusicModTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)

        self.music_files = {i: None for i in range(1, 16)}

        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.
        def refresh():
            self.label.config(text=lang.translate("tab.createmod.music_sfx.label"))

        lang.register(refresh)
        refresh()
