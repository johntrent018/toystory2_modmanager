"""Widgets Tkinter réutilisables. / Reusable Tkinter widgets."""
from __future__ import annotations

import tkinter as tk
import weakref
from tkinter import ttk
from typing import Callable

from app.views.icons import make_icon


class ScrollableFrame(ttk.Frame):
    """Zone défilante verticale ou horizontale. / Vertical or horizontal scrollable area.

    Placer les widgets dans `.inner`. Tkinter n'a pas de frame défilante native :
    on utilise donc le montage classique Canvas + Frame + Scrollbar.
    Le défilement n'est possible que si le contenu dépasse réellement de la zone visible.
    """

    _instances: "weakref.WeakSet[ScrollableFrame]" = weakref.WeakSet()  # zones vivantes (molette)
    _wheel_bound = False

    def __init__(self, parent: tk.Misc, orient: str = "vertical", height: int | None = None) -> None:
        super().__init__(parent)
        self._vertical = orient == "vertical"

        # Le Canvas doit avoir la même couleur de fond que le thème ttk, sinon il se voit.
        background = ttk.Style().lookup("TFrame", "background") or "#f0f0f0"
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=background)
        if height is not None:  # hauteur initiale souhaitée (verticale uniquement)
            self.canvas.configure(height=height)
        self.inner = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        if self._vertical:
            scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)
        else:
            scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=scrollbar.set)
            scrollbar.pack(side="bottom", fill="x")
            self.canvas.pack(side="top", fill="both", expand=True)

        self.inner.bind("<Configure>", self._on_resized)
        self.canvas.bind("<Configure>", self._on_canvas_resized)

        # Molette : UNE seule liaison globale pour toutes les zones défilantes (Windows/macOS
        # envoient <MouseWheel>, Linux envoie Button-4/5). Elle retrouve la zone sous la souris.
        ScrollableFrame._instances.add(self)
        if not ScrollableFrame._wheel_bound:
            for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.bind_all(sequence, ScrollableFrame._dispatch_wheel, add="+")
            ScrollableFrame._wheel_bound = True

    # ---------------------------------------------------------------- taille

    def _overflows(self) -> bool:
        """Le contenu est-il plus grand que la zone visible ? / Is the content larger than the view?"""
        if self._vertical:
            return self.inner.winfo_reqheight() > self.canvas.winfo_height()
        return self.inner.winfo_reqwidth() > self.canvas.winfo_width()

    def _update_scrollregion(self) -> None:
        """Zone défilable = le contenu, mais JAMAIS plus petite que la zone visible.
        Scroll region = the content, but never smaller than the visible area.

        Sans cela, avec peu de contenu, Tk laisse tout de même "tirer" le contenu dans le vide.
        """
        width = max(self.inner.winfo_reqwidth(), self.canvas.winfo_width())
        height = max(self.inner.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, width, height))
        if not self._overflows():  # rien à faire défiler : on remet le contenu en haut / à gauche
            self.canvas.yview_moveto(0)
            self.canvas.xview_moveto(0)

    def _on_resized(self, _event: tk.Event) -> None:
        """Le contenu a changé de taille. / The content changed size."""
        if not self._vertical:
            # En horizontal, le canvas prend la hauteur de son contenu.
            self.canvas.configure(height=self.inner.winfo_reqheight())
        self._update_scrollregion()

    def _on_canvas_resized(self, event: tk.Event) -> None:
        """La zone visible a changé de taille. / The visible area changed size."""
        if self._vertical:  # le contenu occupe toute la largeur disponible
            self.canvas.itemconfigure(self._window_id, width=event.width)
        self._update_scrollregion()

    # ---------------------------------------------------------------- molette

    @staticmethod
    def _dispatch_wheel(event: tk.Event) -> None:
        """Envoie la molette à la zone défilante sous la souris (la plus proche).

        `event.widget` n'est pas toujours un widget : pour certains popups (liste d'une Combobox)
        Tkinter fournit juste un nom (str). On s'appuie donc sur une zone défilante vivante.
        """
        anchor = next((frame for frame in list(ScrollableFrame._instances) if frame.winfo_exists()), None)
        if anchor is None:
            return
        try:
            widget = anchor.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):  # bug connu de Tkinter avec les popups de Combobox
            return
        while widget is not None:
            if isinstance(widget, ScrollableFrame):
                widget._scroll(event)
                return
            widget = getattr(widget, "master", None)

    def _scroll(self, event: tk.Event) -> None:
        if not self._overflows():
            return  # contenu plus petit que la zone : pas de défilement
        if event.num == 4:
            step = -1
        elif event.num == 5:
            step = 1
        else:
            step = -1 if event.delta > 0 else 1
        if self._vertical:
            self.canvas.yview_scroll(step, "units")
        else:
            self.canvas.xview_scroll(step * 3, "units")


class Tooltip:
    """Infobulle affichée après un court survol. / Tooltip shown after a short hover."""

    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 400) -> None:
        self._widget = widget
        self._text = text
        self._delay = delay_ms
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        for sequence in ("<Leave>", "<ButtonPress>", "<Destroy>"):
            widget.bind(sequence, self._hide, add="+")

    def _schedule(self, _event: tk.Event) -> None:
        self._hide()
        self._after_id = self._widget.after(self._delay, self._show)

    def _show(self) -> None:
        try:
            x = self._widget.winfo_rootx() + 8
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            self._window = tk.Toplevel(self._widget)
            self._window.wm_overrideredirect(True)  # pas de barre de titre
            self._window.wm_geometry(f"+{x}+{y}")
            tk.Label(self._window, text=self._text, background="#ffffe0", relief="solid",
                     borderwidth=1, padx=5, pady=2).pack()
        except tk.TclError:  # le widget a été détruit entre-temps
            self._window = None

    def _hide(self, _event: tk.Event | None = None) -> None:
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        if self._window is not None:
            self._window.destroy()
            self._window = None


class IconButton(tk.Label):
    """Bouton-icône cliquable avec infobulle : `color` au repos, `hover_color` au survol.
    Clickable icon button with tooltip: `color` at rest, `hover_color` on hover.

    C'est un tk.Label (et non un ttk.Button) : on peut le placer n'importe où, y compris
    dans des lignes de liste, et lui donner la couleur de fond de la ligne via `background`.
    """

    def __init__(
        self,
        parent: tk.Misc,
        icon: str,
        command: Callable[[], None],
        tooltip: str | None = None,
        color: str = "#555555",
        hover_color: str = "#1a5fb4",
        size: int = 18,
        background: str | None = None,
    ) -> None:
        self._normal_image = make_icon(icon, color, size)
        self._hover_image = make_icon(icon, hover_color, size)
        super().__init__(parent, image=self._normal_image, cursor="hand2", borderwidth=0, padx=3, pady=3,
                         background=background or ttk.Style().lookup("TFrame", "background") or "#f0f0f0")
        self._command = command
        self.bind("<Enter>", lambda _e: self.configure(image=self._hover_image))
        self.bind("<Leave>", lambda _e: self.configure(image=self._normal_image))
        self.bind("<Button-1>", lambda _e: self._command())
        if tooltip:
            Tooltip(self, tooltip)


class Avatar(tk.Canvas):
    """Icône carrée d'un mod ; sans icône : carré gris avec l'initiale du mod.
    Square mod icon; without one: a gray square with the mod's initial.
    """

    def __init__(self, parent: tk.Misc, size: int, background: str) -> None:
        super().__init__(parent, width=size, height=size, highlightthickness=0, borderwidth=0,
                         background=background)
        self._size = size
        self._photo = None  # référence obligatoire, sinon l'image disparaît

    def show(self, logo_bytes: bytes | None, name: str) -> None:
        """Affiche l'icône (octets d'une image) ou l'initiale du nom. / Show the icon or the initial."""
        self.delete("all")
        self._photo = None
        if logo_bytes:
            try:
                from app.views.image_viewer import load_photo  # import local : évite un import circulaire
                self._photo = load_photo(logo_bytes, (self._size, self._size))
                self.create_image(self._size // 2, self._size // 2, image=self._photo)
                return
            except Exception:  # icône illisible : on retombe sur l'initiale
                self._photo = None
        self.create_rectangle(0, 0, self._size, self._size, fill="#c9ced6", outline="")
        self.create_text(self._size // 2, self._size // 2, text=(name[:1] or "?").upper(), fill="#ffffff",
                         font=("TkDefaultFont", max(8, self._size // 2), "bold"))


class GripHandle(tk.Canvas):
    """Poignée « 6 points » (2 colonnes x 3 lignes) indiquant qu'un élément se glisse.
    "6-dot grip" handle showing that an item can be dragged.
    """

    def __init__(self, parent: tk.Misc, background: str, color: str = "#8f98a3") -> None:
        super().__init__(parent, width=14, height=28, highlightthickness=0, borderwidth=0, background=background)
        for column in (3, 9):
            for row in (5, 12, 19):
                self.create_oval(column, row, column + 4, row + 4, fill=color, outline="")


class InsertionMarker:
    """Ligne d'insertion épaisse avec deux embouts, façon « |━━━━━━━| ».
    Thick insertion line with two end caps.

    Ce sont trois petits cadres colorés posés avec `place` : très légers à déplacer, ce qui
    évite les traînées d'affichage qu'on aurait en déplaçant un gros élément.
    """

    def __init__(self, parent: tk.Misc, color: str) -> None:
        self._line = tk.Frame(parent, background=color)
        self._left_cap = tk.Frame(parent, background=color)
        self._right_cap = tk.Frame(parent, background=color)
        self._last_y: int | None = None

    def show(self, y: int) -> None:
        """Place la ligne à la hauteur `y` (en pixels dans le parent). / Move the line to height y."""
        if y == self._last_y:  # rien n'a bougé : on évite de redessiner
            return
        self._last_y = y
        self._line.place(x=6, y=y - 2, relwidth=1, width=-12, height=4)
        self._left_cap.place(x=2, y=y - 6, width=4, height=12)
        self._right_cap.place(relx=1, x=-6, y=y - 6, width=4, height=12)
        for part in (self._line, self._left_cap, self._right_cap):
            part.lift()

    def destroy(self) -> None:
        for part in (self._line, self._left_cap, self._right_cap):
            part.destroy()


class SquareButton(tk.Frame):
    """Bouton à icône, TOUJOURS carré et de taille fixe, avec l'icône centrée.
    Icon button that is always square and fixed-size, with the icon centered.

    Un ttk.Button prend la taille que lui donne son conteneur : il peut donc s'étirer quand la
    fenêtre grandit. Ici, un cadre de taille imposée enferme le bouton, qui le remplit exactement.
    """

    def __init__(self, parent: tk.Misc, icon: str, command: Callable[[], None], tooltip: str | None = None,
                 size: int = 36, icon_size: int = 20, color: str = "#333333") -> None:
        super().__init__(parent, width=size, height=size)
        self.pack_propagate(False)  # le cadre garde sa taille, quel que soit son contenu
        self._icon = make_icon(icon, color, icon_size)
        button = ttk.Button(self, image=self._icon, command=command)
        button.pack(fill="both", expand=True)
        if tooltip:
            Tooltip(button, tooltip)


class VerticalInsertionMarker:
    """Ligne d'insertion verticale épaisse avec deux embouts (haut et bas), pour une liste HORIZONTALE.
    Thick vertical insertion line with two caps, for a HORIZONTAL list.
    """

    def __init__(self, parent: tk.Misc, color: str) -> None:
        self._line = tk.Frame(parent, background=color)
        self._top_cap = tk.Frame(parent, background=color)
        self._bottom_cap = tk.Frame(parent, background=color)
        self._last: tuple[int, int] | None = None

    def show(self, x: int, height: int) -> None:
        """Place la ligne à l'abscisse `x` (pixels dans le parent), sur toute la hauteur `height`."""
        if (x, height) == self._last:  # rien n'a bougé : on évite de redessiner
            return
        self._last = (x, height)
        self._line.place(x=x - 2, y=5, width=4, height=max(4, height - 10))
        self._top_cap.place(x=x - 6, y=1, width=12, height=4)
        self._bottom_cap.place(x=x - 6, y=height - 5, width=12, height=4)
        for part in (self._line, self._top_cap, self._bottom_cap):
            part.lift()

    def destroy(self) -> None:
        for part in (self._line, self._top_cap, self._bottom_cap):
            part.destroy()
