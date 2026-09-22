# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para "Sistema de Gestión de Personal".

Genera una carpeta distribuible (onedir) en dist/SistemaGestionPersonal
que luego se empaqueta en un instalador con Inno Setup:

    pyinstaller --noconfirm --clean spec/app.spec

El modo onedir evita la extracción a TEMP de cada arranque (onefile),
reduce falsos positivos antivirus y acelera el inicio.
"""

import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

spec_root = Path(SPEC).resolve().parent
project_root = spec_root.parent

app_name = "SistemaGestionPersonal"
icono = str(project_root / "assets" / "app.ico")

# Los recursos de icono y versión solo se incrustan en Windows; en Linux
# se omiten para que el mismo spec compile en ambos.
IS_WINDOWS = sys.platform.startswith("win")

# ---------------------------------------------------------------------------
# Recurso de versión de Windows generado dinámicamente desde VERSION,
# para que el ejecutable muestre SIEMPRE la versión real (antes quedaba
# fija en 1.0.3 dentro de spec/version_info.txt).
# ---------------------------------------------------------------------------
def _version_tupla(texto: str) -> tuple:
    """'2.79' -> (2, 79, 0, 0); '2.79.55' -> (2, 79, 55, 0)."""
    numeros = [int(p) for p in re.split(r"[^\d]+", texto.strip()) if p]
    while len(numeros) < 4:
        numeros.append(0)
    return tuple(numeros[:4])


version_texto = (project_root / "VERSION").read_text(encoding="utf-8").strip()
vers = _version_tupla(version_texto)

if IS_WINDOWS:
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    version_resource = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=vers,
            prodvers=vers,
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        u'040904B0',
                        [
                            StringStruct(u'CompanyName', u'LiebeBlack'),
                            StringStruct(u'FileDescription', u'Sistema de Gestión de Personal y Nómina'),
                            StringStruct(u'FileVersion', version_texto),
                            StringStruct(u'InternalName', u'SistemaGestionPersonal'),
                            StringStruct(u'LegalCopyright', u'© 2026. MIT License.'),
                            StringStruct(u'OriginalFilename', u'SistemaGestionPersonal.exe'),
                            StringStruct(u'ProductName', u'Sistema de Gestión de Personal'),
                            StringStruct(u'ProductVersion', version_texto),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct(u'Translation', [1033, 1200])]),
        ],
    )
else:
    version_resource = None

# customtkinter incluye temas y recursos JSON que deben empaquetarse
# junto al código; se recolectan explícitamente.
datas = collect_data_files("customtkinter")

# El binario de Linux se compila en Debian 13 (glibc 2.41) con Python 3.15
# standalone (uv/python-build-standalone). Ese intérprete guarda Tcl/Tk
# (libtcl9tk9.0.so, libtk9.0.so, etc.) en <base_prefix>/lib, fuera del
# árbol estándar de PyInstaller; se añaden explícitamente para que el
# ejecutable pueda inicializar tkinter.
binaries = []
if not IS_WINDOWS:
    import sysconfig

    _dirs_tcltk = [
        Path(sysconfig.get_config_var("TCL_LIBRARY") or "").parent,
        Path(sys.base_prefix) / "lib",
    ]
    _vistos: set[Path] = set()
    for _dir in _dirs_tcltk:
        if not _dir.is_dir():
            continue
        for _patron in ("libtcl9*.so*", "libtk9*.so*", "libtcl8*.so*", "libtk8*.so*"):
            for _origen in sorted(_dir.glob(_patron)):
                if _origen not in _vistos:
                    _vistos.add(_origen)
                    binaries.append((_origen, "."))

# Importaciones dinámicas/opcionales que conviene garantizar
hiddenimports = [
    "customtkinter",
    "PIL",
    "PIL._tkinter_finder",
    "reportlab",
    "dotenv",
    "sqlalchemy.dialects.sqlite",
    *collect_submodules("reportlab.graphics"),
]

a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "matplotlib", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    **({"icon": icono, "version": version_resource} if IS_WINDOWS else {}),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
