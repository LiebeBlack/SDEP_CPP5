# -*- mode: python ; coding: utf-8 -*-
"""
Spec de PyInstaller para el "Actualizador automático de SDEP_CPP5".

Genera un ejecutable único (onefile) sin consola, con ventana de estado
(tkinter) y el ícono de la bandeja del sistema:

    python -m PyInstaller --noconfirm --clean updater/updater.spec

Salida: dist/SDEP_CPP5_AutoUpdater.exe
(build.py lo mueve a dist_updater/SDEP_CPP5_AutoUpdater.exe)
"""

import re
import sys
from pathlib import Path

spec_root = Path(SPEC).resolve().parent
project_root = spec_root.parent

updater_name = "SDEP_CPP5_AutoUpdater"
icono = str(project_root / "assets" / "app.ico")

IS_WINDOWS = sys.platform.startswith("win")

# ---------------------------------------------------------------------------
# Recurso de versión generado desde VERSION, igual que el ejecutable
# principal. Antes se usaba un version_info.txt fijo que quedó en 2.79.0: el
# actualizador distribuido mostraba una versión que no era la del release.
# ---------------------------------------------------------------------------
def _version_tupla(texto: str) -> tuple:
    """'3.0.1' -> (3, 0, 1, 0); '3.0.1.55' -> (3, 0, 1, 55)."""
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
                            StringStruct(u'FileDescription', u'Actualizador automático de Sistema de Gestión de Personal'),
                            StringStruct(u'FileVersion', version_texto),
                            StringStruct(u'InternalName', u'SDEP_CPP5_AutoUpdater'),
                            StringStruct(u'LegalCopyright', u'© 2026. MIT License.'),
                            StringStruct(u'OriginalFilename', u'SDEP_CPP5_AutoUpdater.exe'),
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

a = Analysis(
    [str(spec_root / "auto_updater.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(icono, "assets")],  # ícono para la ventana y la bandeja del sistema
    hiddenimports=["tkinter", "tkinter.ttk"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["customtkinter", "sqlalchemy", "PIL", "reportlab"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Onefile: se pasan a.binaries y a.datas en la posición correcta y
# exclude_binaries=[] (el archivo único contiene todo el bundle).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=updater_name,
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    **( {"icon": [icono], "version": version_resource} if IS_WINDOWS else {}),
)