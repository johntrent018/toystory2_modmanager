"""Onglet « À propos ». / About tab."""
from __future__ import annotations

import re
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import ttk

from app import app_info
from app.language_manager import LanguageManager

LINK_COLOR = "#1a5fb4"


class AboutTab(ttk.Frame):
    """Deux sections encadrées : « Crédits » (auteur + remerciements) et « Licence ».
    Two framed sections: "Credits" (author + thanks) and "Licence".

    Les phrases sont découpées en morceaux : texte normal et mots-liens cliquables, posés
    côte à côte. Les adresses sont dans app/app_info.py (sauf celle de la licence, qui
    dépend de la langue : clé about.license_url).
    """

    def __init__(self, parent: tk.Misc, lang: LanguageManager) -> None:
        super().__init__(parent, padding=12)
        base = tkfont.nametofont("TkDefaultFont")
        size = base.cget("size")
        self._body_font = base.copy()
        self._body_font.configure(size=size + 1 if size > 0 else size - 1)
        self._link_font = self._body_font.copy()
        self._link_font.configure(underline=True)
        t = lang.t

        # --- Crédits
        credits = ttk.LabelFrame(self, text=t("about.credits_title"), padding=12)
        credits.pack(fill="x", pady=(0, 12))
        repo_links = {"author": (app_info.AUTHOR_NAME, app_info.REPO_URL),
                      "handle": (app_info.AUTHOR_HANDLE, app_info.REPO_URL)}  # nom ET @pseudo ouvrent le dépôt
        self._sentence(credits, t("about.developed_by"), repo_links)
        self._sentence(credits, t("about.thanks"), {"discord": (t("about.discord"), app_info.DISCORD_URL)})

        # --- Licence
        licence = ttk.LabelFrame(self, text=t("about.license_title"), padding=12)
        licence.pack(fill="x")
        row = ttk.Frame(licence)
        row.pack(anchor="w", pady=(0, 8))
        self._link(row, t("about.license_name"), t("about.license_url"))
        note = ttk.Label(licence, text=t("about.license_note"), font=self._body_font, justify="left")
        note.pack(anchor="w")
        # Le texte long se replie sur la largeur disponible (réglage léger, sans mesure de texte).
        licence.bind("<Configure>", lambda event: note.configure(wraplength=max(200, event.width - 40)))

    def _sentence(self, parent: tk.Misc, template: str, links: dict[str, tuple[str, str]]) -> None:
        """Une phrase sur une ligne ; chaque {nom} devient un lien (libellé, adresse) pris dans `links`."""
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=2)
        for part in re.split(r"(\{\w+\})", template):
            match = re.fullmatch(r"\{(\w+)\}", part)
            if match and match.group(1) in links:
                label, url = links[match.group(1)]
                self._link(row, label, url)
            elif part:
                ttk.Label(row, text=part, font=self._body_font).pack(side="left")

    def _link(self, parent: tk.Misc, label: str, url: str) -> None:
        """Mot cliquable (bleu, souligné) qui ouvre `url` dans le navigateur. / Clickable word."""
        link = ttk.Label(parent, text=label, font=self._link_font, foreground=LINK_COLOR, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e, target=url: webbrowser.open(target))
