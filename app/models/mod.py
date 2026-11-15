"""Modèle d'un mod et lecture de son mod.json. / Mod model and mod.json parsing."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.language_manager import (DEFAULT_LANGUAGE, LANGUAGE_CODE_RE, base_language,
                                  normalize_language_code)
from app.models.errors import ModError
from app.models.resource_table import ResourceId, get_resources

META_FILE = "mod.json"  # métadonnées à la racine de l'archive zip
I18N_DIR = "i18n"       # textes traduits : i18n/<code>.json (ex. i18n/fr_FR.json)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}  # formats d'image acceptés
SCHEMA_VERSION = 2


def slugify(text: str) -> str:
    """"Ça glisse !" → "ca-glisse". Minuscules, sans accents, sans caractères spéciaux.
    Lowercase, accent-free, filesystem-friendly text.
    """
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def make_mod_id(name: str, author: str) -> str:
    """Identifiant d'un mod : "<nom>_<auteur>" en slug (sert aussi de nom d'archive).
    Mod identifier: slugged "<name>_<author>" (also used as archive name).

    Le nom pris en compte est celui de la langue par défaut du mod. Deux mods de même
    nom ET même auteur ont donc le même identifiant (= doublon).
    """
    return f"{slugify(name)}_{slugify(author)}"


@dataclass(frozen=True)
class ModTexts:
    """Textes d'un mod dans UNE langue. / A mod's texts in ONE language."""

    name: str = ""
    description: str = ""
    warning: str = ""

    def is_empty(self) -> bool:
        """Aucun champ renseigné ? / No field filled in?"""
        return not (self.name.strip() or self.description.strip() or self.warning.strip())

    def stripped(self) -> "ModTexts":
        """Copie sans espaces superflus. / Copy without surrounding whitespace."""
        return ModTexts(self.name.strip(), self.description.strip(), self.warning.strip())

    @classmethod
    def from_dict(cls, data: Any) -> "ModTexts":
        """Depuis le contenu d'un fichier i18n/<code>.json. / From an i18n file content."""
        if not isinstance(data, dict):
            raise ValueError("i18n file must contain a JSON object")
        return cls(str(data.get("name", "")).strip(), str(data.get("description", "")).strip(),
                   str(data.get("warning", "")).strip())

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "description": self.description, "warning": self.warning}


@dataclass
class Mod:
    """Un mod de niveaux, tel que décrit par son archive. / A level mod."""

    mod_id: str
    author: str
    archive_path: Path
    default_language: str  # langue des textes "par défaut" ; "" pour un ancien mod sans i18n
    texts: dict[str, ModTexts]  # code de langue → textes (clé "" pour un ancien mod)
    version: str = ""   # numéro de version libre (facultatif), ex. "1.2"
    images: list[str] = field(default_factory=list)  # chemins INTERNES à l'archive, dans l'ordre d'affichage
    logo: str | None = None  # chemin INTERNE de l'icône du mod (images/_logo.png), s'il y en a une
    levels: dict[int, str] = field(default_factory=dict)  # n° de niveau → chemin interne du NGN
    resources: dict[ResourceId, str] = field(default_factory=dict)  # AUTRES ressources (écrans…) → chemin interne

    # --- Textes dans la langue par défaut du mod
    @property
    def default_texts(self) -> ModTexts:
        return self.texts[self.default_language]

    @property
    def name(self) -> str:
        return self.default_texts.name

    @property
    def description(self) -> str:
        return self.default_texts.description

    @property
    def warning(self) -> str:
        return self.default_texts.warning

    def language_chain(self, language: str) -> list[str]:
        """Ordre dans lequel chercher un texte : la langue demandée, puis les autres variantes
        de la même langue (ex. es_419 → es_ES), puis l'ANGLAIS s'il est présent dans le mod,
        et enfin la langue par défaut du mod.
        Lookup order: requested language, same-language variants, English if present, mod default.
        """
        codes = list(self.texts)
        chain = [language] if language in self.texts else []
        chain += [c for c in codes if c not in chain and c and base_language(c) == base_language(language)]
        chain += [c for c in (DEFAULT_LANGUAGE, "en_US") + tuple(c for c in codes if base_language(c) == "en")
                  if c in self.texts and c not in chain]
        if self.default_language not in chain:
            chain.append(self.default_language)
        return chain

    def localized(self, language: str) -> ModTexts:
        """Textes à afficher dans `language`. Chaque champ est pris dans la première langue de
        `language_chain` où il est renseigné (une traduction partielle est donc complétée).
        Texts to display in `language`; each field comes from the first language in the chain
        where it is filled in, so partial translations are completed.
        """
        chain = [self.texts[c] for c in self.language_chain(language)]

        def pick(field_name: str) -> str:
            return next((value for texts in chain if (value := getattr(texts, field_name))), "")

        return ModTexts(pick("name"), pick("description"), pick("warning"))

    @property
    def all_resources(self) -> dict[ResourceId, str]:
        """Toutes les ressources du mod (niveaux compris) : identifiant → chemin interne.
        Every resource of the mod (levels included): identifier → internal path.
        """
        merged = {ResourceId("levels", str(number)): member for number, member in self.levels.items()}
        merged.update(self.resources)
        return merged

    @property
    def resource_ids(self) -> list[ResourceId]:
        """Identifiants des ressources du mod, triés. / Resource identifiers, sorted."""
        return sorted(self.all_resources)

    @property
    def level_numbers(self) -> list[int]:
        """Numéros des niveaux concernés, triés. / Affected level numbers, sorted."""
        return sorted(self.levels)

    @classmethod
    def from_json(cls, data: Any, archive_path: Path, translations: dict[str, Any]) -> "Mod":
        """Construit un Mod depuis mod.json + les fichiers i18n déjà lus. / Build a Mod.

        Args:
            data: contenu de mod.json.
            translations: code de langue → contenu brut de i18n/<code>.json.

        Raises:
            ModError: si le JSON est incomplet ou incohérent.
        """
        file_name = archive_path.name
        try:
            author = str(data["author"]).strip()
            levels = {int(number): str(member) for number, member in data.get("levels", {}).items()}
            resources = {
                ResourceId(str(category), str(key)): str(member)
                for category, items in data.get("resources", {}).items() for key, member in items.items()
            }
            if "default_language" in data:  # format actuel : textes dans i18n/
                default_language = normalize_language_code(str(data["default_language"]))
                if not LANGUAGE_CODE_RE.match(default_language):
                    raise ModError("errors.invalid_language", file=file_name, language=default_language)
                texts = {code: ModTexts.from_dict(raw) for code, raw in translations.items()}
            else:  # ancien format (v1) : name/description/warning directement dans mod.json
                default_language = ""
                texts = {"": ModTexts.from_dict(data)}
        except (KeyError, AttributeError, ValueError, TypeError) as err:
            raise ModError("errors.invalid_mod", file=file_name) from err

        if default_language not in texts:
            raise ModError("errors.missing_default_language", file=file_name, language=default_language)
        name = texts[default_language].name
        table = get_resources()
        if (not name or not author or not (levels or resources)
                or not all(table.has_level(n) for n in levels)
                or any(rid.category == "levels" or table.by_id(rid) is None for rid in resources)):
            raise ModError("errors.invalid_mod", file=file_name)

        return cls(
            mod_id=make_mod_id(name, author),
            author=author,
            archive_path=archive_path,
            default_language=default_language,
            texts=texts,
            version=str(data.get("version", "")).strip(),
            images=[str(image) for image in data.get("images", [])],
            logo=str(data["logo"]) if data.get("logo") else None,
            levels=levels,
            resources=resources,
        )
