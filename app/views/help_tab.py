"""Onglet « Aide » (informations + FAQ). / Help tab (information + FAQ)."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from app.language_manager import LanguageManager
from app.views.widgets import ScrollableFrame


class HelpTab(ttk.Frame):
    """Contenu provisoire : à remplacer par de vrais textes dans lang/<code>.json (clés help.*).
    Placeholder content: replace with real texts in the language files (help.* keys).

    Les 3 points d'information et les 3 questions/réponses viennent des clés
    help.info_1..3 et help.q1..3 / help.a1..3. Pour en ajouter, augmenter INFO_ITEM_COUNT et/ou FAQ_ITEM_COUNT.
    """

    INFO_ITEM_COUNT = 5
    FAQ_ITEM_COUNT = 5

    def __init__(self, parent: tk.Misc, lang: LanguageManager) -> None:
        super().__init__(parent, padding=12)
        t = lang.t
        self._bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self._bold_font.configure(weight="bold")

        scroll = ScrollableFrame(self, orient="vertical")  # défilante : le contenu pourra grandir
        scroll.pack(fill="both", expand=True)
        content = scroll.inner
        content.columnconfigure(0, weight=1)

        info = ttk.LabelFrame(content, text=t("help.info_title"), padding=12)
        info.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 12))
        for number in range(1, self.INFO_ITEM_COUNT + 1):
            ttk.Label(info, text="•  " + t(f"help.info_{number}"), wraplength=900, justify="left").pack(
                anchor="w", pady=2)

        faq = ttk.LabelFrame(content, text=t("help.faq_title"), padding=12)
        faq.grid(row=1, column=0, sticky="ew", padx=6)
        for number in range(1, self.FAQ_ITEM_COUNT + 1):
            ttk.Label(faq, text=t(f"help.q{number}"), font=self._bold_font, wraplength=900, justify="left").pack(
                anchor="w", pady=(8 if number > 1 else 0, 0))
            ttk.Label(faq, text=t(f"help.a{number}"), wraplength=900, justify="left").pack(anchor="w", pady=(2, 0))
