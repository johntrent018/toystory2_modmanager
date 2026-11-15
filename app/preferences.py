"""Préférences utilisateur (JSON). / User preferences (JSON)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Preferences:
    """Lecture/écriture d'un petit fichier JSON clé → valeur.
    Reads/writes a small key → value JSON file.
    """

    def __init__(self, file_path: Path) -> None:
        self._file = file_path
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            self._data = data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            self._data = {}  # fichier absent ou corrompu : on repart de zéro

    def get(self, key: str, default: Any = None) -> Any:
        """Valeur d'une préférence. / Get a preference."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Modifie une préférence et sauvegarde. / Set a preference and save."""
        self._data[key] = value
        try:
            self._file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as err:
            print(f"Impossible de sauvegarder les préférences : {err}")
