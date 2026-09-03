"""
Script de construcción para Windows

Pasos:
  1. pyinstaller --noconfirm --clean spec/app.spec   -> dist/SistemaGestionPersonal/
  2. Inno Setup (ISCC.exe)  installer/setup.iss      -> dist_installer/SistemaGestionPersonal-Setup-*.exe

El instalador es opcional en local: si ISCC.exe no está instalado, el
script termina con el ejecutable listo y explica cómo generar el setup.

Uso:
    python build.py            # todo
    python build.py --exe      # solo el ejecutable
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def leer_version() -> str:
    """Lee la versión desde VERSION (fuente única junto a pyproject)"""
    archivo = RAIZ / "VERSION"
    version = archivo.read_text(encoding="utf-8").strip()
    return version or "1.0.3"


def localizar_iscc():
    """Localiza ISCC.exe (Inno Setup 6) en las rutas habituales"""
    candidatas = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        / "Inno Setup 6" / "ISCC.exe",
    ]
    iscc = shutil.which("ISCC")
    if iscc:
        return Path(iscc)
    for candidata in candidatas:
        if candidata.exists():
            return candidata
    return None


def build_exe() -> bool:
    """Empaqueta la aplicación con PyInstaller usando spec/app.spec"""
    print("=== [1/2] Ejecutable con PyInstaller ===")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        str(RAIZ / "spec" / "app.spec"),
    ]
    print("$", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: PyInstaller falló ({e})")
        return False

    exe = RAIZ / "dist" / "SistemaGestionPersonal" / "SistemaGestionPersonal.exe"
    if exe.exists():
        tamano = exe.stat().st_size / (1024 * 1024)
        print(f"[OK] Ejecutable: {exe} ({tamano:.1f} MB)")
        return True
    print("[X] No se encontró el ejecutable generado")
    return False


def build_installer() -> bool:
    """Genera el instalador con Inno Setup (si está disponible)"""
    iscc = localizar_iscc()
    if iscc is None:
        print(
            "=== [2/2] Instalador omitido ===\n"
            "Inno Setup 6 no está instalado. Instálelo desde "
            "https://jrsoftware.org/isdl.php o con: choco install innosetup -y\n"
            "Luego ejecute: python build.py"
        )
        return True

    version = leer_version()
    print("=== [2/2] Instalador con Inno Setup ===")
    cmd = [
        str(iscc),
        f"/DMyAppVersion={version}",
        str(RAIZ / "installer" / "setup.iss"),
    ]
    print("$", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Inno Setup falló ({e})")
        return False

    setup = RAIZ / "dist_installer" / f"SistemaGestionPersonal-Setup-{version}.exe"
    if setup.exists():
        tamano = setup.stat().st_size / (1024 * 1024)
        print(f"[OK] Instalador: {setup} ({tamano:.1f} MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Construcción de la app para Windows")
    parser.add_argument("--exe", action="store_true", help="Solo ejecutable (sin instalador)")
    args = parser.parse_args()

    os.chdir(RAIZ)
    print(f"Versión: {leer_version()}")
    ok = build_exe()
    if ok and not args.exe:
        ok = build_installer()
    if not ok:
        sys.exit(1)
    print("Construcción completada.")


if __name__ == "__main__":
    main()
