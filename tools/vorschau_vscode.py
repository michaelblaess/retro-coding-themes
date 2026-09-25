"""Erzeugt die Vorschaubilder in docs/vscode/vorschau/ und die beiden Galerieseiten daneben.

Die Bilder kommen aus einem echten VS Code, sie sind nicht nachgebaut. VS Code gibt seine Fenster
nicht fuer die Fernsteuerung frei, deshalb wird das Fenster ueber Windows abfotografiert:

1. Die Erweiterung wird als .vsix gepackt und in ein leeres Profil installiert, das ein eigenes
   VS Code startet. Das installierte VS Code bleibt unberuehrt, geprueft wird das echte Paket.
2. Als Arbeitsordner dient ein kleines Git-Repo mit der Beispieldatei, damit im Explorer auch
   geaenderte und neue Dateien ihre Farbe zeigen.
3. Je Theme wird `workbench.colorTheme` in der settings.json des Profils gesetzt. VS Code liest
   die Datei selbst neu ein und wechselt das Theme ohne Neustart. Gestartet wird mit einem
   eingebauten Theme, damit schon das erste Retro-Theme ein echter Wechsel ist.
4. Das Fenster wird nach vorn geholt und sein Rechteck vom Bildschirm kopiert.

Waehrend der Aufnahme darf nichts ueber dem Fenster liegen und niemand klicken.

Nur unter Windows. Verwendung:
    uv run --with pillow python tools/vorschau.py                    alle Themes
    uv run --with pillow python tools/vorschau.py synthwave gemstone nur diese
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

# Nur unter Windows. mypy prueft den Rest der Datei dadurch auch nur fuer Windows.
assert sys.platform == "win32", "tools/vorschau_vscode.py laeuft nur unter Windows"

REPO = Path(__file__).resolve().parents[1]
ZIEL = REPO / "docs" / "vscode" / "vorschau"
BEISPIEL = REPO / "tools" / "beispiel.cs"
BREITE, HOEHE = 1400, 860
ORDNERNAME = "retro-themes-vorschau"

KOPF_EN = """# All themes

Every image shows the same C# file in a real VS Code. The extension is packaged from this repo
and installed into a fresh profile (`uv run --with pillow python tools/vorschau.py`, Windows
only). Syntax colours come from the TextMate grammar that ships with VS Code, without a C#
language server.

[Deutsch](vorschau.de.md)
"""

KOPF_DE = """# Alle Themes

Jedes Bild zeigt dieselbe C#-Datei in einem echten VS Code. Die Erweiterung wird aus diesem
Repo gepackt und in ein leeres Profil installiert (`uv run --with pillow python
tools/vorschau.py`, nur unter Windows). Die Syntaxfarben kommen aus der TextMate-Grammatik, die
VS Code mitbringt, ohne C#-Sprachserver.

[English](vorschau.md)
"""

EINSTELLUNGEN = {
    "workbench.startupEditor": "none",
    "workbench.tips.enabled": False,
    "workbench.secondarySideBar.defaultVisibility": "hidden",
    "workbench.layoutControl.enabled": False,
    "chat.disableAIFeatures": True,
    "chat.commandCenter.enabled": False,
    "security.workspace.trust.enabled": False,
    "telemetry.telemetryLevel": "off",
    "update.mode": "none",
    "extensions.ignoreRecommendations": True,
    "editor.minimap.enabled": False,
    "editor.fontSize": 14,
    "git.openRepositoryInParentFolders": "never",
    "window.restoreWindows": "none",
    "window.newWindowDimensions": "default",
}

user32 = ctypes.windll.user32


def _code_exe() -> str:
    """Findet Code.exe - ueber die Umgebungsvariable CODE_EXE oder am ueblichen Ort."""
    kandidaten = [
        os.environ.get("CODE_EXE", ""),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ]
    for kandidat in kandidaten:
        if kandidat and Path(kandidat).is_file():
            return kandidat
    raise SystemExit("Code.exe nicht gefunden, CODE_EXE setzen")


def _label(name: str) -> str:
    sys.path.insert(0, str(REPO / "src"))
    from retro_coding_themes.vscode.render import label

    return label(name)


def _arbeitsordner(basis: Path) -> Path:
    """Kleines Git-Repo: eine Datei unveraendert, eine geaendert, eine neu."""
    ordner = basis / ORDNERNAME
    ordner.mkdir()
    shutil.copyfile(BEISPIEL, ordner / "FahrtRechner.cs")
    (ordner / "Fahrt.cs").write_text("namespace Beispiel.Fahrtenbuch;\n", encoding="utf-8")
    (ordner / "Program.cs").write_text("// Einstieg\n", encoding="utf-8")
    befehle = [
        ["git", "init", "-q"],
        ["git", "add", "."],
        ["git", "-c", "user.name=Vorschau", "-c", "user.email=vorschau@example.invalid", "commit", "-qm", "Start"],
    ]
    for befehl in befehle:
        subprocess.run(befehl, cwd=ordner, check=True)
    (ordner / "Program.cs").write_text("// Einstieg\nSystem.Console.WriteLine();\n", encoding="utf-8")
    (ordner / "Neu.cs").write_text("// neu\n", encoding="utf-8")
    return ordner


def _fenster(titelteil: str, timeout: float = 60.0) -> int:
    """Handle des sichtbaren Fensters, dessen Titel den Ordnernamen enthaelt."""
    gefunden: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)  # type: ignore[untyped-decorator]
    def pruefen(hwnd: int, _: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            laenge = user32.GetWindowTextLengthW(hwnd)
            puffer = ctypes.create_unicode_buffer(laenge + 1)
            user32.GetWindowTextW(hwnd, puffer, laenge + 1)
            if titelteil in puffer.value:
                gefunden.append(hwnd)
        return True

    ende = time.monotonic() + timeout
    while time.monotonic() < ende:
        gefunden.clear()
        user32.EnumWindows(pruefen, 0)
        if gefunden:
            return gefunden[0]
        time.sleep(0.5)
    raise SystemExit(f"Kein Fenster mit '{titelteil}' im Titel gefunden")


def _nach_vorn(hwnd: int) -> None:
    # Windows gibt den Fokus nur her, wenn der Aufrufer gerade eine Eingabe hatte. Ein
    # losgelassenes Alt zaehlt als Eingabe.
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)


def _escape() -> None:
    # Hebt die Menuemarkierung auf, die das Alt aus _nach_vorn hinterlaesst
    user32.keybd_event(0x1B, 0, 0, 0)
    user32.keybd_event(0x1B, 0, 2, 0)


def _paket(basis: Path) -> Path:
    """Packt die Erweiterung und installiert sie in das Testprofil."""
    vsix = basis / "retro-themes.vsix"
    npx = shutil.which("npx") or "npx"
    befehl = [npx, "-y", "@vscode/vsce", "package", "--no-dependencies", "-o", str(vsix)]
    subprocess.run(befehl, cwd=REPO / "vscode", check=True)
    return vsix


def _aufnahme(hwnd: int, ziel: Path) -> None:
    # Nur bei Bedarf nach vorn holen: das Alt dafuer markiert sonst jedes Mal das Menue
    if user32.GetForegroundWindow() != hwnd:
        _nach_vorn(hwnd)
        _escape()
        time.sleep(0.6)
    rechteck = wintypes.RECT()
    # DWM liefert das sichtbare Rechteck ohne den unsichtbaren Rahmen fuer die Groessenaenderung
    ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rechteck), ctypes.sizeof(rechteck))
    bild = ImageGrab.grab(bbox=(rechteck.left, rechteck.top, rechteck.right, rechteck.bottom), all_screens=True)
    bild.save(ziel, optimize=True)


def _galerie(namen_dunkel: list[str], namen_hell: list[str]) -> None:
    """Schreibt docs/vscode/vorschau.md und docs/vscode/vorschau.de.md.

    Die Seiten sind Lesertexte, deshalb stehen in KOPF_DE echte Umlaute.
    """
    for datei, kopf, (dunkel, hell) in (
        ("vorschau.md", KOPF_EN, ("Dark", "Light")),
        ("vorschau.de.md", KOPF_DE, ("Dunkel", "Hell")),
    ):
        teile = [kopf]
        for ueberschrift, namen in ((dunkel, namen_dunkel), (hell, namen_hell)):
            teile.append(f"\n## {ueberschrift}\n")
            for name in namen:
                teile.append(f"\n### {_label(name)}\n\n![{name}](vorschau/{name}.png)\n")
        (REPO / "docs" / "vscode" / datei).write_text("".join(teile), encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    # Echte Pixel statt skalierter Koordinaten, sonst passt das Rechteck nicht zum Bildschirm
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    sys.path.insert(0, str(REPO / "src"))
    from retro_coding_themes.palettes import load_all

    alle = load_all()
    namen = [base.name for base in alle if not argv or base.name in argv]
    ZIEL.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="retro-vorschau-", ignore_cleanup_errors=True) as tmp:
        basis = Path(tmp)
        profil = basis / "profil"
        (profil / "User").mkdir(parents=True)
        einstellungen = profil / "User" / "settings.json"
        start = {**EINSTELLUNGEN, "workbench.colorTheme": "Default Dark Modern"}
        einstellungen.write_text(json.dumps(start), encoding="utf-8")
        ordner = _arbeitsordner(basis)
        profil_args = [f"--user-data-dir={profil}", f"--extensions-dir={basis / 'erweiterungen'}"]
        code_cli = str(Path(_code_exe()).parent / "bin" / "code.cmd")
        subprocess.run([code_cli, *profil_args, "--install-extension", str(_paket(basis))], check=True)

        prozess = subprocess.Popen(
            [
                _code_exe(),
                *profil_args,
                "--disable-workspace-trust",
                "--new-window",
                str(ordner),
                str(ordner / "FahrtRechner.cs"),
            ]
        )
        try:
            hwnd = _fenster(ORDNERNAME)
            user32.ShowWindow(hwnd, 1)
            user32.MoveWindow(hwnd, 40, 40, BREITE, HOEHE, True)
            _nach_vorn(hwnd)
            _escape()
            # Erster Start: Git-Erkennung, Grammatik und Explorer brauchen einen Moment
            time.sleep(12)
            for name in namen:
                daten = {**EINSTELLUNGEN, "workbench.colorTheme": _label(name)}
                einstellungen.write_text(json.dumps(daten), encoding="utf-8")
                time.sleep(2.5)
                _aufnahme(hwnd, ZIEL / f"{name}.png")
                print(f"  {name}")
        finally:
            prozess.terminate()
            # Code.exe startet Kindprozesse, die das Profil noch halten
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(prozess.pid)], capture_output=True)
            time.sleep(2)

    if not argv:
        _galerie([b.name for b in alle if b.dark], [b.name for b in alle if not b.dark])
    print(f"{len(namen)} Bilder in {ZIEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
