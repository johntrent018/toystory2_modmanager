"""Accès aux archives de mods (dossier mods/). / Access to mod archives (mods/ folder)."""
from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

from app.models.errors import ModError
from app.models.file_source import FileSource
from app.language_manager import LANGUAGE_ALIASES, LANGUAGE_CODE_RE
from app.models.logo import LOGO_NAME
from app.models.resource_table import ResourceId, get_resources
from app.models.mod import (I18N_DIR, IMAGE_EXTENSIONS, META_FILE, SCHEMA_VERSION, Mod, ModTexts,
                            make_mod_id)

MAX_MEMBER_SIZE = 512 * 1024 * 1024  # taille max (décompressée) d'un fichier d'archive : 512 Mo
MAX_JSON_SIZE = 1024 * 1024          # taille max d'un fichier JSON (mod.json, i18n/*.json) : 1 Mo
ORDER_FILE = "mod_order.json"        # ordre d'affichage des mods (choisi par l'utilisateur)


class ModRepository:
    """Liste, valide, crée, modifie, importe, exporte et supprime les archives de mods.
    Lists, validates, creates, edits, imports, exports and deletes mod archives.

    Arborescence gérée :
        mods/
        ├── _vanilla/        sauvegardes des fichiers d'origine, créées à l'activation d'un mod
        │   └── levels/3.ngn, bgm/others/menus.wav…  (dossiers = catégories de game_resources.json)
        ├── active_mods.json (géré par ModActivator)
        └── <mod_id>.zip     un mod = une archive
    """

    def __init__(self, mods_dir: Path) -> None:
        self.mods_dir = mods_dir
        self.vanilla_dir = mods_dir / "_vanilla"
        self.vanilla_dir.mkdir(parents=True, exist_ok=True)  # crée aussi mods/
        self._migrate_legacy_vanilla()

    def _migrate_legacy_vanilla(self) -> None:
        """Anciennes versions : NGN d'origine à plat (_vanilla/level3.ngn). On les range dans la
        nouvelle arborescence (_vanilla/levels/3.ngn) : ce sont de vraies sauvegardes d'origine.
        Old versions kept originals flat; move them into the new folder layout.
        """
        table = get_resources()
        for number in table.level_numbers:
            old = self.vanilla_dir / f"level{number}.ngn"
            new = self.vanilla_dir / table.level(number).vanilla_path
            if old.is_file() and not new.exists():
                try:
                    new.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(old, new)
                except OSError:
                    pass  # on réessaiera au prochain lancement

    # ------------------------------------------------- lecture + validation

    def read_mod(self, archive_path: Path) -> Mod:
        """Lit ET valide une archive de mod (principe "zero trust").
        Read AND validate a mod archive (zero-trust principle).

        On ne fait confiance à rien : mod.json doit exister, être complet, et
        chaque fichier qu'il déclare doit réellement se trouver dans l'archive.

        Raises:
            ModError: archive illisible ou invalide (avec un message précis).
        """
        name = archive_path.name
        try:
            with zipfile.ZipFile(archive_path) as archive:
                if META_FILE not in archive.namelist():
                    raise ModError("errors.no_metadata", file=name)
                data = self._read_json(archive, META_FILE, "errors.invalid_json", name)
                if not isinstance(data, dict):
                    raise ModError("errors.invalid_mod", file=name)
                translations = self._read_translations(archive, name) if "default_language" in data else {}
                mod = Mod.from_json(data, archive_path, translations)  # champs obligatoires, niveaux 1 à 15
                self._check_members(archive, mod)
                return mod
        except zipfile.BadZipFile as err:
            raise ModError("errors.not_zip", file=name) from err
        except OSError as err:
            raise ModError("errors.read_failed", file=name, member=META_FILE) from err

    @staticmethod
    def _read_json(archive: zipfile.ZipFile, member: str, error_key: str, file_name: str):
        """Lit un petit fichier JSON de l'archive (taille limitée). / Read a small JSON file."""
        if archive.getinfo(member).file_size > MAX_JSON_SIZE:
            raise ModError(error_key, file=file_name, member=member)
        try:
            return json.loads(archive.read(member).decode("utf-8"))
        except ValueError as err:  # JSON invalide ou mauvais encodage
            raise ModError(error_key, file=file_name, member=member) from err

    def _read_translations(self, archive: zipfile.ZipFile, file_name: str) -> dict[str, object]:
        """Lit tous les i18n/<code>.json de l'archive. / Read every i18n/<code>.json file.

        Seuls les noms de la forme i18n/fr_FR.json sont pris en compte.
        """
        found: dict[str, object] = {}
        for member in archive.namelist():
            folder, _, leaf = member.partition("/")
            if folder != I18N_DIR or not leaf.endswith(".json"):
                continue
            code = leaf[:-len(".json")]
            if not LANGUAGE_CODE_RE.match(code):
                raise ModError("errors.invalid_language", file=file_name, language=code)
            found[code] = self._read_json(archive, member, "errors.invalid_i18n", file_name)
        # Les anciens codes (en_UK) sont convertis ; si le code normalisé existe aussi, il gagne.
        translations = {code: data for code, data in found.items() if code not in LANGUAGE_ALIASES}
        for code, data in found.items():
            if code in LANGUAGE_ALIASES:
                translations.setdefault(LANGUAGE_ALIASES[code], data)
        return translations

    @staticmethod
    def _check_members(archive: zipfile.ZipFile, mod: Mod) -> None:
        """Vérifie que mod.json colle avec le contenu réel de l'archive. / Cross-check mod.json vs files."""
        file_name = mod.archive_path.name

        def check_exists(member: str) -> None:
            try:
                info = archive.getinfo(member)
            except KeyError:
                raise ModError("errors.missing_member", file=file_name, member=member) from None
            if info.is_dir() or info.file_size > MAX_MEMBER_SIZE:
                raise ModError("errors.bad_member", file=file_name, member=member)

        table = get_resources()
        for resource_id, member in mod.all_resources.items():
            expected = table.by_id(resource_id).archive_member  # ex. levels/level4.ngn, screens/loading.ngn
            # Une ressource doit pointer vers SON fichier, sinon on risquerait d'installer celui d'une autre.
            if member != expected:
                raise ModError("errors.bad_resource_path", file=file_name,
                               resource=f"{resource_id.category}/{resource_id.key}", member=member, expected=expected)
            check_exists(member)

        for member in mod.images + ([mod.logo] if mod.logo else []):
            if not ModRepository._is_safe_image_member(member):
                raise ModError("errors.bad_image_path", file=file_name, member=member)
            check_exists(member)

    @staticmethod
    def _is_safe_image_member(member: str) -> bool:
        """images/<nom>.<ext> : un seul niveau de dossier, pas de ".." ni de séparateur étrange.
        images/<name>.<ext>: single folder level, no "..", no odd separators.
        """
        leaf = member[len("images/"):]
        return (member.startswith("images/") and 0 < len(leaf) <= 200 and "/" not in leaf
                and "\\" not in leaf and ".." not in leaf and not any(ord(c) < 32 for c in leaf)
                and Path(leaf).suffix.lower() in IMAGE_EXTENSIONS)

    def list_mods(self) -> list[Mod]:
        """Tous les mods valides trouvés dans mods/, triés par nom.
        All valid mods found in mods/, sorted by name.

        Les archives invalides sont ignorées (jamais de plantage à cause d'un zip
        bancal déposé à la main). Si deux archives ont la même identité
        (ex. "mod (1).zip"), seule la première est retenue.
        """
        mods: dict[str, Mod] = {}
        for archive_path in sorted(self.mods_dir.glob("*.zip")):
            try:
                mod = self.read_mod(archive_path)
            except ModError as err:
                print(f"Archive ignorée {archive_path.name} : {err.key} {err.params}")
                continue
            mods.setdefault(mod.mod_id, mod)
        return sorted(mods.values(), key=lambda m: (m.name.lower(), m.author.lower()))

    # ------------------------------------------------------- ordre d'affichage

    def get_order(self) -> list[str]:
        """Identifiants des mods dans l'ordre choisi par l'utilisateur. / User-chosen mod order."""
        try:
            data = json.loads((self.mods_dir / ORDER_FILE).read_text(encoding="utf-8"))
            return [str(mod_id) for mod_id in data.get("order", [])]
        except (OSError, ValueError, AttributeError):
            return []

    def set_order(self, mod_ids: list[str]) -> None:
        """Enregistre l'ordre d'affichage. / Store the display order."""
        try:
            (self.mods_dir / ORDER_FILE).write_text(json.dumps({"order": mod_ids}, indent=2), encoding="utf-8")
        except OSError as err:
            raise ModError("errors.write_failed", path=str(self.mods_dir / ORDER_FILE), reason=str(err)) from err

    def _rename_in_order(self, old_id: str, new_id: str) -> None:
        """Un mod renommé garde sa place dans la liste. / A renamed mod keeps its place."""
        order = self.get_order()
        if old_id in order and old_id != new_id:
            try:
                self.set_order([new_id if mod_id == old_id else mod_id for mod_id in order])
            except ModError:
                pass  # l'ordre est un confort : on ne fait pas échouer l'enregistrement du mod

    def is_taken(self, name: str, author: str, replacing: Mod | None = None) -> bool:
        """Ce nom + cet auteur sont-ils déjà pris ? / Is this name + author already used?

        `replacing` : mod en cours de modification (il ne compte pas comme doublon de lui-même).
        """
        mod_id = make_mod_id(name, author)
        for mod in self.list_mods():
            if mod.mod_id == mod_id and not self._same_archive(mod, replacing):
                return True
        target = self.mods_dir / f"{mod_id}.zip"
        # Un fichier de ce nom existe déjà (même invalide) : on ne l'écrase pas.
        return target.exists() and not (replacing is not None and target == replacing.archive_path)

    @staticmethod
    def _same_archive(mod: Mod, other: Mod | None) -> bool:
        return other is not None and mod.archive_path == other.archive_path

    def read_file(self, mod: Mod, internal_path: str) -> bytes:
        """Lit un fichier de l'archive (NGN ou image) sans rien extraire sur le disque.
        Reads a file from the archive without extracting anything to disk.

        On ne lit QUE le membre demandé, jamais d'extraction vers un chemin issu de l'archive.
        """
        try:
            with zipfile.ZipFile(mod.archive_path) as archive:
                return archive.read(internal_path)
        except (OSError, KeyError, zipfile.BadZipFile) as err:
            raise ModError("errors.read_failed", file=mod.archive_path.name, member=internal_path) from err

    # ------------------------------------------------- création / modification

    def save_mod(
        self,
        default_language: str,
        texts: dict[str, ModTexts],
        author: str,
        version: str,
        resource_sources: dict[ResourceId, FileSource],
        image_sources: list[FileSource],
        logo_source: FileSource | None = None,
        replacing: Mod | None = None,
    ) -> Mod:
        """Écrit l'archive <mod_id>.zip : création, ou remplacement si `replacing` est donné.
        Write the <mod_id>.zip archive: creation, or replacement when `replacing` is given.

        Contenu : mod.json, i18n/<langue>.json, images/<noms d'origine>, images/_logo.png, levels/level<N>.ngn
        L'identifiant vient du nom dans la langue par défaut : s'il change (ou l'auteur),
        l'ancienne archive est supprimée.

        Raises:
            ModError: doublon (même nom + même auteur), langue invalide ou écriture impossible.
        """
        if not LANGUAGE_CODE_RE.match(default_language):
            raise ModError("errors.invalid_language", file="", language=default_language)
        name = texts[default_language].name
        if self.is_taken(name, author, replacing):
            raise ModError("errors.duplicate_mod", name=name, author=author)

        archive_path = self.mods_dir / f"{make_mod_id(name, author)}.zip"

        # Noms internes : NGN renommés en level<N>.ngn ; images = noms d'origine (dédoublonnés),
        # dans l'ordre choisi ; le logo prend _logo.png en priorité.
        table = get_resources()
        members = {rid: table.by_id(rid).archive_member for rid in sorted(resource_sources)}  # rid → chemin dans l'archive
        levels = {int(rid.key): member for rid, member in members.items() if rid.category == "levels"}
        other_resources: dict[str, dict[str, str]] = {}
        for rid, member in members.items():
            if rid.category != "levels":
                other_resources.setdefault(rid.category, {})[rid.key] = member
        logo = f"images/{LOGO_NAME}" if logo_source else None
        images = [f"images/{name}" for name in self._allocate_image_names(
            [source.name for source in image_sources], reserved=[LOGO_NAME] if logo_source else [])]
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "default_language": default_language,
            "author": author,
            "version": version,
            "images": images,
            **({"logo": logo} if logo else {}),
            "levels": {str(number): member for number, member in levels.items()},
            **({"resources": other_resources} if other_resources else {}),
        }
        # Une langue est écrite si elle contient quelque chose (la langue par défaut toujours).
        language_files = {code: t for code, t in sorted(texts.items())
                          if code == default_language or not t.is_empty()}
        for code in language_files:
            if not LANGUAGE_CODE_RE.match(code):
                raise ModError("errors.invalid_language", file="", language=code)

        def as_json(data: dict) -> bytes:
            return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

        # On écrit dans un fichier temporaire puis on renomme : jamais d'archive à moitié écrite.
        temp_path = archive_path.with_name(archive_path.name + ".tmp")
        try:
            # L'ancienne archive reste ouverte pendant l'écriture : les fichiers non modifiés
            # sont recopiés depuis elle.
            old_archive = zipfile.ZipFile(replacing.archive_path) if replacing else None
            try:
                with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr(META_FILE, as_json(metadata))
                    for code, language_texts in language_files.items():
                        archive.writestr(f"{I18N_DIR}/{code}.json", as_json(language_texts.to_dict()))
                    for rid, member in members.items():
                        archive.writestr(member, resource_sources[rid].read(old_archive))
                    for source, member in zip(image_sources, images):
                        archive.writestr(member, source.read(old_archive))
                    if logo_source and logo:
                        archive.writestr(logo, logo_source.read(old_archive))
            finally:
                if old_archive:
                    old_archive.close()  # à fermer AVANT le remplacement (obligatoire sous Windows)
            os.replace(temp_path, archive_path)
            if replacing and replacing.archive_path != archive_path:
                replacing.archive_path.unlink(missing_ok=True)  # l'identité a changé : ancien nom supprimé
                self._rename_in_order(replacing.mod_id, make_mod_id(name, author))
        except (OSError, KeyError, zipfile.BadZipFile) as err:
            temp_path.unlink(missing_ok=True)
            raise ModError("errors.write_failed", path=str(archive_path), reason=str(err)) from err

        return self.read_mod(archive_path)

    @staticmethod
    def _allocate_image_names(names: list[str], reserved: list[str]) -> list[str]:
        """Noms de fichier uniques pour les images, dans l'ordre. / Unique image file names, in order.

        Un nom déjà pris (ou réservé, ex. _logo.png pour l'icône) devient "nom (1).png", "nom (2).png"…
        Les caractères interdits sous Windows sont remplacés par "_".
        """
        taken = {name.lower() for name in reserved}
        result = []
        for raw in names:
            leaf = Path(raw.replace("\\", "/")).name
            safe = "".join("_" if c in '<>:"/\\|?*' or ord(c) < 32 else c for c in leaf).strip(" .")
            path = Path(safe or "image.png")
            stem, suffix = path.stem[:100] or "image", path.suffix.lower()
            candidate, number = stem + suffix, 0
            while candidate.lower() in taken:
                number += 1
                candidate = f"{stem} ({number}){suffix}"
            taken.add(candidate.lower())
            result.append(candidate)
        return result

    # ------------------------------------------------- import / export / suppression

    def import_mod(self, source: Path) -> Mod:
        """Valide une archive externe puis la copie dans mods/.
        Validate an external archive, then copy it into mods/.

        Raises:
            ModError: archive invalide (voir read_mod), doublon ou copie impossible.
        """
        mod = self.read_mod(source)  # rien n'est copié si l'archive n'est pas valide
        if self.is_taken(mod.name, mod.author):
            raise ModError("errors.duplicate_mod", name=mod.name, author=mod.author)

        # L'archive est renommée selon la convention <mod_id>.zip, quel que soit son nom d'origine.
        destination = self.mods_dir / f"{mod.mod_id}.zip"
        temp_path = destination.with_name(destination.name + ".tmp")
        try:
            shutil.copyfile(source, temp_path)
            os.replace(temp_path, destination)
        except OSError as err:
            temp_path.unlink(missing_ok=True)
            raise ModError("errors.write_failed", path=str(destination), reason=str(err)) from err
        return self.read_mod(destination)

    def export_mod(self, mod: Mod, destination: Path) -> None:
        """Copie l'archive du mod vers `destination`. / Copy the mod archive to `destination`."""
        try:
            shutil.copyfile(mod.archive_path, destination)
        except OSError as err:
            raise ModError("errors.write_failed", path=str(destination), reason=str(err)) from err

    def delete_mod(self, mod: Mod) -> None:
        """Supprime l'archive du mod. / Delete the mod archive."""
        try:
            mod.archive_path.unlink()
        except OSError as err:
            raise ModError("errors.delete_failed", path=str(mod.archive_path), reason=str(err)) from err
