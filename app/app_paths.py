"""Chemins compatibles PyInstaller. / PyInstaller-compatible paths."""
from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Chemin d'un asset embarqué dans l'exe. / Path of an asset bundled in the exe.

    En mode PyInstaller (--onefile), les assets sont extraits dans un dossier
    temporaire exposé par `sys._MEIPASS`. En développement, on part de la racine du projet.
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative_path


def get_app_dir() -> Path:
    """Dossier des données modifiables (mods, préférences). / Folder for writable data.

    Une fois compilé : le dossier de l'exe (PAS le dossier temporaire de PyInstaller,
    qui est supprimé à chaque fermeture). En développement : la racine du projet.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
