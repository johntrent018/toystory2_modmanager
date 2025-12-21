import tkinter as tk
from tkinter import ttk
from preferences import Preferences

class AboutTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.labelCreatedBy_text = ttk.Label(self)
        self.labelCreatedBy_text.pack(padx=20, pady=20)

        def refresh():
            self.labelCreatedBy_text.config(text=lang.translate("tab.about.createdby_text"))

        lang.register(refresh)
        refresh()