"""Curseurs personnalisés (main ouverte / poing fermé). / Custom cursors (open hand / closed fist)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from typing import Iterator

from app.app_paths import resource_path

_FALLBACK = "fleur"  # curseur standard « déplacer » (rose des vents) si le curseur personnalisé est indisponible
_cache: dict[str, str] = {}


def _short_path(path: Path) -> str | None:
    """Chemin court 8.3 (sans espaces) d'un fichier, sous Windows. / Windows 8.3 short path."""
    try:
        import ctypes
        buffer = ctypes.create_unicode_buffer(520)
        if ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, 520):
            return buffer.value
    except (AttributeError, OSError):
        pass
    return None


def _candidate_paths(path: Path) -> Iterator[str]:
    """Chemins à essayer, du plus simple au plus détourné. Tk lit mal certains chemins
    (espaces, caractères spéciaux) : on lui propose plusieurs formes du même fichier.
    """
    yield path.as_posix()
    short = _short_path(path)
    if short:
        yield short.replace("\\", "/")
    try:  # dernier recours : une copie dans le dossier temporaire (chemin généralement simple)
        copy = Path(tempfile.gettempdir()) / "ts2_modmanager_cursors" / path.name
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, copy)
        yield copy.as_posix()
    except OSError:
        return


def grab_cursor(name: str, widget: tk.Misc) -> str:
    """Spécification de curseur pour `name` ("grab" = main ouverte, "grabbing" = poing fermé).
    Cursor specification for `name`.

    Tk ne propose pas de main sur toutes les plateformes : sous Windows on charge un fichier
    assets/cursors/<name>.cur. Si le chargement échoue, on retombe sur le curseur standard
    « fleur » (l'appli reste utilisable) et la raison est écrite dans la console.
    """
    if name in _cache:
        return _cache[name]
    spec = _FALLBACK
    path = resource_path(f"assets/cursors/{name}.cur")
    if sys.platform.startswith("win"):
        if not path.is_file():
            print(f"[curseur] « {name} » : fichier introuvable : {path}", file=sys.stderr)
        else:
            probe = tk.Label(widget)  # widget jetable pour tester si Tk accepte le curseur
            errors = []
            found = False
            for raw in _candidate_paths(path):
                # Deux écritures : brute, puis entre accolades (chemin avec espaces).
                for candidate in (f"@{raw}", f"@{{{raw}}}"):
                    try:
                        probe.configure(cursor=candidate)
                        spec, found = candidate, True
                        break
                    except tk.TclError as err:
                        errors.append(f"{candidate} → {err}")
                if found:
                    break
            probe.destroy()
            if not found:
                print(f"[curseur] « {name} » refusé par Tk, curseur de secours utilisé :", file=sys.stderr)
                for line in errors:
                    print("   ", line, file=sys.stderr)
    _cache[name] = spec
    return spec
