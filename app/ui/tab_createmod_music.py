# Importations de base
import tkinter as tk
from tkinter import ttk

class CreateMusicModTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)

        self.music_files = {i: None for i in range(1, 16)}

        # Ajout des widgets dans une Frame (nécessaire pour le widget Text de la description)

        self.infosContent_text = ttk.Label(self)
        self.infosContent_text.pack(padx=10, pady=10)

        infosContent = ttk.Frame(self)
        infosContent.pack(fill="both", padx=10, pady=10)

        ## Formulaire des infos du mod
        self.enterModName_text = ttk.Label(infosContent)
        self.enterModName_text.grid(row=2, column=0, padx=10, pady=10)
        self.enterModAuthor_text = ttk.Label(infosContent)
        self.enterModAuthor_text.grid(row=3, column=0, padx=10, pady=10)
        self.enterModDescription_text = ttk.Label(infosContent)
        self.enterModDescription_text.grid(row=4, column=0, padx=10, pady=10)

        self.var_name = tk.StringVar(value='',name='modname')
        self.var_author = tk.StringVar(value='',name='modauthor')
        self.var_description = tk.StringVar(value='',name='moddescription')
        ttk.Entry(infosContent, textvariable=self.var_name, width=40).grid(row=2, column=1, padx=10, pady=10)
        ttk.Entry(infosContent, textvariable=self.var_author, width=40).grid(row=3, column=1, padx=10, pady=10)
        tk.Text(infosContent, height=4, width=40).grid(row=4, column=1, padx=10, pady=10)
        
        self.fichiersContent_text = ttk.Label(self)
        self.fichiersContent_text.pack(padx=10, pady=10)

        fichiersContent = ttk.Frame(self)
        fichiersContent.pack(fill="both", padx=10, pady=10)





        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.
        def refresh():
            self.infosContent_text.config(text=lang.translate("tab.createmod.music_sfx.infosLabel"))
            self.enterModName_text.config(text=lang.translate("tab.createmod.music_sfx.enterModName"))
            self.enterModAuthor_text.config(text=lang.translate("tab.createmod.music_sfx.enterModAuthor"))
            self.enterModDescription_text.config(text=lang.translate("tab.createmod.music_sfx.enterModDescription"))
            self.fichiersContent_text.config(text=lang.translate("tab.createmod.music_sfx.fichiersLabel"), wraplength=400)

        lang.register(refresh)
        refresh()
