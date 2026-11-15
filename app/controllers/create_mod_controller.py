"""Contrôleur de l'onglet « Créer un mod » (création ET modification). / Controller for the create/edit tab."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.event_bus import EventBus, Events
from app.language_manager import LanguageManager
from app.models.errors import ModError
from app.models.file_source import FileSource
from app.models.resource_table import Resource, ResourceId, get_resources
from app.models.logo import LOGO_NAME, build_logo_png, load_image
from app.models.mod import IMAGE_EXTENSIONS, Mod, ModTexts, slugify
from app.models.mod_activator import ModActivator
from app.models.mod_repository import ModRepository


class CreateModController:
    """Garde l'état du formulaire (niveaux, images, textes par langue), le valide, crée ou modifie le mod.
    Holds the form state (levels, images, per-language texts), validates it, creates or edits the mod.

    Mode création : `editing` vaut None. Mode modification : `editing` est le mod modifié,
    et le formulaire est prérempli avec ses fichiers et ses textes.

    Textes multilingues : nom / description / avertissement sont mémorisés PAR LANGUE
    (`_drafts`). La vue ne connaît que les textes de la langue affichée ; quand on change
    de langue, elle les confie au contrôleur (`switch_language`) qui rend ceux de la nouvelle langue.

    Les méthodes qui peuvent échouer renvoient un message d'erreur traduit
    (ou None si tout va bien) : la vue n'a qu'à l'afficher.
    """

    def __init__(self, repository: ModRepository, activator: ModActivator, bus: EventBus, lang: LanguageManager) -> None:
        self._repo = repository
        self._activator = activator
        self._bus = bus
        self._lang = lang
        self._editing: Mod | None = None
        self._resources: dict[ResourceId, FileSource] = {}  # ressource → fichier (UN SEUL par ressource)
        self._images: list[FileSource] = []      # ORDRE = ordre d'affichage de la galerie
        self._logo: FileSource | None = None     # icône du mod (carrée, déjà recadrée)
        self._drafts: dict[str, ModTexts] = {}    # code de langue → textes saisis
        self._default_language = lang.preferred_language  # langue par défaut du mod
        self._form_language = self._default_language      # langue actuellement affichée dans le formulaire

        # Observer : la liste demande une modification ; un mod supprimé peut être celui qu'on édite ;
        # la langue préférée peut changer (elle devient la langue par défaut des nouveaux mods).
        bus.subscribe(Events.EDIT_MOD_REQUESTED, self._on_edit_requested, owner=self)
        bus.subscribe(Events.MOD_DELETED, self._on_mod_deleted, owner=self)
        bus.subscribe(Events.LANGUAGE_CHANGED, self._on_language_changed, owner=self)

    # ------------------------------------------------------------------- mode

    @property
    def editing(self) -> Mod | None:
        """Mod en cours de modification (None = mode création). / Mod being edited."""
        return self._editing

    def editing_is_active(self) -> bool:
        """Le mod modifié est-il actuellement activé ? / Is the edited mod currently enabled?"""
        return self._editing is not None and self._activator.is_active(self._editing.mod_id)

    def _on_edit_requested(self, mod: Mod, **_: object) -> None:
        """Préremplit le formulaire avec le mod. / Prefill the form with the mod."""
        self._editing = mod
        self._resources = {rid: FileSource(member=member) for rid, member in sorted(mod.all_resources.items())}
        self._images = [FileSource(member=member) for member in mod.images]
        self._logo = FileSource(member=mod.logo) if mod.logo else None
        # Un ancien mod (sans i18n) n'a pas de langue : ses textes passent dans la langue préférée.
        self._default_language = mod.default_language or self._lang.preferred_language
        self._drafts = {(code or self._default_language): texts for code, texts in mod.texts.items()}
        self._form_language = self._default_language
        self._bus.publish(Events.EDIT_STATE_CHANGED, mod=mod)

    def _on_mod_deleted(self, mod_id: str, **_: object) -> None:
        if self._editing is not None and self._editing.mod_id == mod_id:
            self.cancel_edit()

    def _on_language_changed(self, **_: object) -> None:
        # Changer de langue se fait depuis les Paramètres : le formulaire y est toujours vide
        # (quitter l'onglet de création le vide). On repart de la nouvelle langue par défaut.
        if self._editing is None:
            self.reset()

    def cancel_edit(self) -> None:
        """Abandonne la modification et revient au formulaire de création vide.
        Abandon editing and go back to an empty creation form.
        """
        self.reset()

    def reset(self) -> None:
        """Vide l'état du formulaire et repasse en mode création. / Clear state, back to create mode."""
        self._editing = None
        self._resources.clear()
        self._images.clear()
        self._logo = None
        self._drafts = {}
        self._default_language = self._lang.preferred_language
        self._form_language = self._default_language
        self._bus.publish(Events.EDIT_STATE_CHANGED, mod=None)

    def is_dirty(self, current: ModTexts, author: str, version: str) -> bool:
        """Quitter l'onglet ferait-il perdre quelque chose ? / Would leaving the tab lose something?

        En modification : toujours oui (la vue demande confirmation). En création : seulement
        si quelque chose a été saisi ou choisi.
        """
        if self._editing is not None:
            return True
        other_languages = any(not texts.is_empty() for code, texts in self._drafts.items()
                              if code != self._form_language)
        return bool(not current.is_empty() or other_languages or author.strip() or version.strip()
                    or self._resources or self._images or self._logo)

    # ----------------------------------------------------------------- langues

    @property
    def form_language(self) -> str:
        """Langue dont les textes sont affichés dans le formulaire. / Language shown in the form."""
        return self._form_language

    @property
    def default_language(self) -> str:
        """Langue par défaut du mod en cours. / Default language of the current mod."""
        return self._default_language

    def language_choices(self) -> list[tuple[str, str]]:
        """Langues proposables : celles de l'appli + celles déjà présentes dans le mod édité.
        Offered languages: the app's, plus any already present in the edited mod.
        """
        choices = self._lang.available_languages()
        known = {code for code, _ in choices}
        choices += [(code, code) for code in self._drafts if code not in known]
        return choices

    def form_texts(self) -> ModTexts:
        """Textes mémorisés pour la langue affichée. / Stored texts for the displayed language."""
        return self._drafts.get(self._form_language, ModTexts())

    def switch_language(self, current: ModTexts, new_language: str) -> ModTexts:
        """Change la langue affichée : mémorise les textes actuels, rend ceux de `new_language`.
        Switch the displayed language: store the current texts, return those of `new_language`.
        """
        self._drafts[self._form_language] = current
        self._form_language = new_language
        return self._drafts.get(new_language, ModTexts())

    # -------------------------------------------------------------- ressources

    def available_resources(self, category: str) -> list[Resource]:
        """Ressources de la catégorie pas encore ajoutées au mod. / Category resources not yet added."""
        return [r for r in get_resources().in_category(category) if r.id not in self._resources]

    def selected_resources(self, category: str) -> list[tuple[Resource, FileSource]]:
        """Ressources ajoutées de la catégorie, avec leur fichier, dans l'ordre du JSON.
        Added resources of the category with their file, in JSON order.
        """
        return [(r, self._resources[r.id]) for r in get_resources().in_category(category)
                if r.id in self._resources]

    def _check_file(self, file_text: str, resource: Resource) -> tuple[Path | None, str | None]:
        """Vérifie qu'un fichier choisi existe et a l'extension attendue (celle du fichier du jeu).
        Check that a picked file exists and has the extension of the game's file.
        """
        path = Path(file_text)
        if path.suffix.lower() != resource.extension:
            return None, self._lang.t("errors.wrong_extension", file=path.name, extension=resource.extension)
        if not path.is_file():
            return None, self._lang.t("errors.file_not_found", file=str(path))
        return path, None

    def add_resource(self, resource_id: ResourceId | None, file_text: str) -> str | None:
        """Associe un fichier à une ressource. / Attach a file to a resource."""
        if resource_id is None:
            return self._lang.t("errors.no_item_selected")
        if resource_id in self._resources:
            return self._lang.t("errors.already_added")
        resource = get_resources().by_id(resource_id)
        path, error = self._check_file(file_text, resource)
        if error:
            return error
        self._resources[resource_id] = FileSource(path=path)
        return None

    def change_resource_file(self, resource_id: ResourceId, file_text: str) -> str | None:
        """Remplace le fichier d'une ressource déjà ajoutée. / Replace the file of an added resource."""
        path, error = self._check_file(file_text, get_resources().by_id(resource_id))
        if error:
            return error
        self._resources[resource_id] = FileSource(path=path)
        return None

    def remove_resource(self, resource_id: ResourceId) -> None:
        """Retire une ressource du mod. / Remove a resource from the mod."""
        self._resources.pop(resource_id, None)

    # ----------------------------------------------------------------- images

    @property
    def images(self) -> list[FileSource]:
        """Images choisies. / Chosen images."""
        return list(self._images)

    def add_images(self, file_texts: list[str]) -> str | None:
        """Ajoute des images (les doublons sont ignorés). / Add images (duplicates ignored)."""
        error = None
        for text in file_texts:
            path = Path(text)
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                error = self._lang.t("errors.bad_image", file=path.name)
                continue
            source = FileSource(path=path)
            if source not in self._images:
                self._images.append(source)
        return error

    def remove_image(self, index: int) -> None:
        """Retire une image. / Remove an image."""
        if 0 <= index < len(self._images):
            del self._images[index]

    def image_bytes(self, index: int) -> bytes | None:
        """Contenu de l'image n° `index` (pour en faire une miniature), ou None si illisible.
        Content of image `index` (to build a thumbnail), or None if unreadable.
        """
        try:
            source = self._images[index]
            if source.data is not None:
                return source.data
            if source.path is not None:
                return source.path.read_bytes()
            if self._editing is not None and source.member:
                return self._repo.read_file(self._editing, source.member)
        except (OSError, ModError, IndexError):
            pass
        return None

    def move_image(self, index: int, new_index: int) -> None:
        """Déplace une image dans l'ordre d'affichage. / Move an image in the display order."""
        if 0 <= index < len(self._images) and 0 <= new_index < len(self._images):
            self._images.insert(new_index, self._images.pop(index))

    # ------------------------------------------------------------------- logo

    @property
    def has_logo(self) -> bool:
        """Le mod a-t-il une icône ? / Does the mod have an icon?"""
        return self._logo is not None

    def logo_bytes(self) -> bytes | None:
        """Contenu de l'icône (pour l'aperçu). / Icon content (for the preview)."""
        if self._logo is None:
            return None
        if self._logo.data is not None:
            return self._logo.data
        try:
            return self._repo.read_file(self._editing, self._logo.member) if self._editing else None
        except ModError:
            return None

    def check_logo_source(self, image_path: str) -> str | None:
        """L'image choisie peut-elle servir d'icône ? (None = oui, sinon message d'erreur)."""
        path = Path(image_path)
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return self._lang.t("errors.bad_image", file=path.name)
        try:
            load_image(path)
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        return None

    def set_logo(self, image_path: str, box: tuple[int, int, int, int]) -> str | None:
        """Définit l'icône : découpe `box` dans l'image choisie. / Set the icon from a cropped image.

        Le carré visible devient le logo (PNG 256x256, enregistré sous _logo.png) ; le reste de l'image est perdu.
        """
        try:
            png = build_logo_png(Path(image_path), box)
        except ModError as err:
            return self._lang.t(err.key, **err.params)
        self._logo = FileSource(data=png, label=LOGO_NAME)
        return None

    def remove_logo(self) -> None:
        """Retire l'icône du mod. / Remove the mod icon."""
        self._logo = None

    # ------------------------------------------------------------ enregistrement

    def save(
        self,
        current: ModTexts,
        author: str,
        version: str,
        confirm_conflicts: Callable[[list[Mod], str], bool],
    ) -> tuple[Mod | None, str | None]:
        """Valide le formulaire puis crée (ou met à jour) l'archive du mod.
        Validate the form, then create (or update) the mod archive.

        Args:
            current: textes affichés dans le formulaire (langue `form_language`).
            confirm_conflicts: fournie par la vue ; reçoit les mods actifs en conflit et le nom du
                mod enregistré, renvoie True si l'utilisateur accepte de les désactiver. N'est
                appelée que si le mod modifié est actif et que ses niveaux entrent en conflit.

        Modifier un mod ACTIF : la nouvelle version est appliquée au jeu dès l'enregistrement
        et le mod reste actif (le jeu charge le NGN au lancement du niveau).

        Returns:
            (mod, None) si enregistré (le formulaire est alors réinitialisé),
            (None, message) en cas d'erreur, (None, None) si l'utilisateur a annulé.
        """
        t = self._lang.t
        self._drafts[self._form_language] = current
        author, version = author.strip(), version.strip()
        texts = {code: draft.stripped() for code, draft in self._drafts.items()}
        default_name = texts.get(self._default_language, ModTexts()).name

        if not default_name:
            return None, t("errors.default_name_required", language=self._lang.language_name(self._default_language))
        if not author:
            return None, t("errors.author_required")
        if not slugify(default_name) or not slugify(author):
            return None, t("errors.invalid_name")  # ex. un nom fait uniquement de symboles
        if not self._resources:
            return None, t("errors.no_resource")
        # Doublon vérifié AVANT de toucher à quoi que ce soit.
        if self._repo.is_taken(default_name, author, self._editing):
            return None, t("errors.duplicate_mod", name=default_name, author=author)

        old_mod = self._editing
        was_active = self.editing_is_active()
        try:
            if was_active:
                self._activator.check_replace(old_mod, self._resources)  # le jeu pourra-t-il être mis à jour ?
                conflicts = self._activator.get_resource_conflicts(self._resources, old_mod.mod_id, self._repo.list_mods())
                if conflicts:
                    if not confirm_conflicts(conflicts, default_name):
                        return None, None
                    # Même règle que l'activation : désactivation complète des mods en conflit.
                    for other in conflicts:
                        self._activator.deactivate(other)

            new_mod = self._repo.save_mod(self._default_language, texts, author, version,
                                          dict(self._resources), list(self._images), self._logo,
                                          replacing=old_mod)
            if was_active:
                self._activator.replace_active(old_mod, new_mod)
        except ModError as err:
            return None, t(err.key, **err.params)

        self.reset()
        self._bus.publish(Events.MODS_CHANGED)
        return new_mod, None
