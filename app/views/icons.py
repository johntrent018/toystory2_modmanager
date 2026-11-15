"""Icônes dessinées avec Pillow (aucun fichier image à embarquer). / Icons drawn with Pillow.

Chaque icône est dessinée sur une grille de 24x24 puis agrandie x8 et réduite
(anti-crénelage), ce qui donne des icônes nettes à n'importe quelle taille et dans
n'importe quelle couleur. Pour ajouter une icône : écrire une fonction `_draw_xxx`
et l'inscrire dans DRAWERS.
"""
from __future__ import annotations

import math
from typing import Callable

from PIL import Image, ImageDraw, ImageTk

_SUPERSAMPLING = 8  # dessin x8 puis réduction = bords lissés


def _draw_refresh(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Flèche circulaire qui tourne dans le sens des aiguilles d'une montre. / Clockwise arrow."""
    cx = cy = 12 * u
    radius = 7.5 * u
    # Arc ouvert côté droit : de 20° à 320° (angles Pillow : 0° = 3 h, sens horaire).
    draw.arc([cx - radius, cy - radius, cx + radius, cy + radius], start=20, end=320,
             fill=color, width=round(2.4 * u))
    # Pointe de flèche à l'extrémité de l'arc, orientée dans le sens horaire.
    angle = math.radians(320)
    end = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
    tangent = (-math.sin(angle), math.cos(angle))   # direction de rotation horaire
    normal = (math.cos(angle), math.sin(angle))     # direction radiale
    tip = (end[0] + tangent[0] * 4.2 * u, end[1] + tangent[1] * 4.2 * u)
    base = (end[0] - tangent[0] * 0.8 * u, end[1] - tangent[1] * 0.8 * u)
    wing = 4.2 * u
    draw.polygon([tip,
                  (base[0] + normal[0] * wing, base[1] + normal[1] * wing),
                  (base[0] - normal[0] * wing, base[1] - normal[1] * wing)], fill=color)


def _draw_pencil(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Crayon incliné (modifier). / Tilted pencil (edit)."""
    def pts(*points: tuple[float, float]) -> list[tuple[float, float]]:
        return [(x * u, y * u) for x, y in points]

    draw.polygon(pts((16.5, 3.5), (20.5, 7.5), (9, 19), (5, 15)), fill=color)   # corps
    draw.polygon(pts((4.2, 15.8), (8.2, 19.8), (3, 21)), fill=color)            # mine
    draw.line(pts((14.2, 5.8), (18.2, 9.8)), fill=(0, 0, 0, 0), width=round(1.1 * u))  # bague de la gomme


def _draw_trash(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Poubelle (supprimer). / Trash can (delete)."""
    def box(x0: float, y0: float, x1: float, y1: float) -> list[float]:
        return [x0 * u, y0 * u, x1 * u, y1 * u]

    draw.rounded_rectangle(box(8.5, 3, 15.5, 5.5), radius=0.8 * u, fill=color)       # poignée
    draw.rounded_rectangle(box(3.5, 5.5, 20.5, 7.8), radius=0.8 * u, fill=color)     # couvercle
    draw.polygon([(5.8 * u, 8.6 * u), (18.2 * u, 8.6 * u), (17.2 * u, 21 * u), (6.8 * u, 21 * u)], fill=color)  # corps
    for x in (9.6, 12, 14.4):                                                         # fentes
        draw.line([(x * u, 11.5 * u), (x * u, 18 * u)], fill=(0, 0, 0, 0), width=round(1.2 * u))


def _draw_warning(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Panneau triangulaire avec point d'exclamation. / Triangular warning sign with exclamation mark."""
    draw.polygon([(12 * u, 2.2 * u), (22.6 * u, 20.6 * u), (1.4 * u, 20.6 * u)], fill=color)
    draw.line([(12 * u, 2.2 * u), (22.6 * u, 20.6 * u), (1.4 * u, 20.6 * u), (12 * u, 2.2 * u)],
              fill=color, width=round(1.6 * u), joint="curve")  # coins arrondis
    clear = (0, 0, 0, 0)
    draw.rounded_rectangle([10.9 * u, 8 * u, 13.1 * u, 14.6 * u], radius=1.1 * u, fill=clear)  # barre
    draw.ellipse([10.8 * u, 16 * u, 13.2 * u, 18.4 * u], fill=clear)                           # point


def _round_line(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], width: float, color: str) -> None:
    """Ligne épaisse aux extrémités arrondies. / Thick line with rounded ends."""
    draw.line(points, fill=color, width=round(width))
    for x, y in (points[0], points[-1]):
        draw.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=color)


def _draw_arrow_up(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Vraie flèche vers le haut : une tige et une pointe en « V ». / Real up arrow: shaft + chevron head."""
    width = 2.8 * u
    _round_line(draw, [(12 * u, 20 * u), (12 * u, 5 * u)], width, color)                       # tige
    _round_line(draw, [(5.5 * u, 11.5 * u), (12 * u, 5 * u), (18.5 * u, 11.5 * u)], width, color)  # pointe


def _draw_arrow_down(draw: ImageDraw.ImageDraw, u: float, color: str) -> None:
    """Vraie flèche vers le bas. / Real down arrow."""
    width = 2.8 * u
    _round_line(draw, [(12 * u, 4 * u), (12 * u, 19 * u)], width, color)
    _round_line(draw, [(5.5 * u, 12.5 * u), (12 * u, 19 * u), (18.5 * u, 12.5 * u)], width, color)


DRAWERS: dict[str, Callable[[ImageDraw.ImageDraw, float, str], None]] = {
    "refresh": _draw_refresh,
    "pencil": _draw_pencil,
    "trash": _draw_trash,
    "warning": _draw_warning,
    "arrow_up": _draw_arrow_up,
    "arrow_down": _draw_arrow_down,
}


def render_icon(name: str, color: str, size: int = 18) -> Image.Image:
    """Image Pillow (RGBA) d'une icône. / Pillow (RGBA) image of an icon."""
    big = size * _SUPERSAMPLING
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    DRAWERS[name](ImageDraw.Draw(image), big / 24, color)
    return image.resize((size, size), Image.Resampling.LANCZOS)


_cache: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}


def make_icon(name: str, color: str, size: int = 18) -> ImageTk.PhotoImage:
    """Icône prête pour Tkinter (mise en cache). / Tkinter-ready icon (cached)."""
    key = (name, color, size)
    if key not in _cache:
        _cache[key] = ImageTk.PhotoImage(render_icon(name, color, size))
    return _cache[key]
