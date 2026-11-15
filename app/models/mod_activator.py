"""Activation / désactivation des mods dans le dossier du jeu. / Enabling/disabling mods in the game."""
from __future__ import annotations

import json
import os
import shutil
import zipfile
import zlib
from pathlib import Path
from typing import Iterable

from app.event_bus import EventBus, Events
from app.game_path_manager import GamePath_Manager
from app.models.errors import ModError
from app.models.mod import Mod
from app.models.mod_repository import ModRepository
from app.models.resource_table import ResourceId, get_resources


class ModActivator:
    """Installe les fichiers d'un mod dans le jeu, ou remet les fichiers d'origine.
    Installs a mod's files into the game, or puts the original files back.

    Principe de la sauvegarde (aucune copie des fichiers d'origine n'est livrée avec l'appli) :
      - ACTIVATION : avant d'écraser un fichier du jeu, on en garde l'original dans
        mods/_vanilla/<catégorie>/<clé>.<ext> (seulement si cette sauvegarde n'existe pas déjà :
        une sauvegarde existante n'est JAMAIS écrasée, c'est l'original) ;
      - DÉSACTIVATION : on recopie la sauvegarde dans le jeu. La sauvegarde est conservée
        (la réactiver ou activer un autre mod sur la même ressource évite de la refaire).

    Les écritures se font en deux temps : tous les fichiers sont d'abord copiés sous un nom
    temporaire à côté de leur destination, puis renommés d'un coup. Un problème de lecture ou
    d'écriture pendant la copie laisse donc le jeu intact. Les fichiers sont copiés en flux
    (jamais chargés entièrement en mémoire) : prévu pour de gros fichiers (musiques, vidéos).
    """

    def __init__(self, repository: ModRepository, game_path_manager: GamePath_Manager, bus: EventBus) -> None:
        self._repo = repository
        self._game_path_manager = game_path_manager
        self._bus = bus
        self._table = get_resources()
        self._state_file = repository.mods_dir / "active_mods.json"

    # ------------------------------------------------------- état (mods actifs)

    def _load_active_ids(self) -> list[str]:
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            return [str(mod_id) for mod_id in data.get("active", [])]
        except (OSError, json.JSONDecodeError, AttributeError):
            return []  # fichier absent ou illisible : aucun mod actif

    def _save_active_ids(self, ids: list[str]) -> None:
        try:
            self._state_file.write_text(json.dumps({"active": ids}, indent=2), encoding="utf-8")
        except OSError as err:
            raise ModError("errors.write_failed", path=str(self._state_file), reason=str(err)) from err

    def _set_active(self, mod_id: str, active: bool) -> None:
        """Met à jour active_mods.json puis prévient les vues. / Update state, notify views."""
        ids = [i for i in self._load_active_ids() if i != mod_id]
        if active:
            ids.append(mod_id)
        self._save_active_ids(ids)
        self._bus.publish(Events.MOD_STATE_CHANGED, mod_id=mod_id)

    def is_active(self, mod_id: str) -> bool:
        """Ce mod est-il actif ? / Is this mod active?"""
        return mod_id in self._load_active_ids()

    def get_conflicts(self, mod: Mod, all_mods: list[Mod]) -> list[Mod]:
        """Mods ACTIFS (autres que `mod`) qui touchent au moins une ressource en commun.
        Active mods (other than `mod`) sharing at least one resource with it.
        """
        return self.get_resource_conflicts(mod.resource_ids, mod.mod_id, all_mods)

    def get_resource_conflicts(self, resource_ids: Iterable[ResourceId], exclude_id: str,
                               all_mods: list[Mod]) -> list[Mod]:
        """Mods actifs (sauf `exclude_id`) dont les ressources recoupent `resource_ids`.
        Active mods (except `exclude_id`) whose resources overlap `resource_ids`.
        """
        active_ids = set(self._load_active_ids())
        wanted = set(resource_ids)
        return [
            other for other in all_mods
            if other.mod_id != exclude_id and other.mod_id in active_ids and wanted & set(other.resource_ids)
        ]

    # -------------------------------------------------------------- opérations

    def activate(self, mod: Mod) -> None:
        """Installe les NGN du mod dans le jeu (en sauvegardant les originaux au passage).
        Install the mod's NGN files (backing up the originals on the way).

        Raises:
            ModError: chemin du jeu absent, archive illisible, écriture impossible…
        """
        self._apply(mod, install=set(mod.resource_ids), restore=set())
        self._set_active(mod.mod_id, True)

    def deactivate(self, mod: Mod) -> None:
        """Remet les fichiers d'origine (sauvegardés dans mods/_vanilla) à la place de ceux du mod.
        Put the original files (backed up in mods/_vanilla) back in place of the mod's.

        Raises:
            ModError: chemin du jeu absent, sauvegarde manquante, écriture impossible…
        """
        self._apply(None, install=set(), restore=set(mod.resource_ids))
        self._set_active(mod.mod_id, False)

    def check_replace(self, old_mod: Mod, new_resources: Iterable[ResourceId]) -> None:
        """Vérifie, AVANT d'enregistrer, que `replace_active` pourra réussir (sans rien modifier).
        Check, BEFORE saving, that `replace_active` will succeed (changing nothing).
        """
        new_set = set(new_resources)
        self._preflight(self._require_game_path(), install=new_set, restore=set(old_mod.resource_ids) - new_set)

    def replace_active(self, old_mod: Mod, new_mod: Mod) -> None:
        """Applique au jeu la nouvelle version d'un mod ACTIF et le garde actif.
        Apply the new version of an ACTIVE mod to the game and keep it active.

        - ressources de la nouvelle version : fichiers du mod copiés dans le jeu ;
        - ressources retirées du mod : fichiers d'origine restaurés ;
        - l'identifiant actif est remplacé (il change si le nom ou l'auteur a changé).

        Le jeu charge un NGN au lancement du niveau : écraser le fichier pendant une partie
        n'est pas gênant, la nouvelle version sera prise en compte au prochain lancement du niveau.
        """
        removed = set(old_mod.resource_ids) - set(new_mod.resource_ids)
        self._apply(new_mod, install=set(new_mod.resource_ids), restore=removed)
        ids = [i for i in self._load_active_ids() if i not in (old_mod.mod_id, new_mod.mod_id)]
        ids.append(new_mod.mod_id)
        self._save_active_ids(ids)
        self._bus.publish(Events.MOD_STATE_CHANGED, mod_id=new_mod.mod_id)

    # ----------------------------------------------------------- cœur du travail

    def _game_file(self, game_path: Path, resource_id: ResourceId) -> Path:
        return game_path / self._table.by_id(resource_id).game_path

    def _vanilla_file(self, resource_id: ResourceId) -> Path:
        return self._repo.vanilla_dir / self._table.by_id(resource_id).vanilla_path

    def _preflight(self, game_path: Path, install: set[ResourceId], restore: set[ResourceId]) -> dict[ResourceId, Path]:
        """Toutes les vérifications, sans rien modifier. Renvoie les fichiers cibles du jeu.
        All checks, changing nothing. Returns the game's target files.
        """
        targets = {rid: self._game_file(game_path, rid) for rid in install | restore}
        for target in targets.values():
            if not target.parent.is_dir():  # sinon ce n'est pas le bon dossier de jeu
                raise ModError("errors.level_folder_missing", folder=str(target.parent))
        for rid in restore:  # restaurer exige une sauvegarde
            vanilla = self._vanilla_file(rid)
            if not vanilla.is_file():
                raise ModError("errors.vanilla_missing", file=vanilla.relative_to(self._repo.vanilla_dir).as_posix())
        for rid in install:  # installer exige de pouvoir sauvegarder l'original (ou d'en avoir déjà une)
            if not self._vanilla_file(rid).is_file() and not targets[rid].is_file():
                raise ModError("errors.game_file_missing", file=targets[rid].relative_to(game_path).as_posix())
        return targets

    def _apply(self, mod: Mod | None, install: set[ResourceId], restore: set[ResourceId]) -> None:
        """Installe les ressources `install` (depuis `mod`) et restaure les ressources `restore`.
        Install resources `install` (from `mod`) and restore resources `restore`.
        """
        game_path = self._require_game_path()
        targets = self._preflight(game_path, install, restore)

        staged: list[tuple[Path, Path]] = []  # (copie temporaire, destination)
        try:
            # 1) Sauvegarde des originaux qui vont être écrasés (sans rien écraser côté jeu).
            for rid in install:
                self._backup_if_needed(rid, targets[rid])
            # 2) Copie temporaire de TOUT ce qui doit être écrit.
            if install and mod is not None:
                with zipfile.ZipFile(mod.archive_path) as archive:
                    for rid in sorted(install):
                        temp = self._temp_name(targets[rid])
                        staged.append((temp, targets[rid]))
                        self._copy_from_archive(archive, mod, mod.all_resources[rid], temp)
            for rid in sorted(restore):
                temp = self._temp_name(targets[rid])
                staged.append((temp, targets[rid]))
                self._copy_file(self._vanilla_file(rid), temp)
            # 3) Seulement maintenant, on met tout en place d'un coup.
            for temp, target in staged:
                os.replace(temp, target)
        except ModError:
            self._discard(staged)
            raise
        except (zipfile.BadZipFile, zlib.error, EOFError) as err:  # données de l'archive abîmées
            self._discard(staged)
            name = mod.archive_path.name if mod is not None else ""
            raise ModError("errors.archive_corrupt", file=name, reason=str(err)) from err
        except OSError as err:  # écriture ou lecture de fichier impossible
            self._discard(staged)
            raise ModError("errors.write_failed", path=str(game_path), reason=str(err)) from err

    def _backup_if_needed(self, rid: int, target: Path) -> None:
        """Garde l'original du jeu dans mods/_vanilla, s'il n'y est pas déjà. / Back up the original."""
        vanilla = self._vanilla_file(rid)
        if vanilla.is_file():
            return  # déjà sauvegardé : on ne touche JAMAIS à une sauvegarde existante
        vanilla.parent.mkdir(parents=True, exist_ok=True)
        temp = self._temp_name(vanilla)
        try:
            self._copy_file(target, temp)
            os.replace(temp, vanilla)
        except OSError as err:
            temp.unlink(missing_ok=True)
            raise ModError("errors.write_failed", path=str(vanilla), reason=str(err)) from err

    # ------------------------------------------------------------------ outils

    def _require_game_path(self) -> Path:
        game_path = self._game_path_manager.get_path()
        if game_path is None:
            raise ModError("errors.game_path_missing")
        return game_path

    @staticmethod
    def _temp_name(target: Path) -> Path:
        return target.with_name(target.name + ".tmp")

    @staticmethod
    def _copy_file(source: Path, destination: Path) -> None:
        shutil.copyfile(source, destination)  # copie en flux, par blocs

    def _copy_from_archive(self, archive: zipfile.ZipFile, mod: Mod, member: str, destination: Path) -> None:
        """Extrait UN fichier de l'archive vers `destination`, en flux. / Stream one file out of the archive."""
        try:
            source = archive.open(member)
        except KeyError as err:
            raise ModError("errors.read_failed", file=mod.archive_path.name, member=member) from err
        with source, open(destination, "wb") as output:
            shutil.copyfileobj(source, output)

    @staticmethod
    def _discard(staged: list[tuple[Path, Path]]) -> None:
        """Supprime les copies temporaires après un échec. / Remove temp copies after a failure."""
        for temp, _target in staged:
            temp.unlink(missing_ok=True)
