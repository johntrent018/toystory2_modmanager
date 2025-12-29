# Importations de base
import tkinter as tk
from tkinter import ttk
# Importation de composants
from app.ui.tab_modlist import ModListTab
from app.ui.tab_createmod import CreateModTab
from app.ui.tab_help import HelpTab
from app.ui.tab_settings import SettingsTab
from app.ui.tab_about import AboutTab
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

        # Taille minimale de la fenêtre
        self.minsize(640, 480)

        # Création du Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Création des onglets du Notebook
        self.modlist = ModListTab(self.notebook, lang)
        self.createmod = CreateModTab(self.notebook, lang)
        self.tutorial = HelpTab(self.notebook, lang)
        self.settings = SettingsTab(self.notebook, lang, prefs)
        self.about = AboutTab(self.notebook, lang)

        # Ajout des onglets au Notebook
        self.notebook.add(self.modlist)
        self.notebook.add(self.createmod)
        self.notebook.add(self.tutorial)
        self.notebook.add(self.settings)
        self.notebook.add(self.about)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.
        def refresh():
            self.title(lang.translate("app_data.app_title"))
            self.notebook.tab(self.modlist, text=lang.translate("app_data.tabs.mods_list.tab_title"))
            self.notebook.tab(self.createmod, text=lang.translate("app_data.tabs.create_mod.tab_title"))
            self.notebook.tab(self.tutorial, text=lang.translate("app_data.tabs.help_tuto.tab_title"))
            self.notebook.tab(self.settings, text=lang.translate("app_data.tabs.settings.tab_title"))
            self.notebook.tab(self.about, text=lang.translate("app_data.tabs.about.tab_title"))

        lang.register(refresh)
        refresh()