# -*- mode: python ; coding: utf-8 -*-
"""
Spec de PyInstaller para el "Actualizador automático de SDEP_CPP5".

Genera un ejecutable único (onefile) sin consola, con ventana de estado
(tkinter) y el ícono de la bandeja del sistema:

    python -m PyInstaller --noconfirm --clean updater/updater.spec

Salida: dist/SDEP_CPP5_AutoUpdater.exe
(build.py lo mueve a dist_updater/SDEP_CPP5_AutoUpdater.exe)
"""

import sys
from pathlib import Path

spec_root = Path(SPEC).resolve().parent
project_root = spec_root.parent

updater_name = "SDEP_CPP5_AutoUpdater"
icono = str(project_root / "assets" / "app.ico")
version_resource = str(spec_root / "version_info.txt")

IS_WINDOWS = sys.platform.startswith("win")

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