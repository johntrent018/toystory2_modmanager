"""Fenêtre de rognage de l'icône d'un mod. / Mod icon cropping dialog."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageDraw, ImageEnhance, ImageTk

from app.language_manager import LanguageManager
from app.models.errors import ModError
from app.models.logo import fit_square_box, load_image

MAX_DISPLAY = (560, 420)  # taille maximale d'affichage de l'image dans la fenêtre


class CropDialog(tk.Toplevel):
    """Modale : on déplace un carré sur l'image (glisser) et on règle sa taille (curseur).
    Modal: drag a square over the image and adjust its size with a slider.

    Après `wait_window()`, `result` vaut le carré (gauche, haut, droite, bas) en pixels de
    l'image d'ORIGINE, ou None si annulé. / `result` is the box in ORIGINAL pixels, or None.
    """

    def __init__(self, parent: tk.Misc, lang: LanguageManager, image: Image.Image) -> None:
        super().__init__(parent)
        self.result: tuple[int, int, int, int] | None = None
        self._image = image
        self._width, self._height = image.size
        self._scale = min(MAX_DISPLAY[0] / self._width, MAX_DISPLAY[1] / self._height, 1.0)
        display_size = (max(1, round(self._width * self._scale)), max(1, round(self._height * self._scale)))
        # Image affichée normale + version assombrie (pour tout ce qui est HORS du carré).
        self._base = image.convert("RGB").resize(display_size, Image.Resampling.LANCZOS)
        self._dim = ImageEnhance.Brightness(self._base).enhance(0.4)
        self._center = (self._width / 2, self._height / 2)
        self._zoom = tk.DoubleVar(value=100)  # taille du carré, en % du petit côté de l'image
        self._photo: ImageTk.PhotoImage | None = None

        self.title(lang.t("crop.title"))
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        ttk.Label(self, text=lang.t("crop.help"), wraplength=display_size[0]).pack(padx=12, pady=(12, 6))
        self._canvas = tk.Canvas(self, width=display_size[0], height=display_size[1], highlightthickness=0,
                                 cursor="fleur")
        self._canvas.pack(padx=12)
        self._item = self._canvas.create_image(0, 0, anchor="nw")
        self._canvas.bind("<Button-1>", self._on_drag)
        self._canvas.bind("<B1-Motion>", self._on_drag)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=12, pady=8)
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text=lang.t("crop.zoom")).grid(row=0, column=0, padx=(0, 8))
        ttk.Scale(controls, from_=10, to=100, variable=self._zoom, command=lambda _v: self._render()).grid(
            row=0, column=1, sticky="ew")
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(buttons, text=lang.t("crop.ok"), command=self._on_ok).pack(side="right")
        ttk.Button(buttons, text=lang.t("crop.cancel"), command=self.destroy).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self.destroy())

        self._render()
        self.wait_visibility()  # grab_set exige une fenêtre déjà affichée
        self.grab_set()         # rend la fenêtre modale
        self.focus_set()

    def _box(self) -> tuple[int, int, int, int]:
        """Carré actuel en pixels de l'image d'origine. / Current square in original pixels."""
        size = min(self._width, self._height) * self._zoom.get() / 100
        return fit_square_box(self._width, self._height, self._center[0], self._center[1], size)

    def _on_drag(self, event: tk.Event) -> None:
        self._center = (event.x / self._scale, event.y / self._scale)
        self._render()

    def _render(self) -> None:
        """Redessine : fond assombri, carré à l'éclairage normal, liseré blanc. / Redraw."""
        left, top, right, bottom = (round(v * self._scale) for v in self._box())
        out = self._dim.copy()
        out.paste(self._base.crop((left, top, right, bottom)), (left, top))
        ImageDraw.Draw(out).rectangle((left, top, right - 1, bottom - 1), outline="white", width=2)
        self._photo = ImageTk.PhotoImage(out)  # garder la référence
        self._canvas.itemconfigure(self._item, image=self._photo)

    def _on_ok(self) -> None:
        self.result = self._box()
        self.destroy()


def ask_crop_box(parent: tk.Misc, lang: LanguageManager, path: Path) -> tuple[int, int, int, int] | None:
    """Ouvre l'image, affiche la fenêtre de rognage et renvoie le carré choisi (ou None).
    Open the image, show the crop dialog and return the chosen box (or None).

    Renvoie None si l'image est illisible (le contrôleur l'a normalement déjà vérifiée).
    """
    try:
        image = load_image(path)
    except ModError:
        return None
    dialog = CropDialog(parent, lang, image)
    dialog.wait_window()
    return dialog.result
