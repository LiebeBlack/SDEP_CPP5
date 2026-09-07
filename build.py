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
    python build.py --updater  # solo el actualizador automático
    python build.py --all      # ejecutable + instalador + actualizador
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def leer_version() -> str:
    """Lee la versión desde VERSION (fuente única junto a pyproject)"""
    archivo = RAIZ / "VERSION"
    version = archivo.read_text(encoding="utf-8").strip()
    return version or "2.79"


def leer_commit() -> str:
    """Commit corto del repositorio (o 'dev' si no es un repo git)"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=RAIZ,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "dev"


def generar_build_info() -> None:
    """Genera src/config/build_info.py con la versión/commit del build.

    El CI pasa BUILD_VERSION/BUILD_COMMIT (p. ej. "2.79.55" en releases
    continuas); en local se usan VERSION y el commit de git.
    """
    version = os.environ.get("BUILD_VERSION") or leer_version()
    commit = os.environ.get("BUILD_COMMIT") or leer_commit()
    fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
    contenido = (
        '"""Generado automaticamente por build.py / CI. No editar."""\n'
        f"BUILD_VERSION = {version!r}\n"
        f"BUILD_COMMIT = {commit!r}\n"
        f"BUILD_DATE = {fecha!r}\n"
    )
    destino = RAIZ / "src" / "config" / "build_info.py"
    destino.write_text(contenido, encoding="utf-8")
    print(f"[OK] Información de build: {destino} (v{version}, commit {commit})")


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
    generar_build_info()
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


def build_updater() -> bool:
    """Empaqueta el actualizador automático (updater/auto_updater.py)"""
    print("=== Actualizador automático (PyInstaller onefile) ===")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        str(RAIZ / "updater" / "updater.spec"),
    ]
    print("$", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: PyInstaller falló ({e})")
        return False

    generado = RAIZ / "dist" / "SDEP_CPP5_AutoUpdater.exe"
    destino_dir = RAIZ / "dist_updater"
    if generado.exists():
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / "SDEP_CPP5_AutoUpdater.exe"
        shutil.move(str(generado), str(destino))
        tamano = destino.stat().st_size / (1024 * 1024)
        print(f"[OK] Actualizador: {destino} ({tamano:.1f} MB)")
        return True
    print("[X] No se encontró el actualizador generado")
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
    parser.add_argument("--updater", action="store_true", help="Solo actualizador automático")
    parser.add_argument("--all", action="store_true", help="Ejecutable + instalador + actualizador")
    args = parser.parse_args()

    os.chdir(RAIZ)
    print(f"Versión: {leer_version()}")
    if args.updater:
        ok = build_updater()
    elif args.all:
        ok = build_exe()
        if ok:
            ok = build_installer()
        if ok:
            ok = build_updater()
    else:
        ok = build_exe()
        if ok and not args.exe:
            ok = build_installer()
    if not ok:
        sys.exit(1)
    print("Construcción completada.")


if __name__ == "__main__":
    main()
