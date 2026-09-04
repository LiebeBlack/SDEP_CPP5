# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para "Sistema de Gestión de Personal".

Genera una carpeta distribuible (onedir) en dist/SistemaGestionPersonal
que luego se empaqueta en un instalador con Inno Setup:

    pyinstaller --noconfirm --clean spec/app.spec

El modo onedir evita la extracción a TEMP de cada arranque (onefile),
reduce falsos positivos antivirus y acelera el inicio.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

spec_root = Path(SPEC).resolve().parent
project_root = spec_root.parent

app_name = "SistemaGestionPersonal"
icono = str(project_root / "assets" / "app.ico")
version_resource = str(project_root / "spec" / "version_info.txt")

# Los recursos de icono y versión (version_info.txt) solo existen en
# Windows; en Linux se omiten para que el mismo spec compile en ambos.
IS_WINDOWS = sys.platform.startswith("win")

# customtkinter incluye temas y recursos JSON que deben empaquetarse
# junto al código; se recolectan explícitamente.
datas = collect_data_files("customtkinter")

# El binario de Linux se compila dentro de Ubuntu 22.04 (el sistema
# objetivo más antiguo), de modo que todo lo que PyInstaller empaqueta
# (libpython, Tcl/Tk 8.6, libstdc++, etc.) exige como máximo glibc 2.35.
binaries = []

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
