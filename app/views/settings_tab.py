"""Onglet « Paramètres ». / Settings tab."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.controllers.settings_controller import SettingsController
from app.event_bus import EventBus, Events
from app.language_manager import LanguageManager

GREEN = "#2e7d32"
RED = "#c62828"


class SettingsTab(ttk.Frame):
    """Choix du dossier d'installation du jeu. / Game installation folder selection.

    Vue "passive" : aucune règle métier ici, tout passe par le contrôleur.
    """

    def __init__(self, parent: tk.Misc, controller: SettingsController, lang: LanguageManager, bus: EventBus) -> None:
        super().__init__(parent, padding=12)
        self._controller = controller
        self._lang = lang
        self._path_var = tk.StringVar()
        self._language_codes: list[str] = []
        self._build_ui()
        bus.subscribe(Events.GAME_PATH_CHANGED, self._on_game_path_changed, owner=self)
        self._refresh()

    def _build_ui(self) -> None:
        t = self._lang.t

        # --- Dossier du jeu
        game = ttk.LabelFrame(self, text=t("settings.game_path.title"), padding=12)
        game.pack(fill="x", pady=(0, 12))
        game.columnconfigure(0, weight=1)
        ttk.Label(game, text=t("settings.game_path.help"), wraplength=800, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Entry(game, textvariable=self._path_var, state="readonly").grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(game, text=t("common.browse"), command=self._on_browse).grid(row=1, column=1)
        self._status = ttk.Label(game)
        self._status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # --- Langue préférée
        language = ttk.LabelFrame(self, text=t("settings.language.title"), padding=12)
        language.pack(fill="x", pady=(0, 12))
        language.columnconfigure(0, weight=1)
        ttk.Label(language, text=t("settings.language.help"), wraplength=800, justify="left").grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        choices = self._controller.language_choices()
        self._language_codes = [code for code, _ in choices]
        self._language_combo = ttk.Combobox(language, state="readonly", values=[name for _, name in choices], width=30)
        self._language_combo.grid(row=1, column=0, sticky="w")
        preferred = self._controller.preferred_language()
        if preferred in self._language_codes:
            self._language_combo.current(self._language_codes.index(preferred))
        self._language_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

    def _on_language_selected(self, _event: tk.Event) -> None:
        """Appliqué tout de suite : la fenêtre principale reconstruit l'interface dans la nouvelle langue."""
        index = self._language_combo.current()
        if 0 <= index < len(self._language_codes):
            self._controller.set_preferred_language(self._language_codes[index])

    def _on_browse(self) -> None:
        current = self._controller.game_path_text()
        initial = current if current and Path(current).is_dir() else str(Path.home())
        folder = filedialog.askdirectory(parent=self, title=self._lang.t("settings.game_path.dialog_title"),
                                         initialdir=initial, mustexist=True)
        if not folder:  # boîte de dialogue annulée
            return
        error = self._controller.set_game_path(folder)
        if error:
            messagebox.showerror(self._lang.t("common.error"), error, parent=self)

    def _on_game_path_changed(self, **_: object) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """Affiche le chemin et son état (valide ou non). / Show the path and its status."""
        self._path_var.set(self._controller.game_path_text())
        if self._controller.is_game_path_valid():
            self._status.configure(text=self._lang.t("settings.game_path.status_valid"), foreground=GREEN)
        else:
            self._status.configure(text=self._lang.t("settings.game_path.status_invalid"), foreground=RED)
