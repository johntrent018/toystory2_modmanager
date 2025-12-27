# Importations de base
import tkinter as tk
from tkinter import ttk, font
import webbrowser
# Importation de composants
from preferences import Preferences

class AboutTab(ttk.Frame):

    def __init__(self, parent, lang):

        super().__init__(parent)

        # Ajout des widgets
        self.labelCreatedBy_text = ttk.Label(self, cursor="hand2")
        self.labelCreatedBy_text.pack(padx=20, pady=20)
        self.labelCreatedBy_text.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("tab.about.createdby_link")))

        self.labelThanksDiscord_text = ttk.Label(self, cursor="hand2")
        self.labelThanksDiscord_text.pack(padx=20, pady=20)
        self.labelThanksDiscord_text.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("tab.about.thanksDiscord_link")))

        self.labelLicense_text = ttk.Label(self)
        self.labelLicense_text.pack(padx=20, pady=20)
        self.labelLicense_description = ttk.Label(self)
        self.labelLicense_description.pack(padx=20, pady=20)
        self.labelLicense_link = ttk.Label(self, cursor="hand2")
        self.labelLicense_link.pack(padx=20, pady=20)
        self.labelLicense_link.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("tab.about.license_link")))

        # Méthode dans laquelle on vient ajouter une ligne par widget qu'on souhaite traduire
        # et servant à afficher/ré-afficher les widgets en allant chercher le texte associée dans la langue des réglages
        def refresh():
            self.labelCreatedBy_text.config(text=lang.translate("tab.about.createdby_text"))
            self.labelThanksDiscord_text.config(text=lang.translate("tab.about.thanksDiscord_text"))
            self.labelLicense_text.config(text=lang.translate("tab.about.license_text"))
            self.labelLicense_description.config(text=lang.translate("tab.about.license_description"), wraplength=500)
            self.labelLicense_link.config(text=lang.translate("tab.about.license_link"))

        lang.register(refresh)
        refresh()

    def openwebpage(self, url):
        webbrowser.open_new(url)