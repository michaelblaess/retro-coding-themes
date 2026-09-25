"""Bildet ein abgeleitetes Farbschema auf die Farbkategorien von Visual Studio 2026 ab.

Kategorien und Eintragsnamen stammen aus den mitgelieferten Themes von VS 2026, gelesen am
24.09.2026 aus `Theme.JuicyPlum.pkgdef`, `EditorColors.pkgdef` und
`Microsoft.VisualStudio.LanguageServices.pkgdef`. Alles, was hier nicht steht, erbt ein Theme
ueber `FallbackId` von Dark oder Light - genau so sind die neuen Themes von VS 2026 gebaut.

Die Syntax folgt der Zuordnung fuer Neovim und VS Code in diesem Paket, damit dasselbe
Theme in allen drei Editoren gleich aussieht.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..color import contrast, mix
from ..derive import TEXT_TARGET, Scheme

# Basis-Themes von Visual Studio, aus Themes.Registration.pkgdef
DARK = "{1ded0138-47ce-435e-84ef-9ec1f439b749}"
LIGHT = "{de3dbbcd-f642-433c-8353-8f1df4370aba}"

# Aus dem Namen abgeleitet, damit jedes Theme ueber alle Versionen dieselbe GUID behaelt. Eine
# neue GUID waere fuer Visual Studio ein neues Theme, die Auswahl der Nutzer ginge verloren.
NAMESPACE = uuid.UUID("6f2b8f4e-8c1a-4d53-9d0e-5b7a2e1c9a01")

SHELL = "{73708ded-2d56-4aad-b8eb-73b20d3f4bff}"
SHELL_INTERNAL = "{5af241b7-5627-4d12-bfb1-2b67d11127d7}"
TEXT_MANAGER = "{58e96763-1d3b-4e05-b6ba-ff7115fd0b7b}"
LANGUAGE_SERVICE = "{e0187991-b458-4f7e-8ca9-42c9a573b56c}"
# Roslyn und der allgemeine Editor teilen sich diese GUID unter zwei Schluesselnamen
MEF = "{75a05685-00a8-4ded-bae5-e7a50bfa929a}"

LABELS = {
    "ascot": "Ascot",
    "beastie": "Beastie",
    "bebox": "BeBox",
    "bluesy": "Bluesy",
    "boing": "Boing",
    "brick": "Brick",
    "brotkasten": "Brotkasten",
    "bunty": "Bunty",
    "christophorus": "Christophorus",
    "classic-navy": "Classic Navy",
    "classic-terminal": "Classic Terminal",
    "clipper": "Clipper",
    "commandr": "Commandr",
    "corleone": "Corleone",
    "crimson": "Crimson",
    "cupertino": "Cupertino",
    "fifty-eight": "Fifty-Eight",
    "flughund": "Flughund",
    "geeko": "Geeko",
    "gemstone": "Gemstone",
    "golden-brown": "Golden Brown",
    "goldfinder": "Goldfinder",
    "goldrunner": "Goldrunner",
    "hercules": "Hercules",
    "hulkula": "Hulkula",
    "joker": "Joker",
    "lenseflare": "Lenseflare",
    "luna": "Luna",
    "marley": "Marley",
    "metropolis": "Metropolis",
    "miami": "Miami",
    "minty": "Minty",
    "motif": "Motif",
    "next": "Next",
    "plan9": "Plan 9",
    "platoon": "Platoon",
    "racing": "Racing",
    "razzy": "Razzy",
    "spiderized": "Spiderized",
    "synthwave": "Synthwave",
    "warp": "Warp",
}

# Hintergrund und Vordergrund eines Eintrags, None heisst "nicht setzen, vom Basis-Theme erben"
Farbe = tuple[str | None, str | None]

# Anteil der Akzentfarbe in der Auswahl, bevor er fuer die Lesbarkeit zurueckgenommen wird
SELECTION_AMOUNT = 0.35
# Anteil der Leitfarbe in der Oberflaeche von VS 2026. 45 % waren Michael zu grell (25.09.2026),
# mit 18 % liegt Synthwave bei #43114C, nah an Juicy Plum (#452372) von Microsoft.
ENVIRONMENT_AMOUNT = 0.18
# Anteil der Textfarbe in der Flaeche der Werkzeugfenster
TOOL_AMOUNT = 0.07


@dataclass(frozen=True, slots=True)
class Kategorie:
    """Eine Farbkategorie von Visual Studio mit ihren Eintraegen."""

    name: str
    guid: str
    eintraege: dict[str, Farbe]


def label(name: str) -> str:
    """Anzeigename im Theme-Waehler von Visual Studio."""
    return f"Retro {LABELS[name]}"


def theme_guid(name: str) -> str:
    """Feste GUID eines Themes, in geschweiften Klammern wie in der Registry."""
    return "{" + str(uuid.uuid5(NAMESPACE, name)) + "}"


def fallback(scheme: Scheme) -> str:
    """GUID des Basis-Themes, von dem alle nicht gesetzten Farben kommen."""
    return DARK if scheme.dark else LIGHT


def _readable_amount(bg: str, overlay: str, text: str, start: float) -> float:
    """Groesster Anteil der Ueberlagerung, bei dem der Text darauf noch lesbar bleibt."""
    amount = start
    while amount > 0.02 and contrast(text, mix(bg, overlay, amount)) < TEXT_TARGET:
        amount *= 0.8
    return amount


def chrome(scheme: Scheme) -> str:
    """Flaeche fuer Werkzeugfenster wie den Projektmappen-Explorer.

    Leicht zum Text hin verschoben, also heller als der Editor im dunklen Theme. Frueher war sie
    dunkler, und bei fast schwarzen Editoren wie classic-terminal waren Editor und
    Projektmappen-Explorer nicht mehr zu unterscheiden (Michael, 25.09.2026). Juicy Plum von
    Microsoft macht es genauso: Werkzeugflaeche #27242B, Editor aus Dark #1E1E1E.
    """
    return mix(scheme.bg, scheme.fg, TOOL_AMOUNT)


def environment(scheme: Scheme) -> str:
    """Flaeche von Titelleiste, Menue und Statusleiste in VS 2026, leicht in der Leitfarbe getoent."""
    return mix(scheme.bg, scheme.statusline_bg, ENVIRONMENT_AMOUNT)


def kategorien(scheme: Scheme) -> list[Kategorie]:
    """Alle Kategorien, die ein Theme setzt, in fester Reihenfolge."""
    s = scheme
    selection_amount = _readable_amount(s.bg, s.accent, s.fg, SELECTION_AMOUNT)
    selection = mix(s.bg, s.accent, selection_amount)
    inactive = mix(s.bg, s.accent, selection_amount * 0.5)
    search = mix(s.bg, s.number, _readable_amount(s.bg, s.number, s.fg, SELECTION_AMOUNT))
    typ: Farbe = (None, s.type_)
    kommentar: Farbe = (None, s.comment)
    return [
        # VS 2026 leitet die Oberflaeche aus diesen Akzenten ab, wie bei den eigenen neuen Themes
        Kategorie("Shell", SHELL, {
            "AccentFillDefault": (s.accent, None),
            "SolidBackgroundFillTertiary": (chrome(s), None),
            "SolidBackgroundFillQuaternary": (s.bg_float, None),
            "SurfaceBackgroundFillDefault": (s.bg_float, None),
        }),
        Kategorie("ShellInternal", SHELL_INTERNAL, {
            "EnvironmentBackground": (environment(s), None),
            "EnvironmentBorder": (s.accent, None),
            "EnvironmentLogo": (s.accent, None),
        }),
        Kategorie("Text Editor Text Manager Items", TEXT_MANAGER, {
            "Plain Text": (s.bg, s.fg),
            "Selected Text": (selection, None),
            "Inactive Selected Text": (inactive, None),
            "Indicator Margin": (s.bg, None),
            "Visible Whitespace": (None, mix(s.bg, s.fg, 0.22)),
            "Line Number": (s.bg, s.fg_faint),
        }),
        Kategorie("Text Editor Language Service Items", LANGUAGE_SERVICE, {
            "Keyword": (None, s.keyword),
            "Comment": kommentar,
            "String": (None, s.string),
            "String(C# @ Verbatim)": (None, s.string),
            "Number": (None, s.number),
            "Operator": (None, s.operator),
            "Preprocessor Keyword": (None, s.special),
            "Excluded Code": (None, s.fg_faint),
            "User Types": typ,
            "User Types(Value types)": typ,
            "User Types(Interfaces)": typ,
            "User Types(Delegates)": typ,
            "User Types(Enums)": typ,
            "User Types(Type parameters)": typ,
            "XML Doc Comment": kommentar,
            "XML Doc Tag": kommentar,
            "XML Doc Attribute": kommentar,
            "XML Comment": kommentar,
            "XML Name": (None, s.keyword),
            "XML Attribute": (None, s.function),
            "XML Attribute Value": (None, s.string),
            "XML Delimiter": (None, s.operator),
            "XML Text": (None, s.fg),
            "XAML Comment": kommentar,
            "XAML Name": (None, s.keyword),
            "XAML Attribute": (None, s.function),
            "XAML Attribute Value": (None, s.string),
            "XAML Delimiter": (None, s.operator),
            "XAML Text": (None, s.fg),
            "Error": (None, s.error),
        }),
        Kategorie("Roslyn Text Editor MEF Items", MEF, {
            "keyword - control": (None, s.keyword),
            "punctuation": (None, s.operator),
            "operator - overloaded": (None, s.function),
            "string - verbatim": (None, s.string),
            "class name": typ,
            "delegate name": typ,
            "enum name": typ,
            "interface name": typ,
            "module name": typ,
            "struct name": typ,
            "type parameter name": typ,
            "record class name": typ,
            "record struct name": typ,
            "namespace name": typ,
            "method name": (None, s.function),
            "extension method name": (None, s.function),
            "local name": (None, s.fg),
            "parameter name": (None, s.fg),
            "field name": (None, s.fg),
            "property name": (None, s.fg),
            "event name": (None, s.fg),
            "enum member name": (None, s.number),
            "constant name": (None, s.number),
            "preprocessor text": (None, s.fg),
            "xml doc comment - text": kommentar,
            "xml doc comment - delimiter": kommentar,
            "xml doc comment - name": kommentar,
            "xml doc comment - attribute name": kommentar,
            "xml doc comment - attribute quotes": kommentar,
            "xml doc comment - attribute value": kommentar,
            "xml doc comment - comment": kommentar,
            "inline hints": (None, s.fg_faint),
        }),
        Kategorie("Text Editor MEF Items", MEF, {
            "brace pair level one": (None, s.keyword),
            "brace pair level two": (None, s.function),
            "brace pair level three": (None, s.type_),
            "mismatched brace": (None, s.error),
            "string - escape character": (None, s.special),
            "brace matching": (s.bg_elevated, None),
            "MarkerFormatDefinition/HighlightedReference": (mix(s.bg, s.fg, 0.14), None),
            "MarkerFormatDefinition/FindHighlight": (search, None),
        }),
    ]
