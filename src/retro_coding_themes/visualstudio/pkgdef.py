"""Schreibt und liest die .pkgdef-Dateien, in denen Visual Studio seine Themes ablegt.

Das Format ist nicht dokumentiert. Es ist gelesen aus den mitgelieferten Themes von VS 2026 und
aus der Ausgabe des `VsixColorCompiler` (VS 2022, Version 17.0.0.4). Der Schreiber hier liefert
fuer alle 41 Themes dieselben Bytes wie dieser Compiler, belegt am 25.09.2026, die Referenzen
liegen unter tests/referenz/.

Je Kategorie steht ein Registry-Schluessel mit einem Wert "Data". Der Block beginnt mit
Gesamtlaenge, Version 11 und Anzahl der Kategorien (je uint32, little endian). Dann je Kategorie
die GUID in Microsoft-Byteordnung, die Anzahl der Eintraege und je Eintrag: Laenge und Name in
ASCII, danach Hintergrund und Vordergrund als Typbyte plus RGBA. Typ 0 heisst "keine Farbe", dann
folgen keine Farbbytes.
"""

from __future__ import annotations

import re
import struct
import uuid
from dataclasses import dataclass

from ..derive import Scheme
from .render import Farbe, Kategorie, fallback, kategorien, label, theme_guid

VERSION = 11
CT_RAW = 1
BOM = "﻿"


def _farbe(color: str | None) -> bytes:
    if color is None:
        return b"\x00"
    return bytes([CT_RAW, int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), 0xFF])


def block(guid: str, eintraege: dict[str, Farbe]) -> bytes:
    """Der Binaerblock einer Kategorie, wie er hinter "Data"=hex: steht."""
    teil = uuid.UUID(guid).bytes_le + struct.pack("<I", len(eintraege))
    for name, (bg, fg) in eintraege.items():
        roh = name.encode("ascii")
        teil += struct.pack("<I", len(roh)) + roh + _farbe(bg) + _farbe(fg)
    kopf = struct.pack("<II", VERSION, 1)
    return struct.pack("<I", 4 + len(kopf) + len(teil)) + kopf + teil


def _zusammenlegen(liste: list[Kategorie]) -> list[Kategorie]:
    """Legt Kategorien mit derselben GUID zusammen, unter dem Namen der ersten.

    So macht es der Compiler auch. Roslyn und der allgemeine Editor teilen sich eine GUID.
    """
    nach_guid: dict[str, Kategorie] = {}
    for kategorie in liste:
        if kategorie.guid in nach_guid:
            nach_guid[kategorie.guid].eintraege.update(kategorie.eintraege)
        else:
            nach_guid[kategorie.guid] = Kategorie(kategorie.name, kategorie.guid, dict(kategorie.eintraege))
    return list(nach_guid.values())


def render(scheme: Scheme) -> str:
    """Der Text der .pkgdef eines Themes, mit Registrierung, ohne BOM, Zeilenenden CRLF."""
    guid = theme_guid(scheme.name)
    name = label(scheme.name)
    zeilen = [
        f"[$RootKey$\\Themes\\{guid}]",
        f'@="{name}"',
        f'"Name"="{name}"',
        f'"FallbackId"="{fallback(scheme)}"',
        "",
    ]
    for kategorie in _zusammenlegen(kategorien(scheme)):
        daten = ",".join(f"{b:02x}" for b in block(kategorie.guid, kategorie.eintraege))
        zeilen += [f"[$RootKey$\\Themes\\{guid}\\{kategorie.name}]", f'"Data"=hex:{daten}', ""]
    return "\r\n".join(zeilen)


def render_all(schemes: list[Scheme]) -> str:
    """Alle Themes in einer Datei, mit BOM wie die mitgelieferten .pkgdef-Dateien."""
    return BOM + "\r\n".join(render(scheme) for scheme in schemes)


@dataclass(frozen=True, slots=True)
class Eintrag:
    """Ein gelesener Eintrag: Name, Hintergrund und Vordergrund als #RRGGBB oder None."""

    name: str
    hintergrund: str | None
    vordergrund: str | None


def _lies_farbe(daten: bytes, pos: int) -> tuple[str | None, int]:
    typ = daten[pos]
    if typ == 0:
        return None, pos + 1
    r, g, b, a = daten[pos + 1 : pos + 5]
    if typ != CT_RAW or a != 0xFF:
        raise ValueError(f"Nicht unterstuetzte Farbe: Typ {typ}, Alpha {a}")
    return f"#{r:02X}{g:02X}{b:02X}", pos + 5


def lies_block(daten: bytes) -> dict[str, list[Eintrag]]:
    """Gegenstueck zu `block`: liest einen Binaerblock, Ergebnis je Kategorie-GUID."""
    laenge, version, anzahl = struct.unpack_from("<III", daten, 0)
    if laenge != len(daten) or version != VERSION:
        raise ValueError(f"Block passt nicht: Laenge {laenge}/{len(daten)}, Version {version}")
    pos = 12
    ergebnis: dict[str, list[Eintrag]] = {}
    for _ in range(anzahl):
        guid = "{" + str(uuid.UUID(bytes_le=daten[pos : pos + 16])) + "}"
        (n,) = struct.unpack_from("<I", daten, pos + 16)
        pos += 20
        eintraege: list[Eintrag] = []
        for _ in range(n):
            (nl,) = struct.unpack_from("<I", daten, pos)
            name = daten[pos + 4 : pos + 4 + nl].decode("ascii")
            bg, pos = _lies_farbe(daten, pos + 4 + nl)
            fg, pos = _lies_farbe(daten, pos)
            eintraege.append(Eintrag(name, bg, fg))
        ergebnis[guid] = eintraege
    return ergebnis


def data_zeilen(text: str) -> dict[str, bytes]:
    """Alle "Data"-Werte einer .pkgdef, je Registry-Schluessel."""
    ergebnis: dict[str, bytes] = {}
    for m in re.finditer(r'^\[([^\]]+)\]\r?\n"Data"=hex:([0-9a-fA-F,]+)', text.lstrip(BOM), re.M):
        ergebnis[m.group(1)] = bytes(int(x, 16) for x in m.group(2).split(","))
    return ergebnis
