"""Libellés des ressources moddables, dans la langue courante. / Moddable resource labels."""
from __future__ import annotations

from typing import Iterable

from app.language_manager import LanguageManager
from app.models.resource_table import ResourceId

# Ordre d'affichage des catégories (aussi celui des sous-onglets de « Ressources modifiées »).
CATEGORY_ORDER = ["levels", "bgm", "sfx", "screens", "cutscenes"]


def resource_label(lang: LanguageManager, resource_id: ResourceId) -> str:
    """Nom lisible d'une ressource : "4. Le chantier", "Chargement"…
    Readable name of a resource.

    Les textes sont dans les fichiers de langue sous le chemin de la catégorie
    (levels.4, screens.loading, bgm.levels.3…).
    """
    if resource_id.category == "levels":
        return lang.level_label(int(resource_id.key))
    return lang.t(f"{resource_id.category.replace('/', '.')}.{resource_id.key}")


def describe_resources(lang: LanguageManager, resource_ids: Iterable[ResourceId]) -> str:
    """Résumé groupé par type : "Niveaux : 1. X, 2. Y ; Écrans : Chargement".
    Summary grouped by type.
    """
    groups: dict[str, list[str]] = {}
    for resource_id in sorted(resource_ids):
        groups.setdefault(resource_id.top_category, []).append(resource_label(lang, resource_id))
    ordered = sorted(groups, key=lambda top: CATEGORY_ORDER.index(top) if top in CATEGORY_ORDER else 99)
    return " ; ".join(f"{lang.t('resource_types.' + top)} : {', '.join(groups[top])}" for top in ordered)
