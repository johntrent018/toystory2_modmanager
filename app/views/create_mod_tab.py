"""Onglet « Créer un mod » (aussi utilisé pour modifier un mod). / Create tab (also used to edit a mod)."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from app.controllers.create_mod_controller import CreateModController
from app.event_bus import EventBus, Events
from app.language_manager import LanguageManager
from app.models.mod import Mod, ModTexts
from app.views.crop_dialog import ask_crop_box
from app.views.image_strip import THUMB_SIZE, ImageStrip
from app.views.image_viewer import load_photo
from app.views.resource_labels import CATEGORY_ORDER, describe_resources
from app.views.resource_panel import ResourcePanel
from app.views.widgets import Avatar, SquareButton


class CreateModTab(ttk.Frame):
    """Formulaire de création / modification d'un mod. / Mod creation / edition form.

    Vue "passive" : l'état (niveaux, images choisis, mode modification) et les validations
    sont dans le contrôleur ; la vue ne fait qu'afficher et relayer les clics.
    """

    SUPPORTED_CATEGORIES = {"levels", "screens"}  # types de ressources déjà gérés (les autres : « bientôt »)

    def __init__(self, parent: tk.Misc, controller: CreateModController, lang: LanguageManager,
                 bus: EventBus) -> None:
        super().__init__(parent, padding=12)
        self._controller = controller
        self._lang = lang
        self._panels: list[ResourcePanel] = []  # un panneau par catégorie de ressources gérée
        self._language_codes: list[str] = []  # codes de langue, dans l'ordre de la liste déroulante
        self._thumb_cache: dict[tuple, object] = {}  # miniatures déjà décodées (le décodage d'une grande image est lent)
        self._bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self._bold_font.configure(weight="bold")
        self._build_ui()
        bus.subscribe(Events.EDIT_STATE_CHANGED, self._on_edit_state_changed, owner=self)
        self._refresh_all()

    # ------------------------------------------------------------ construction

    def _build_ui(self) -> None:
        t = self._lang.t
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # seule la zone « ressources » prend la hauteur disponible

        # --- Ligne du haut : bandeau "mode modification" à gauche, langue du contenu tout à droite
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(0, weight=1)
        self._banner = ttk.Label(top, font=self._bold_font, foreground="#1a5fb4")
        self._banner.grid(row=0, column=0, sticky="w")
        ttk.Label(top, text=t("create_mod.language")).grid(row=0, column=1, padx=(8, 6))
        self._language_combo = ttk.Combobox(top, state="readonly", width=24)
        self._language_combo.grid(row=0, column=2)
        self._language_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        # --- Informations générales
        info = ttk.LabelFrame(self, text=t("create_mod.info"), padding=10)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        info.columnconfigure(1, weight=1)
        self._name_var = tk.StringVar()
        self._author_var = tk.StringVar()
        self._version_var = tk.StringVar()
        for row, (key, variable) in enumerate((("name", self._name_var), ("author", self._author_var),
                                               ("version", self._version_var))):
            ttk.Label(info, text=t(f"create_mod.{key}")).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Entry(info, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=2, padx=(8, 0))
        # Icône du mod (facultative) : aperçu carré + boutons, à droite des champs.
        logo_box = ttk.Frame(info)
        logo_box.grid(row=0, column=2, rowspan=5, sticky="n", padx=(16, 0))
        ttk.Label(logo_box, text=t("create_mod.logo")).pack()
        self._logo_avatar = Avatar(logo_box, 72, ttk.Style().lookup("TFrame", "background") or "#f0f0f0")
        self._logo_avatar.pack(pady=4)
        ttk.Button(logo_box, text=t("create_mod.logo_choose"), command=self._on_choose_logo).pack(fill="x")
        self._logo_remove_button = ttk.Button(logo_box, text=t("create_mod.logo_remove"),
                                              command=self._on_remove_logo)
        self._logo_remove_button.pack(fill="x", pady=(4, 0))

        ttk.Label(info, text=t("create_mod.description")).grid(row=3, column=0, sticky="nw", pady=2)
        self._description = tk.Text(info, height=3, wrap="word")
        self._description.grid(row=3, column=1, sticky="ew", pady=2, padx=(8, 0))

        # Avertissement (facultatif) : simple champ de la section « Informations ».
        ttk.Label(info, text=t("create_mod.warning")).grid(row=4, column=0, sticky="nw", pady=2)
        self._warning = tk.Text(info, height=2, wrap="word")
        self._warning.grid(row=4, column=1, sticky="ew", pady=2, padx=(8, 0))

        # --- Ressources modifiées : un sous-onglet par type de ressource
        resources = ttk.LabelFrame(self, text=t("create_mod.resources"), padding=10)
        resources.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        resources.columnconfigure(0, weight=1)
        resources.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(resources)
        notebook.grid(row=0, column=0, sticky="nsew")
        for category in CATEGORY_ORDER:  # Niveaux, Musiques, Effets sonores, Écrans, Cinématiques
            if category in self.SUPPORTED_CATEGORIES:
                panel = ResourcePanel(notebook, self._controller, self._lang, category)
                self._panels.append(panel)
                notebook.add(panel, text=t(f"resource_types.{category}"))
            else:  # prévu pour une prochaine version
                placeholder = ttk.Frame(notebook, padding=12)
                ttk.Label(placeholder, text=t("create_mod.coming_soon"), foreground="#777777").pack(anchor="w")
                notebook.add(placeholder, text=t(f"resource_types.{category}"))

        # --- Images (facultatif)
        images = ttk.LabelFrame(self, text=t("create_mod.images"), padding=10)
        images.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        images.columnconfigure(0, weight=1)
        ttk.Label(images, text=t("create_mod.images_hint"), foreground="#777777").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        # Bande de miniatures : glisser une image la déplace (ligne d'insertion verticale).
        self._image_strip = ImageStrip(images, on_move=self._on_image_moved, empty_text=t("create_mod.no_images_yet"))
        self._image_strip.grid(row=1, column=0, sticky="ew")
        buttons = ttk.Frame(images)
        buttons.grid(row=1, column=1, sticky="n", padx=(8, 0))  # hauteur naturelle : ne s'étire pas
        ttk.Button(buttons, text=t("create_mod.add_images"), command=self._on_add_images).pack(fill="x")
        ttk.Button(buttons, text=t("create_mod.remove"), command=self._on_remove_images).pack(fill="x", pady=(6, 0))
        arrows = ttk.Frame(buttons)
        arrows.pack(pady=(10, 0))
        # Boutons carrés de taille fixe, avec de vraies flèches dessinées (centrées par construction).
        SquareButton(arrows, "arrow_up", lambda: self._move_selected_image(-1),
                     tooltip=t("create_mod.move_up")).pack(side="left", padx=(0, 6))
        SquareButton(arrows, "arrow_down", lambda: self._move_selected_image(1),
                     tooltip=t("create_mod.move_down")).pack(side="left")

        # --- Validation
        footer = ttk.Frame(self)
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, text=t("create_mod.required_hint")).grid(row=0, column=0, sticky="w")
        self._cancel_button = ttk.Button(footer, text=t("create_mod.cancel_edit"),
                                         command=self._controller.cancel_edit)
        self._cancel_button.grid(row=0, column=1, padx=(0, 8))
        self._save_button = ttk.Button(footer, command=self._on_save)
        self._save_button.grid(row=0, column=2)

    # ---------------------------------------------------------- rafraîchissement

    def _refresh_all(self) -> None:
        self._refresh_language()
        self._refresh_mode()
        for panel in self._panels:
            panel.refresh()
        self._refresh_images()
        self._refresh_logo()

    def _refresh_logo(self) -> None:
        """Aperçu de l'icône (ou initiale si aucune) et bouton « Retirer ». / Icon preview."""
        self._logo_avatar.show(self._controller.logo_bytes(), self._name_var.get())
        if self._controller.has_logo:
            self._logo_remove_button.state(["!disabled"])
        else:
            self._logo_remove_button.state(["disabled"])

    def _refresh_mode(self) -> None:
        """Texte du bouton principal et bandeau selon le mode (création / modification)."""
        t = self._lang.t
        editing = self._controller.editing
        if editing:
            self._banner.configure(text=t("create_mod.editing_banner", name=editing.localized(self._lang.language).name))
            self._banner.grid()
            self._save_button.configure(text=t("create_mod.save_button"))
            self._cancel_button.grid()
        else:
            self._banner.grid_remove()
            self._save_button.configure(text=t("create_mod.create_button"))
            self._cancel_button.grid_remove()

    def _refresh_images(self, select: int | None = None) -> None:
        """Reconstruit la bande de miniatures. / Rebuild the thumbnail strip."""
        editing = self._controller.editing.mod_id if self._controller.editing else ""
        items = []
        for index, source in enumerate(self._controller.images):
            key = (editing, str(source.path) if source.path is not None else source.member)
            if key not in self._thumb_cache:
                data = self._controller.image_bytes(index)
                try:
                    self._thumb_cache[key] = load_photo(data, THUMB_SIZE) if data else None
                except Exception:  # image illisible : on affichera un "?" plutôt que de planter
                    self._thumb_cache[key] = None
            items.append((source.name, self._thumb_cache[key]))
        if select is None:
            select = self._image_strip.selected  # garde la sélection actuelle
        self._image_strip.set_items(items, select)

    def _on_edit_state_changed(self, mod: Mod | None = None, **_: object) -> None:
        """Le contrôleur entre/sort du mode modification : on (pré)remplit ou on vide le formulaire."""
        self._thumb_cache.clear()  # autre mod (ou formulaire vidé) : miniatures à refaire
        self._author_var.set(mod.author if mod else "")
        self._version_var.set(mod.version if mod else "")
        self._fill_texts(self._controller.form_texts())
        self._refresh_all()

    def _fill_texts(self, texts: ModTexts) -> None:
        """Affiche les textes d'une langue dans les trois champs. / Show one language's texts."""
        self._name_var.set(texts.name)
        self._set_text(self._description, texts.description)
        self._set_text(self._warning, texts.warning)

    def _current_texts(self) -> ModTexts:
        """Textes actuellement saisis (langue affichée). / Texts currently typed (displayed language)."""
        return ModTexts(self._name_var.get(), self._description.get("1.0", "end-1c"),
                        self._warning.get("1.0", "end-1c"))

    def _refresh_language(self) -> None:
        """Remplit la liste déroulante des langues et sélectionne celle du formulaire."""
        choices = self._controller.language_choices()
        self._language_codes = [code for code, _ in choices]
        self._language_combo.configure(values=[name for _, name in choices])
        form_language = self._controller.form_language
        if form_language in self._language_codes:
            self._language_combo.current(self._language_codes.index(form_language))

    def _on_language_selected(self, _event: tk.Event) -> None:
        """Changement de langue : les champs prennent les textes mémorisés de la nouvelle langue."""
        index = self._language_combo.current()
        if not 0 <= index < len(self._language_codes):
            return
        texts = self._controller.switch_language(self._current_texts(), self._language_codes[index])
        self._fill_texts(texts)

    def confirm_leave(self) -> bool:
        """Appelée avant de quitter l'onglet. Renvoie False si l'utilisateur veut rester.
        Called before leaving the tab. Returns False if the user wants to stay.

        S'il y a quelque chose à perdre (modification en cours, ou saisie de création),
        une confirmation Oui/Non est demandée ; Oui abandonne la modification / la saisie.
        """
        t = self._lang.t
        if not self._controller.is_dirty(self._current_texts(), self._author_var.get(), self._version_var.get()):
            return True
        editing = self._controller.editing
        message = (t("create_mod.leave_edit", name=editing.localized(self._lang.language).name)
                   if editing else t("create_mod.leave_create"))
        if messagebox.askyesno(t("create_mod.leave_title"), message, icon="warning", parent=self):
            self._controller.reset()
            return True
        return False

    @staticmethod
    def _set_text(widget: tk.Text, text: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    # ------------------------------------------------------------------- actions

    def _on_add_images(self) -> None:
        t = self._lang.t
        files = filedialog.askopenfilenames(
            parent=self, title=t("create_mod.dialog_images"),
            filetypes=[(t("create_mod.image_files"), "*.png *.jpg *.jpeg *.gif *.webp")])
        if not files:
            return
        error = self._controller.add_images(list(files))
        if error:
            messagebox.showerror(t("common.error"), error, parent=self)
        self._refresh_images()

    def _on_remove_images(self) -> None:
        selected = self._image_strip.selected
        if selected is not None:
            self._controller.remove_image(selected)
            self._refresh_images(select=min(selected, len(self._controller.images) - 1))

    def _move_selected_image(self, delta: int) -> None:
        """Boutons ↑ ↓ : déplace l'image sélectionnée d'un cran. / Move the selected image one step."""
        selected = self._image_strip.selected
        if selected is None:
            return
        target = selected + delta
        if 0 <= target < len(self._controller.images):
            self._controller.move_image(selected, target)
            self._refresh_images(select=target)

    def _on_image_moved(self, index: int, new_index: int) -> None:
        """Glisser-déposer d'une miniature : la bande nous donne l'ancienne et la nouvelle position."""
        self._controller.move_image(index, new_index)
        self._refresh_images(select=new_index)

    # ------------------------------------------------------------------- icône

    def _on_choose_logo(self) -> None:
        """Choix d'une image, puis fenêtre de rognage : le carré choisi devient l'icône."""
        t = self._lang.t
        file_text = filedialog.askopenfilename(
            parent=self, title=t("create_mod.logo_dialog"),
            filetypes=[(t("create_mod.image_files"), "*.png *.jpg *.jpeg *.gif *.webp")])
        if not file_text:
            return
        error = self._controller.check_logo_source(file_text)
        if not error:
            box = ask_crop_box(self, self._lang, Path(file_text))
            if box is None:  # rognage annulé
                return
            error = self._controller.set_logo(file_text, box)
        if error:
            messagebox.showerror(t("common.error"), error, parent=self)
        self._refresh_logo()

    def _on_remove_logo(self) -> None:
        self._controller.remove_logo()
        self._refresh_logo()

    def _on_save(self) -> None:
        t = self._lang.t
        was_editing = self._controller.editing is not None
        mod, error = self._controller.save(self._current_texts(), self._author_var.get(),
                                           self._version_var.get(), self._confirm_conflicts)
        if error:
            messagebox.showerror(t("common.error"), error, parent=self)
        elif mod is not None:  # (None, None) = l'utilisateur a annulé : on ne fait rien
            # Succès : le contrôleur a réinitialisé le formulaire (événement EDIT_STATE_CHANGED).
            messagebox.showinfo(t("common.success"),
                                t("create_mod.saved" if was_editing else "create_mod.created", name=mod.name),
                                parent=self)

    def _confirm_conflicts(self, conflicts: list[Mod], mod_name: str) -> bool:
        """Modale Oui/Non : des mods actifs touchent aux mêmes niveaux que le mod enregistré.
        Yes/No dialog: active mods overlap the saved mod's levels.
        """
        t = self._lang.t
        lines = [t("create_mod.conflict_intro", name=mod_name)]
        for other in conflicts:
            lines.append(t("mod_list.conflict.entry", name=other.localized(self._lang.language).name,
                           author=other.author, resources=describe_resources(self._lang, other.resource_ids)))
        lines.append(t("mod_list.conflict.question"))
        return messagebox.askyesno(t("mod_list.conflict.title"), "\n\n".join(lines), icon="warning", parent=self)
