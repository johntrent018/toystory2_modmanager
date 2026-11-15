"""Fenêtre principale. / Main window."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.controllers.create_mod_controller import CreateModController
from app.controllers.mod_list_controller import ModListController
from app.controllers.settings_controller import SettingsController
from app.event_bus import EventBus, Events
from app.language_manager import LanguageManager
from app.models.mod import Mod
from app.views.about_tab import AboutTab
from app.views.create_mod_tab import CreateModTab
from app.views.help_tab import HelpTab
from app.views.mod_list_tab import ModListTab
from app.views.settings_tab import SettingsTab


class MainWindow:
    """Assemble les trois onglets dans la fenêtre, et les reconstruit quand la langue change.
    Assembles the three tabs, and rebuilds them when the language changes.
    """

    def __init__(
        self,
        root: tk.Tk,
        lang: LanguageManager,
        bus: EventBus,
        list_controller: ModListController,
        create_controller: CreateModController,
        settings_controller: SettingsController,
    ) -> None:
        self._root = root
        self._lang = lang
        self._bus = bus
        self._controllers = (list_controller, create_controller, settings_controller)
        root.geometry("1150x800")
        root.minsize(900, 760)  # en dessous, le formulaire de création ne tiendrait plus en hauteur

        self._build()

        # Quand une modification de mod démarre, on bascule sur l'onglet du formulaire.
        bus.subscribe(Events.EDIT_STATE_CHANGED, self._on_edit_state_changed, owner=self)
        # Changement de langue : on reconstruit l'interface (voir _rebuild).
        bus.subscribe(Events.LANGUAGE_CHANGED, self._on_language_changed, owner=self)

    def _build(self, selected_index: int = 0) -> None:
        """Crée (ou recrée) le carnet d'onglets avec les textes de la langue courante."""
        t = self._lang.t
        list_controller, create_controller, settings_controller = self._controllers
        self._root.title(t("app_data.title"))

        self._notebook = ttk.Notebook(self._root)
        self._notebook.pack(fill="both", expand=True, padx=6, pady=6)  # le contenu occupe toute la fenêtre
        self._list_tab = ModListTab(self._notebook, list_controller, self._lang, self._bus)
        self._create_tab = CreateModTab(self._notebook, create_controller, self._lang, self._bus)
        self._settings_tab = SettingsTab(self._notebook, settings_controller, self._lang, self._bus)
        self._notebook.add(self._list_tab, text=t("app_data.tabs.mod_list"))
        self._notebook.add(self._create_tab, text=t("app_data.tabs.create_mod"))
        self._notebook.add(self._settings_tab, text=t("app_data.tabs.settings"))
        self._notebook.add(HelpTab(self._notebook, self._lang), text=t("app_data.tabs.help"))
        self._notebook.add(AboutTab(self._notebook, self._lang), text=t("app_data.tabs.about"))
        self._notebook.select(selected_index)

        # Garde-fou : quitter l'onglet de création/modification demande confirmation s'il y a
        # quelque chose à perdre. Un onglet ttk ne peut pas être "refusé" : on y revient.
        self._previous_tab: tk.Misc = self._notebook.nametowidget(self._notebook.select())
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ------------------------------------------------------ changement de langue

    def _on_language_changed(self, **_: object) -> None:
        # On attend la fin du traitement de l'événement en cours (clic dans la liste des langues,
        # qui fait partie de l'onglet qu'on va détruire) avant de reconstruire.
        self._root.after_idle(self._rebuild)

    def _rebuild(self) -> None:
        """Détruit puis recrée les onglets : tous les textes sont relus dans la nouvelle langue."""
        selected_index = self._notebook.index(self._notebook.select())
        for tab in (self._list_tab, self._create_tab, self._settings_tab):
            self._bus.unsubscribe_owner(tab)  # les onglets détruits ne doivent plus recevoir d'événements
        self._notebook.destroy()
        self._build(selected_index)

    # -------------------------------------------------------------- onglets

    def _on_edit_state_changed(self, mod: Mod | None = None, **_: object) -> None:
        if mod is not None:
            self._notebook.select(self._create_tab)

    def _on_tab_changed(self, _event: tk.Event) -> None:
        selected = self._notebook.nametowidget(self._notebook.select())
        if self._previous_tab is self._create_tab and selected is not self._create_tab:
            if not self._create_tab.confirm_leave():
                self._notebook.select(self._create_tab)  # on reste ; l'événement suivant remet _previous_tab
                return
        self._previous_tab = selected
