# retro-coding-themes

<p align="center">
  <img src="docs/flags/gb.svg" height="13" alt=""> <a href="README.md">English</a> ·
  <img src="docs/flags/de.svg" height="13" alt=""> <b>Deutsch</b>
</p>

---

41 Farb-Themes zum Programmieren, 36 dunkle und 5 helle, gebaut aus den Retro-Paletten von
[textual-themes](https://github.com/michaelblaess/textual-themes). Eine Ableitung, drei Editoren:
Neovim, VS Code und Visual Studio 2026. Dasselbe Theme sieht überall gleich aus.

Die Farben sind nicht eins zu eins übernommen. Eine Palette für eine TUI hat kleine Textfelder,
ein Editor ist eine einzige große Textfläche. Jede Farbe wird deshalb geprüft und angehoben, bis
sie lesbar ist, und Syntaxfarben, die sich ähneln würden, werden auseinandergezogen.

![retro-synthwave in Neovim](docs/nvim/vorschau/retro-synthwave.png)

**Galerien:** [Neovim](docs/nvim/vorschau.de.md) · [VS Code](docs/vscode/vorschau.de.md)

## Installation

### Neovim

Dieses Repo ist das Plugin, die Farbschemata liegen in `colors/`. Mit `vim.pack` unter Neovim 0.12:

```lua
vim.pack.add({ "https://github.com/michaelblaess/retro-coding-themes" })
vim.cmd.colorscheme("retro-synthwave")
```

### VS Code

In den Erweiterungen nach **Retro Themes** von Michael Blaess suchen, oder:

```
code --install-extension michaelblaess.retro-themes
```

### Visual Studio 2026

Paket bauen und mit dem VSIX-Installer von Visual Studio 2026 installieren:

```
uv run python -m retro_coding_themes --vsix
"C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\VSIXInstaller.exe" dist\RetroCodingThemes-0.1.0.vsix
```

Danach unter **Extras > Optionen > Umgebung > Allgemein > Farbdesign** ein Theme wählen.

## Die Regeln hinter den Farben

- **Lesbarkeit zuerst.** Text und Syntax erreichen mindestens 4,5:1, Zeilennummern mindestens 3:1.
  Farbton und Sättigung bleiben, das Theme behält seinen Charakter.
- **Die Fläche rückt vom Text ab**, bis der Fließtext 8:1 erreicht.
- **Syntaxfarben bleiben unterscheidbar**, untereinander und zum Fließtext, mindestens 22 in CIE76.
- **Rot ist für Fehler da.** Keine Syntaxfarbe liegt im Rotbereich, es sei denn, Rot ist die
  Leitfarbe des Themes. Sonst sähe ein Klassenname aus wie eine Fehlermeldung.

Jede Regel prüft ein Test über alle 41 Themes.

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `src/retro_coding_themes/` | Paletten, Farbrechnung und die gemeinsame Ableitung |
| `src/retro_coding_themes/nvim/`, `vscode/`, `visualstudio/` | die Abbildung auf den jeweiligen Editor |
| `colors/` | Farbschemata für Neovim, erzeugt |
| `vscode/` | die Erweiterung für VS Code, Themes erzeugt |
| `visualstudio/` | die `.pkgdef` für Visual Studio, erzeugt |

```
uv run python -m retro_coding_themes            # alle drei Ziele schreiben
uv run python -m retro_coding_themes --report   # nur die Kontrasttabelle
uv run --extra dev pytest                       # jedes Theme prüfen
```

Die Themes für Visual Studio entstehen ohne das Visual Studio SDK. Das Format der `.pkgdef` ist
nicht dokumentiert. Es ist aus den mitgelieferten Themes gelesen und gegen den
`VsixColorCompiler` von Microsoft geprüft: Die Ausgabe ist Byte für Byte dieselbe, die
Referenzdateien liegen in `tests/referenz/`.

## Haftung

Die Themes sind Freizeitarbeit und werden ohne Gewähr bereitgestellt, so wie es die
Apache-2.0-Lizenz beschreibt. Sie ändern die Darstellung im Editor, sonst nichts. Wer sie
einsetzt, tut das auf eigenes Risiko.

## Marken und Namen

Die Namen der Themes stammen aus [textual-themes](https://github.com/michaelblaess/textual-themes)
und sind Anspielungen auf Rechner, Oberflächen und Filme, die mir etwas bedeuten. Sie bezeichnen
Farbpaletten, nicht die Erzeugnisse anderer, und es besteht keine Verbindung zu deren Inhabern.
Dieses Projekt steht in keiner Verbindung zu Microsoft oder zum Neovim-Projekt.

Microsoft, Visual Studio and Visual Studio Code are trademarks of the Microsoft group of companies.
Andere genannte Marken gehören ihren jeweiligen Inhabern.

## Lizenz

Apache-2.0.
