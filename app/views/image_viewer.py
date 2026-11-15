"""Visionneuse d'images en modale. / Modal image viewer."""
from __future__ import annotations

import io
import tkinter as tk
from tkinter import ttk
from typing import Callable

from PIL import Image, ImageTk

from app.language_manager import LanguageManager


def load_photo(data: bytes, max_size: tuple[int, int]) -> ImageTk.PhotoImage:
    """Décode une image et la réduit pour tenir dans `max_size` (proportions conservées).
    Decode an image and shrink it to fit `max_size` (aspect ratio kept).

    Pillow permet de lire JPG/WEBP en plus de PNG/GIF, que Tkinter seul ne sait pas lire.
    """
    image = Image.open(io.BytesIO(data))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    image.thumbnail(max_size)
    return ImageTk.PhotoImage(image)


class ImageViewer(tk.Toplevel):
    """Fenêtre modale : image agrandie + flèches gauche/droite pour naviguer.
    Modal window: enlarged image + left/right arrows to browse.
    """

    def __init__(
        self,
        parent: tk.Misc,
        lang: LanguageManager,
        count: int,
        load_image: Callable[[int], bytes],
        start_index: int = 0,
    ) -> None:
        super().__init__(parent)
        self._lang = lang
        self._count = count
        self._load_image = load_image  # index -> octets de l'image (chargée à la demande)
        self._index = start_index
        self._photo: ImageTk.PhotoImage | None = None  # référence obligatoire, sinon l'image disparaît
        self._max_size = (int(self.winfo_screenwidth() * 0.7), int(self.winfo_screenheight() * 0.7))

        self.transient(parent.winfo_toplevel())
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._image_label = ttk.Label(self, anchor="center")
        self._image_label.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        if count > 1:
            ttk.Button(self, text="◀", width=3, command=self.previous).grid(row=0, column=0, padx=(8, 0))
            ttk.Button(self, text="▶", width=3, command=self.next).grid(row=0, column=2, padx=(0, 8))

        self.bind("<Left>", lambda _e: self.previous())
        self.bind("<Right>", lambda _e: self.next())
        self.bind("<Escape>", lambda _e: self.destroy())

        self._show()
        self.wait_visibility()  # grab_set exige une fenêtre déjà affichée
        self.grab_set()         # rend la fenêtre modale
        self.focus_set()

    def previous(self) -> None:
        """Image précédente (boucle). / Previous image (wraps around)."""
        self._index = (self._index - 1) % self._count
        self._show()

    def next(self) -> None:
        """Image suivante (boucle). / Next image (wraps around)."""
        self._index = (self._index + 1) % self._count
        self._show()

    def _show(self) -> None:
        self.title(self._lang.t("image_viewer.title", current=self._index + 1, total=self._count))
        try:
            self._photo = load_photo(self._load_image(self._index), self._max_size)
            self._image_label.configure(image=self._photo, text="")
        except Exception:  # image corrompue ou format non géré : on affiche un message
            self._photo = None
            self._image_label.configure(image="", text=self._lang.t("image_viewer.load_failed"))
