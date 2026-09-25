"""Prueft Schreiber, Leser und Paket - gegen den Microsoft-Compiler und gegen sich selbst."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from retro_coding_themes.__main__ import VISUALSTUDIO_PKGDEF as PKGDEF_PATH
from retro_coding_themes.color import contrast, delta_e
from retro_coding_themes.derive import DIM_TARGET, TEXT_TARGET, Scheme, derive
from retro_coding_themes.palettes import load, load_all
from retro_coding_themes.visualstudio.pkgdef import block, data_zeilen, lies_block, render, render_all
from retro_coding_themes.visualstudio.render import (
    LABELS,
    TEXT_MANAGER,
    Farbe,
    chrome,
    environment,
    kategorien,
    theme_guid,
)
from retro_coding_themes.visualstudio.vsix import PKGDEF, build

REFERENZ = Path(__file__).parent / "referenz"
SCHEMES = [derive(base) for base in load_all()]
IDS = [scheme.name for scheme in SCHEMES]


@pytest.mark.parametrize("name", ["synthwave", "classic-terminal", "clipper"])
def test_writer_matches_microsoft_compiler(name: str) -> None:
    # Die Referenzen hat der VsixColorCompiler aus VS 2022 am 25.09.2026 erzeugt. Ihre Eintraege
    # werden gelesen und mit dem eigenen Schreiber neu geschrieben. So prueft der Test den
    # Schreiber, unabhaengig davon, welche Farben die Themes inzwischen haben.
    referenz = data_zeilen((REFERENZ / f"retro-{name}.pkgdef").read_text(encoding="utf-8"))
    assert len(referenz) == 5
    for schluessel, daten in referenz.items():
        kategorien_im_block = lies_block(daten)
        assert len(kategorien_im_block) == 1, schluessel
        ((guid, eintraege),) = kategorien_im_block.items()
        neu = block(guid, {e.name: (e.hintergrund, e.vordergrund) for e in eintraege})
        assert neu == daten, schluessel


def test_comparison_can_fail() -> None:
    # Gegenprobe: eine einzige andere Farbe muss den Block veraendern
    scheme = derive(load("synthwave"))
    eintraege: dict[str, Farbe] = {"Keyword": (None, scheme.keyword)}
    anders: dict[str, Farbe] = {"Keyword": (None, "#000001")}
    assert block(TEXT_MANAGER, eintraege) != block(TEXT_MANAGER, anders)


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_roundtrip(scheme: Scheme) -> None:
    gelesen: dict[str, dict[str, Farbe]] = {}
    for daten in data_zeilen(render(scheme)).values():
        for guid, eintraege in lies_block(daten).items():
            gelesen.setdefault(guid, {}).update({e.name: (e.hintergrund, e.vordergrund) for e in eintraege})
    erwartet: dict[str, dict[str, Farbe]] = {}
    for kategorie in kategorien(scheme):
        erwartet.setdefault(kategorie.guid, {}).update(kategorie.eintraege)
    gross = {g: {n: (b and b.upper(), f and f.upper()) for n, (b, f) in e.items()} for g, e in erwartet.items()}
    assert gelesen == gross


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_editor_readable(scheme: Scheme) -> None:
    editor = {k.name: k.eintraege for k in kategorien(scheme)}["Text Editor Text Manager Items"]
    bg, fg = editor["Plain Text"]
    assert bg is not None and fg is not None
    auswahl = editor["Selected Text"][0]
    assert auswahl is not None
    assert contrast(fg, bg) >= TEXT_TARGET
    assert contrast(fg, auswahl) >= TEXT_TARGET, "Text auf Auswahl"
    zeilennummer = editor["Line Number"][1]
    assert zeilennummer is not None
    assert contrast(zeilennummer, bg) >= DIM_TARGET


def test_every_theme_has_label_and_unique_guid() -> None:
    assert set(LABELS) == set(IDS)
    assert len({theme_guid(name) for name in IDS}) == len(IDS)


def test_committed_pkgdef_matches_generator() -> None:
    assert PKGDEF_PATH.read_bytes() == render_all(SCHEMES).encode("utf-8")


def test_vsix_has_valid_v3_layout(tmp_path: Path) -> None:
    ziel = build(render_all(SCHEMES[:2]), "Lizenz", "0.0.1", tmp_path / "probe.vsix")
    with zipfile.ZipFile(ziel) as zf:
        namen = set(zf.namelist())
        assert {"[Content_Types].xml", "extension.vsixmanifest", "manifest.json", "catalog.json", PKGDEF} <= namen
        manifest = json.loads(zf.read("manifest.json"))
        for eintrag in manifest["files"]:
            inhalt = zf.read(eintrag["fileName"].lstrip("/"))
            assert hashlib.sha256(inhalt).hexdigest().upper() == eintrag["sha256"]
        # Jede Datei ohne Endung braucht einen eigenen Eintrag, sonst ist das Paket ungueltig
        typen = zf.read("[Content_Types].xml").decode("utf-8")
        for name in namen - {"[Content_Types].xml"}:
            if "." not in name:
                assert f'PartName="/{name}"' in typen, name


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_menu_text_readable_on_environment(scheme: Scheme) -> None:
    # Die Schrift in Titelleiste und Menue erbt VS 2026 vom Basis-Theme. Gerechnet wird mit Weiss
    # bzw. Fast-Schwarz. Mit 45 % Leitfarbe fiel BeBox auf 3,9:1.
    text = "#FFFFFF" if scheme.dark else "#1B1B1B"
    assert contrast(text, environment(scheme)) >= TEXT_TARGET


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_tool_windows_differ_from_editor(scheme: Scheme) -> None:
    # Projektmappen-Explorer und Editor muessen sich sichtbar unterscheiden
    assert delta_e(chrome(scheme), scheme.bg) >= 3.0
    assert contrast(scheme.fg, chrome(scheme)) >= TEXT_TARGET
