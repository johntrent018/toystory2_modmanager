"""Système Observer/pubsub minimal. / Minimal Observer/pubsub system."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class Events:
    """Noms des événements publiés. / Names of published events."""

    MODS_CHANGED = "mods_changed"            # la liste des mods a changé (création, rafraîchissement)
    MOD_STATE_CHANGED = "mod_state_changed"  # un mod a été activé ou désactivé
    GAME_PATH_CHANGED = "game_path_changed"  # le dossier du jeu a été modifié
    MOD_DELETED = "mod_deleted"              # un mod a été supprimé (payload : mod_id)
    LANGUAGE_CHANGED = "language_changed"    # la langue (interface + défaut des nouveaux mods) a changé
    EDIT_MOD_REQUESTED = "edit_mod_requested"  # la liste demande à modifier un mod (payload : mod)
    EDIT_STATE_CHANGED = "edit_state_changed"  # le formulaire entre/sort du mode modification (payload : mod ou None)


class EventBus:
    """Abonnement et publication d'événements. / Event subscription and publishing."""

    def __init__(self) -> None:
        # événement → liste de (callback, propriétaire)
        self._subscribers: dict[str, list[tuple[Callable[..., None], object]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[..., None], owner: object = None) -> None:
        """S'abonne à un événement. / Subscribe to an event.

        Le callback reçoit les données de l'événement en arguments nommés ;
        il doit donc accepter `**kwargs` (ex. `def on_x(self, **_)`).
        `owner` permet de désabonner d'un coup tous les callbacks d'un objet (ex. un onglet
        détruit lors d'un changement de langue) : voir `unsubscribe_owner`.
        """
        self._subscribers[event].append((callback, owner))

    def unsubscribe_owner(self, owner: object) -> None:
        """Retire tous les abonnements d'un propriétaire. / Remove all of an owner's subscriptions."""
        for event in self._subscribers:
            self._subscribers[event] = [(cb, o) for cb, o in self._subscribers[event] if o is not owner]

    def publish(self, event: str, **payload: Any) -> None:
        """Notifie tous les abonnés. / Notify all subscribers."""
        for callback, _owner in list(self._subscribers[event]):
            callback(**payload)
