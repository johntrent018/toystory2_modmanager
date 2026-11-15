"""Panneau « ressources d'une catégorie » (onglet Niveaux, Écrans…). / Resource panel for one category."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from app.controllers.create_mod_controller import CreateModController
from app.language_manager import LanguageManager
from app.models.resource_table import Resource
from app.views.resource_labels import resource_label
from app.views.widgets import IconButton, ScrollableFrame


class ResourcePanel(ttk.Frame):
    """Choisir une ressource de la catégorie, lui associer UN fichier, voir/modifier la liste.
    Pick a resource of the category, attach ONE file to it, see/edit the list.

    Un même panneau sert pour les niveaux, les écrans… : seule la catégorie change. L'extension du
    fichier attendu (.ngn, .bmp…) est celle du fichier du jeu à remplacer. Vue passive : l'état est
    dans le contrôleur.
    """

    def __init__(self, parent: tk.Misc, controller: CreateModController, lang: LanguageManager, category: str) -> None:
        super().__init__(parent, padding=(0, 6, 0, 0))
        self._controller = controller
        self._lang = lang
        self._category = category
        self._available: list[Resource] = []  # ressources proposées dans la liste déroulante
        self._bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self._bold_font.configure(weight="bold")
        t = lang.t

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        picker = ttk.Frame(self)
        picker.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        picker.columnconfigure(0, weight=1)
        self._combo = ttk.Combobox(picker, state="readonly")
        self._combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._add_button = ttk.Button(picker, text=t("create_mod.choose_file"), command=self._on_add)
        self._add_button.grid(row=0, column=1)
        ttk.Label(self, text=t("create_mod.row_hint"), foreground="#666666").grid(row=1, column=0, sticky="w", pady=(0, 4))
        self._table = ScrollableFrame(self, orient="vertical", height=64)
        self._table.grid(row=2, column=0, sticky="nsew")
        self._table.inner.columnconfigure(0, weight=1, uniform="cols")
        self._table.inner.columnconfigure(1, weight=1, uniform="cols")

    # ------------------------------------------------------------ rafraîchissement

    def refresh(self) -> None:
        """Reconstruit le tableau des ressources ajoutées et la liste de celles qui restent."""
        t = self._lang.t
        grid = self._table.inner
        for child in grid.winfo_children():
            child.destroy()

        selected = self._controller.selected_resources(self._category)
        if selected:
            ttk.Label(grid, text=t(f"resource_item.{self._category}"), font=self._bold_font).grid(
                row=0, column=0, sticky="w", padx=4, pady=(0, 4))
            ttk.Label(grid, text=t("create_mod.col_file"), font=self._bold_font).grid(
                row=0, column=1, sticky="w", padx=4, pady=(0, 4))
        else:
            ttk.Label(grid, text=t("create_mod.nothing_added_yet"), foreground="#666666").grid(
                row=0, column=0, columnspan=3, sticky="w", padx=4, pady=4)

        for row, (resource, source) in enumerate(selected, start=1):
            name_label = ttk.Label(grid, text=resource_label(self._lang, resource.id))
            file_label = ttk.Label(grid, text=source.name)
            name_label.grid(row=row, column=0, sticky="w", padx=4, pady=2)
            file_label.grid(row=row, column=1, sticky="w", padx=4, pady=2)
            # Poubelle à droite de la ligne : retire cette ressource.
            IconButton(grid, "trash", lambda r=resource: self._on_remove(r), tooltip=t("create_mod.remove_item"),
                       hover_color="#c62828", size=16).grid(row=row, column=2, padx=(4, 8))
            # Double-clic sur la ligne : choisir un autre fichier pour cette ressource.
            for widget in (name_label, file_label):
                widget.bind("<Double-Button-1>", lambda _e, r=resource: self._on_change(r))

        self._available = self._controller.available_resources(self._category)
        if self._available:
            self._combo.configure(values=[resource_label(self._lang, r.id) for r in self._available])
            self._combo.current(0)
            self._add_button.state(["!disabled"])
        else:
            self._combo.configure(values=[])
            self._combo.set(t("create_mod.no_item_left"))
            self._add_button.state(["disabled"])

    # ------------------------------------------------------------------- actions

    def _pick_file(self, resource: Resource | None, title_key: str) -> str:
        """Boîte de dialogue de choix du fichier ("" si annulée). / File picker."""
        t = self._lang.t
        filters = [(t("create_mod.all_files"), "*.*")]
        if resource is not None:  # filtre sur l'extension attendue (.ngn, .bmp…)
            filters.insert(0, (t("create_mod.files_of_type", type=resource.extension.lstrip(".").upper()),
                               f"*{resource.extension}"))
        return filedialog.askopenfilename(parent=self, title=t(title_key), filetypes=filters)

    def _show_error(self, message: str | None) -> None:
        if message:
            messagebox.showerror(self._lang.t("common.error"), message, parent=self)

    def _on_add(self) -> None:
        index = self._combo.current()
        resource = self._available[index] if 0 <= index < len(self._available) else None
        file_text = self._pick_file(resource, "create_mod.dialog_file")
        if not file_text:  # boîte de dialogue annulée
            return
        self._show_error(self._controller.add_resource(resource.id if resource else None, file_text))
        self.refresh()

    def _on_change(self, resource: Resource) -> None:
        file_text = self._pick_file(resource, "create_mod.dialog_change_file")
        if not file_text:
            return
        self._show_error(self._controller.change_resource_file(resource.id, file_text))
        self.refresh()

    def _on_remove(self, resource: Resource) -> None:
        self._controller.remove_resource(resource.id)
        self.refresh()
