"""Erreur métier traduisible. / Translatable business error."""
from __future__ import annotations

from typing import Any


class ModError(Exception):
    """Erreur levée par les modèles. / Error raised by the models.

    Elle porte une CLÉ de traduction (ex. "errors.vanilla_missing") et ses paramètres :
    les modèles ne connaissent pas le LanguageManager, ce sont les contrôleurs
    qui traduisent le message pour la vue.
    """

    def __init__(self, key: str, **params: Any) -> None:
        super().__init__(key)
        self.key = key
        self.params = params
