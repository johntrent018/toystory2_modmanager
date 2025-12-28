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

        self.lvl1_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl1_uploadwav_btn.grid(row=0, column=0, padx=10, pady=10)
        self.lvl2_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl2_uploadwav_btn.grid(row=0, column=1, padx=10, pady=10)
        self.lvl3_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl3_uploadwav_btn.grid(row=0, column=2, padx=10, pady=10)
        self.lvl4_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl4_uploadwav_btn.grid(row=0, column=3, padx=10, pady=10)
        self.lvl5_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl5_uploadwav_btn.grid(row=0, column=4, padx=10, pady=10)
        self.lvl6_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl6_uploadwav_btn.grid(row=1, column=0, padx=10, pady=10)
        self.lvl7_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl7_uploadwav_btn.grid(row=1, column=1, padx=10, pady=10)
        self.lvl8_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl8_uploadwav_btn.grid(row=1, column=2, padx=10, pady=10)
        self.lvl9_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl9_uploadwav_btn.grid(row=1, column=3, padx=10, pady=10)
        self.lvl10_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl10_uploadwav_btn.grid(row=1, column=4, padx=10, pady=10)
        self.lvl11_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl11_uploadwav_btn.grid(row=2, column=0, padx=10, pady=10)
        self.lvl12_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl12_uploadwav_btn.grid(row=2, column=1, padx=10, pady=10)
        self.lvl13_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl13_uploadwav_btn.grid(row=2, column=2, padx=10, pady=10)
        self.lvl14_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl14_uploadwav_btn.grid(row=2, column=3, padx=10, pady=10)
        self.lvl15_uploadwav_btn = tk.Button(fichiersContent, command=self.uploadwavfile)
        self.lvl15_uploadwav_btn.grid(row=2, column=4, padx=10, pady=10)

        self.createMod_btn = tk.Button(self, command=self.uploadwavfile)
        self.createMod_btn.pack(padx=10, pady=10)

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
            self.lvl1_uploadwav_btn.config(text=lang.translate("levels_name_1"))
            self.lvl2_uploadwav_btn.config(text=lang.translate("levels_name_2"))
            self.lvl3_uploadwav_btn.config(text=lang.translate("levels_name_3"))
            self.lvl4_uploadwav_btn.config(text=lang.translate("levels_name_4"))
            self.lvl5_uploadwav_btn.config(text=lang.translate("levels_name_5"))
            self.lvl6_uploadwav_btn.config(text=lang.translate("levels_name_6"))
            self.lvl7_uploadwav_btn.config(text=lang.translate("levels_name_7"))
            self.lvl8_uploadwav_btn.config(text=lang.translate("levels_name_8"))
            self.lvl9_uploadwav_btn.config(text=lang.translate("levels_name_9"))
            self.lvl10_uploadwav_btn.config(text=lang.translate("levels_name_10"))
            self.lvl11_uploadwav_btn.config(text=lang.translate("levels_name_11"))
            self.lvl12_uploadwav_btn.config(text=lang.translate("levels_name_12"))
            self.lvl13_uploadwav_btn.config(text=lang.translate("levels_name_13"))
            self.lvl14_uploadwav_btn.config(text=lang.translate("levels_name_14"))
            self.lvl15_uploadwav_btn.config(text=lang.translate("levels_name_15"))
            self.lvl15_uploadwav_btn.config(text=lang.translate("levels_name_15"))
            self.createMod_btn.config(text=lang.translate("tab.createmod.music_sfx.createmodBtn"))

        lang.register(refresh)
        refresh()

    def uploadwavfile():
        filename = filedialog.askopenfilename()
        print('Selected:', filename)
