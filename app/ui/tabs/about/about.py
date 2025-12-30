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
        self.labelCreatedBy_text.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("app_data.tabs.about.createdBy_link")))

        self.labelThanksDiscord_text = ttk.Label(self, cursor="hand2")
        self.labelThanksDiscord_text.pack(padx=20, pady=20)
        self.labelThanksDiscord_text.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("app_data.tabs.about.thanksDiscord_link")))

        self.labelLicense_text = ttk.Label(self)
        self.labelLicense_text.pack(padx=20, pady=20)
        self.labelLicense_description = ttk.Label(self)
        self.labelLicense_description.pack(padx=20, pady=20)
        self.labelLicense_link = ttk.Label(self, cursor="hand2")
        self.labelLicense_link.pack(padx=20, pady=20)
        self.labelLicense_link.bind("<Button-1>", lambda e: self.openwebpage(lang.translate("app_data.tabs.about.license_link")))

        # Méthode dans laquelle on vient ajouter une ligne par widget qu'on souhaite traduire
        # et servant à afficher/ré-afficher les widgets en allant chercher le texte associée dans la langue des réglages
        def refresh():
            strings = lang.translate("app_data.tabs.about")
            self.labelCreatedBy_text.config(text=strings["createdBy_label"])
            self.labelThanksDiscord_text.config(text=strings["thanksDiscord_label"], wraplength=500)
            self.labelLicense_text.config(text=strings["licenseName_label"])
            self.labelLicense_description.config(text=strings["licenseDescription_label"], wraplength=500)
            self.labelLicense_link.config(text=strings["license_link"])

        lang.register(refresh)
        refresh()

    def openwebpage(self, url):
        webbrowser.open_new(url)