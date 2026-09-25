"""Grundfarben der dunklen retro-themes, geladen aus dem Snapshot in `data/`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True, slots=True)
class Base:
    """Die elf Grundfarben eines Themes plus das Hell/Dunkel-Kennzeichen, Feldnamen wie in textual-themes."""

    name: str
    primary: str
    secondary: str
    accent: str
    foreground: str
    background: str
    surface: str
    panel: str
    boost: str
    warning: str
    error: str
    success: str
    dark: bool


def load_all() -> list[Base]:
    """Liest alle Themes aus `data/*.json`, alphabetisch nach Name."""
    themes: list[Base] = []
    for entry in resources.files("retro_coding_themes").joinpath("data").iterdir():
        if not entry.name.endswith(".json"):
            continue
        raw = json.loads(entry.read_text(encoding="utf-8"))
        themes.append(Base(name=raw["name"], dark=raw["dark"], **raw["base"]))
    return sorted(themes, key=lambda theme: theme.name)


def load(name: str) -> Base:
    """Liest ein einzelnes Theme.

    Raises:
        KeyError: Wenn es das Theme nicht gibt.
    """
    for theme in load_all():
        if theme.name == name:
            return theme
    raise KeyError(name)
