# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Folio's Windows onedir build (issue #14).

Run from the repo root (installer/build.ps1 does this):

    python -m PyInstaller --noconfirm --clean Folio.spec

Output: dist/Folio/Folio.exe plus dist/Folio/_internal/ — the tree that
installer/folio.iss wraps into the setup executable.
"""

from pathlib import Path
import re

ROOT = Path(SPECPATH)

# ---------------------------------------------------------------------------
# Version metadata — single source of truth is utils/constants.py. Parsed,
# not imported: importing would drag reportlab into the spec's interpreter.
# ---------------------------------------------------------------------------
_constants_src = (ROOT / "utils" / "constants.py").read_text(encoding="utf-8")


def _const(name: str, default: str) -> str:
    m = re.search(rf'{name}\s*:\s*str\s*=\s*"([^"]*)"', _constants_src)
    return m.group(1) if m else default


APP_NAME = _const("APP_NAME", "Folio")
APP_VERSION = _const("APP_VERSION", "0.1.0")
AUTHOR = _const("AUTHOR", "Aaqil")
DESCRIPTION = _const("DESCRIPTION", "Turn any PDF into a print-ready booklet")
WEBSITE_URL = _const("WEBSITE_URL", "https://github.com/Aaqil101/Folio")

# Windows wants a four-part version (x.y.z.0 for a three-part release).
_file_version = ".".join((*APP_VERSION.split("."), "0")[-4:])

# Written into build/ (gitignored) rather than committed, so bumping
# APP_VERSION can never leave a stale version resource behind.
_version_txt = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({APP_VERSION.replace('.', ', ')}, 0),
    prodvers=({APP_VERSION.replace('.', ', ')}, 0),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', '{AUTHOR}'),
            StringStruct('FileDescription', '{DESCRIPTION}'),
            StringStruct('FileVersion', '{_file_version}'),
            StringStruct('InternalName', '{APP_NAME}'),
            StringStruct('LegalCopyright', '{AUTHOR}'),
            StringStruct('OriginalFilename', '{APP_NAME}.exe'),
            StringStruct('ProductName', '{APP_NAME}'),
            StringStruct('ProductVersion', '{APP_VERSION}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
_version_path = ROOT / "build" / "file_version_info.txt"
_version_path.parent.mkdir(parents=True, exist_ok=True)
_version_path.write_text(_version_txt, encoding="utf-8")

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    # assets/ rides along for utils/resources.py's file-system fallback; the
    # compiled resources_rc (hiddenimport below) is the primary path.
    datas=[(str(ROOT / "assets"), "assets")],
    # resources.py imports this inside try/except — declare it so the
    # static analysis can never miss it and silently ship the fallback path.
    hiddenimports=["resources_rc"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Dev-only tooling — exercised via `python -m core.<module>`, never
        # imported by main.py; excludes keep accidental edges out.
        "core.generate_test_pdf",
        "core.generate_test_images",
        "core.manual_test_suite",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "application" / "folio.ico"),
    version=str(_version_path),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
