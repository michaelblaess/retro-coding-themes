"""Packt die Themes in eine .vsix fuer Visual Studio 2026.

Ohne manifest.json und catalog.json lehnt der VSIX-Installer von VS 2026 das Paket mit "Die
Datei ist kein gueltiges VSIX-Paket" ab, belegt am 24.09.2026. Mit beiden lief die Installation
durch. Der Aufbau folgt dem Format, das das VS-SDK fuer VSIX v3 erzeugt.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ID = "michaelblaess.RetroCodingThemes"
TITLE = "Retro Coding Themes"
DESCRIPTION = "41 retro colour themes for Visual Studio 2026, tuned for readable contrast."
PUBLISHER = "Michael Blaess"
PKGDEF = "RetroCodingThemes.pkgdef"
# Nur VS 2026, eine zweite Version pflegt Michael nicht (25.09.2026)
VS_RANGE = "[18.0,19.0)"
EXTENSION_DIR = "[installdir]\\Common7\\IDE\\Extensions\\RetroCodingThemes"


def manifest_xml(version: str) -> str:
    """Das extension.vsixmanifest."""
    ziele = "\n".join(
        f'    <InstallationTarget Id="Microsoft.VisualStudio.{sku}" Version="{VS_RANGE}">'
        "<ProductArchitecture>amd64</ProductArchitecture></InstallationTarget>"
        for sku in ("Community", "Pro", "Enterprise")
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Id="{ID}" Version="{version}" Language="en-US" Publisher="{PUBLISHER}" />
    <DisplayName>{TITLE}</DisplayName>
    <Description>{DESCRIPTION}</Description>
    <MoreInfo>https://github.com/michaelblaess/retro-coding-themes</MoreInfo>
    <License>LICENSE</License>
    <Tags>theme, color theme, retro, dark, light</Tags>
  </Metadata>
  <Installation>
{ziele}
  </Installation>
  <Prerequisites>
    <Prerequisite Id="Microsoft.VisualStudio.Component.CoreEditor" Version="{VS_RANGE}"
                  DisplayName="Visual Studio core editor" />
  </Prerequisites>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.VsPackage" d:Source="File" Path="{PKGDEF}" />
  </Assets>
</PackageManifest>
"""


CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="pkgdef" ContentType="text/plain" />
  <Default Extension="json" ContentType="application/json" />
  <Override PartName="/LICENSE" ContentType="text/plain" />
</Types>
"""


def build(pkgdef_text: str, license_text: str, version: str, target: Path) -> Path:
    """Schreibt die .vsix nach `target` und gibt den Pfad zurueck."""
    dateien: dict[str, bytes] = {
        "extension.vsixmanifest": manifest_xml(version).encode("utf-8"),
        PKGDEF: pkgdef_text.encode("utf-8"),
        "LICENSE": license_text.encode("utf-8"),
    }
    groesse = sum(len(inhalt) for inhalt in dateien.values())
    manifest = {
        "id": ID,
        "version": version,
        "type": "Vsix",
        "vsixId": ID,
        "extensionDir": EXTENSION_DIR,
        "files": [
            {"fileName": "/" + name, "sha256": hashlib.sha256(inhalt).hexdigest().upper()}
            for name, inhalt in dateien.items()
        ],
        "installSizes": {"targetDrive": groesse},
        "dependencies": {"Microsoft.VisualStudio.Component.CoreEditor": VS_RANGE},
    }
    catalog = {
        "manifestVersion": "1.1",
        "info": {"id": f"{ID},version={version}", "manifestType": "Extension"},
        "packages": [
            {
                "id": f"Component.{ID}",
                "version": version,
                "type": "Component",
                "extension": True,
                "dependencies": {ID: version, "Microsoft.VisualStudio.Component.CoreEditor": VS_RANGE},
                "localizedResources": [{"language": "en-US", "title": TITLE, "description": DESCRIPTION}],
            },
            {
                "id": ID,
                "version": version,
                "type": "Vsix",
                "payloads": [{"fileName": target.name, "size": groesse}],
                "vsixId": ID,
                "extensionDir": EXTENSION_DIR,
                "installSizes": {"targetDrive": groesse},
            },
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        for name, inhalt in dateien.items():
            zf.writestr(name, inhalt)
        zf.writestr("manifest.json", json.dumps(manifest, separators=(",", ":")))
        zf.writestr("catalog.json", json.dumps(catalog, separators=(",", ":")))
    return target
