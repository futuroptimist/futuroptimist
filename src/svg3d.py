"""Utility to draw isometric bars with svgwrite."""

from __future__ import annotations


import svgwrite as sw

CELL = 12
DEPTH = 4


def _clamp(val: int) -> int:
    """Clamp RGB component to the valid 0-255 range."""

    return max(0, min(255, val))


def _shade(color: str, factor: float) -> str:
    c = int(color.lstrip("#"), 16)
    r = (c >> 16) & 0xFF
    g = (c >> 8) & 0xFF
    b = c & 0xFF
    r = _clamp(int(r * factor))
    g = _clamp(int(g * factor))
    b = _clamp(int(b * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_bar(dwg: sw.Drawing, x: float, y: float, height: float, color: str) -> None:
    """Draw a pseudo-3-D bar at grid position."""
    top = [
        (x, y - height),
        (x + CELL, y - height),
        (x + CELL + DEPTH, y - height - DEPTH),
        (x + DEPTH, y - height - DEPTH),
    ]
    right = [
        (x + CELL, y),
        (x + CELL + DEPTH, y - DEPTH),
        (x + CELL + DEPTH, y - height - DEPTH),
        (x + CELL, y - height),
    ]
    left = [
        (x, y),
        (x + DEPTH, y - DEPTH),
        (x + DEPTH, y - height - DEPTH),
        (x, y - height),
    ]
    dwg.add(dwg.polygon(top, fill=_shade(color, 1.1)))
    dwg.add(dwg.polygon(right, fill=_shade(color, 0.9)))
    dwg.add(dwg.polygon(left, fill=color))
