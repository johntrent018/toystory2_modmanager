"""Icône (logo) carrée d'un mod. / Square mod icon (logo)."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

from app.models.errors import ModError

LOGO_SIZE = 256            # côté de l'icône enregistrée (pixels)
LOGO_NAME = "_logo.png"    # nom de l'icône dans images/


def load_image(path: Path) -> Image.Image:
    """Ouvre une image en respectant son orientation EXIF. / Open an image honouring EXIF rotation.

    Raises:
        ModError: fichier illisible ou format non géré.
    """
    try:
        with Image.open(path) as image:
            image.load()
            return ImageOps.exif_transpose(image)
    except (OSError, ValueError, Image.DecompressionBombError) as err:
        raise ModError("errors.image_unreadable", file=path.name) from err


def fit_square_box(width: int, height: int, center_x: float, center_y: float, size: float) -> tuple[int, int, int, int]:
    """Carré (gauche, haut, droite, bas) de côté `size`, centré au plus près de (center_x, center_y)
    mais toujours entièrement DANS l'image. / Square box kept fully inside the image.
    """
    size = max(1, min(int(round(size)), width, height))
    left = int(round(min(max(center_x - size / 2, 0), width - size)))
    top = int(round(min(max(center_y - size / 2, 0), height - size)))
    return left, top, left + size, top + size


def build_logo_png(path: Path, box: tuple[int, int, int, int]) -> bytes:
    """Découpe `box` dans l'image et renvoie un PNG carré LOGO_SIZE x LOGO_SIZE.
    Crop `box` out of the image and return a square LOGO_SIZE x LOGO_SIZE PNG.

    Raises:
        ModError: image illisible.
    """
    image = load_image(path)
    left, top, right, bottom = box
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ModError("errors.image_unreadable", file=path.name)
    cropped = image.crop(box).convert("RGBA").resize((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG")
    return buffer.getvalue()
