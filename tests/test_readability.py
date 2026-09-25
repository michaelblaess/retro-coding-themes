"""Prueft die Lesbarkeitszusagen an jedem einzelnen Theme."""

from __future__ import annotations

from dataclasses import replace

import pytest

from retro_coding_themes.color import contrast, delta_e, luminance, mix
from retro_coding_themes.derive import DIM_TARGET, DISTINCT, RED_LEAD, TEXT_TARGET, Scheme, derive, is_red
from retro_coding_themes.palettes import load_all

SCHEMES = [derive(base) for base in load_all()]
IDS = [scheme.name for scheme in SCHEMES]


def _syntax(scheme: Scheme) -> dict[str, str]:
    return {
        "keyword": scheme.keyword,
        "function": scheme.function,
        "string": scheme.string,
        "number": scheme.number,
        "type": scheme.type_,
        "special": scheme.special,
    }


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_syntax_readable_on_every_surface(scheme: Scheme) -> None:
    for role, color in _syntax(scheme).items():
        for surface in scheme.text_surfaces:
            assert contrast(color, surface) >= TEXT_TARGET, f"{scheme.name}: {role} auf {surface}"


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_text_readable_on_every_surface(scheme: Scheme) -> None:
    for role, color in (("fg", scheme.fg), ("fg_dim", scheme.fg_dim), ("comment", scheme.comment)):
        for surface in scheme.text_surfaces:
            assert contrast(color, surface) >= TEXT_TARGET, f"{scheme.name}: {role} auf {surface}"


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_dim_text_readable(scheme: Scheme) -> None:
    # Zeilennummern und Rahmen duerfen leiser sein, aber nicht verschwinden
    for role, color in (("fg_faint", scheme.fg_faint), ("border", scheme.border)):
        assert contrast(color, scheme.bg) >= DIM_TARGET, f"{scheme.name}: {role}"


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_text_readable_on_selection(scheme: Scheme) -> None:
    assert contrast(scheme.fg, scheme.bg_visual) >= TEXT_TARGET


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_syntax_colors_distinguishable(scheme: Scheme) -> None:
    roles = list(_syntax(scheme).items())
    for index, (role_a, color_a) in enumerate(roles):
        for role_b, color_b in roles[index + 1 :]:
            assert delta_e(color_a, color_b) >= DISTINCT, f"{scheme.name}: {role_a} und {role_b}"


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_statusline_readable(scheme: Scheme) -> None:
    assert contrast(scheme.statusline_fg, scheme.statusline_bg) >= TEXT_TARGET


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_light_and_dark_are_not_mixed_up(scheme: Scheme) -> None:
    # Das Kennzeichen waehlt Dark oder Light als Basis, es muss zur Flaeche passen
    heller_hintergrund = luminance(scheme.bg) > luminance(scheme.fg)
    assert heller_hintergrund != scheme.dark, scheme.name


def test_check_can_fail() -> None:
    # Gegenprobe: dieselbe Pruefung muss anschlagen, wenn eine Farbe absichtlich verdorben wird
    scheme = derive(load_all()[0])
    verdorben = replace(scheme, comment=mix(scheme.bg, scheme.fg, 0.05), keyword=scheme.function)
    assert contrast(verdorben.comment, verdorben.bg) < TEXT_TARGET
    assert delta_e(verdorben.keyword, verdorben.function) < DISTINCT


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_syntax_colors_differ_from_text(scheme: Scheme) -> None:
    # Eine Syntaxfarbe, die aussieht wie Fliesstext, hebt nichts hervor
    for role, color in _syntax(scheme).items():
        assert delta_e(color, scheme.fg) >= DISTINCT, f"{scheme.name}: {role} wie Text"


@pytest.mark.parametrize("scheme", SCHEMES, ids=IDS)
def test_no_error_red_in_syntax(scheme: Scheme) -> None:
    # Rot ist fuer Fehler da (Michael, 25.09.2026). Ausnahme: Themes mit roter Leitfarbe.
    base = scheme.base
    if min(delta_e(base.primary, base.error), delta_e(base.accent, base.error)) < RED_LEAD:
        pytest.skip("Leitfarbe selbst rot")
    for role, color in _syntax(scheme).items():
        assert not is_red(color), f"{scheme.name}: {role} {color} sieht aus wie ein Fehler"
        assert delta_e(color, scheme.error) >= DISTINCT, f"{scheme.name}: {role} wie Fehlerfarbe"


def test_red_check_can_fail() -> None:
    # Gegenprobe: die roten Typen, die classic-terminal vor dieser Regel hatte
    assert is_red("#FF4444")
    assert not is_red("#FF7722")
