"""Leitet aus den elf Grundfarben eines Themes die Farbrollen ab, gemeinsam fuer alle Editoren.

Zwei Regeln bestimmen alles Weitere:

* **Lesbarkeit geht vor Treue zur Palette.** Jede Schriftfarbe wird so lange aufgehellt, bis sie
  auf allen Flaechen, auf denen sie vorkommt, den Mindestkontrast erreicht. Farbton und
  Saettigung bleiben dabei erhalten, das Theme behaelt also seinen Charakter.
* **Syntaxfarben muessen unterscheidbar sein.** Mehrere Themes benutzen dieselbe Farbe fuer
  primary und accent oder setzen secondary gleich background. Kommen sich zwei Rollen zu nah,
  wird die naechste Farbe aus einer Kandidatenliste genommen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .color import (
    contrast,
    delta_e,
    fill_for_text,
    hue,
    lightness,
    mix,
    readable_on_all,
    saturation,
    with_hue_shift,
    with_lightness,
)
from .palettes import Base

# Mindestkontrast fuer Fliesstext und Syntax, WCAG AA fuer normalen Text
TEXT_TARGET = 4.5
# Mindestkontrast fuer Nebensaechliches wie Zeilennummern und Trennlinien
DIM_TARGET = 3.0
# Ab diesem Farbabstand (CIE76) gelten zwei Syntaxfarben als unterscheidbar
DISTINCT = 22.0
# Mindestkontrast zwischen Text und Editorflaeche. Hoeher als AA, weil darauf noch sechs
# Syntaxfarben Platz finden muessen - sonst laufen sie alle gegen Weiss bzw. gegen Schwarz.
BG_TARGET = 8.0
# Obergrenze fuer Syntaxfarben. Ohne sie landet eine ausweichende Farbe im hellen Theme fast bei
# Schwarz und im dunklen fast bei Weiss - lesbar, aber ohne Farbe.
MAX_CONTRAST = 13.0
# Unter diesem Farbabstand (CIE76) zur Fehlerfarbe gilt eine Leitfarbe als rot
RED_LEAD = 25.0
# Rotbereich im Farbkreis (Grad) und Mindestsaettigung, ab der eine Farbe als Fehlerrot gilt
RED_HUE_FROM = 345.0
RED_HUE_TO = 15.0
RED_SATURATION = 0.45


@dataclass(frozen=True, slots=True)
class Scheme:
    """Alle Farben, die der Erzeuger fuer ein Theme braucht."""

    name: str
    base: Base
    dark: bool
    # Flaechen
    bg: str
    bg_cursorline: str
    bg_float: str
    bg_elevated: str
    bg_visual: str
    border: str
    # Schrift
    fg: str
    fg_dim: str
    fg_faint: str
    comment: str
    # Syntax
    keyword: str
    function: str
    string: str
    number: str
    type_: str
    special: str
    operator: str
    # Zustaende
    accent: str
    error: str
    warning: str
    info: str
    hint: str
    success: str
    statusline_bg: str
    statusline_fg: str
    terminal: list[str] = field(default_factory=list)

    @property
    def text_surfaces(self) -> tuple[str, ...]:
        """Flaechen, auf denen Fliesstext und Syntax stehen koennen."""
        return (self.bg, self.bg_cursorline, self.bg_float)


def _readable(color: str, surfaces: tuple[str, ...], target: float) -> str:
    """Wie `readable_on_all`, weicht aber auf Weiss aus, statt abzubrechen."""
    try:
        return readable_on_all(color, list(surfaces), target)
    except ValueError:
        return "#FFFFFF"


def _distance(color: str, taken: list[str]) -> float:
    return min((delta_e(color, other) for other in taken), default=100.0)


def is_red(color: str) -> bool:
    """Liegt die Farbe im Rotbereich, der nach Fehlermeldung aussieht?

    Gemessen am Farbton, nicht am Farbabstand: CIE76 haelt ein kraeftiges Rot wie #FF4864 fuer weit
    entfernt vom Fehlerrot und ein harmloses Orange fuer nah dran.
    """
    return (hue(color) >= RED_HUE_FROM or hue(color) <= RED_HUE_TO) and saturation(color) >= RED_SATURATION


def _pick(
    candidates: list[str],
    taken: list[str],
    surfaces: tuple[str, ...],
    reserve: tuple[str, ...] = (),
    rot_meiden: bool = False,
) -> str:
    """Waehlt die erste lesbare Kandidatenfarbe, die zu den vergebenen genug Abstand hat.

    Reicht keine, wird in dieser Reihenfolge ausgewichen:

    1. Die beste Kandidatin in der Helligkeit verschieben. Das haelt den Farbton und ist der
       einzige Weg, der bei einfarbigen Themes wie einem Phosphor-Terminal ueberhaupt bleibt.
    2. Die uebrigen Farben der Palette. Ein Grau laesst sich im Farbton nicht drehen, und die
       Palette passt besser zum Theme als ein gedrehter Farbton.
    3. Den Farbton der besten Kandidatin drehen.

    Jede Ausweichfarbe bleibt unter MAX_CONTRAST, sonst landet sie fast bei Schwarz oder Weiss.
    """
    readable = [_readable(color, surfaces, TEXT_TARGET) for color in candidates]
    def frei(color: str) -> bool:
        return _distance(color, taken) >= DISTINCT and not (rot_meiden and is_red(color))

    for color in readable:
        if frei(color):
            return color

    best = max(readable, key=lambda color: _distance(color, taken))
    base_lightness = lightness(best)
    variants: list[str] = []
    for step in range(1, 26):
        for direction in (1, -1):
            variants.append(with_lightness(best, base_lightness + direction * step * 0.02))
    variants.extend(reserve)
    # Ein Grau laesst sich im Farbton nicht drehen. Dann wird die gesaettigtste Farbe gedreht,
    # die Kandidaten und Reserve hergeben (next fand sonst nur Grau fuer seine Typen).
    drehbasis = best if saturation(best) >= 0.2 else max((*candidates, *reserve), key=saturation)
    for degrees in range(10, 190, 10):
        for direction in (1, -1):
            variants.append(with_hue_shift(drehbasis, direction * degrees))
    ausweichend: list[str] = []
    for variant in variants:
        candidate = _readable(variant, surfaces, TEXT_TARGET)
        if not frei(candidate):
            continue
        if contrast(candidate, surfaces[0]) <= MAX_CONTRAST:
            return candidate
        ausweichend.append(candidate)
    return ausweichend[0] if ausweichend else best


def _on(color: str, options: tuple[str, ...]) -> str:
    """Schriftfarbe auf einer farbigen Flaeche: die mit dem hoechsten Kontrast."""
    return max(options, key=lambda option: contrast(color, option))


def derive(base: Base) -> Scheme:
    """Baut aus den Grundfarben eines Themes das vollstaendige Farbschema, hell wie dunkel."""
    fg = base.foreground
    # Die Paletten kommen aus Oberflaechen mit kleinen Textfeldern. Ein Editor ist eine einzige
    # grosse Textflaeche, deshalb wird die Flaeche vom Text weggezogen, bis genug Raum da ist:
    # ein dunkles Theme wird dunkler, ein helles heller. Der Farbton bleibt.
    bg = base.background
    if contrast(fg, bg) < BG_TARGET:
        bg = fill_for_text(bg, fg, BG_TARGET) or mix(bg, "#000000" if base.dark else "#FFFFFF", 0.6)

    # Flaechen entstehen aus dem Hintergrund, damit sie den Farbton des Themes behalten.
    # surface und panel taugen dafuer nicht: sie sind in einigen Themes greller als der Text.
    bg_cursorline = mix(bg, fg, 0.07)
    bg_float = mix(bg, fg, 0.10)
    bg_elevated = mix(bg, fg, 0.18)
    border = _readable(mix(bg, fg, 0.35), (bg, bg_float), DIM_TARGET)

    # Auswahl so kraeftig wie moeglich, aber der Text darauf muss lesbar bleiben
    bg_visual = mix(bg, base.accent, 0.35)
    while contrast(fg, bg_visual) < TEXT_TARGET and delta_e(bg_visual, bg) > 2:
        bg_visual = mix(bg_visual, bg, 0.2)

    # Syntax steht auf dem Hintergrund, der Cursorzeile und in Fenstern - nicht auf der
    # hervorgehobenen Flaeche, dort setzen die Gruppen ihre Schriftfarbe selbst
    surfaces = (bg, bg_cursorline, bg_float)
    fg_dim = _readable(mix(fg, bg, 0.35), surfaces, TEXT_TARGET)
    fg_faint = _readable(mix(fg, bg, 0.55), surfaces, DIM_TARGET)
    comment = _readable(mix(fg, base.secondary, 0.5), surfaces, TEXT_TARGET)

    # Rot ist fuer Fehler da. Eine Syntaxfarbe in der Fehlerfarbe liest sich wie eine Meldung
    # (Michael, 25.09.2026, an classic-terminal: rote Typen). Deshalb gilt die Fehlerfarbe als
    # vergeben - ausser bei Themes, deren Leitfarbe selbst rot ist, dort ist Rot der Charakter.
    fehler = _readable(base.error, surfaces, TEXT_TARGET)
    rote_leitfarbe = min(delta_e(base.primary, base.error), delta_e(base.accent, base.error)) < RED_LEAD
    belegt = [fg] if rote_leitfarbe else [fg, fehler]
    meiden = not rote_leitfarbe

    # Uebrige Farben der Palette, falls keine Kandidatin Abstand haelt
    reserve: tuple[str, ...] = (base.boost, base.warning, base.success, base.primary, base.accent, base.secondary)
    if rote_leitfarbe:
        reserve += (base.error,)

    # Reihenfolge ist Absicht: Schluesselwoerter zuerst, sie tragen das Theme. Die Textfarbe
    # gilt von Anfang an als vergeben - eine Syntaxfarbe, die aussieht wie Fliesstext, hebt
    # nichts hervor (classic-terminal hatte Funktionen in exakt der Textfarbe).
    keyword = _pick([base.accent, base.primary, base.boost], belegt, surfaces, reserve, meiden)
    taken = [*belegt, keyword]
    function = _pick(
        [base.primary, base.boost, base.secondary, mix(base.accent, base.success, 0.5)],
        taken,
        surfaces,
        reserve,
        meiden,
    )
    taken.append(function)
    string = _pick(
        [base.success, mix(base.success, base.accent, 0.35), base.secondary], taken, surfaces, reserve, meiden
    )
    taken.append(string)
    number = _pick([base.warning, mix(base.warning, base.error, 0.35), base.boost], taken, surfaces, reserve, meiden)
    taken.append(number)
    type_ = _pick(
        [base.secondary, base.boost, mix(base.primary, base.success, 0.5), mix(base.accent, fg, 0.45)],
        taken,
        surfaces,
        reserve,
        meiden,
    )
    taken.append(type_)
    special = _pick(
        [base.boost, mix(base.error, base.warning, 0.5), mix(base.primary, base.accent, 0.5), base.error],
        taken,
        surfaces,
        reserve,
        meiden,
    )

    operator = _readable(mix(fg, bg, 0.2), surfaces, TEXT_TARGET)
    accent = _readable(base.accent, surfaces, TEXT_TARGET)
    error = _readable(base.error, surfaces, TEXT_TARGET)
    warning = _readable(base.warning, surfaces, TEXT_TARGET)
    success = _readable(base.success, surfaces, TEXT_TARGET)
    info = _readable(base.primary, surfaces, TEXT_TARGET)
    hint = _readable(mix(base.secondary, fg, 0.35), surfaces, TEXT_TARGET)

    # Die Statuszeile traegt die Leitfarbe, wie in den Oberflaechen der Vorbilder
    statusline_bg = base.primary
    statusline_fg = _on(statusline_bg, (bg, fg, "#000000", "#FFFFFF"))

    # Die zweite Haelfte der Terminalfarben ist die "helle" Variante. Auf einer hellen Flaeche
    # waere sie nicht mehr zu sehen, dort wird stattdessen nachgedunkelt.
    betont = "#FFFFFF" if base.dark else "#000000"
    terminal = [
        mix(bg, fg, 0.25 if base.dark else 0.9),  # 0 schwarz
        error,
        success,
        warning,
        info,
        special,
        keyword,
        fg_dim,
        mix(bg, fg, 0.45 if base.dark else 0.6),  # 8 helles schwarz
        mix(error, betont, 0.2),
        mix(success, betont, 0.2),
        mix(warning, betont, 0.2),
        mix(info, betont, 0.2),
        mix(special, betont, 0.2),
        mix(keyword, betont, 0.2),
        fg,
    ]

    return Scheme(
        name=base.name,
        base=base,
        dark=base.dark,
        bg=bg,
        bg_cursorline=bg_cursorline,
        bg_float=bg_float,
        bg_elevated=bg_elevated,
        bg_visual=bg_visual,
        border=border,
        fg=fg,
        fg_dim=fg_dim,
        fg_faint=fg_faint,
        comment=comment,
        keyword=keyword,
        function=function,
        string=string,
        number=number,
        type_=type_,
        special=special,
        operator=operator,
        accent=accent,
        error=error,
        warning=warning,
        info=info,
        hint=hint,
        success=success,
        statusline_bg=statusline_bg,
        statusline_fg=statusline_fg,
        terminal=terminal,
    )
