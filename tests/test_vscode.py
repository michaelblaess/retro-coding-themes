"""Prueft die erzeugten VS-Code-Themes am fertigen JSON, so wie VS Code sie liest.

Halbtransparente Farben werden dabei auf ihre Unterlage gemischt, bevor der Kontrast gemessen
wird. Genau das macht auch der Editor.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from retro_coding_themes.color import contrast, luminance, mix
from retro_coding_themes.derive import DIM_TARGET, TEXT_TARGET, derive
from retro_coding_themes.palettes import load, load_all
from retro_coding_themes.vscode.render import LABELS, package_entry, render, write

ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "vscode" / "themes"
HEX = re.compile(r"^#[0-9A-F]{6}([0-9A-F]{2})?$")
BASES = load_all()
IDS = [base.name for base in BASES]

# Schrift auf Flaeche, jeweils mit Mindestkontrast. Die Flaeche kann selbst halbtransparent sein,
# sie liegt dann auf der dritten Angabe.
UI_PAIRS: list[tuple[str, str, str, float]] = [
    ("editor.foreground", "editor.background", "editor.background", TEXT_TARGET),
    ("editor.foreground", "editor.selectionBackground", "editor.background", TEXT_TARGET),
    ("editor.foreground", "editor.findMatchBackground", "editor.background", TEXT_TARGET),
    ("editor.foreground", "editor.lineHighlightBackground", "editor.background", TEXT_TARGET),
    ("editorLineNumber.foreground", "editor.background", "editor.background", DIM_TARGET),
    ("editorLineNumber.activeForeground", "editor.background", "editor.background", TEXT_TARGET),
    ("sideBar.foreground", "sideBar.background", "sideBar.background", TEXT_TARGET),
    ("list.activeSelectionForeground", "list.activeSelectionBackground", "sideBar.background", TEXT_TARGET),
    ("list.highlightForeground", "sideBar.background", "sideBar.background", TEXT_TARGET),
    ("activityBar.foreground", "activityBar.background", "activityBar.background", TEXT_TARGET),
    ("activityBar.inactiveForeground", "activityBar.background", "activityBar.background", DIM_TARGET),
    ("titleBar.activeForeground", "titleBar.activeBackground", "titleBar.activeBackground", TEXT_TARGET),
    ("tab.activeForeground", "tab.activeBackground", "tab.activeBackground", TEXT_TARGET),
    ("tab.inactiveForeground", "tab.inactiveBackground", "tab.inactiveBackground", TEXT_TARGET),
    ("statusBar.foreground", "statusBar.background", "statusBar.background", TEXT_TARGET),
    ("button.foreground", "button.background", "button.background", TEXT_TARGET),
    ("badge.foreground", "badge.background", "badge.background", TEXT_TARGET),
    ("activityBarBadge.foreground", "activityBarBadge.background", "activityBarBadge.background", TEXT_TARGET),
    ("statusBar.debuggingForeground", "statusBar.debuggingBackground", "statusBar.debuggingBackground", TEXT_TARGET),
    ("input.foreground", "input.background", "input.background", TEXT_TARGET),
    ("editorWidget.foreground", "editorWidget.background", "editorWidget.background", TEXT_TARGET),
    ("editorSuggestWidget.highlightForeground", "editorSuggestWidget.background", "editor.background", TEXT_TARGET),
    ("panelTitle.activeForeground", "panel.background", "panel.background", TEXT_TARGET),
    ("terminal.foreground", "terminal.background", "terminal.background", TEXT_TARGET),
    ("breadcrumb.foreground", "breadcrumb.background", "breadcrumb.background", TEXT_TARGET),
]


def _flat(color: str, under: str) -> str:
    """Mischt eine Farbe mit Alphakanal auf ihre Unterlage."""
    if len(color) == 9:
        return mix(under, color[:7], int(color[7:], 16) / 255)
    return color


def _theme(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((THEMES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return result


def test_every_theme_has_a_file_and_a_label() -> None:
    erzeugt = {path.stem for path in THEMES_DIR.glob("*.json")}
    assert erzeugt == set(IDS)
    assert set(LABELS) == set(IDS)


def test_package_json_lists_every_theme() -> None:
    package = json.loads((ROOT / "vscode" / "package.json").read_text(encoding="utf-8"))
    assert package["contributes"]["themes"] == [package_entry(derive(base)) for base in BASES]


def test_labels_of_existing_themes_are_unchanged() -> None:
    # VS Code merkt sich das gewaehlte Theme ueber das Label. Diese 38 gab es in Version 1.0.0.
    frueher = {"brotkasten", "boing", "gemstone", "classic-terminal", "next", "bebox", "bunty", "cupertino"}
    for name in frueher:
        assert render(derive(load(name)))["name"] == f"Retro — {LABELS[name]}"


@pytest.mark.parametrize("name", IDS)
def test_file_matches_generator(name: str) -> None:
    assert _theme(name) == render(derive(load(name)))


@pytest.mark.parametrize("name", IDS)
def test_all_colors_are_hex(name: str) -> None:
    theme = _theme(name)
    for key, value in theme["colors"].items():
        assert HEX.match(value), f"{name}/{key}: {value}"
    for rule in theme["tokenColors"]:
        color = rule["settings"].get("foreground")
        assert color is None or HEX.match(color), f"{name}/{rule['name']}: {color}"


@pytest.mark.parametrize("name", IDS)
def test_ui_pairs_readable(name: str) -> None:
    colors = _theme(name)["colors"]
    for fg_key, bg_key, under_key, target in UI_PAIRS:
        under = colors[under_key]
        surface = _flat(colors[bg_key], under)
        text = _flat(colors[fg_key], surface)
        assert contrast(text, surface) >= target, f"{name}: {fg_key} auf {bg_key} = {contrast(text, surface):.2f}"


@pytest.mark.parametrize("name", IDS)
def test_token_colors_readable(name: str) -> None:
    theme = _theme(name)
    colors = theme["colors"]
    bg = colors["editor.background"]
    surfaces = [bg, _flat(colors["editor.lineHighlightBackground"], bg), colors["peekViewEditor.background"]]
    for rule in theme["tokenColors"]:
        color = rule["settings"].get("foreground")
        if color is None:
            continue
        for surface in surfaces:
            assert contrast(color, surface) >= TEXT_TARGET, f"{name}: {rule['name']} auf {surface}"


@pytest.mark.parametrize("name", IDS)
def test_type_matches_background(name: str) -> None:
    theme = _theme(name)

    hell = luminance(theme["colors"]["editor.background"]) > luminance(theme["colors"]["editor.foreground"])
    assert theme["type"] == ("light" if hell else "dark")


def test_ui_check_can_fail() -> None:
    # Gegenprobe: weisse Schrift auf gelbem Knopf, wie im alten Commandr-Theme, muss auffallen
    assert contrast("#FFFFFF", "#FFFF55") < TEXT_TARGET
    assert _flat("#FF000080", "#000000") != "#FF0000"


def test_written_file_matches_render(tmp_path: Path) -> None:
    scheme = derive(load("boing"))
    path = write(scheme, tmp_path)
    assert path.name == "boing.json"
    assert json.loads(path.read_text(encoding="utf-8")) == render(scheme)
