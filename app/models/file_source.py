"""Origine d'un fichier du formulaire de mod. / Origin of a file in the mod form."""
from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileSource:
    """Un NGN, une image ou le logo : fichier choisi sur le disque, fichier déjà présent dans
    l'archive du mod en cours de modification, ou contenu en mémoire (logo recadré).
    An NGN, image or logo: a file picked on disk, a file already inside the edited mod's archive,
    or in-memory content (cropped logo).
    """

    path: Path | None = None   # fichier choisi sur le disque
    member: str | None = None  # sinon : chemin interne dans l'ancienne archive
    data: bytes | None = None  # sinon : contenu déjà en mémoire
    label: str = ""            # nom affiché pour un contenu en mémoire

    @property
    def name(self) -> str:
        """Nom de fichier à afficher. / File name to display."""
        if self.path is not None:
            return self.path.name
        if self.member is not None:
            return Path(self.member).name
        return self.label

    def read(self, old_archive: zipfile.ZipFile | None) -> bytes:
        """Contenu du fichier. / File content.

        Raises:
            KeyError: fichier de l'archive demandé alors qu'aucune archive n'est ouverte.
        """
        if self.data is not None:
            return self.data
        if self.path is not None:
            return self.path.read_bytes()
        if old_archive is None or self.member is None:
            raise KeyError(self.member)
        return old_archive.read(self.member)
