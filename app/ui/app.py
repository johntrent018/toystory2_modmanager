# Importations de base
import tkinter as tk
from tkinter import ttk
# Importation de composants
from app.ui.tabs import HomeTab, TutorialTab, SettingsTab
# Importations tierces
from app.utils.helpers import resource_path

class App(tk.Tk):

    # Constructeur
    def __init__(self, lang, prefs):

        super().__init__()

        # Stockage des dépendances (préférences) pour transmission en aval
        self.lang = lang
        self.prefs = prefs

        # On donne à la fenêtre l'icône du jeu.
        # Si on n'y arrive pas pour une quelconque raison, on laisse l'icône par défaut Tkinter.
        try:
            self.iconbitmap(resource_path("assets/toy2.ico"))
        except Exception:
            pass
        self.minsize(1280, 720)

        # Création du Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Création des onglets du Notebook
        self.home = HomeTab(self.notebook, lang)
        self.tutorial = TutorialTab(self.notebook, lang)
        self.settings = SettingsTab(self.notebook, lang, prefs)

        # Ajout des onglets au Notebook
        self.notebook.add(self.home)
        self.notebook.add(self.tutorial)
        self.notebook.add(self.settings)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.
        def refresh():
            self.title(lang.translate("app.title"))
            self.notebook.tab(self.home, text=lang.translate("tab.home"))
            self.notebook.tab(self.tutorial, text=lang.translate("tab.tutorial"))
            self.notebook.tab(self.settings, text=lang.translate("tab.settings"))

        lang.register(refresh)
        refresh()