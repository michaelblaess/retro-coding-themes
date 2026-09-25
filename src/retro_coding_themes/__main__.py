"""Erzeugt die Themes fuer alle Editoren aus einer gemeinsamen Ableitung.

Verwendung:
    uv run python -m retro_coding_themes            alle Ziele schreiben
    uv run python -m retro_coding_themes --vsix     zusaetzlich die .vsix fuer Visual Studio bauen
    uv run python -m retro_coding_themes --report   nur die Kontrasttabelle

Ziele:
    colors/retro-*.lua                        Neovim, in der Wurzel wegen der Plugin-Manager
    vscode/themes/*.json, vscode/package.json VS Code
    visualstudio/RetroCodingThemes.pkgdef     Visual Studio 2026
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from .color import contrast, delta_e
from .derive import Scheme, derive
from .nvim.render import write as write_lua
from .palettes import load_all
from .visualstudio.pkgdef import render_all
from .visualstudio.vsix import PKGDEF, build
from .vscode.render import package_entry
from .vscode.render import write as write_json

ROOT = Path(__file__).resolve().parents[2]
NVIM_DIR = ROOT / "colors"
VSCODE_DIR = ROOT / "vscode"
VISUALSTUDIO_PKGDEF = ROOT / "visualstudio" / PKGDEF


def _report_line(scheme: Scheme) -> str:
    syntax = (scheme.keyword, scheme.function, scheme.string, scheme.number, scheme.type_, scheme.special)
    min_contrast = min(contrast(color, scheme.bg) for color in (*syntax, scheme.comment, scheme.fg))
    min_distance = min(delta_e(a, b) for i, a in enumerate(syntax) for b in syntax[i + 1 :])
    return (
        f"{scheme.name:<18} Kommentar {contrast(scheme.comment, scheme.bg):5.2f}  "
        f"Syntax min {min_contrast:5.2f}  Abstand min {min_distance:5.1f}"
    )


def version() -> str:
    """Die Version aus der pyproject.toml. Sie gilt fuer die .vsix von Visual Studio."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _write_vscode(schemes: list[Scheme]) -> None:
    themes_dir = VSCODE_DIR / "themes"
    for scheme in schemes:
        write_json(scheme, themes_dir)
    stale = {path.stem for path in themes_dir.glob("*.json")} - {scheme.name for scheme in schemes}
    for name in sorted(stale):
        (themes_dir / f"{name}.json").unlink()
    package_json = VSCODE_DIR / "package.json"
    package = json.loads(package_json.read_text(encoding="utf-8"))
    package["contributes"]["themes"] = [package_entry(scheme) for scheme in schemes]
    package_json.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    schemes = [derive(base) for base in load_all()]
    for scheme in schemes:
        print(_report_line(scheme))
    if "--report" in argv:
        return 0

    for scheme in schemes:
        write_lua(scheme, NVIM_DIR)
    _write_vscode(schemes)
    text = render_all(schemes)
    VISUALSTUDIO_PKGDEF.parent.mkdir(parents=True, exist_ok=True)
    VISUALSTUDIO_PKGDEF.write_bytes(text.encode("utf-8"))
    print(f"{len(schemes)} Themes: colors/, vscode/themes/, {VISUALSTUDIO_PKGDEF.relative_to(ROOT)}")

    if "--vsix" in argv:
        ziel = ROOT / "dist" / f"RetroCodingThemes-{version()}.vsix"
        build(text, (ROOT / "LICENSE").read_text(encoding="utf-8"), version(), ziel)
        print(f"Visual-Studio-Paket: {ziel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
