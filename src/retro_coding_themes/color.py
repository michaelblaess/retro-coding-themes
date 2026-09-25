"""Farbrechnung ohne Abhaengigkeiten: Kontrast nach WCAG, Farbabstand in CIE-Lab, Helligkeit.

Urspruenglich aus web-themes uebernommen, ergaenzt um mix, Farbton und Saettigung.

Alle Funktionen sind rein und arbeiten mit Hexwerten der Form `#RRGGBB`.
"""

from __future__ import annotations

import colorsys
import math
import re
from collections.abc import Sequence

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SCHRITT = 0.01
_MAX_SCHRITTE = 100


def _rgb(hex_value: str) -> tuple[float, float, float]:
    if not _HEX.match(hex_value):
        raise ValueError(f"Kein Hexwert der Form #RRGGBB: {hex_value!r}")
    return (int(hex_value[1:3], 16) / 255, int(hex_value[3:5], 16) / 255, int(hex_value[5:7], 16) / 255)


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in rgb)


def _linear(channel: float, threshold: float) -> float:
    return channel / 12.92 if channel <= threshold else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_value: str) -> float:
    """Relative Leuchtdichte nach WCAG 2.x.

    Args:
        hex_value: Farbe als `#RRGGBB`.

    Returns:
        Wert zwischen 0 (schwarz) und 1 (weiss).
    """
    r, g, b = (_linear(c, 0.03928) for c in _rgb(hex_value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """Kontrastverhaeltnis zweier Farben nach WCAG, unabhaengig von der Reihenfolge.

    Returns:
        Wert zwischen 1 und 21.
    """
    hell, dunkel = sorted((luminance(a), luminance(b)), reverse=True)
    return (hell + 0.05) / (dunkel + 0.05)


def _lab(hex_value: str) -> tuple[float, float, float]:
    r, g, b = (_linear(c, 0.04045) for c in _rgb(hex_value))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


def delta_e(a: str, b: str) -> float:
    """Farbabstand CIE76 im Lab-Raum. Unter etwa 2,3 sieht das Auge keinen Unterschied."""
    return math.dist(_lab(a), _lab(b))


def mix(a: str, b: str, amount: float) -> str:
    """Mischt zwei Farben im sRGB-Raum.

    Args:
        a: Ausgangsfarbe.
        b: Zielfarbe.
        amount: 0 ergibt a, 1 ergibt b.
    """
    t = max(0.0, min(1.0, amount))
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return _hex((ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t))


def with_hue_shift(hex_value: str, degrees: float) -> str:
    """Dreht den Farbton um die angegebenen Grad, Helligkeit und Saettigung bleiben."""
    hue, hell, sat = colorsys.rgb_to_hls(*_rgb(hex_value))
    return _hex(colorsys.hls_to_rgb((hue + degrees / 360) % 1.0, hell, sat))


def lightness(hex_value: str) -> float:
    """HLS-Helligkeit einer Farbe, Gegenstueck zu `with_lightness`."""
    return colorsys.rgb_to_hls(*_rgb(hex_value))[1]


def hue(hex_value: str) -> float:
    """HLS-Farbton einer Farbe in Grad, 0 ist Rot."""
    return colorsys.rgb_to_hls(*_rgb(hex_value))[0] * 360


def saturation(hex_value: str) -> float:
    """HLS-Saettigung einer Farbe, 0 fuer Grau."""
    return colorsys.rgb_to_hls(*_rgb(hex_value))[2]


def with_lightness(hex_value: str, lightness: float) -> str:
    """Setzt die HLS-Helligkeit und behaelt Farbton und Saettigung."""
    h, _, s = colorsys.rgb_to_hls(*_rgb(hex_value))
    return _hex(colorsys.hls_to_rgb(h, max(0.0, min(1.0, lightness)), s))


def readable_on_all(color: str, surfaces: Sequence[str], target: float) -> str:
    """Hebt eine Schriftfarbe, bis sie auf jeder Flaeche das Ziel erreicht.

    Die Helligkeit wandert von den Flaechen weg: auf hellen Flaechen dunkler, auf
    dunklen heller. Farbton und Saettigung bleiben.

    Args:
        color: Die gewuenschte Schriftfarbe.
        surfaces: Alle Flaechen, auf denen sie stehen kann. Die erste bestimmt die Richtung.
        target: Mindestkontrast auf jeder Flaeche.

    Returns:
        Die angepasste Farbe, oder die urspruengliche, wenn sie das Ziel schon erreicht.

    Raises:
        ValueError: Wenn das Ziel auch am Rand der Helligkeit nicht erreichbar ist.
    """
    if not surfaces:
        raise ValueError("Mindestens eine Flaeche noetig")
    nach_unten = luminance(surfaces[0]) > 0.4
    _, hell, _ = colorsys.rgb_to_hls(*_rgb(color))
    kandidat = color.upper()
    for _ in range(_MAX_SCHRITTE + 1):
        if min(contrast(kandidat, s) for s in surfaces) >= target:
            return kandidat
        hell += -_SCHRITT if nach_unten else _SCHRITT
        kandidat = with_lightness(color, hell)
    raise ValueError(f"{color} erreicht {target}:1 nicht auf {list(surfaces)}")


def fill_for_text(color: str, text: str, target: float) -> str | None:
    """Passt eine Flaechenfarbe an, bis die gegebene Schrift darauf das Ziel erreicht.

    Dunkle Schrift braucht eine hellere Flaeche, helle Schrift eine dunklere.

    Returns:
        Die angepasste Flaeche, oder None, wenn das Ziel mit dieser Schrift nicht erreichbar ist.
    """
    nach_oben = luminance(text) < 0.5
    _, hell, _ = colorsys.rgb_to_hls(*_rgb(color))
    kandidat = color.upper()
    for _ in range(_MAX_SCHRITTE + 1):
        if contrast(text, kandidat) >= target:
            return kandidat
        hell += _SCHRITT if nach_oben else -_SCHRITT
        kandidat = with_lightness(color, hell)
    return None
