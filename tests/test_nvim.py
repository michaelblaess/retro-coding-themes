"""Prueft die erzeugten Lua-Dateien - Form und, wenn Neovim da ist, das Laden."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from retro_coding_themes.derive import derive
from retro_coding_themes.nvim.groups import build
from retro_coding_themes.nvim.render import render, write
from retro_coding_themes.palettes import load, load_all

COLORS_DIR = Path(__file__).resolve().parents[1] / "colors"
HEX = re.compile(r"^#[0-9A-F]{6}$")


def test_every_theme_has_a_file() -> None:
    erzeugt = {path.stem for path in COLORS_DIR.glob("retro-*.lua")}
    erwartet = {f"retro-{base.name}" for base in load_all()}
    assert erwartet <= erzeugt, f"fehlen: {sorted(erwartet - erzeugt)}"


def test_all_colors_are_hex() -> None:
    for base in load_all():
        for group, spec in build(derive(base)).items():
            for key in ("fg", "bg", "sp"):
                value = spec.get(key)
                if value is not None:
                    assert isinstance(value, str) and HEX.match(value), f"{base.name}/{group}/{key}: {value!r}"


def test_background_line_matches_theme() -> None:
    for base in load_all():
        erwartet = "dark" if base.dark else "light"
        assert f'vim.o.background = "{erwartet}"' in render(derive(base)), base.name


def test_render_is_deterministic() -> None:
    scheme = derive(load("synthwave"))
    assert render(scheme) == render(scheme)


def test_written_file_matches_render(tmp_path: Path) -> None:
    scheme = derive(load("boing"))
    path = write(scheme, tmp_path)
    assert path.name == "retro-boing.lua"
    assert path.read_text(encoding="utf-8") == render(scheme)


@pytest.mark.skipif(shutil.which("nvim") is None, reason="Neovim nicht im PATH")
def test_neovim_loads_every_colorscheme() -> None:
    names = sorted(path.stem for path in COLORS_DIR.glob("retro-*.lua"))
    # Neovim nimmt hoechstens zehn -c-Argumente, deshalb alle Themes in einer Lua-Schleife
    liste = ", ".join(f'"{name}"' for name in names)
    lua = f"for _, name in ipairs({{{liste}}}) do vim.cmd.colorscheme(name) end"
    ergebnis = subprocess.run(
        ["nvim", "--headless", "--clean", "-c", f"set rtp+={COLORS_DIR.parent}", "-c", f"lua {lua}", "-c", "qa!"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    # Neovim schreibt Fehler beim Laden eines Farbschemas nach stderr und endet trotzdem mit 0
    assert ergebnis.returncode == 0, ergebnis.stderr
    assert "E" not in ergebnis.stderr.replace("\n", ""), ergebnis.stderr
