# Importations de base
import tkinter as tk
from tkinter import ttk
# Importation de composants
from preferences import Preferences
from app.ui.tab_createmod_ngn import CreateNGNModTab
from app.ui.tab_createmod_music import CreateMusicModTab

class CreateModTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)

        # Création du Notebook
        self.createmod_notebook = ttk.Notebook(self)
        self.createmod_notebook.pack(fill="both", expand=True)
        
        # Création des onglets du Notebook
        self.createmod_ngn = CreateNGNModTab(self.createmod_notebook, lang)
        self.createmod_music = CreateMusicModTab(self.createmod_notebook, lang)
        
        # Ajout des onglets au Notebook
        self.createmod_notebook.add(self.createmod_ngn)
        self.createmod_notebook.add(self.createmod_music)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.

        def refresh():
            self.createmod_notebook.tab(self.createmod_ngn, text=lang.translate("app_data.tabs.create_mod.sub_tabs.ngn.tab_title"))
            self.createmod_notebook.tab(self.createmod_music, text=lang.translate("app_data.tabs.create_mod.sub_tabs.music_sfx.tab_title"))
        
        lang.register(refresh)
        refresh()