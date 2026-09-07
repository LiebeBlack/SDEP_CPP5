"""
Actualizador automático de "Sistema de Gestión de Personal" (SDEP_CPP5).

Qué hace:
  1. Se registra en el Programador de tareas de Windows para ejecutarse
     cada 6 horas (y al iniciar sesión), con privilegios elevados.
  2. En cada ejecución consulta la última Release de GitHub
     (https://github.com/LiebeBlack/SDEP_CPP5/releases).
  3. Si hay una versión más nueva que la última instalada registrada,
     descarga el instalador (Setup.exe) y lo instala en modo silencioso.
  4. Se cierra solo al terminar (no queda residente).

El estado se guarda en %LOCALAPPDATA%\\SDEP_CPP5\\auto_updater.json
y el registro de actividad en %LOCALAPPDATA%\\SDEP_CPP5\\updater.log.

Variables de entorno (opcionales, útiles para pruebas):
  SDEP_UPDATE_API_URL            : URL del JSON de la Release "latest"
  SDEP_UPDATE_STATE_DIR          : carpeta del estado y del log
  SDEP_UPDATE_INSTALL_DIR        : ruta de instalación esperada
  SDEP_UPDATE_INSTALL_IF_MISSING : "0" para no instalar si no está instalado

Solo usa la biblioteca estándar: el .exe compilado es pequeño y no
depende del entorno virtual de la aplicación.

Uso:
    python updater/auto_updater.py            # flujo normal (registra + actualiza)
    python updater/auto_updater.py --check    # solo consulta y muestra el estado
    python updater/auto_updater.py --register # registra las tareas y actualiza
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
REPO = "LiebeBlack/SDEP_CPP5"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
API_LATEST_URL = os.environ.get(
    "SDEP_UPDATE_API_URL", f"https://api.github.com/repos/{REPO}/releases/latest"
)

APP_NAME = "Sistema de Gestión de Personal"
APP_EXE_NAME = "SistemaGestionPersonal.exe"
APP_INSTALL_DIR = os.environ.get(
    "SDEP_UPDATE_INSTALL_DIR", r"C:\Program Files\Sistema de Gestión de Personal"
)
APP_ID = "{8C1E9F5A-3B6D-4A2E-9C41-D7F06B2A5E91}"
UNINSTALL_KEY = rf"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}_is1"
UNINSTALL_KEY_WOW64 = (
    rf"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}_is1"
)

TASK_NAME = "SDEP_CPP5 AutoUpdater"
TASK_NAME_LOGON = "SDEP_CPP5 AutoUpdater (Logon)"
CHECK_INTERVAL_HOURS = 6
INSTALL_IF_MISSING = os.environ.get("SDEP_UPDATE_INSTALL_IF_MISSING", "1") == "1"
LOCK_MAX_AGE_SECONDS = 30 * 60  # una ejecución no debería durar más de 30 min
LOG_MAX_BYTES = 1024 * 1024     # rotación simple del log (1 MB)

USER_AGENT = (
    "Mozilla/5.0 (compatible; SDEP_CPP5-AutoUpdater/2.79; "
    "+https://github.com/LiebeBlack/SDEP_CPP5)"
)

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


# ---------------------------------------------------------------------------
# Utilidades de versión (puras, testeadas en tests/test_auto_updater.py)
# ---------------------------------------------------------------------------
def parse_version(text: str | None) -> tuple[int, int, int] | None:
    """Extrae (mayor, menor, parche) de una etiqueta o versión libre.

    "continuous-v2.79.55" -> (2, 79, 55); "v2.79" -> (2, 79, 0); None si no hay.
    """
    if not text:
        return None
    m = _VERSION_RE.search(str(text))
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def version_to_str(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def is_newer(candidate: tuple[int, int, int], current: tuple[int, int, int]) -> bool:
    """True si candidate es más nueva que current (comparación por partes)."""
    return candidate > current


# ---------------------------------------------------------------------------
# Estado y log
# ---------------------------------------------------------------------------
def state_dir() -> Path:
    override = os.environ.get("SDEP_UPDATE_STATE_DIR")
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(local) / "SDEP_CPP5"


def state_path() -> Path:
    return state_dir() / "auto_updater.json"


def log_path() -> Path:
    return state_dir() / "updater.log"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(message: str) -> None:
    """Añade una línea al log (con rotación) y la muestra por consola si hay."""
    try:
        state_dir().mkdir(parents=True, exist_ok=True)
        if log_path().exists() and log_path().stat().st_size > LOG_MAX_BYTES:
            log_path().write_text(
                "--- log rotado ---\n", encoding="utf-8"
            )
        with log_path().open("a", encoding="utf-8") as fh:
            fh.write(f"[{now_utc()}] {message}\n")
    except OSError:
        pass
    print(message, flush=True)


def load_state() -> dict:
    try:
        with state_path().open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
    except (OSError, ValueError):
        pass
    return {}


def save_state(state: dict) -> None:
    state_dir().mkdir(parents=True, exist_ok=True)
    tmp = state_path().with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, state_path())


# ---------------------------------------------------------------------------
# GitHub Releases
# ---------------------------------------------------------------------------
def fetch_latest() -> dict:
    """Consulta la última Release publicada. Lanza RuntimeError si falla."""
    last_error: Exception | None = None
    for attempt in range(1, 4):  # 3 intentos con espera creciente
        try:
            request = urllib.request.Request(
                API_LATEST_URL,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            tag = str(data.get("tag_name") or "")
            assets = [
                {
                    "name": str(asset.get("name") or ""),
                    "url": str(asset.get("browser_download_url") or ""),
                    "size": int(asset.get("size") or 0),
                }
                for asset in data.get("assets") or []
            ]
            return {"tag": tag, "name": str(data.get("name") or tag), "assets": assets}
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"No se pudo consultar {API_LATEST_URL}: {last_error}")


def find_setup_asset(assets: list[dict]) -> dict | None:
    """Localiza el instalador (Setup.exe) entre los activos de la Release."""
    for asset in assets:
        name = asset["name"].lower()
        if name.endswith(".exe") and "setup" in name:
            return asset
    for asset in assets:  # alternativa: cualquier .exe que no sea código fuente
        if asset["name"].lower().endswith(".exe"):
            return asset
    return None


def download(url: str, destination: Path, expected_size: int = 0) -> Path:
    """Descarga un archivo con reintentos y verificación de tamaño."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        tmp = destination.with_name(destination.name + ".part")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                with tmp.open("wb") as fh:
                    shutil.copyfileobj(response, fh, length=256 * 1024)
            if expected_size and tmp.stat().st_size != expected_size:
                raise RuntimeError(
                    f"Tamaño inesperado: {tmp.stat().st_size} bytes "
                    f"(se esperaban {expected_size})"
                )
            os.replace(tmp, destination)
            return destination
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            last_error = exc
            tmp.unlink(missing_ok=True)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Fallo al descargar {url}: {last_error}")


# ---------------------------------------------------------------------------
# Windows: administrador, registro, instalador, tareas programadas
# ---------------------------------------------------------------------------
def is_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def self_exe() -> Path:
    """Ruta del propio ejecutable (o del script en desarrollo)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(__file__).resolve()


def registry_display_version() -> str | None:
    """Versión registrada por Inno Setup en el registro de Windows (si existe)."""
    if sys.platform != "win32":
        return None
    for key in (UNINSTALL_KEY, UNINSTALL_KEY_WOW64):
        try:
            result = subprocess.run(
                ["reg", "query", key, "/v", "DisplayVersion"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            match = re.search(r"DisplayVersion\s+REG_SZ\s+(\S+)", result.stdout)
            if match:
                return match.group(1)
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def app_installed() -> bool:
    """¿Está la aplicación instalada? (registro de desinstalación o carpeta)."""
    if registry_display_version():
        return True
    return Path(APP_INSTALL_DIR, APP_EXE_NAME).exists()


def close_app_if_running() -> None:
    """Cierra la aplicación con un aviso amable (WM_CLOSE, sin forzar) para
    que el instalador no falle por archivos bloqueados."""
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            ["taskkill", "/IM", APP_EXE_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            log(f"Aplicación {APP_EXE_NAME} cerrada antes de actualizar")
            for _ in range(30):  # espera hasta 15 s a que termine
                check = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {APP_EXE_NAME}"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if APP_EXE_NAME not in check.stdout:
                    break
                time.sleep(0.5)
    except (OSError, subprocess.SubprocessError):
        pass


def _script_instalador_powershell(setup_path: Path) -> str:
    """Comando PowerShell que ejecuta el instalador elevado y espera.

    Se construye por concatenación (NUNCA con str.format): el script
    contiene llaves literales de PowerShell y .format lanzaría ValueError.
    """
    quoted = str(setup_path).replace("'", "''")
    return (
        "& { $p = Start-Process -FilePath '" + quoted + "' "
        "-ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') "
        "-Verb RunAs -Wait -PassThru; exit $p.ExitCode }"
    )


def install_setup(setup_path: Path) -> int:
    """Ejecuta el instalador de Inno en silencio y devuelve su código de salida.

    Si el proceso actual no es administrador, se relanza el instalador con
    elevación (aparecerá una sola confirmación de UAC).
    """
    args = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
    if is_admin():
        proc = subprocess.run(
            [str(setup_path), *args],
            capture_output=True,
            text=True,
            timeout=30 * 60,
        )
        return proc.returncode
    script = _script_instalador_powershell(setup_path)
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30 * 60,
    )
    return proc.returncode


def tasks_registered() -> bool:
    if sys.platform != "win32":
        return True
    for task in (TASK_NAME, TASK_NAME_LOGON):
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", task],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return False
        except (OSError, subprocess.SubprocessError):
            return False
    return True


def register_tasks() -> None:
    """Crea (o actualiza) las tareas: cada 6 horas y al iniciar sesión."""
    if sys.platform != "win32":
        return
    exe = self_exe()
    tr_value = f'"{exe}"'
    commands = [
        (
            "cada 6 horas",
            ["schtasks", "/Create", "/F", "/TN", TASK_NAME, "/SC", "HOURLY",
             "/MO", str(CHECK_INTERVAL_HOURS), "/TR", tr_value, "/RL", "HIGHEST"],
        ),
        (
            "al iniciar sesión",
            ["schtasks", "/Create", "/F", "/TN", TASK_NAME_LOGON, "/SC",
             "ONLOGON", "/TR", tr_value, "/RL", "HIGHEST"],
        ),
    ]
    for description, command in commands:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30
            )
            status = "OK" if result.returncode == 0 else f"ERROR ({result.returncode})"
            log(f"Tarea '{command[4]}' ({description}): {status}")
        except (OSError, subprocess.SubprocessError) as exc:
            log(f"No se pudo crear la tarea '{command[4]}': {exc}")


def relaunch_elevated_register() -> bool:
    """Relanza este mismo programa con privilegios para que registre las
    tareas (una sola confirmación de UAC) y complete la actualización."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", str(self_exe()), "--register", None, 0
        )
        return result > 32
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Bloqueo de ejecución (evita dos instalaciones simultáneas)
# ---------------------------------------------------------------------------
def acquire_lock() -> bool:
    try:
        state_dir().mkdir(parents=True, exist_ok=True)
        lock = state_dir() / "lock"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        return True
    except FileExistsError:
        lock = state_dir() / "lock"
        try:
            age = time.time() - lock.stat().st_mtime
        except OSError:
            return acquire_lock()
        if age > LOCK_MAX_AGE_SECONDS:  # bloqueo obsoleto (proceso murió)
            lock.unlink(missing_ok=True)
            return acquire_lock()
        log("Otra instancia del actualizador ya está en ejecución; saliendo")
        return False


def release_lock() -> None:
    try:
        (state_dir() / "lock").unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------------------------
def run_check(install: bool) -> int:
    """Consulta GitHub y, si hay versión más nueva, la descarga e instala.

    Devuelve: 0 = sin cambios / 1 = error / 2 = actualización realizada.
    """
    state = load_state()
    try:
        release = fetch_latest()
    except RuntimeError as exc:
        log(f"ERROR al consultar actualizaciones: {exc}")
        state["last_error"] = str(exc)
        state["last_check_utc"] = now_utc()
        save_state(state)
        return 1

    tag = release["tag"]
    version = parse_version(tag)
    if version is None:
        log(f"ERROR: no se pudo interpretar la etiqueta de la Release: {tag!r}")
        return 1

    state["last_check_utc"] = now_utc()
    state.pop("last_error", None)
    save_state(state)

    last_tag = state.get("last_tag")
    if last_tag:
        last_version = parse_version(last_tag)
        if last_version and not is_newer(version, last_version):
            log(f"Ya está actualizado: {last_tag} (última Release: {tag})")
            return 0

    if not install:
        log(f"Hay una versión más nueva: {tag} "
            f"(página: {RELEASES_PAGE})")
        return 2

    if not app_installed() and not INSTALL_IF_MISSING:
        log("La aplicación no está instalada y SDEP_UPDATE_INSTALL_IF_MISSING=0; "
            "se omite la instalación")
        return 0

    log(f"Actualización disponible: {last_tag or '(primera instalación)'} -> {tag}")

    asset = find_setup_asset(release["assets"])
    if asset is None:
        log("ERROR: no se encontró el instalador (Setup.exe) en la Release")
        return 1
    if not asset["url"]:
        log("ERROR: el instalador de la Release no tiene URL de descarga")
        return 1

    destino = (
        Path(os.environ.get("TEMP") or state_dir()) / "sdep_updater" / asset["name"]
    )
    log(f"Descargando {asset['name']} "
        f"({asset['size'] / (1024 * 1024):.1f} MB) desde GitHub...")
    try:
        download(asset["url"], destino, expected_size=asset["size"])
    except RuntimeError as exc:
        log(f"ERROR al descargar: {exc}")
        return 1
    log(f"Descarga completada: {destino} ({destino.stat().st_size} bytes)")

    close_app_if_running()
    log("Instalando en modo silencioso (esto puede tardar un par de minutos)...")
    try:
        exit_code = install_setup(destino)
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"ERROR al instalar: {exc}")
        return 1

    if exit_code == 0:
        state["last_tag"] = tag
        state["last_installed_utc"] = now_utc()
        save_state(state)
        log(f"Actualización completada: {tag}")
        return 2
    log(f"ERROR: el instalador terminó con el código {exit_code}")
    state["last_error"] = f"instalador devolvió {exit_code}"
    save_state(state)
    return 1


def main() -> int:
    args = sys.argv[1:]

    if "--version" in args:
        print("SDEP_CPP5 AutoUpdater 2.79")
        return 0

    if "--check" in args:
        return run_check(install=False)

    if "--register" in args:
        register_tasks()
        return run_check(install=True)

    # Flujo normal: garantiza la programación y ejecuta la comprobación.
    if not acquire_lock():
        return 0
    try:
        if is_admin():
            if not tasks_registered():
                register_tasks()
        elif not tasks_registered():
            # Sin privilegios y sin tareas: se relanza elevado una sola vez.
            log("Registrando el actualizador cada 6 horas (confirmación UAC)...")
            if relaunch_elevated_register():
                return 0  # el proceso elevado completa el trabajo
        return run_check(install=True)
    finally:
        release_lock()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)