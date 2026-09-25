"""Kopiert die Grundfarben der retro-themes aus textual-themes nach src/retro_coding_themes/data.

Einmaliger Snapshot statt Abhaengigkeit: Neovim-Themes werden eigens abgestimmt, ein erneuter Lauf
ueberschreibt Handaenderungen an den JSON-Dateien.

Verwendung:
    uv run python tools/snapshot_from_textual.py [<pfad-zu-textual-themes>]
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ZIEL = Path(__file__).resolve().parents[1] / "src" / "retro_coding_themes" / "data"
STANDARD_QUELLE = Path(__file__).resolve().parents[2] / "textual-themes"
FELDER = (
    "primary",
    "secondary",
    "accent",
    "foreground",
    "background",
    "surface",
    "panel",
    "boost",
    "warning",
    "error",
    "success",
)


def _palettes_laden(repo: Path) -> ModuleType:
    # palettes.py hat keine Abhaengigkeiten, deshalb direkt laden statt textual-themes zu installieren
    pfad = repo / "src" / "textual_themes" / "palettes.py"
    spec = importlib.util.spec_from_file_location("textual_palettes", pfad)
    if spec is None or spec.loader is None:
        raise SystemExit(f"palettes.py nicht gefunden: {pfad}")
    modul = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modul
    spec.loader.exec_module(modul)
    return modul


def _version(repo: Path) -> str:
    for zeile in (repo / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if zeile.startswith("version"):
            return zeile.split("=", 1)[1].strip().strip('"')
    return "unbekannt"


def main() -> None:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else STANDARD_QUELLE
    modul = _palettes_laden(repo)
    version = _version(repo)
    ZIEL.mkdir(parents=True, exist_ok=True)
    anzahl = 0
    for palette in modul.RETRO_PALETTES:
        eintrag = {
            "name": palette.name,
            "dark": palette.dark,
            "source": {"origin": "textual-themes palettes.py", "textual_themes": version},
            "base": {feld: str(getattr(palette, feld)).upper() for feld in FELDER},
        }
        (ZIEL / f"{palette.name}.json").write_text(json.dumps(eintrag, indent=2) + "\n", encoding="utf-8")
        anzahl += 1
    print(f"{anzahl} Themes nach {ZIEL} geschrieben (textual-themes {version})")


if __name__ == "__main__":
    main()
