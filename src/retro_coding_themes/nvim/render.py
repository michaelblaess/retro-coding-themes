"""Schreibt ein Farbschema als Lua-Datei nach `colors/`."""

from __future__ import annotations

from pathlib import Path

from ..derive import Scheme
from .groups import Spec, build

KOPF = """-- {theme} - erzeugt von retro-coding-themes, nicht von Hand aendern.
-- Quelle: src/retro_coding_themes/data/{name}.json, Ableitung in derive.py.

vim.cmd("highlight clear")
if vim.fn.exists("syntax_on") == 1 then
  vim.cmd("syntax reset")
end

vim.o.background = "{hintergrund}"
vim.g.colors_name = "{theme}"

local hl = vim.api.nvim_set_hl
"""


def _lua_value(value: str | bool) -> str:
    return "true" if value is True else f'"{value}"'


def _lua_spec(spec: Spec) -> str:
    parts = [f"{key} = {_lua_value(value)}" for key, value in spec.items()]
    return "{ " + ", ".join(parts) + " }"


def render(scheme: Scheme) -> str:
    """Erzeugt den Lua-Quelltext eines Farbschemas."""
    theme = f"retro-{scheme.name}"
    lines = [KOPF.format(theme=theme, name=scheme.name, hintergrund="dark" if scheme.dark else "light")]
    for group, spec in build(scheme).items():
        lines.append(f'hl(0, "{group}", {_lua_spec(spec)})')
    lines.append("")
    for index, color in enumerate(scheme.terminal):
        lines.append(f'vim.g.terminal_color_{index} = "{color}"')
    return "\n".join(lines) + "\n"


def write(scheme: Scheme, target_dir: Path) -> Path:
    """Schreibt das Farbschema nach `<target_dir>/retro-<name>.lua` und gibt den Pfad zurueck."""
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"retro-{scheme.name}.lua"
    path.write_text(render(scheme), encoding="utf-8", newline="\n")
    return path
