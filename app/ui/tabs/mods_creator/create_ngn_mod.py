# Importations de base
import tkinter as tk
from tkinter import ttk
from preferences import Preferences

class CreateNGNModTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)
        
        self.ngn_files = {i: None for i in range(1, 16)}

        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.
        def refresh():
            self.label.config(text=lang.translate("app_data.tabs.create_mod.sub_tabs.ngn.h1"))

        lang.register(refresh)
        refresh()
