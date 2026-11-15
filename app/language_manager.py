"""Traductions par clés en dot-notation, et langue préférée. / Dot-notation translations and preferred language."""
from __future__ import annotations

import json
import re
from typing import Any

from app.app_paths import resource_path
from app.event_bus import EventBus, Events
from app.preferences import Preferences

DEFAULT_LANGUAGE = "en_GB"  # langue par défaut de l'appli (avant tout choix) et texte de secours
# Format d'un code de langue : langue ISO 639 + "_" + pays ISO 3166 (fr_FR, en_GB, zh_CN)
# ou région numérique UN M.49 (es_419 = espagnol d'Amérique latine). Sert aussi de nom de
# fichier : le format strict évite toute injection de chemin.
LANGUAGE_CODE_RE = re.compile(r"^[A-Za-z]{2,3}_(?:[A-Za-z]{2,4}|[0-9]{3})$")
# Anciens codes → code normalisé (les premiers mods utilisaient en_UK ; la norme est en_GB).
LANGUAGE_ALIASES = {"en_UK": "en_GB"}


def normalize_language_code(code: str) -> str:
    """Remplace un ancien code par le code normalisé. / Replace a legacy code by the standard one."""
    return LANGUAGE_ALIASES.get(code, code)


def base_language(code: str) -> str:
    """"es_419" → "es". / Language part of a code."""
    return code.split("_")[0].lower()


class LanguageManager:
    """Charge lang/<code>.json et retrouve les textes par clé (ex. "mod_list.enable").
    Loads lang/<code>.json and looks texts up by key.

    Pour ajouter une langue : déposer lang/<code>.json (ex. de_DE.json) avec un bloc
    {"_meta": {"language_name": "Deutsch"}} — elle apparaît automatiquement dans l'appli.
    To add a language: drop lang/<code>.json — it shows up automatically.

    La langue PRÉFÉRÉE (préférence "language") est utilisée au lancement pour l'interface
    et comme langue par défaut des nouveaux mods.
    """

    PREF_KEY = "language"

    def __init__(self, preferences: Preferences, bus: EventBus) -> None:
        self._prefs = preferences
        self._bus = bus
        self._available = self._scan_languages()
        self._fallback = self._read_file(DEFAULT_LANGUAGE)  # texte de secours si une clé manque ailleurs
        self.language = self.preferred_language  # langue actuelle de l'interface
        self._translations = self._read_file(self.language)

    # ------------------------------------------------------------- langues

    @staticmethod
    def _read_file(code: str) -> dict[str, Any]:
        try:
            with open(resource_path(f"lang/{code}.json"), encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _scan_languages(self) -> dict[str, str]:
        """Langues disponibles : code → nom affiché. / Available languages: code → display name."""
        languages: dict[str, str] = {}
        for path in sorted(resource_path("lang").glob("*.json")):
            code = path.stem
            if not LANGUAGE_CODE_RE.match(code):
                continue
            meta = self._read_file(code).get("_meta", {})
            name = meta.get("language_name") if isinstance(meta, dict) else None
            languages[code] = str(name or code)
        return languages

    def available_languages(self) -> list[tuple[str, str]]:
        """[(code, nom affiché), …]. / [(code, display name), …]."""
        return list(self._available.items())

    def language_name(self, code: str) -> str:
        """Nom affiché d'une langue (le code si inconnue). / Display name (code if unknown)."""
        return self._available.get(code, code)

    @property
    def preferred_language(self) -> str:
        """Langue préférée (anglais britannique si non définie ou introuvable)."""
        code = normalize_language_code(str(self._prefs.get(self.PREF_KEY, DEFAULT_LANGUAGE)))
        return code if code in self._available else DEFAULT_LANGUAGE

    def set_preferred_language(self, code: str) -> None:
        """Change la langue : mémorisée, appliquée tout de suite, et publiée aux vues.
        Change the language: stored, applied immediately, and published to the views.

        La langue sert à la fois pour l'interface et comme langue par défaut des nouveaux mods.
        """
        if code in self._available:
            self._prefs.set(self.PREF_KEY, code)
            self.language = code
            self._translations = self._read_file(code)
            self._bus.publish(Events.LANGUAGE_CHANGED)

    # ---------------------------------------------------------- traductions

    def t(self, key: str, **params: Any) -> str:
        """Traduit une clé, avec paramètres {nom} facultatifs.
        Translate a key, with optional {name} parameters.

        Clé absente de la langue courante → texte français de secours ; absente partout →
        la clé elle-même (une traduction manquante se voit à l'écran sans faire planter l'appli).
        """
        text = self._lookup(self._translations, key)
        if text is None:
            text = self._lookup(self._fallback, key)
        if text is None:
            return key
        return text.format(**params) if params else text

    @staticmethod
    def _lookup(tree: dict[str, Any], key: str) -> str | None:
        node: Any = tree
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node if isinstance(node, str) else None

    def level_label(self, number: int) -> str:
        """Libellé d'un niveau, ex. "4. Le chantier". / Level label."""
        return f"{number}. {self.t(f'levels.{number}')}"
