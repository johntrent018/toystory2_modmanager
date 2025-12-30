import tkinter as tk
from tkinter import ttk
from app.core.preferences import Preferences

class HelpTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        def refresh():
            self.label.config(text=lang.translate("app_data.tabs.help_tuto.h1"))

        lang.register(refresh)
        refresh()