"""Icône de la fenêtre de l'application. / Application window icon."""
from __future__ import annotations

import sys
import tkinter as tk

from PIL import Image, ImageTk

from app.app_paths import resource_path

ICON_ICO = "assets/ts2_manager.ico"  # Windows : fichier .ico (plusieurs tailles dans le même fichier)
ICON_PNG = "assets/ts2_manager.png"  # autres systèmes, ou repli si le .ico est refusé


def apply_app_icon(root: tk.Tk) -> None:
    """Remplace la plume Tk par l'icône de l'appli ; si elle est absente ou illisible, on garde la plume.
    Replace the Tk feather with the app icon; if it is missing or unreadable, keep the feather.

    Un échec n'est jamais bloquant : le message est simplement écrit dans la console.
    """
    if sys.platform == "win32":
        try:  # sans cela, la barre des tâches affiche l'icône de Python au lieu de celle de l'appli
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ts2.modmanager")
        except (AttributeError, OSError):
            pass
        ico = resource_path(ICON_ICO)
        if ico.is_file():
            try:
                root.iconbitmap(default=str(ico))  # "default" : s'applique aussi aux fenêtres secondaires
                return
            except tk.TclError as err:
                print(f"[icône] {ico.name} refusé ({err}) : essai avec le PNG", file=sys.stderr)

    png = resource_path(ICON_PNG)
    if png.is_file():
        try:
            photo = ImageTk.PhotoImage(Image.open(png))
            root.iconphoto(True, photo)
            root._app_icon = photo  # garder la référence, sinon l'image disparaît
        except (OSError, tk.TclError) as err:
            print(f"[icône] {png.name} illisible ({err}) : icône par défaut", file=sys.stderr)
