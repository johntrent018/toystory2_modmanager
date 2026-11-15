"""Contrôleur de l'onglet « Liste des mods ». / Controller for the mod list tab."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.event_bus import EventBus, Events
from app.game_path_manager import GamePath_Manager
from app.language_manager import LanguageManager
from app.models.errors import ModError
from app.models.mod import Mod
from app.models.mod_activator import ModActivator
from app.models.mod_repository import ModRepository


@dataclass
class ImportReport:
    """Bilan d'un import de plusieurs archives. / Report of a multi-archive import."""

    imported: list[Mod] = field(default_factory=list)          # mods importés avec succès
    failed: list[tuple[str, str]] = field(default_factory=list)  # (nom du fichier, raison de l'échec)


class ModListController:
    """Fait le lien entre la vue (liste + détail d'un mod) et les modèles.
    Glue between the view (list + mod details) and the models.

    Les méthodes qui peuvent échouer renvoient un message d'erreur traduit
    (ou None si tout va bien) : la vue n'a qu'à l'afficher.
    """

    def __init__(
        self,
        repository: ModRepository,
        activator: ModActivator,
        game_path_manager: GamePath_Manager,
        bus: EventBus,
        lang: LanguageManager,
    ) -> None:
        self._repo = repository
        self._activator = activator
        self._game_path_manager = game_path_manager
        self._bus = bus
        self._lang = lang
        self._mods: list[Mod] = []
        self._logo_cache: dict[tuple[str, float], bytes | None] = {}  # (archive, date de modif.) → icône
        self.reload()

    # ---------------------------------------------------------------- lecture

    def reload(self) -> None:
        """Relit le dossier mods/. / Re-scan the mods/ folder.

        Ordre : celui choisi par l'utilisateur (glisser-déposer) ; les mods qui n'y figurent pas
        (nouveaux) viennent ensuite, triés par nom dans la langue de l'interface.
        Order: the user's drag-and-drop order; mods not in it (new ones) follow, sorted by name.
        """
        language = self._lang.language
        mods = sorted(self._repo.list_mods(),
                      key=lambda m: (m.localized(language).name.lower(), m.author.lower()))
        by_id = {mod.mod_id: mod for mod in mods}
        ordered = [by_id.pop(mod_id) for mod_id in self._repo.get_order() if mod_id in by_id]
        self._mods = ordered + list(by_id.values())

    @property
    def mods(self) -> list[Mod]:
        """Mods connus (dernier scan). / Known mods (last scan)."""
        return self._mods

    def is_active(self, mod: Mod) -> bool:
        """Le mod est-il actif ? / Is the mod active?"""
        return self._activator.is_active(mod.mod_id)

    def can_toggle(self) -> bool:
        """Activer/désactiver n'est possible que si le dossier du jeu est valide.
        Enabling/disabling requires a valid game folder.
        """
        return self._game_path_manager.is_valid()

    def get_image_bytes(self, mod: Mod, index: int) -> bytes:
        """Contenu de la n-ième image du mod. / Bytes of the mod's n-th image."""
        return self._repo.read_file(mod, mod.images[index])

    def get_logo_bytes(self, mod: Mod) -> bytes | None:
        """Contenu de l'icône du mod, ou None (pas d'icône / illisible). / Mod icon bytes.

        Le résultat est mis en cache (clé : archive + date de modification) : changer de langue
        reconstruit toute l'interface, inutile de rouvrir chaque archive à chaque fois.
        """
        if not mod.logo:
            return None
        try:
            key = (str(mod.archive_path), mod.archive_path.stat().st_mtime)
        except OSError:
            return None
        if key not in self._logo_cache:
            try:
                self._logo_cache[key] = self._repo.read_file(mod, mod.logo)
            except ModError:
                self._logo_cache[key] = None
        return self._logo_cache[key]

    def set_order(self, mod_ids: list[str]) -> str | None:
        """Enregistre l'ordre d'affichage choisi par glisser-déposer. / Store the drag-and-drop order."""
        try:
            self._repo.set_order(mod_ids)
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        by_id = {mod.mod_id: mod for mod in self._mods}
        self._mods = [by_id[i] for i in mod_ids if i in by_id]
        return None

    # ----------------------------------------------------------------- actions

    def toggle(self, mod: Mod, confirm_conflicts: Callable[[list[Mod]], bool]) -> str | None:
        """Active ou désactive un mod. / Enable or disable a mod.

        Args:
            mod: le mod ciblé.
            confirm_conflicts: fournie par la vue ; reçoit les mods actifs en conflit
                (mêmes niveaux) et renvoie True si l'utilisateur accepte de les désactiver.

        Returns:
            None si tout s'est bien passé (ou si l'utilisateur a annulé),
            sinon le message d'erreur traduit à afficher.
        """
        try:
            if self._activator.is_active(mod.mod_id):
                self._activator.deactivate(mod)
                return None

            conflicts = self._activator.get_conflicts(mod, self._mods)
            if conflicts:
                if not confirm_conflicts(conflicts):
                    return None
                # Règle actuelle : désactivation COMPLÈTE des mods en conflit, même pour
                # leurs niveaux non concernés par le nouveau mod (pas de cohabitation).
                for other in conflicts:
                    self._activator.deactivate(other)

            self._activator.activate(mod)
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        return None

    def import_mods(self, file_texts: list[str]) -> ImportReport:
        """Importe plusieurs archives .zip de mods. / Import several mod .zip archives.

        Chaque archive est traitée indépendamment : une archive invalide (ou en doublon)
        est signalée dans le bilan avec sa raison, sans empêcher l'import des autres.
        """
        report = ImportReport()
        for file_text in file_texts:
            path = Path(file_text)
            try:
                report.imported.append(self._repo.import_mod(path))
            except ModError as err:
                report.failed.append((path.name, self._lang.t(err.key, **err.params)))
        if report.imported:
            self._bus.publish(Events.MODS_CHANGED)  # la liste se recharge une seule fois
        return report

    def export_mod(self, mod: Mod, destination_text: str) -> str | None:
        """Exporte l'archive du mod vers le chemin choisi. / Export the mod archive."""
        try:
            self._repo.export_mod(mod, Path(destination_text))
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        return None

    def delete_mod(self, mod: Mod) -> str | None:
        """Supprime un mod (le désactive d'abord s'il est actif).
        Delete a mod (disabling it first if it is active).

        Si la désactivation échoue (ex. dossier du jeu introuvable), rien n'est supprimé :
        on ne laisse jamais un mod "actif" dont l'archive a disparu.
        """
        try:
            if self._activator.is_active(mod.mod_id):
                self._activator.deactivate(mod)
            self._repo.delete_mod(mod)
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        self._bus.publish(Events.MOD_DELETED, mod_id=mod.mod_id)
        self._bus.publish(Events.MODS_CHANGED)
        return None

    def request_edit(self, mod: Mod) -> None:
        """Demande l'ouverture du mod dans l'onglet de création (mode modification).
        Ask for the mod to be opened in the create tab (edit mode).
        """
        self._bus.publish(Events.EDIT_MOD_REQUESTED, mod=mod)
