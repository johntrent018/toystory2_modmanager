"""Onglet « Liste des mods ». / Mod list tab."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from app.controllers.mod_list_controller import ModListController
from app.event_bus import EventBus, Events
from app.language_manager import LanguageManager
from app.models.mod import Mod, ModTexts
from app.views.icons import make_icon
from app.views.cursors import grab_cursor
from app.views.image_viewer import ImageViewer, load_photo
from app.views.resource_labels import CATEGORY_ORDER, describe_resources, resource_label
from app.views.widgets import Avatar, GripHandle, IconButton, InsertionMarker, ScrollableFrame, Tooltip

DOT_ACTIVE = "#2e9e44"    # voyant vert : mod activé
DOT_INACTIVE = "#d03030"  # voyant rouge : mod désactivé
DOT_SIZE = 12             # diamètre du voyant
ROW_SELECTED = "#cfe3ff"  # fond de la ligne sélectionnée
THUMB_SIZE = (160, 120)   # taille des miniatures de la galerie
LIST_ICON_SIZE = 26       # icônes crayon / poubelle de la liste (côte à côte)
LIST_AVATAR_SIZE = 40     # icône du mod dans la liste
HEADER_AVATAR_SIZE = 56   # icône du mod dans le panneau de droite
EDIT_COLOR, EDIT_HOVER = "#3f5f80", "#243d57"      # crayon : bleu-gris foncé, neutre
DELETE_COLOR, DELETE_HOVER = "#c62828", "#8e1c1c"  # poubelle : rouge
WARNING_COLOR = "#9a5b00"  # texte, icône et bordure de l'avertissement de l'auteur
DRAG_THRESHOLD = 6         # pixels à parcourir avant qu'un clic devienne un glisser
DRAG_DIM = "#e3e7ee"       # fond de la ligne d'origine pendant qu'on la déplace (emplacement vide)
DRAG_ACCENT = "#1a73e8"    # contour de l'élément saisi et ligne d'insertion
ACTION_BUTTON_WIDTH = -16   # largeur minimale commune (en caractères) des 3 gros boutons ; négatif = minimum
AUTOSCROLL_EDGE = 28       # distance au bord (px) où la liste défile pendant un glisser


@dataclass
class _Row:
    """Widgets d'une ligne de la liste de gauche. / Widgets of one left-list row."""

    frame: tk.Frame
    dot: tk.Canvas
    dot_id: int
    grip: tk.Canvas
    paintable: list  # tous les widgets dont la couleur de fond change avec la sélection


class ModListTab(ttk.Frame):
    """À gauche : liste des mods (réordonnable par glisser-déposer). À droite : détail du mod.
    Left: mod list (drag to reorder). Right: details of the selected mod.

    Vue "passive" : aucune règle métier ici, tout passe par le contrôleur.
    """

    def __init__(self, parent: tk.Misc, controller: ModListController, lang: LanguageManager, bus: EventBus) -> None:
        super().__init__(parent)
        self._controller = controller
        self._lang = lang
        self._selected_id: str | None = None
        self._rows: dict[str, _Row] = {}
        self._order: list[str] = []  # identifiants dans l'ordre affiché à gauche
        self._drag_id: str | None = None
        self._drag_start_y = 0
        self._dragging = False
        self._drop_index = 0      # position d'insertion visée (parmi les autres lignes)
        self._marker: InsertionMarker | None = None  # ligne d'insertion "ça atterrira ici"
        self._last_pointer_y = 0
        self._autoscroll_job: str | None = None
        self._thumb_refs: list = []  # références aux miniatures (sinon Tkinter les efface)
        self._row_bg = ttk.Style().lookup("TFrame", "background") or "#f0f0f0"

        # Polices dérivées de la police par défaut du thème.
        base = tkfont.nametofont("TkDefaultFont")
        self._bold_font = base.copy()
        self._bold_font.configure(weight="bold")
        self._title_font = base.copy()
        self._title_font.configure(size=18, weight="bold")
        # Même style pour Importer / Exporter / Activer : marges intérieures plus larges que hautes.
        ttk.Style().configure("Action.TButton", padding=(14, 5))

        self._build_ui()

        # Observer : la vue réagit aux événements. `owner=self` permet de se désabonner d'un coup
        # quand l'onglet est détruit (changement de langue).
        bus.subscribe(Events.MODS_CHANGED, self._on_mods_changed, owner=self)
        bus.subscribe(Events.MOD_STATE_CHANGED, self._on_state_changed, owner=self)
        bus.subscribe(Events.GAME_PATH_CHANGED, self._on_game_path_changed, owner=self)

        self._refresh_list()

    # ------------------------------------------------------------ construction

    def _build_ui(self) -> None:
        t = self._lang.t
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # ----- Panneau gauche : barre d'outils + liste des mods
        left = ttk.Frame(paned, width=340)
        left.pack_propagate(False)  # garde la largeur demandée
        paned.add(left, weight=0)
        self._left = left

        toolbar = ttk.Frame(left)
        toolbar.pack(side="top", fill="x", padx=6, pady=6)
        ttk.Button(toolbar, text=t("mod_list.import"), style="Action.TButton", width=ACTION_BUTTON_WIDTH,
                   command=self._on_import).pack(side="left")
        IconButton(toolbar, "refresh", self._on_mods_changed, tooltip=t("mod_list.refresh"),
                   size=30).pack(side="right", padx=(10, 2))  # alignée à droite du panneau

        # Recherche : le filtrage est instantané (à chaque touche), sans casse, sur le nom TEL QU'AFFICHÉ
        # (dans la langue courante, avec ses replis), donc pas de bouton loupe.
        search_row = ttk.Frame(left)
        search_row.pack(side="top", fill="x", padx=6, pady=(0, 6))
        ttk.Label(search_row, text=t("mod_list.search")).pack(side="left")
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self._search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        Tooltip(search_entry, t("mod_list.search_help"))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        self._list = ScrollableFrame(left, orient="vertical")
        self._list.pack(side="top", fill="both", expand=True)

        # ----- Panneau droit : détail (ou message "sélectionnez un mod")
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        self._placeholder = ttk.Label(right, text=t("mod_list.select_prompt"), anchor="center")
        self._details = ttk.Frame(right, padding=12)
        self._details.columnconfigure(0, weight=1)
        self._details.rowconfigure(3, weight=1)  # description
        self._details.rowconfigure(5, weight=1)  # niveaux

        # En-tête : icône | nom + auteur/version | boutons Exporter + Activer/Désactiver tout à droite.
        header = ttk.Frame(self._details)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        self._header_avatar = Avatar(header, HEADER_AVATAR_SIZE, self._row_bg)
        self._header_avatar.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        self._name_label = ttk.Label(header, font=self._title_font)
        self._name_label.grid(row=0, column=1, sticky="sw")
        self._author_label = ttk.Label(header)
        self._author_label.grid(row=1, column=1, sticky="nw")
        buttons = ttk.Frame(header)
        buttons.grid(row=0, column=2, rowspan=2, sticky="ne")
        ttk.Button(buttons, text=t("mod_list.export"), style="Action.TButton", width=ACTION_BUTTON_WIDTH,
                   command=self._on_export).pack(side="left", padx=(0, 18))
        self._toggle_button = ttk.Button(buttons, style="Action.TButton", width=ACTION_BUTTON_WIDTH,
                                         command=self._on_toggle)
        self._toggle_button.pack(side="left")

        # Avertissement affiché si le dossier du jeu n'est pas renseigné.
        self._hint = ttk.Label(self._details, text=t("mod_list.game_path_required"),
                               foreground="#b26a00", wraplength=700, justify="left")
        self._hint.grid(row=1, column=0, sticky="w", pady=(6, 0))

        # Avertissement de l'auteur (masqué s'il est vide). Le cadre est un tk.Frame coloré dont le
        # remplissage (padx/pady) forme une bordure épaisse de la même couleur que le texte.
        self._warning_box = tk.Frame(self._details, background=WARNING_COLOR, padx=3, pady=3)
        self._warning_box.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        inside = tk.Frame(self._warning_box, background=self._row_bg, padx=12, pady=10)
        inside.pack(fill="both", expand=True)
        self._warning_icon = make_icon("warning", WARNING_COLOR, 40)  # garder la référence
        tk.Label(inside, image=self._warning_icon, background=self._row_bg).pack(side="left", padx=(0, 14))
        warning_text = tk.Frame(inside, background=self._row_bg)
        warning_text.pack(side="left", fill="x", expand=True)
        tk.Label(warning_text, text=t("mod_list.warning"), font=self._bold_font, foreground=WARNING_COLOR,
                 background=self._row_bg, anchor="w").pack(fill="x")
        self._warning_label = tk.Label(warning_text, font=self._bold_font, foreground=WARNING_COLOR,
                                       background=self._row_bg, justify="left", anchor="w", wraplength=700)
        self._warning_label.pack(fill="x")

        description = ttk.LabelFrame(self._details, text=t("mod_list.description"), padding=6)
        description.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        description.columnconfigure(0, weight=1)
        description.rowconfigure(0, weight=1)
        self._description = tk.Text(description, height=5, wrap="word", state="disabled", borderwidth=0,
                                    background=self._row_bg)
        self._description.grid(row=0, column=0, sticky="nsew")

        gallery = ttk.LabelFrame(self._details, text=t("mod_list.gallery"), padding=6)
        gallery.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        gallery.columnconfigure(0, weight=1)
        self._gallery = ScrollableFrame(gallery, orient="horizontal")
        self._gallery.grid(row=0, column=0, sticky="ew")

        levels = ttk.LabelFrame(self._details, text=t("mod_list.affected_resources"), padding=6)
        levels.grid(row=5, column=0, sticky="nsew", pady=(10, 0))
        levels.columnconfigure(0, weight=1)
        levels.rowconfigure(0, weight=1)
        self._levels_list = tk.Listbox(levels, height=6, activestyle="none", exportselection=False)
        self._levels_list.grid(row=0, column=0, sticky="nsew")
        levels_scroll = ttk.Scrollbar(levels, orient="vertical", command=self._levels_list.yview)
        self._levels_list.configure(yscrollcommand=levels_scroll.set)
        levels_scroll.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------- liste de gauche

    def _refresh_list(self) -> None:
        """Reconstruit la liste des mods depuis le contrôleur. / Rebuild the mod list."""
        for child in self._list.inner.winfo_children():
            child.destroy()
        self._rows.clear()

        mods = self._controller.mods
        self._order = [mod.mod_id for mod in mods]
        if not mods:
            ttk.Label(self._list.inner, text=self._lang.t("mod_list.empty"), wraplength=290,
                      justify="left").pack(padx=10, pady=10, anchor="w")
        for mod in mods:
            self._rows[mod.mod_id] = self._create_row(mod)

        self._no_results = ttk.Label(self._list.inner, text=self._lang.t("mod_list.no_results"),
                                     wraplength=290, justify="left")  # affiché seulement si la recherche ne trouve rien
        if self._selected_id not in self._rows:  # le mod sélectionné a disparu
            self._selected_id = None
        self._paint_rows()
        self._show_details()
        self._apply_filter()

    def _search_query(self) -> str:
        """Texte recherché, sans casse ni espaces autour. / Search text, case-insensitive."""
        return self._search_var.get().strip().casefold()

    def _matches(self, mod: Mod, query: str) -> bool:
        """Le mod correspond-il à la recherche ? / Does the mod match the search?

        - "by:xxx"      : le nom de l'AUTEUR contient xxx ;
        - "version:1.3" : la VERSION commence par 1.3 (donc "1.3" trouve 1.3.4 mais pas 11.3) ;
        - sinon         : le NOM du mod tel qu'il est affiché (langue courante, avec ses replis) contient le texte.
        Un filtre à la fois (pas de combinaison) ; un filtre sans valeur ("by:") n'élimine rien.
        """
        if query.startswith("by:"):
            return query[3:].strip() in mod.author.casefold()
        if query.startswith("version:"):
            return mod.version.casefold().startswith(query[8:].strip())
        return query in self._texts(mod).name.casefold()

    def _apply_filter(self) -> None:
        """N'affiche que les mods qui correspondent à la recherche. / Show only matching mods."""
        if not self._rows:
            return
        query = self._search_query()
        by_id = {mod.mod_id: mod for mod in self._controller.mods}
        visible = [mod_id for mod_id in self._order if not query or self._matches(by_id[mod_id], query)]
        for mod_id in self._order:
            self._rows[mod_id].frame.pack_forget()
        self._no_results.pack_forget()
        for mod_id in visible:
            self._rows[mod_id].frame.pack(fill="x")
        if query and not visible:
            self._no_results.pack(padx=10, pady=10, anchor="w")

    def _create_row(self, mod: Mod) -> _Row:
        """Une ligne : [poignée] [icône] [nom + voyant / auteur] [crayon] [poubelle]. / One row."""
        t = self._lang.t
        texts = self._texts(mod)
        frame = tk.Frame(self._list.inner, padx=6, pady=6)
        frame.pack(fill="x")
        frame.columnconfigure(2, weight=1)

        # Poignée « 6 points » : curseur "main ouverte" ; elle montre que la ligne se glisse.
        grip = GripHandle(frame, self._row_bg)
        grip.configure(cursor=grab_cursor("grab", self))
        grip.grid(row=0, column=0, padx=(0, 6))
        Tooltip(grip, t("mod_list.drag_handle"))

        avatar = Avatar(frame, LIST_AVATAR_SIZE, self._row_bg)
        avatar.show(self._controller.get_logo_bytes(mod), texts.name)
        avatar.grid(row=0, column=1, padx=(0, 10))

        # Bloc texte : première ligne = nom + voyant à sa droite, seconde ligne = auteur.
        text_block = tk.Frame(frame)
        text_block.grid(row=0, column=2, sticky="w")
        top_line = tk.Frame(text_block)
        top_line.pack(anchor="w")
        name = tk.Label(top_line, text=texts.name, font=self._bold_font, anchor="w")
        name.pack(side="left")
        dot = tk.Canvas(top_line, width=DOT_SIZE, height=DOT_SIZE, highlightthickness=0)
        dot_id = dot.create_oval(1, 1, DOT_SIZE - 1, DOT_SIZE - 1, outline="")
        dot.pack(side="left", padx=(6, 0))
        author = tk.Label(text_block, text=mod.author, anchor="w", fg="#666666")
        author.pack(anchor="w")

        # Boutons d'action côte à côte (crayon à gauche), bien espacés pour éviter les clics ratés.
        actions = tk.Frame(frame)
        actions.grid(row=0, column=3, sticky="e", padx=(8, 0))
        edit_button = IconButton(actions, "pencil", lambda m=mod: self._controller.request_edit(m),
                                 tooltip=t("mod_list.edit"), color=EDIT_COLOR, hover_color=EDIT_HOVER,
                                 size=LIST_ICON_SIZE)
        edit_button.pack(side="left", padx=(0, 8))
        delete_button = IconButton(actions, "trash", lambda m=mod: self._on_delete(m),
                                   tooltip=t("mod_list.delete"), color=DELETE_COLOR, hover_color=DELETE_HOVER,
                                   size=LIST_ICON_SIZE)
        delete_button.pack(side="left")

        # Toute la partie à GAUCHE des boutons réagit : clic = sélectionner, glisser = réordonner,
        # double-clic = activer / désactiver.
        for widget in (frame, grip, avatar, text_block, top_line, name, dot, author):
            widget.bind("<ButtonPress-1>", lambda e, mod_id=mod.mod_id: self._on_press(e, mod_id))
            widget.bind("<B1-Motion>", self._on_motion)
            widget.bind("<ButtonRelease-1>", self._on_release)
            widget.bind("<Double-Button-1>", lambda _e, mod_id=mod.mod_id: self._on_row_double_click(mod_id))
        return _Row(frame, dot, dot_id, grip, [frame, grip, avatar, text_block, top_line, name, dot, author,
                                               actions, edit_button, delete_button])

    def _paint_rows(self) -> None:
        """Couleurs : fond (sélection) et voyant (actif/inactif). / Colors: background and light."""
        for mod in self._controller.mods:
            row = self._rows[mod.mod_id]
            background = ROW_SELECTED if mod.mod_id == self._selected_id else self._row_bg
            for widget in row.paintable:
                widget.configure(background=background)
            colour = DOT_ACTIVE if self._controller.is_active(mod) else DOT_INACTIVE
            row.dot.itemconfigure(row.dot_id, fill=colour)

    def _select(self, mod_id: str) -> None:
        self._selected_id = mod_id
        self._paint_rows()
        self._show_details()

    # ----------------------------------------------- réordonner (glisser-déposer)
    #
    # Pendant le glissement, la ligne d'origine reste en place (grisée) et une ligne d'insertion
    # bleue épaisse montre où l'élément atterrira. Rien d'autre ne bouge : pas de traînées.
    # L'ordre n'est modifié (et enregistré) qu'au relâchement du clic.

    def _on_press(self, event: tk.Event, mod_id: str) -> None:
        self._select(mod_id)
        self._drag_id = mod_id
        self._drag_start_y = event.y_root
        self._dragging = False

    def _on_motion(self, event: tk.Event) -> None:
        if self._drag_id is None or (not self._dragging and self._search_query()):
            return  # pendant une recherche, la liste est filtrée : on ne réordonne pas
        if not self._dragging:
            if abs(event.y_root - self._drag_start_y) < DRAG_THRESHOLD:
                return
            self._begin_drag()
        self._last_pointer_y = event.y_root
        self._update_drag()

    def _begin_drag(self) -> None:
        """Le clic maintenu devient un glisser : ligne d'origine grisée, marqueur d'insertion, poing fermé."""
        if self._drag_id not in self._rows:
            return
        self._dragging = True
        self._marker = InsertionMarker(self._list.inner, DRAG_ACCENT)
        for widget in self._rows[self._drag_id].paintable:  # la ligne d'origine devient un emplacement grisé
            widget.configure(background=DRAG_DIM)
        self._set_drag_cursor(grab_cursor("grabbing", self))

    def _update_drag(self) -> None:
        """Calcule où l'élément s'insérera et déplace le marqueur. / Compute the drop spot, move the marker."""
        inner = self._list.inner
        pointer_y = self._last_pointer_y - inner.winfo_rooty()  # y dans la liste (tient compte du défilement)

        # Position d'insertion = nombre d'AUTRES lignes dont le milieu est au-dessus du pointeur.
        others = [mod_id for mod_id in self._order if mod_id != self._drag_id]
        self._drop_index = sum(
            1 for mod_id in others
            if self._rows[mod_id].frame.winfo_y() + self._rows[mod_id].frame.winfo_height() / 2 < pointer_y)
        if self._drop_index < len(others):  # juste au-dessus de la ligne qui sera juste après
            line_y = self._rows[others[self._drop_index]].frame.winfo_y()
        elif others:                        # tout en bas de la liste
            last = self._rows[others[-1]].frame
            line_y = last.winfo_y() + last.winfo_height()
        else:
            line_y = 0
        self._marker.show(line_y)

        # Près du bord haut/bas de la zone visible : la liste défile toute seule.
        canvas = self._list.canvas
        near_edge = (self._last_pointer_y < canvas.winfo_rooty() + AUTOSCROLL_EDGE
                     or self._last_pointer_y > canvas.winfo_rooty() + canvas.winfo_height() - AUTOSCROLL_EDGE)
        if near_edge and self._autoscroll_job is None:
            self._autoscroll_job = self.after(60, self._autoscroll)

    def _autoscroll(self) -> None:
        self._autoscroll_job = None
        if not self._dragging:
            return
        canvas = self._list.canvas
        if self._last_pointer_y < canvas.winfo_rooty() + AUTOSCROLL_EDGE:
            canvas.yview_scroll(-1, "units")
        elif self._last_pointer_y > canvas.winfo_rooty() + canvas.winfo_height() - AUTOSCROLL_EDGE:
            canvas.yview_scroll(1, "units")
        else:
            return
        self._update_drag()  # relance aussi le défilement tant que la souris reste au bord

    def _set_drag_cursor(self, cursor: str) -> None:
        """Curseur de toute la fenêtre pendant le glisser (poing fermé), puis retour à la normale.
        Les widgets sans curseur propre héritent de celui de la fenêtre.
        """
        self.winfo_toplevel().configure(cursor=cursor if self._dragging else "")
        for row in self._rows.values():
            row.grip.configure(cursor=cursor)

    def _on_release(self, _event: tk.Event) -> None:
        if self._dragging:
            self._end_drag()
        self._drag_id = None
        self._dragging = False

    def _end_drag(self) -> None:
        """Relâchement : on retire les éléments visuels puis on applique le nouvel ordre."""
        if self._marker is not None:
            self._marker.destroy()
            self._marker = None
        if self._autoscroll_job is not None:
            self.after_cancel(self._autoscroll_job)
            self._autoscroll_job = None
        self._dragging = False
        self._set_drag_cursor(grab_cursor("grab", self))  # poignées : retour à la main ouverte

        others = [mod_id for mod_id in self._order if mod_id != self._drag_id]
        new_order = others[:self._drop_index] + [self._drag_id] + others[self._drop_index:]
        if new_order != self._order:
            self._order = new_order
            for mod_id in self._order:  # on ré-empile les lignes dans le nouvel ordre
                self._rows[mod_id].frame.pack_forget()
            for mod_id in self._order:
                self._rows[mod_id].frame.pack(fill="x")
            error = self._controller.set_order(self._order)
            if error:
                messagebox.showerror(self._lang.t("common.error"), error, parent=self)
        self._paint_rows()  # remet les couleurs normales (la ligne n'est plus grisée)

    def _on_row_double_click(self, mod_id: str) -> None:
        """Double-clic sur une ligne = activer / désactiver le mod (comme le bouton de droite)."""
        if self._controller.can_toggle():  # sans dossier du jeu, rien à faire (le bouton est grisé aussi)
            self._select(mod_id)
            self._on_toggle()

    def _texts(self, mod: Mod) -> ModTexts:
        """Textes du mod dans la langue de l'interface (repli : anglais, puis langue du mod)."""
        return mod.localized(self._lang.language)

    def _current_mod(self) -> Mod | None:
        return next((m for m in self._controller.mods if m.mod_id == self._selected_id), None)

    # --------------------------------------------------------- panneau droit

    def _show_details(self) -> None:
        """Affiche le mod sélectionné (ou le message d'invite). / Show selected mod details."""
        t = self._lang.t
        mod = self._current_mod()
        if mod is None:
            self._details.pack_forget()
            self._placeholder.pack(expand=True)
            return
        self._placeholder.pack_forget()
        self._details.pack(fill="both", expand=True)

        texts = self._texts(mod)
        self._header_avatar.show(self._controller.get_logo_bytes(mod), texts.name)
        self._name_label.configure(text=texts.name)
        subtitle = t("mod_list.by_author", author=mod.author)
        if mod.version:
            subtitle += " · " + t("mod_list.version", version=mod.version)
        self._author_label.configure(text=subtitle)

        if texts.warning:
            self._warning_label.configure(text=texts.warning)
            self._warning_box.grid()
        else:
            self._warning_box.grid_remove()

        self._description.configure(state="normal")
        self._description.delete("1.0", "end")
        self._description.insert("1.0", texts.description or t("mod_list.no_description"))
        self._description.configure(state="disabled")

        self._fill_gallery(mod)
        self._fill_resources(mod)
        self._refresh_toggle()

    def _fill_resources(self, mod: Mod) -> None:
        """Liste des ressources du mod, groupées par type (Niveaux, Écrans…). / Resources grouped by type."""
        self._levels_list.delete(0, "end")
        groups: dict[str, list] = {}
        for resource_id in mod.resource_ids:
            groups.setdefault(resource_id.top_category, []).append(resource_id)
        for top in sorted(groups, key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99):
            self._levels_list.insert("end", self._lang.t(f"resource_types.{top}"))
            self._levels_list.itemconfigure("end", foreground="#1a5fb4")  # titre de groupe
            for resource_id in groups[top]:
                self._levels_list.insert("end", "    " + resource_label(self._lang, resource_id))

    def _fill_gallery(self, mod: Mod) -> None:
        """Miniatures cliquables, dans l'ordre du mod (clic → visionneuse). / Clickable thumbnails."""
        for child in self._gallery.inner.winfo_children():
            child.destroy()
        self._thumb_refs.clear()

        if not mod.images:
            ttk.Label(self._gallery.inner, text=self._lang.t("mod_list.no_images")).pack(padx=8, pady=8)
            return
        for index in range(len(mod.images)):
            label = ttk.Label(self._gallery.inner, cursor="hand2")
            try:
                photo = load_photo(self._controller.get_image_bytes(mod, index), THUMB_SIZE)
                label.configure(image=photo)
                self._thumb_refs.append(photo)
            except Exception:  # image illisible : on affiche un "?" plutôt que de planter
                label.configure(text="?")
            label.pack(side="left", padx=4, pady=4)
            label.bind("<Button-1>", lambda _e, m=mod, i=index: self._open_viewer(m, i))

    def _open_viewer(self, mod: Mod, index: int) -> None:
        ImageViewer(self, self._lang, len(mod.images),
                    lambda i: self._controller.get_image_bytes(mod, i), index)

    def _refresh_toggle(self) -> None:
        """Texte du bouton (Activer/Désactiver) et état (grisé sans dossier du jeu)."""
        mod = self._current_mod()
        if mod is None:
            return
        key = "mod_list.disable" if self._controller.is_active(mod) else "mod_list.enable"
        self._toggle_button.configure(text=self._lang.t(key))
        if self._controller.can_toggle():
            self._toggle_button.state(["!disabled"])
            self._hint.grid_remove()
        else:
            self._toggle_button.state(["disabled"])
            self._hint.grid()

    # ---------------------------------------------------------------- actions

    def _on_toggle(self) -> None:
        mod = self._current_mod()
        if mod is None:
            return
        error = self._controller.toggle(mod, self._confirm_conflicts)
        if error:
            messagebox.showerror(self._lang.t("common.error"), error, parent=self)

    def _confirm_conflicts(self, conflicts: list[Mod]) -> bool:
        """Modale Oui/Non : liste les mods actifs en conflit et leurs niveaux.
        Yes/No dialog listing the conflicting active mods and their levels.
        """
        t = self._lang.t
        target = self._current_mod()
        lines = [t("mod_list.conflict.intro", name=self._texts(target).name if target else "")]
        for other in conflicts:
            lines.append(t("mod_list.conflict.entry", name=self._texts(other).name, author=other.author,
                           resources=describe_resources(self._lang, other.resource_ids)))
        lines.append(t("mod_list.conflict.question"))
        return messagebox.askyesno(t("mod_list.conflict.title"), "\n\n".join(lines), icon="warning", parent=self)

    def _on_import(self) -> None:
        t = self._lang.t
        files = filedialog.askopenfilenames(
            parent=self, title=t("mod_list.import_dialog"),
            filetypes=[(t("mod_list.zip_files"), "*.zip"), (t("create_mod.all_files"), "*.*")])
        if files:  # vide si la boîte de dialogue est annulée
            self._import_files(list(files))

    def _import_files(self, files: list[str]) -> None:
        """Importe une ou plusieurs archives .zip et affiche le bilan."""
        t = self._lang.t
        report = self._controller.import_mods(files)
        if report.imported:
            self._select(report.imported[-1].mod_id)  # la liste est déjà rechargée (MODS_CHANGED)
        if len(files) == 1 and not report.failed:
            return  # un seul mod importé sans souci : la sélection suffit, pas de popup

        lines = []
        if report.imported:
            lines.append(t("mod_list.import_report.success_header", count=len(report.imported)))
            lines += [t("mod_list.import_report.success_entry", name=self._texts(mod).name) for mod in report.imported]
        if report.failed:
            if lines:
                lines.append("")
            lines.append(t("mod_list.import_report.failure_header", count=len(report.failed)))
            lines += [t("mod_list.import_report.failure_entry", file=name, reason=reason)
                      for name, reason in report.failed]
        title, text = t("mod_list.import_report.title"), "\n".join(lines)
        if not report.failed:
            messagebox.showinfo(title, text, parent=self)
        elif not report.imported:
            messagebox.showerror(title, text, parent=self)
        else:
            messagebox.showwarning(title, text, parent=self)

    def _on_export(self) -> None:
        t = self._lang.t
        mod = self._current_mod()
        if mod is None:
            return
        destination = filedialog.asksaveasfilename(
            parent=self, title=t("mod_list.export_dialog"), initialfile=mod.archive_path.name,
            defaultextension=".zip", filetypes=[(t("mod_list.zip_files"), "*.zip")])
        if not destination:
            return
        error = self._controller.export_mod(mod, destination)
        if error:
            messagebox.showerror(t("common.error"), error, parent=self)
        else:
            messagebox.showinfo(t("common.success"), t("mod_list.exported", path=destination), parent=self)

    def _on_delete(self, mod: Mod) -> None:
        """Modale de confirmation, puis suppression. / Confirmation dialog, then deletion."""
        t = self._lang.t
        message = t("mod_list.delete_confirm", name=self._texts(mod).name, author=mod.author)
        if self._controller.is_active(mod):
            message += "\n\n" + t("mod_list.delete_confirm_active")
        if not messagebox.askyesno(t("mod_list.delete_title"), message, icon="warning", parent=self):
            return
        error = self._controller.delete_mod(mod)
        if error:
            messagebox.showerror(t("common.error"), error, parent=self)

    # ------------------------------------------------- réactions aux événements

    def _on_mods_changed(self, **_: object) -> None:
        # Le contrôleur relit le disque, puis la vue se redessine.
        self._controller.reload()
        self._refresh_list()

    def _on_state_changed(self, **_: object) -> None:
        self._paint_rows()
        self._refresh_toggle()

    def _on_game_path_changed(self, **_: object) -> None:
        self._refresh_toggle()
