"""Bande horizontale de miniatures réordonnables. / Horizontal strip of reorderable thumbnails."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from PIL import ImageTk

from app.views.cursors import grab_cursor
from app.views.widgets import ScrollableFrame, VerticalInsertionMarker

THUMB_SIZE = (96, 72)       # taille des miniatures (pixels)
CAPTION_CHARS = 16          # longueur maximale du nom affiché sous une miniature
SELECTED_COLOR = "#1a73e8"  # contour de la miniature sélectionnée / ligne d'insertion
DIM_COLOR = "#e3e7ee"       # fond de la miniature d'origine pendant le glissement
DRAG_THRESHOLD = 6          # pixels à parcourir avant qu'un clic devienne un glisser
AUTOSCROLL_EDGE = 30        # distance au bord (px) où la bande défile pendant un glisser


class ImageStrip(ttk.Frame):
    """Miniatures côte à côte : clic = sélectionner, glisser = réordonner (avec ligne d'insertion).
    Thumbnails side by side: click = select, drag = reorder (with an insertion line).

    Widget "passif" : il ne connaît pas les images. On lui donne (nom, miniature) via `set_items`
    et il prévient quand l'utilisateur déplace une image (`on_move(ancien_index, nouvel_index)`).
    """

    def __init__(self, parent: tk.Misc, on_move: Callable[[int, int], None], empty_text: str) -> None:
        super().__init__(parent)
        self._on_move = on_move
        self._empty_text = empty_text
        self._background = ttk.Style().lookup("TFrame", "background") or "#f0f0f0"
        self._scroll = ScrollableFrame(self, orient="horizontal")
        self._scroll.pack(fill="x")
        self._cells: list[tk.Frame] = []
        self._widgets: list[list[tk.Misc]] = []  # widgets de chaque cellule (pour le fond et le curseur)
        self._photos: list[ImageTk.PhotoImage | None] = []  # références (sinon Tkinter efface les images)
        self.selected: int | None = None
        self._drag_index: int | None = None
        self._drag_start_x = 0
        self._dragging = False
        self._drop_index = 0
        self._last_pointer_x = 0
        self._marker: VerticalInsertionMarker | None = None
        self._autoscroll_job: str | None = None

    # ------------------------------------------------------------------ contenu

    def set_items(self, items: list[tuple[str, ImageTk.PhotoImage | None]], selected: int | None = None) -> None:
        """Remplace les miniatures. / Replace the thumbnails."""
        for child in self._scroll.inner.winfo_children():
            child.destroy()
        self._cells, self._widgets, self._photos = [], [], []
        self.selected = selected if selected is not None and 0 <= selected < len(items) else None

        if not items:
            ttk.Label(self._scroll.inner, text=self._empty_text, foreground="#777777").pack(padx=8, pady=28)
            return
        for index, (name, photo) in enumerate(items):
            cell = tk.Frame(self._scroll.inner, padx=4, pady=4, highlightthickness=2,
                            highlightbackground=self._background, background=self._background)
            cell.pack(side="left", padx=2, pady=2)
            picture = tk.Label(cell, image=photo or "", text="" if photo else "?", width=THUMB_SIZE[0],
                               height=THUMB_SIZE[1], background=self._background, anchor="center")
            picture.pack()
            shown = name if len(name) <= CAPTION_CHARS else name[:CAPTION_CHARS - 1] + "…"
            caption = tk.Label(cell, text=shown, background=self._background, foreground="#555555")
            caption.pack()
            self._cells.append(cell)
            self._widgets.append([cell, picture, caption])
            self._photos.append(photo)
            for widget in (cell, picture, caption):
                widget.configure(cursor=grab_cursor("grab", self))
                widget.bind("<ButtonPress-1>", lambda e, i=index: self._on_press(e, i))
                widget.bind("<B1-Motion>", self._on_motion)
                widget.bind("<ButtonRelease-1>", self._on_release)
        self._paint()

    def _paint(self) -> None:
        """Contour bleu sur la miniature sélectionnée. / Blue outline on the selected thumbnail."""
        for index, cell in enumerate(self._cells):
            cell.configure(highlightbackground=SELECTED_COLOR if index == self.selected else self._background)

    # ------------------------------------------------- sélection / glisser-déposer

    def _on_press(self, event: tk.Event, index: int) -> None:
        self.selected = index
        self._paint()
        self._drag_index = index
        self._drag_start_x = event.x_root
        self._dragging = False

    def _on_motion(self, event: tk.Event) -> None:
        if self._drag_index is None:
            return
        if not self._dragging:
            if abs(event.x_root - self._drag_start_x) < DRAG_THRESHOLD:
                return
            self._begin_drag()
        self._last_pointer_x = event.x_root
        self._update_drag()

    def _begin_drag(self) -> None:
        """Le clic maintenu devient un glisser : miniature d'origine grisée, ligne d'insertion, poing fermé."""
        self._dragging = True
        self._marker = VerticalInsertionMarker(self._scroll.inner, SELECTED_COLOR)
        for widget in self._widgets[self._drag_index]:
            widget.configure(background=DIM_COLOR)
        self._set_cursor(grab_cursor("grabbing", self))

    def _update_drag(self) -> None:
        """Calcule où l'image s'insérera et déplace la ligne. / Compute the drop spot, move the line."""
        inner = self._scroll.inner
        pointer_x = self._last_pointer_x - inner.winfo_rootx()  # x dans la bande (tient compte du défilement)
        others = [i for i in range(len(self._cells)) if i != self._drag_index]
        # Position d'insertion = nombre d'AUTRES miniatures dont le milieu est à gauche du pointeur.
        self._drop_index = sum(1 for i in others
                               if self._cells[i].winfo_x() + self._cells[i].winfo_width() / 2 < pointer_x)
        if self._drop_index < len(others):  # juste à gauche de la miniature qui sera juste après
            x = self._cells[others[self._drop_index]].winfo_x()
        elif others:                        # tout à droite de la bande
            last = self._cells[others[-1]]
            x = last.winfo_x() + last.winfo_width()
        else:
            x = 0
        self._marker.show(x - 2, inner.winfo_height())

        # Près du bord gauche/droit de la zone visible : la bande défile toute seule.
        canvas = self._scroll.canvas
        near_edge = (self._last_pointer_x < canvas.winfo_rootx() + AUTOSCROLL_EDGE
                     or self._last_pointer_x > canvas.winfo_rootx() + canvas.winfo_width() - AUTOSCROLL_EDGE)
        if near_edge and self._autoscroll_job is None:
            self._autoscroll_job = self.after(60, self._autoscroll)

    def _autoscroll(self) -> None:
        self._autoscroll_job = None
        if not self._dragging:
            return
        canvas = self._scroll.canvas
        if self._last_pointer_x < canvas.winfo_rootx() + AUTOSCROLL_EDGE:
            canvas.xview_scroll(-1, "units")
        elif self._last_pointer_x > canvas.winfo_rootx() + canvas.winfo_width() - AUTOSCROLL_EDGE:
            canvas.xview_scroll(1, "units")
        else:
            return
        self._update_drag()  # relance aussi le défilement tant que la souris reste au bord

    def _set_cursor(self, cursor: str) -> None:
        """Curseur de toute la fenêtre pendant le glisser (poing fermé), puis retour à la normale."""
        self.winfo_toplevel().configure(cursor=cursor if self._dragging else "")
        for widgets in self._widgets:
            for widget in widgets:
                widget.configure(cursor=cursor)

    def _on_release(self, _event: tk.Event) -> None:
        dragged, was_dragging = self._drag_index, self._dragging
        if was_dragging:
            if self._marker is not None:
                self._marker.destroy()
                self._marker = None
            if self._autoscroll_job is not None:
                self.after_cancel(self._autoscroll_job)
                self._autoscroll_job = None
            self._dragging = False
            self._set_cursor(grab_cursor("grab", self))
        self._drag_index = None
        self._dragging = False
        if was_dragging and dragged is not None and self._drop_index != dragged:
            self._on_move(dragged, self._drop_index)  # la vue/contrôleur réordonne puis rappelle set_items
        elif was_dragging:
            self._paint_all_normal()

    def _paint_all_normal(self) -> None:
        """Remet les couleurs normales (la miniature n'est plus grisée). / Restore normal colors."""
        for widgets in self._widgets:
            for widget in widgets:
                widget.configure(background=self._background)
