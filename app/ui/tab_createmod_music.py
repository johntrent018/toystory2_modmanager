# Importations de base
import tkinter as tk
from tkinter import ttk, filedialog

class CreateMusicModTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)

        self.music_files = {i: None for i in range(1, 16)}

        self.infosContent_text = ttk.Label(self)
        self.infosContent_text.pack(padx=10, pady=10)

        # Ajout des widgets d'information dans une Frame (nécessaire pour le widget Text de la description)

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
        
        ## Fin de la première Frame

        self.fichiersContent_text = ttk.Label(self)
        self.fichiersContent_text.pack(padx=10, pady=10)

        # Ajout des widgets d'envoi de fichiers dans une seconde Frame

        fichiersContent = ttk.Frame(self)
        fichiersContent.pack(fill="both", padx=10, pady=10)

        ## Voir pour optimiser ça pour un code plus propre.
        ## Pour chaque niveau, on créé un bouton d'upload de fichier

        liste_niveaux = lang.translate("game.levels.names")
        print(liste_niveaux[0])

        self.lvl1_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl1_uploadwav_btn.grid(row=0, column=0, padx=10, pady=10)
        self.lvl2_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl2_uploadwav_btn.grid(row=1, column=0, padx=10, pady=10)
        self.lvl3_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl3_uploadwav_btn.grid(row=2, column=0, padx=10, pady=10)
        self.lvl4_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl4_uploadwav_btn.grid(row=3, column=0, padx=10, pady=10)
        self.lvl5_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl5_uploadwav_btn.grid(row=4, column=0, padx=10, pady=10)
        self.lvl6_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl6_uploadwav_btn.grid(row=5, column=0, padx=10, pady=10)
        self.lvl7_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl7_uploadwav_btn.grid(row=6, column=0, padx=10, pady=10)
        self.lvl8_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl8_uploadwav_btn.grid(row=7, column=0, padx=10, pady=10)
        self.lvl9_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl9_uploadwav_btn.grid(row=8, column=0, padx=10, pady=10)
        self.lvl10_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl10_uploadwav_btn.grid(row=9, column=0, padx=10, pady=10)
        self.lvl11_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl11_uploadwav_btn.grid(row=10, column=0, padx=10, pady=10)
        self.lvl12_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl12_uploadwav_btn.grid(row=11, column=0, padx=10, pady=10)
        self.lvl13_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl13_uploadwav_btn.grid(row=12, column=0, padx=10, pady=10)
        self.lvl14_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl14_uploadwav_btn.grid(row=13, column=0, padx=10, pady=10)
        self.lvl15_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl15_uploadwav_btn.grid(row=14, column=0, padx=10, pady=10)

        self.createMod_btn = tk.Button(self, command=self.uploadwavfile)
        self.createMod_btn.pack(padx=10, pady=10)

        # Méthode de rafraîchissement de l'interface (design pattern : Observer)
        # afin de permettre au bouton de sauvegarde de la langue (onglet des paramètres)
        # d'appeler la méthode refresh() dans l'app et dans chaque onglet du Notebook
        # afin de rafraîchir le texte.

        def refresh():
            # On récupère les strings pour ce sous-onglet
            strings = lang.translate("app_data.tabs.create_mod.sub_tabs.music_sfx")
            self.infosContent_text.config(text=lang.translate(strings["infosMod_label"]))
            self.enterModName_text.config(text=lang.translate(strings["inputName_label"]))
            self.enterModAuthor_text.config(text=lang.translate(strings["inputAuthor_label"]))
            self.enterModDescription_text.config(text=lang.translate(strings["inputDescription_label"]))
            self.fichiersContent_text.config(text=lang.translate(strings["fichiersMod_label"]), wraplength=400)
            self.createMod_btn.config(text=lang.translate(strings["createMod_btn"]))
            # On récupère les strings des noms des niveaux
            levelsNamesStrings = lang.translate("game_data.levels_names")
            for i in range(0, 15):
                btn = getattr(self, f"lvl{i+1}_uploadwav_btn")
                btn.config(text=lang.translate(levelsNamesStrings[i]))

        lang.register(refresh)
        refresh()

    def uploadwavfile(self):
        filename = filedialog.askopenfilename()
        print('Selected:', filename)
