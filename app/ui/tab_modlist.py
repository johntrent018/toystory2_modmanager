import tkinter as tk
from tkinter import ttk
from preferences import Preferences

class ModListTab(ttk.Frame):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.label = ttk.Label(self)
        self.label.pack(padx=20, pady=20)

        def refresh():
            self.label.config(text=lang.translate("modlist.label"))

        lang.register(refresh)
        refresh()