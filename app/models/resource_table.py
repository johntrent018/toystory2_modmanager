"""Table des ressources moddables du jeu (chargée depuis assets/game_resources.json).
Table of the game's moddable resources (loaded from assets/game_resources.json).

Le fichier JSON est LA source de vérité : il relie chaque nom de l'interface (ex. le niveau 3,
la musique du menu…) au fichier du jeu à remplacer. Sa structure :

    "levels": {"3": "data/level06/level.ngn", ...}                 → catégorie ("levels",), clé "3"
    "bgm": {"levels": {"1": "audio/fullhouse.wav"}, "others": {…}} → catégorie ("bgm", "levels"), clé "1"

Les dictionnaires imbriqués forment les dossiers (catégories) ; les textes sont les ressources.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.app_paths import resource_path

RESOURCES_FILE = "assets/game_resources.json"


@dataclass(frozen=True, order=True)
class ResourceId:
    """Identifiant d'une ressource : sa catégorie et sa clé dans game_resources.json.
    Identifier of a resource: its category and its key in game_resources.json.

    `category` est le chemin de dossiers séparé par "/" : "levels", "screens", "bgm/levels"…
    """

    category: str
    key: str

    @property
    def top_category(self) -> str:
        """Première partie de la catégorie ("bgm/levels" → "bgm"). / First part of the category."""
        return self.category.split("/")[0]


@dataclass(frozen=True)
class Resource:
    """Un fichier du jeu pouvant être remplacé par un mod. / A game file a mod can replace."""

    category: tuple[str, ...]  # chemin de dossiers dans le JSON, ex. ("bgm", "levels")
    key: str                   # nom de la ressource dans le JSON, ex. "3" ou "menus"
    game_path: Path            # chemin du fichier, relatif à la racine du jeu

    @property
    def id(self) -> ResourceId:
        return ResourceId("/".join(self.category), self.key)

    @property
    def extension(self) -> str:
        """Extension attendue pour le fichier d'un mod, en minuscules (ex. ".ngn", ".bmp").
        Extension the mod's file must have, lowercase.
        """
        return self.game_path.suffix.lower()

    @property
    def archive_member(self) -> str:
        """Nom du fichier DANS l'archive d'un mod. / File name INSIDE a mod archive.

        Les niveaux gardent leur nom historique (levels/level4.ngn : compatibilité avec les anciens mods) ;
        les autres catégories utilisent <catégorie>/<clé><extension> (ex. screens/loading.ngn).
        """
        if self.category == ("levels",):
            return f"levels/level{self.key}.ngn"
        return f"{'/'.join(self.category)}/{self.key}{self.extension}"

    @property
    def vanilla_path(self) -> Path:
        """Où est rangée la sauvegarde du fichier d'origine, relativement à mods/_vanilla.
        Where the original file's backup is kept, relative to mods/_vanilla.

        Dossiers = catégories du JSON ; nom = clé + extension d'origine
        (ex. levels/3.ngn, bgm/others/menus.wav).
        """
        return Path(*self.category) / f"{self.key}{self.game_path.suffix}"


class ResourceTable:
    """Accès aux ressources par catégorie et par clé. / Access to resources by category and key."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._resources: dict[tuple[tuple[str, ...], str], Resource] = {}
        self._walk(data, ())

    def _walk(self, node: dict[str, Any], category: tuple[str, ...]) -> None:
        for key, value in node.items():
            if isinstance(value, dict):
                self._walk(value, category + (key,))  # un sous-objet = un sous-dossier
            elif isinstance(value, str):
                game_path = Path(value)
                if game_path.is_absolute() or ".." in game_path.parts:
                    raise ValueError(f"Chemin de ressource non autorisé dans {RESOURCES_FILE} : {value!r}")
                self._resources[(category, key)] = Resource(category, key, game_path)

    @classmethod
    def load(cls) -> "ResourceTable":
        """Lit assets/game_resources.json. / Read assets/game_resources.json."""
        with open(resource_path(RESOURCES_FILE), encoding="utf-8") as file:
            return cls(json.load(file))

    def get(self, category: tuple[str, ...], key: str) -> Resource | None:
        """Ressource d'une catégorie, ou None. / A category's resource, or None."""
        return self._resources.get((category, key))

    def by_id(self, resource_id: ResourceId) -> Resource | None:
        """Ressource correspondant à un identifiant, ou None. / Resource for an identifier, or None."""
        return self._resources.get((tuple(resource_id.category.split("/")), resource_id.key))

    def in_category(self, category: str) -> list[Resource]:
        """Ressources d'une catégorie, dans l'ordre du JSON (niveaux : par numéro).
        A category's resources, in JSON order (levels: by number).
        """
        wanted = tuple(category.split("/"))
        found = [r for (cat, _key), r in self._resources.items() if cat == wanted]
        return sorted(found, key=lambda r: int(r.key)) if category == "levels" else found

    # ----------------------------------------------------------------- niveaux

    @property
    def level_numbers(self) -> list[int]:
        """Numéros des niveaux connus, triés. / Known level numbers, sorted."""
        return sorted(int(key) for (category, key) in self._resources if category == ("levels",))

    def has_level(self, number: int) -> bool:
        return self.get(("levels",), str(number)) is not None

    def level(self, number: int) -> Resource:
        """Fichier NGN d'un niveau. / A level's NGN file."""
        resource = self.get(("levels",), str(number))
        if resource is None:
            raise KeyError(number)
        return resource


@lru_cache(maxsize=1)
def get_resources() -> ResourceTable:
    """Table chargée une seule fois. / Table, loaded once."""
    return ResourceTable.load()
