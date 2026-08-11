# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Sistema de Gestión de Personal
"""

import os
import sys

# Get the directory containing this spec file
spec_root = os.path.dirname(SPEC)
# Get the project root (parent of spec directory)
project_root = os.path.dirname(spec_root)

block_cipher = None

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'src'), 'src'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'reportlab',
        'SQLAlchemy',
        'pydantic',
        'pydantic_core',
        'typing_extensions',
        'python_dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SistemaGestionPersonal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
