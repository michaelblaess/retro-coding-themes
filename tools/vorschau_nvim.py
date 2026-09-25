"""Erzeugt die Vorschaubilder in docs/nvim/vorschau/ und die beiden Galerieseiten daneben.

Die Bilder kommen aus Neovim selbst, sie sind nicht nachgebaut.

Ablauf je Theme: Neovim laedt das Farbschema und die Beispieldatei, faerbt sie mit Treesitter
und gibt die Ansicht ueber `:TOhtml` als HTML aus. Ein Chromium nimmt die Seite als PNG auf.
Die Farben im Bild sind damit die, die Neovim wirklich setzt.

Voraussetzungen:
    - `nvim` im PATH, Treesitter-Parser `c_sharp` installiert (`:TSInstall c_sharp`)
    - ein Chromium: ueber die Umgebungsvariable CHROME, sonst wird gesucht

Verwendung:
    uv run python tools/vorschau.py                    alle Themes
    uv run python tools/vorschau.py synthwave gemstone nur diese
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BEISPIEL = REPO / "tools" / "beispiel.cs"
ZIEL = REPO / "docs" / "nvim" / "vorschau"
BREITE, HOEHE = 900, 700

KOPF_EN = """# All colorschemes

Every image shows the same C# file. They come out of Neovim itself: `:TOhtml` writes the
highlighted view as HTML and a Chromium takes the picture
(`uv run python tools/vorschau.py`). The colours are the ones Neovim actually sets.

[Deutsch](vorschau.de.md)
"""

KOPF_DE = """# Alle Farbschemata

Die Bilder zeigen dieselbe C#-Datei in jedem Theme. Sie kommen aus Neovim selbst: `:TOhtml`
gibt die gefärbte Ansicht als HTML aus, ein Chromium nimmt sie auf
(`uv run python tools/vorschau.py`). Die Farben sind also die, die Neovim wirklich setzt.

[English](vorschau.md)
"""


def _chromium() -> str:
    """Sucht einen Chromium. Die Umgebungsvariable CHROME hat Vorrang."""
    aus_umgebung = os.environ.get("CHROME")
    if aus_umgebung:
        return aus_umgebung
    for name in ("chrome-headless-shell", "chromium", "chromium-browser", "google-chrome"):
        gefunden = shutil.which(name)
        if gefunden:
            return gefunden
    # Playwright legt seine Browser unter einen versionierten Ordner, der juengste gewinnt
    cache = Path.home() / "AppData" / "Local" / "ms-playwright"
    kandidaten = sorted(cache.glob("chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell.exe"))
    if kandidaten:
        return str(kandidaten[-1])
    for pfad in (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/google-chrome"),
    ):
        if pfad.exists():
            return str(pfad)
    raise SystemExit("Kein Chromium gefunden. CHROME setzen.")


def _html(theme: str, ziel: Path) -> None:
    """Laesst Neovim die Beispieldatei im Farbschema `theme` nach HTML schreiben."""
    site = Path.home() / "AppData" / "Local" / "nvim-data" / "site"
    lua = (
        "vim.fn.writefile("
        f"require('tohtml').tohtml(vim.api.nvim_get_current_win(), {{title='{theme}'}}), "
        f"[[{ziel.as_posix()}]])"
    )
    befehl = [
        "nvim",
        "--headless",
        "--clean",
        "--cmd",
        f"set termguicolors rtp+={REPO.as_posix()} rtp+={site.as_posix()}",
        "-c",
        "packadd nvim.tohtml",
        "-c",
        f"colorscheme {theme}",
        "-c",
        f"edit {BEISPIEL.as_posix()}",
        "-c",
        "lua vim.treesitter.start(0, 'c_sharp')",
        "-c",
        "sleep 300m",
        "-c",
        f"lua {lua}",
        "-c",
        "qa!",
    ]
    ergebnis = subprocess.run(befehl, capture_output=True, text=True, timeout=120)
    if not ziel.exists():
        raise SystemExit(f"{theme}: Neovim hat kein HTML geschrieben\n{ergebnis.stderr}")


def _png(html: Path, ziel: Path, browser: str) -> None:
    subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={ziel}",
            f"--window-size={BREITE},{HOEHE}",
            html.resolve().as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if not ziel.exists():
        raise SystemExit(f"Kein Bild erzeugt: {ziel}")


def _galerie(namen_dunkel: list[str], namen_hell: list[str]) -> None:
    """Schreibt docs/nvim/vorschau.md und docs/nvim/vorschau.de.md, immer ueber alle Themes.

    Die Seiten sind Lesertexte, deshalb stehen in KOPF_DE echte Umlaute.
    """
    for datei, kopf, titel in (
        ("vorschau.md", KOPF_EN, ("Dark", "Light")),
        ("vorschau.de.md", KOPF_DE, ("Dunkel", "Hell")),
    ):
        teile = [kopf]
        for ueberschrift, namen in zip(titel, (namen_dunkel, namen_hell), strict=True):
            teile.append(f"\n## {ueberschrift}\n")
            for name in namen:
                teile.append(f"\n### retro-{name}\n\n![retro-{name}](vorschau/retro-{name}.png)\n")
        (REPO / "docs" / "nvim" / datei).write_text("".join(teile), encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(REPO / "src"))
    from retro_coding_themes.palettes import load_all

    alle = load_all()
    nur = [arg for arg in argv if not arg.startswith("-")]
    themes = [base.name for base in alle if not nur or base.name in nur]
    unbekannt = set(nur) - set(themes)
    if unbekannt:
        print(f"Unbekannte Themes: {', '.join(sorted(unbekannt))}", file=sys.stderr)
        return 1

    browser = _chromium()
    ZIEL.mkdir(parents=True, exist_ok=True)
    _galerie([base.name for base in alle if base.dark], [base.name for base in alle if not base.dark])
    with tempfile.TemporaryDirectory() as tmp:
        for name in themes:
            html = Path(tmp) / f"{name}.html"
            _html(f"retro-{name}", html)
            _png(html, ZIEL / f"retro-{name}.png", browser)
            print(f"[OK] {name}")
    print(f"{len(themes)} Bilder in {ZIEL}, Galerie in docs/nvim/vorschau.md und docs/nvim/vorschau.de.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
