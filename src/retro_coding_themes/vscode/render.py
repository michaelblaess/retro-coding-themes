"""Bildet ein abgeleitetes Farbschema auf ein VS-Code-Theme ab.

Die Rollen kommen aus `derive.py` und sind dort schon auf Lesbarkeit gehoben. Hier wird nur
noch verteilt: welche Rolle auf welche Oberflaeche, welchen TextMate-Scope und welchen
semantischen Token faellt. Die Zuordnung der Syntax folgt der fuer Neovim, damit dasselbe
Theme in beiden Editoren gleich aussieht.

Ueberlagerungen wie Auswahl, Suche und aktuelle Zeile sind halbtransparent, weil VS Code darunter
weitere Dekorationen zeichnet. Ihr Alpha ist so gewaehlt, dass die Mischung auf dem Hintergrund
genau der Flaeche entspricht, die `derive.py` vorsieht.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..color import contrast, delta_e, mix
from ..derive import TEXT_TARGET, Scheme

# Anzeigenamen im Theme-Waehler. VS Code merkt sich das gewaehlte Theme ueber dieses Label,
# deshalb bleiben die bestehenden Namen unveraendert.
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

# Anteil der Akzentfarbe in der Auswahl, bevor er fuer die Lesbarkeit zurueckgenommen wird
SELECTION_AMOUNT = 0.35
# Anteil der Zahlenfarbe im Suchtreffer, gleiche Regel
SEARCH_AMOUNT = 0.35


def label(name: str) -> str:
    """Anzeigename eines Themes im Waehler von VS Code."""
    return f"Retro — {LABELS[name]}"


def _alpha(color: str, amount: float) -> str:
    """Haengt einen Alphawert an. Auf dem Hintergrund ergibt das genau `mix(bg, color, amount)`."""
    return f"{color}{round(max(0.0, min(1.0, amount)) * 255):02X}"


def _readable_amount(bg: str, overlay: str, text: str, start: float) -> float:
    """Groesster Anteil der Ueberlagerung, bei dem der Text darauf noch lesbar bleibt."""
    amount = start
    while amount > 0.02 and contrast(text, mix(bg, overlay, amount)) < TEXT_TARGET:
        amount *= 0.8
    return amount


def _on(color: str, options: tuple[str, ...]) -> str:
    """Schriftfarbe auf einer farbigen Flaeche: die mit dem hoechsten Kontrast."""
    return max(options, key=lambda option: contrast(color, option))


def _chrome(scheme: Scheme) -> str:
    """Flaeche fuer Seitenleiste, Panel und Titelzeile.

    Im dunklen Theme etwas dunkler als der Editor, im hellen etwas dunkler als das Papier. So
    tritt der Editor als hellste bzw. ruhigste Flaeche hervor.
    """
    return mix(scheme.bg, "#000000", 0.22) if scheme.dark else mix(scheme.bg, scheme.fg, 0.05)


def ui_colors(scheme: Scheme) -> dict[str, str]:
    """Die Farben der Oberflaeche, Schluessel wie in der VS-Code-Referenz."""
    s = scheme
    chrome = _chrome(s)
    deep = mix(chrome, "#000000", 0.2) if s.dark else mix(s.bg, s.fg, 0.09)
    on_accent = _on(s.accent, (s.bg, s.fg, "#000000", "#FFFFFF"))
    on_error = _on(s.error, (s.bg, s.fg, "#000000", "#FFFFFF"))
    on_warning = _on(s.warning, (s.bg, s.fg, "#000000", "#FFFFFF"))
    input_bg = mix(s.bg, s.fg, 0.05)

    selection = _readable_amount(s.bg, s.accent, s.fg, SELECTION_AMOUNT)
    search = _readable_amount(s.bg, s.number, s.fg, SEARCH_AMOUNT)
    list_selection = _readable_amount(chrome, s.accent, s.fg, SELECTION_AMOUNT)

    return {
        # Allgemein
        "foreground": s.fg,
        "descriptionForeground": s.fg_dim,
        "disabledForeground": s.fg_faint,
        "errorForeground": s.error,
        "focusBorder": s.accent,
        "icon.foreground": s.fg_dim,
        "selection.background": _alpha(s.accent, selection),
        "widget.shadow": _alpha("#000000", 0.35 if s.dark else 0.15),
        "sash.hoverBorder": s.accent,
        "textLink.foreground": s.info,
        "textLink.activeForeground": s.accent,
        "textPreformat.foreground": s.string,
        "textBlockQuote.background": s.bg_float,
        "textBlockQuote.border": s.border,
        "textCodeBlock.background": s.bg_float,
        "textSeparator.foreground": s.border,
        # Editor
        "editor.background": s.bg,
        "editor.foreground": s.fg,
        "editorCursor.foreground": s.accent,
        "editor.lineHighlightBackground": _alpha(s.fg, 0.07),
        "editor.lineHighlightBorder": _alpha(s.fg, 0.0),
        "editor.selectionBackground": _alpha(s.accent, selection),
        "editor.inactiveSelectionBackground": _alpha(s.accent, selection * 0.5),
        "editor.selectionHighlightBackground": _alpha(s.accent, selection * 0.45),
        "editor.wordHighlightBackground": _alpha(s.fg, 0.12),
        "editor.wordHighlightStrongBackground": _alpha(s.fg, 0.18),
        "editor.findMatchBackground": _alpha(s.number, search),
        "editor.findMatchBorder": s.number,
        "editor.findMatchHighlightBackground": _alpha(s.number, search * 0.5),
        "editor.findRangeHighlightBackground": _alpha(s.fg, 0.06),
        "editor.hoverHighlightBackground": _alpha(s.accent, selection * 0.35),
        "editor.rangeHighlightBackground": _alpha(s.fg, 0.06),
        "editorLineNumber.foreground": s.fg_faint,
        "editorLineNumber.activeForeground": s.accent,
        "editorWhitespace.foreground": mix(s.bg, s.fg, 0.22),
        "editorIndentGuide.background1": mix(s.bg, s.fg, 0.12),
        "editorIndentGuide.activeBackground1": mix(s.bg, s.fg, 0.35),
        "editorRuler.foreground": mix(s.bg, s.fg, 0.12),
        "editorBracketMatch.background": s.bg_elevated,
        "editorBracketMatch.border": s.accent,
        "editorBracketHighlight.foreground1": s.keyword,
        "editorBracketHighlight.foreground2": s.function,
        "editorBracketHighlight.foreground3": s.type_,
        "editorBracketHighlight.foreground4": s.string,
        "editorBracketHighlight.foreground5": s.number,
        "editorBracketHighlight.foreground6": s.special,
        "editorBracketHighlight.unexpectedBracket.foreground": s.error,
        "editorCodeLens.foreground": s.fg_faint,
        "editorInlayHint.foreground": s.fg_faint,
        "editorInlayHint.background": _alpha(s.fg, 0.0),
        "editorLink.activeForeground": s.info,
        "editorError.foreground": s.error,
        "editorWarning.foreground": s.warning,
        "editorInfo.foreground": s.info,
        "editorHint.foreground": s.hint,
        "editorUnnecessaryCode.opacity": "#000000A0",
        "editorGutter.background": s.bg,
        "editorGutter.addedBackground": s.success,
        "editorGutter.modifiedBackground": s.info,
        "editorGutter.deletedBackground": s.error,
        "editorGutter.foldingControlForeground": s.fg_dim,
        "editorOverviewRuler.border": _alpha(s.fg, 0.0),
        "editorOverviewRuler.errorForeground": s.error,
        "editorOverviewRuler.warningForeground": s.warning,
        "editorOverviewRuler.infoForeground": s.info,
        "editorOverviewRuler.findMatchForeground": s.number,
        "editorOverviewRuler.selectionHighlightForeground": s.accent,
        "editorOverviewRuler.addedForeground": s.success,
        "editorOverviewRuler.modifiedForeground": s.info,
        "editorOverviewRuler.deletedForeground": s.error,
        "editorStickyScroll.background": s.bg,
        "editorStickyScrollHover.background": s.bg_cursorline,
        # Schwebende Fenster
        "editorWidget.background": s.bg_float,
        "editorWidget.foreground": s.fg,
        "editorWidget.border": s.border,
        "editorHoverWidget.background": s.bg_float,
        "editorHoverWidget.foreground": s.fg,
        "editorHoverWidget.border": s.border,
        "editorHoverWidget.statusBarBackground": s.bg_elevated,
        "editorSuggestWidget.background": s.bg_float,
        "editorSuggestWidget.foreground": s.fg,
        "editorSuggestWidget.border": s.border,
        "editorSuggestWidget.highlightForeground": s.accent,
        "editorSuggestWidget.focusHighlightForeground": s.accent,
        "editorSuggestWidget.selectedBackground": s.bg_elevated,
        "editorSuggestWidget.selectedForeground": s.fg,
        "editorSuggestWidget.selectedIconForeground": s.fg,
        "peekView.border": s.accent,
        "peekViewEditor.background": s.bg_float,
        "peekViewEditor.matchHighlightBackground": _alpha(s.number, search),
        "peekViewResult.background": chrome,
        "peekViewResult.fileForeground": s.fg,
        "peekViewResult.lineForeground": s.fg_dim,
        "peekViewResult.matchHighlightBackground": _alpha(s.number, search),
        "peekViewResult.selectionBackground": _alpha(s.accent, list_selection),
        "peekViewResult.selectionForeground": s.fg,
        "peekViewTitle.background": chrome,
        "peekViewTitleLabel.foreground": s.fg,
        "peekViewTitleDescription.foreground": s.fg_dim,
        "quickInput.background": s.bg_float,
        "quickInput.foreground": s.fg,
        "quickInputTitle.background": s.bg_elevated,
        "pickerGroup.foreground": s.accent,
        "pickerGroup.border": s.border,
        "menu.background": s.bg_float,
        "menu.foreground": s.fg,
        "menu.selectionBackground": s.bg_elevated,
        "menu.selectionForeground": s.fg,
        "menu.separatorBackground": s.border,
        "menu.border": s.border,
        "notifications.background": s.bg_float,
        "notifications.foreground": s.fg,
        "notifications.border": s.border,
        "notificationCenterHeader.background": s.bg_elevated,
        "notificationCenterHeader.foreground": s.fg,
        "notificationLink.foreground": s.info,
        "notificationsErrorIcon.foreground": s.error,
        "notificationsWarningIcon.foreground": s.warning,
        "notificationsInfoIcon.foreground": s.info,
        # Listen und Baeume
        "list.activeSelectionBackground": _alpha(s.accent, list_selection),
        "list.activeSelectionForeground": s.fg,
        "list.activeSelectionIconForeground": s.fg,
        "list.inactiveSelectionBackground": _alpha(s.accent, list_selection * 0.5),
        "list.inactiveSelectionForeground": s.fg,
        "list.focusBackground": _alpha(s.accent, list_selection),
        "list.focusForeground": s.fg,
        "list.focusOutline": s.accent,
        "list.hoverBackground": _alpha(s.fg, 0.07),
        "list.hoverForeground": s.fg,
        "list.highlightForeground": s.accent,
        "list.focusHighlightForeground": s.accent,
        "list.errorForeground": s.error,
        "list.warningForeground": s.warning,
        "list.dropBackground": _alpha(s.accent, 0.2),
        "tree.indentGuidesStroke": mix(chrome, s.fg, 0.25),
        # Titelzeile, Aktivitaetsleiste, Seitenleiste
        "titleBar.activeBackground": deep,
        "titleBar.activeForeground": s.fg,
        "titleBar.inactiveBackground": deep,
        "titleBar.inactiveForeground": s.fg_dim,
        "titleBar.border": _alpha(s.fg, 0.0),
        "commandCenter.background": chrome,
        "commandCenter.foreground": s.fg_dim,
        "commandCenter.border": s.border,
        "commandCenter.activeBackground": s.bg_float,
        "commandCenter.activeForeground": s.fg,
        "activityBar.background": deep,
        "activityBar.foreground": s.fg,
        "activityBar.inactiveForeground": s.fg_faint,
        "activityBar.activeBorder": s.accent,
        "activityBar.border": _alpha(s.fg, 0.0),
        "activityBarBadge.background": s.accent,
        "activityBarBadge.foreground": on_accent,
        "sideBar.background": chrome,
        "sideBar.foreground": s.fg,
        "sideBar.border": deep,
        "sideBarTitle.foreground": s.fg,
        "sideBarSectionHeader.background": chrome,
        "sideBarSectionHeader.foreground": s.fg,
        "sideBarSectionHeader.border": mix(chrome, s.fg, 0.12),
        # Reiter
        "editorGroupHeader.tabsBackground": chrome,
        "editorGroupHeader.tabsBorder": _alpha(s.fg, 0.0),
        "editorGroup.border": deep,
        "editorGroup.dropBackground": _alpha(s.accent, 0.2),
        "tab.activeBackground": s.bg,
        "tab.activeForeground": s.fg,
        "tab.activeBorderTop": s.accent,
        "tab.activeBorder": s.bg,
        "tab.inactiveBackground": chrome,
        "tab.inactiveForeground": s.fg_dim,
        "tab.hoverBackground": s.bg_cursorline,
        "tab.border": chrome,
        "tab.unfocusedActiveForeground": s.fg_dim,
        "tab.unfocusedInactiveForeground": s.fg_faint,
        "tab.unfocusedActiveBorderTop": s.border,
        "breadcrumb.background": s.bg,
        "breadcrumb.foreground": s.fg_dim,
        "breadcrumb.focusForeground": s.fg,
        "breadcrumb.activeSelectionForeground": s.accent,
        "breadcrumbPicker.background": s.bg_float,
        # Panel und Terminal
        "panel.background": chrome,
        "panel.border": deep,
        "panelTitle.activeBorder": s.accent,
        "panelTitle.activeForeground": s.fg,
        "panelTitle.inactiveForeground": s.fg_dim,
        "panelSection.border": deep,
        "terminal.background": chrome,
        "terminal.foreground": s.fg,
        "terminal.selectionBackground": _alpha(s.accent, list_selection),
        "terminalCursor.foreground": s.accent,
        # Statusleiste traegt die Leitfarbe, wie die Statuszeile in Neovim
        "statusBar.background": s.statusline_bg,
        "statusBar.foreground": s.statusline_fg,
        "statusBar.border": s.statusline_bg,
        "statusBar.noFolderBackground": s.bg_elevated,
        "statusBar.noFolderForeground": s.fg,
        "statusBar.debuggingBackground": s.warning,
        "statusBar.debuggingForeground": on_warning,
        "statusBarItem.hoverBackground": _alpha(s.statusline_fg, 0.12),
        "statusBarItem.remoteBackground": s.accent,
        "statusBarItem.remoteForeground": on_accent,
        "statusBarItem.errorBackground": s.error,
        "statusBarItem.errorForeground": on_error,
        "statusBarItem.warningBackground": s.warning,
        "statusBarItem.warningForeground": on_warning,
        # Eingaben und Knoepfe
        "input.background": input_bg,
        "input.foreground": s.fg,
        "input.border": s.border,
        "input.placeholderForeground": s.fg_faint,
        "inputOption.activeBorder": s.accent,
        "inputOption.activeBackground": _alpha(s.accent, 0.2),
        "inputValidation.errorBorder": s.error,
        "inputValidation.errorBackground": s.bg_float,
        "inputValidation.warningBorder": s.warning,
        "inputValidation.warningBackground": s.bg_float,
        "inputValidation.infoBorder": s.info,
        "inputValidation.infoBackground": s.bg_float,
        "dropdown.background": input_bg,
        "dropdown.foreground": s.fg,
        "dropdown.border": s.border,
        "dropdown.listBackground": s.bg_float,
        "checkbox.background": input_bg,
        "checkbox.border": s.border,
        "button.background": s.accent,
        "button.foreground": on_accent,
        "button.hoverBackground": mix(s.accent, on_accent, 0.12),
        "button.secondaryBackground": s.bg_elevated,
        "button.secondaryForeground": s.fg,
        "button.secondaryHoverBackground": mix(s.bg_elevated, s.fg, 0.1),
        "badge.background": s.accent,
        "badge.foreground": on_accent,
        "progressBar.background": s.accent,
        "scrollbar.shadow": _alpha("#000000", 0.3 if s.dark else 0.1),
        "scrollbarSlider.background": _alpha(s.fg, 0.15),
        "scrollbarSlider.hoverBackground": _alpha(s.fg, 0.25),
        "scrollbarSlider.activeBackground": _alpha(s.fg, 0.35),
        "minimap.findMatchHighlight": s.number,
        "minimap.selectionHighlight": _alpha(s.accent, 0.6),
        "minimap.errorHighlight": s.error,
        "minimap.warningHighlight": s.warning,
        # Diff und Zusammenfuehren
        "diffEditor.insertedTextBackground": _alpha(s.success, 0.18),
        "diffEditor.removedTextBackground": _alpha(s.error, 0.18),
        "diffEditor.insertedLineBackground": _alpha(s.success, 0.09),
        "diffEditor.removedLineBackground": _alpha(s.error, 0.09),
        "merge.currentHeaderBackground": _alpha(s.success, 0.35),
        "merge.currentContentBackground": _alpha(s.success, 0.12),
        "merge.incomingHeaderBackground": _alpha(s.info, 0.35),
        "merge.incomingContentBackground": _alpha(s.info, 0.12),
        # Git
        "gitDecoration.addedResourceForeground": s.success,
        "gitDecoration.modifiedResourceForeground": s.info,
        "gitDecoration.deletedResourceForeground": s.error,
        "gitDecoration.untrackedResourceForeground": s.success,
        "gitDecoration.conflictingResourceForeground": s.warning,
        "gitDecoration.ignoredResourceForeground": s.fg_faint,
        "gitDecoration.renamedResourceForeground": s.hint,
        "gitDecoration.submoduleResourceForeground": s.type_,
        # Debug
        "debugToolBar.background": s.bg_float,
        "editor.stackFrameHighlightBackground": _alpha(s.warning, 0.15),
        "editor.focusedStackFrameHighlightBackground": _alpha(s.success, 0.15),
        # Terminalfarben
        **{f"terminal.ansi{name}": color for name, color in zip(_ANSI, s.terminal, strict=True)},
    }


_ANSI = (
    "Black",
    "Red",
    "Green",
    "Yellow",
    "Blue",
    "Magenta",
    "Cyan",
    "White",
    "BrightBlack",
    "BrightRed",
    "BrightGreen",
    "BrightYellow",
    "BrightBlue",
    "BrightMagenta",
    "BrightCyan",
    "BrightWhite",
)


def _token(name: str, scope: list[str], color: str | None = None, style: str | None = None) -> dict[str, Any]:
    settings: dict[str, str] = {}
    if color is not None:
        settings["foreground"] = color
    if style is not None:
        settings["fontStyle"] = style
    return {"name": name, "scope": scope, "settings": settings}


def token_colors(scheme: Scheme) -> list[dict[str, Any]]:
    """TextMate-Regeln. Spaetere Regeln gewinnen bei gleicher Spezifitaet, Spezielles steht unten."""
    s = scheme
    return [
        _token("Text", ["source", "text"], s.fg),
        _token(
            "Comment",
            ["comment", "punctuation.definition.comment", "string.quoted.docstring"],
            s.comment,
            "italic",
        ),
        _token(
            "Keyword",
            [
                "keyword",
                "keyword.control",
                "storage.type",
                "storage.modifier",
                "keyword.other",
                "variable.language",
                "keyword.operator.new",
                "keyword.operator.expression",
            ],
            s.keyword,
        ),
        _token("Operator", ["keyword.operator", "punctuation.accessor"], s.operator),
        _token("Punctuation", ["punctuation", "meta.brace"], s.operator),
        _token("String", ["string", "punctuation.definition.string"], s.string),
        _token(
            "Escape and regex",
            ["constant.character.escape", "string.regexp", "constant.other.placeholder", "constant.character.format"],
            s.special,
        ),
        _token(
            "Number and constant",
            [
                "constant.numeric",
                "constant.language",
                "constant.character",
                "support.constant",
                "variable.other.constant",
                "variable.other.enummember",
                "entity.name.constant",
            ],
            s.number,
        ),
        _token("Variable", ["variable", "variable.other", "variable.parameter", "meta.definition.variable"], s.fg),
        _token(
            "Property",
            ["variable.other.property", "variable.other.object.property", "support.variable.property"],
            s.fg,
        ),
        _token(
            "Function",
            ["entity.name.function", "meta.function-call.generic", "support.function.magic", "entity.name.method"],
            s.function,
        ),
        _token("Builtin function", ["support.function"], s.special),
        _token(
            "Type",
            [
                "entity.name.type",
                "entity.name.class",
                "entity.name.struct",
                "entity.name.interface",
                "entity.name.enum",
                "entity.other.inherited-class",
                "support.type",
                "support.class",
                "entity.name.namespace",
                "entity.name.module",
            ],
            s.type_,
        ),
        _token(
            "Builtin type",
            ["keyword.type", "storage.type.primitive", "support.type.primitive", "support.type.builtin"],
            s.type_,
            "italic",
        ),
        _token(
            "Decorator and attribute",
            [
                "meta.decorator",
                "punctuation.decorator",
                "storage.type.annotation",
                "meta.attribute",
                "entity.name.function.decorator",
            ],
            s.special,
        ),
        _token("Tag", ["entity.name.tag", "punctuation.definition.tag"], s.keyword),
        _token("Tag attribute", ["entity.other.attribute-name"], s.function, "italic"),
        _token("Object key", ["support.type.property-name", "meta.object-literal.key"], s.function),
        _token("Label", ["entity.name.label"], s.keyword),
        _token("Invalid", ["invalid", "invalid.illegal"], s.error),
        _token("Deprecated", ["invalid.deprecated"], s.warning, "strikethrough"),
        # Markdown und andere Auszeichnung
        _token("Heading", ["markup.heading", "entity.name.section", "markup.heading.setext"], s.accent, "bold"),
        _token("Bold", ["markup.bold"], None, "bold"),
        _token("Italic", ["markup.italic"], None, "italic"),
        _token("Strikethrough", ["markup.strikethrough"], None, "strikethrough"),
        _token("Link", ["markup.underline.link", "string.other.link"], s.info),
        _token("Code", ["markup.inline.raw", "markup.fenced_code", "markup.raw"], s.string),
        _token("Quote", ["markup.quote"], s.comment, "italic"),
        _token("List marker", ["punctuation.definition.list.begin.markdown", "markup.list"], s.special),
        _token("Inserted", ["markup.inserted"], s.success),
        _token("Deleted", ["markup.deleted"], s.error),
        _token("Changed", ["markup.changed"], s.warning),
    ]


def semantic_token_colors(scheme: Scheme) -> dict[str, Any]:
    """Farben fuer semantische Token, die Sprachserver wie C#, TypeScript oder Python liefern."""
    s = scheme
    return {
        "namespace": s.type_,
        "type": s.type_,
        "class": s.type_,
        "struct": s.type_,
        "interface": s.type_,
        "enum": s.type_,
        "typeParameter": {"foreground": s.type_, "italic": True},
        "enumMember": s.number,
        "function": s.function,
        "method": s.function,
        "function.defaultLibrary": s.special,
        "macro": s.special,
        "decorator": s.special,
        "keyword": s.keyword,
        "variable": s.fg,
        "variable.readonly": s.number,
        "variable.defaultLibrary": s.special,
        "parameter": s.fg,
        "property": s.fg,
        "property.readonly": s.fg,
        "string": s.string,
        "number": s.number,
        "regexp": s.special,
        "operator": s.operator,
        "comment": {"foreground": s.comment, "italic": True},
        "*.deprecated": {"strikethrough": True},
    }


def render(scheme: Scheme) -> dict[str, Any]:
    """Erzeugt das vollstaendige Theme als JSON-Objekt."""
    return {
        "$schema": "vscode://schemas/color-theme",
        "name": label(scheme.name),
        "type": "dark" if scheme.dark else "light",
        "semanticHighlighting": True,
        "colors": ui_colors(scheme),
        "tokenColors": token_colors(scheme),
        "semanticTokenColors": semantic_token_colors(scheme),
    }


def write(scheme: Scheme, target_dir: Path) -> Path:
    """Schreibt das Theme nach `<target_dir>/<name>.json` und gibt den Pfad zurueck."""
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{scheme.name}.json"
    text = json.dumps(render(scheme), indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def package_entry(scheme: Scheme) -> dict[str, str]:
    """Eintrag fuer `contributes.themes` in der package.json."""
    return {
        "label": label(scheme.name),
        "uiTheme": "vs-dark" if scheme.dark else "vs",
        "path": f"./themes/{scheme.name}.json",
    }


def min_syntax_distance(scheme: Scheme) -> float:
    """Kleinster Farbabstand zweier Syntaxrollen, fuer den Bericht."""
    syntax = (scheme.keyword, scheme.function, scheme.string, scheme.number, scheme.type_, scheme.special)
    return min(delta_e(a, b) for i, a in enumerate(syntax) for b in syntax[i + 1 :])
