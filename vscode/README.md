# Retro Themes

41 colour themes, 36 dark and 5 light: vintage 8-bit, terminal phosphor, Unix workstation, watch,
comic-pulp, 80s-pastel and mafia-noir palettes. Built from the retro palettes of
[textual-themes](https://github.com/michaelblaess/textual-themes) and tuned for reading code.

The same themes exist for Neovim and Visual Studio 2026, from the same derivation, in
[retro-coding-themes](https://github.com/michaelblaess/retro-coding-themes).

The colours are not copied one to one. A palette made for a TUI has small text fields, an editor
is one large text surface. Every colour is therefore checked and lifted until it is readable, and
syntax colours that would look alike are pulled apart.

![Retro — Synthwave](https://raw.githubusercontent.com/michaelblaess/retro-coding-themes/main/docs/vscode/vorschau/synthwave.png)

Synthwave on top, below it Classic Terminal and Clipper.
**[See all 41 themes](https://github.com/michaelblaess/retro-coding-themes/blob/main/docs/vscode/vorschau.md)**

![Retro — Classic Terminal](https://raw.githubusercontent.com/michaelblaess/retro-coding-themes/main/docs/vscode/vorschau/classic-terminal.png)

![Retro — Clipper](https://raw.githubusercontent.com/michaelblaess/retro-coding-themes/main/docs/vscode/vorschau/clipper.png)

## Install

Open the Extensions view (`Ctrl+Shift+X`), search for **Retro Themes** by Michael Blaess and
install it, or from a terminal:

```
code --install-extension michaelblaess.retro-themes
```

Then open the Command Palette (`Ctrl+Shift+P`), choose **Preferences: Color Theme** and pick any
theme starting with **Retro**.

## The rules behind the colours

- **Readable first.** Text and syntax reach a contrast of at least 4.5:1 on the editor, the current
  line and the hover windows, line numbers at least 3:1.
- **The surface moves away from the text** until the body text reaches 8:1.
- **Syntax colours stay apart**, from each other and from the body text, at least 22 in CIE76.
- **Red is for errors.** No syntax colour sits in the red range, unless red is the theme's lead
  colour.
- **Text on coloured surfaces** such as buttons, badges and the status bar always takes the colour
  with the highest contrast.

## Liability

These themes are a hobby project and come without any warranty, exactly as the Apache-2.0 licence
describes. They change how the editor looks, nothing else. Use them at your own risk.

## Trade marks and names

The theme names allude to machines, desktops and films. They name colour palettes, not anyone
else's products, and there is no connection to their owners. This extension is not affiliated with
Microsoft.

Microsoft, Visual Studio and Visual Studio Code are trademarks of the Microsoft group of companies.
Any other trade marks mentioned belong to their respective owners.

## Licence

Apache-2.0.
