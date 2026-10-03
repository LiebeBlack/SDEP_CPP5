"""
Actualizador automático de "Sistema de Gestión de Personal" (SDEP_CPP5).

Qué hace:
  1. Se registra en el Programador de tareas de Windows para ejecutarse
     CADA 2 DÍAS a las 09:00, con privilegios elevados.
  2. En cada ejecución consulta la última Release de GitHub
     (https://github.com/LiebeBlack/SDEP_CPP5/releases).
  3. Si hay una versión más nueva que la última instalada registrada,
     descarga el instalador (Setup.exe) y lo instala en modo silencioso.
  4. Mientras trabaja muestra una VENTANA de estado (comprobando,
     descargando, instalando, resultado) y un ícono en la BANDEJA del
     sistema (barra inferior derecha, Windows). Al terminar se cierra.

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
    python updater/auto_updater.py                 # flujo normal (ventana + bandeja)
    python updater/auto_updater.py --check         # solo consulta (sin instalar)
    python updater/auto_updater.py --check --gui   # consulta con ventana
    python updater/auto_updater.py --register      # registra las tareas y actualiza
    python updater/auto_updater.py --register-only # SOLO registra la tarea (instalador)
    python updater/auto_updater.py --unregister    # quita las tareas (desinstalador)
    python updater/auto_updater.py --no-gui        # fuerza modo texto
"""

import base64
import ctypes
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

# Los comandos del sistema (``reg``, ``taskkill``, ``tasklist``, ``schtasks``)
# escriben en la página de códigos OEM de Windows, mientras que Python 3.15
# decodifica en UTF-8 por omisión: un acento en un mensaje localizado hacía
# fallar la lectura dentro del hilo de ``subprocess`` y la salida del comando
# se perdía. Con ``errors="replace"`` el comando se lee siempre y lo que luego
# se interpreta —nombres e identificadores— es ASCII.
class _TextoComando(TypedDict):
    """Opciones de lectura comunes a los comandos del sistema"""

    errors: str


_TEXTO_SISTEMA: _TextoComando = {"errors": "replace"}

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
APP_EXE_NAMES = (APP_EXE_NAME, "SDEP_CPP5.exe")
APP_INSTALL_DIR = os.environ.get(
    "SDEP_UPDATE_INSTALL_DIR", r"C:\Program Files\Sistema de Gestión de Personal"
)
APP_ID = "{8C1E9F5A-3B6D-4A2E-9C41-D7F06B2A5E91}"
UNINSTALL_KEY = rf"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}_is1"
UNINSTALL_KEY_WOW64 = (
    rf"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{APP_ID}_is1"
)

TASK_NAME = "SDEP_CPP5 AutoUpdater"
TASK_NAME_LOGON = "SDEP_CPP5 AutoUpdater (Logon)"  # tarea antigua (solo para limpieza)
CHECK_INTERVAL_DAYS = 2
CHECK_START_TIME = "09:00"
INSTALL_IF_MISSING = os.environ.get("SDEP_UPDATE_INSTALL_IF_MISSING", "1") == "1"
SIGNING_ISSUER_NAME = "LiebeBlack Code Signing Issuing CA v2"
SIGNING_ROOT_NAME = "LiebeBlack Global Master Root Authority 2026"
LOCK_MAX_AGE_SECONDS = 30 * 60  # una ejecución no debería durar más de 30 min
LOG_MAX_BYTES = 1024 * 1024  # rotación simple del log (1 MB)

USER_AGENT = (
    "Mozilla/5.0 (compatible; SDEP_CPP5-AutoUpdater/3.0.0; "
    "+https://github.com/LiebeBlack/SDEP_CPP5)"
)

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?")

# Ganchos opcionales que la GUI (updater/updater_gui.py) engancha para
# mostrar el progreso en su ventana y en la bandeja del sistema.
on_progress: Callable[[str], None] | None = None
on_download: Callable[[int, int], None] | None = None


# ---------------------------------------------------------------------------
# Utilidades de versión (puras, testeadas en tests/test_auto_updater.py)
# ---------------------------------------------------------------------------
def parse_version(text: str | None) -> tuple[int, ...] | None:
    """Extrae componentes de versión (mayor, menor, parche y build opcional).

    "continuous-v2.79.55" -> (2, 79, 55);
    "continuous-v3.0.0.55" -> (3, 0, 0, 55);
    "v2.79" -> (2, 79, 0); None si no hay.
    """
    if not text:
        return None
    m = _VERSION_RE.search(str(text))
    if not m:
        return None
    version = (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
    if m.group(4) is not None:
        return (*version, int(m.group(4)))
    return version


def version_to_str(version: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)


def is_newer(candidate: tuple[int, ...], current: tuple[int, ...]) -> bool:
    """Compara versiones de tres o cuatro partes (el build por defecto es 0)."""
    partes = max(len(candidate), len(current))
    candidata = candidate + (0,) * (partes - len(candidate))
    actual = current + (0,) * (partes - len(current))
    return candidata > actual


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
            log_path().write_text("--- log rotado ---\n", encoding="utf-8")
        with log_path().open("a", encoding="utf-8") as fh:
            fh.write(f"[{now_utc()}] {message}\n")
    except OSError:
        pass
    if on_progress is not None:
        try:
            on_progress(message)
        except Exception:
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
                try:
                    total = int(response.headers.get("Content-Length") or 0)
                except (TypeError, ValueError):
                    total = 0
                done = 0
                with tmp.open("wb") as fh:
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        fh.write(chunk)
                        done += len(chunk)
                        if on_download is not None:
                            try:
                                on_download(done, total)
                            except Exception:
                                pass
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


def _powershell_executable() -> Path:
    return (
        Path(os.environ.get("SystemRoot") or r"C:\Windows")
        / "System32"
        / "WindowsPowerShell"
        / "v1.0"
        / "powershell.exe"
    )


def _script_instalador_verificado(setup_path: Path) -> str:
    """Crea una copia protegida, valida su firma y ejecuta esa misma copia."""
    encoded_path = base64.b64encode(str(setup_path.resolve()).encode("utf-8")).decode("ascii")
    return (
        "$ErrorActionPreference='Stop'; "
        f"$source=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_path}')); "
        "$code=1; $staged=$null; try { "
        "$directory=Join-Path $env:ProgramData 'SDEP_CPP5\\updates'; "
        "if (-not (Test-Path -LiteralPath $directory)) { "
        "New-Item -ItemType Directory -Path $directory -Force | Out-Null }; "
        "$item=Get-Item -LiteralPath $directory -Force; "
        "if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) "
        "{ throw 'La carpeta segura de actualización es un enlace no permitido' }; "
        "$system=New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18'); "
        "$admins=New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-544'); "
        "$acl=New-Object System.Security.AccessControl.DirectorySecurity; "
        "$acl.SetAccessRuleProtection($true,$false); "
        "$acl.SetOwner($admins); "
        "$inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor "
        "[System.Security.AccessControl.InheritanceFlags]::ObjectInherit; "
        "$rule=New-Object System.Security.AccessControl.FileSystemAccessRule("
        "$system,'FullControl',$inherit,'None','Allow'); $acl.AddAccessRule($rule); "
        "$rule=New-Object System.Security.AccessControl.FileSystemAccessRule("
        "$admins,'FullControl',$inherit,'None','Allow'); $acl.AddAccessRule($rule); "
        "Set-Acl -LiteralPath $directory -AclObject $acl; "
        "$staged=Join-Path $directory ('setup-' + [Guid]::NewGuid().ToString('N') + '.exe'); "
        "Copy-Item -LiteralPath $source -Destination $staged; "
        "$sig=Get-AuthenticodeSignature -LiteralPath $staged; "
        "if ($null -eq $sig.SignerCertificate -or $sig.Status -eq 'HashMismatch') "
        "{ throw 'El instalador no tiene una firma válida' }; "
        "$chain=New-Object System.Security.Cryptography.X509Certificates.X509Chain; "
        "$chain.ChainPolicy.RevocationMode="
        "[System.Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck; "
        "if (-not $chain.Build($sig.SignerCertificate)) "
        "{ throw 'No se pudo validar la cadena de certificados del instalador' }; "
        "$issuer=$sig.SignerCertificate.GetNameInfo("
        "[System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName,$true); "
        "$root=$chain.ChainElements[$chain.ChainElements.Count-1].Certificate.GetNameInfo("
        "[System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName,$false); "
        f"if ($issuer -ne '{SIGNING_ISSUER_NAME}' -or "
        f"$root -ne '{SIGNING_ROOT_NAME}') "
        "{ throw 'El certificado del instalador no pertenece al editor oficial' }; "
        "$process=Start-Process -FilePath $staged "
        "-ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') "
        "-Wait -PassThru; $code=$process.ExitCode "
        "} finally { if ($staged -and (Test-Path -LiteralPath $staged)) "
        "{ Remove-Item -LiteralPath $staged -Force } }; exit $code"
    )


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
                **_TEXTO_SISTEMA,
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
    return any(Path(APP_INSTALL_DIR, nombre).exists() for nombre in APP_EXE_NAMES)


def close_app_if_running() -> None:
    """Cierra la aplicación con un aviso amable (WM_CLOSE, sin forzar) para
    que el instalador no falle por archivos bloqueados."""
    if sys.platform != "win32":
        return
    for nombre in APP_EXE_NAMES:
        try:
            result = subprocess.run(
                ["taskkill", "/IM", nombre],
                capture_output=True,
                text=True,
                **_TEXTO_SISTEMA,
                timeout=30,
            )
            if result.returncode != 0:
                continue
            log(f"Aplicación {nombre} cerrada antes de actualizar")
            for _ in range(30):  # espera hasta 15 s a que termine
                check = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {nombre}"],
                    capture_output=True,
                    text=True,
                    **_TEXTO_SISTEMA,
                    timeout=15,
                )
                if nombre.lower() not in check.stdout.lower():
                    break
                time.sleep(0.5)
        except (OSError, subprocess.SubprocessError) as exc:
            log(f"No se pudo cerrar {nombre} antes de actualizar: {exc}")


def install_setup(setup_path: Path) -> int:
    """Ejecuta el instalador de Inno en silencio y devuelve su código de salida.

    Eleva primero y valida/ejecuta una copia en ProgramData protegida por ACL,
    para evitar sustituciones entre la validación y la ejecución.
    """
    powershell = _powershell_executable()
    if not powershell.is_file():
        raise RuntimeError("No se encontró Windows PowerShell para ejecutar la actualización")

    script = _script_instalador_verificado(setup_path)
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    if is_admin():
        proc = subprocess.run(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded_script,
            ],
            capture_output=True,
            text=True,
            **_TEXTO_SISTEMA,
            timeout=30 * 60,
        )
        return proc.returncode

    elevation_script = (
        "$process=Start-Process -FilePath '"
        + str(powershell).replace("'", "''")
        + "' -Verb RunAs -ArgumentList @('-NoProfile','-NonInteractive',"
        "'-ExecutionPolicy','Bypass','-EncodedCommand','"
        + encoded_script
        + "') -Wait -PassThru; exit $process.ExitCode"
    )
    proc = subprocess.run(
        [
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            elevation_script,
        ],
        capture_output=True,
        text=True,
        **_TEXTO_SISTEMA,
        timeout=30 * 60,
    )
    return proc.returncode


def tasks_registered() -> bool:
    if sys.platform != "win32":
        return True
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", TASK_NAME],
            capture_output=True,
            text=True,
            **_TEXTO_SISTEMA,
            timeout=15,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def register_tasks() -> None:
    """Crea (o actualiza) la tarea programada: cada 2 días a las 09:00.

    También elimina la tarea antigua "al iniciar sesión" de versiones
    previas del actualizador, que ya no se usa.
    """
    if sys.platform != "win32":
        return
    exe = self_exe()
    tr_value = f'"{exe}"'
    command = [
        "schtasks",
        "/Create",
        "/F",
        "/TN",
        TASK_NAME,
        "/SC",
        "DAILY",
        "/MO",
        str(CHECK_INTERVAL_DAYS),
        "/ST",
        CHECK_START_TIME,
        "/TR",
        tr_value,
        "/RL",
        "HIGHEST",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, **_TEXTO_SISTEMA, timeout=30
        )
        status = "OK" if result.returncode == 0 else f"ERROR ({result.returncode})"
        log(
            f"Tarea '{TASK_NAME}' (cada {CHECK_INTERVAL_DAYS} días a las "
            f"{CHECK_START_TIME}): {status}"
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"No se pudo crear la tarea '{TASK_NAME}': {exc}")
    # Limpieza: quitar la tarea antigua "al iniciar sesión" (si existe)
    try:
        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME_LOGON, "/F"],
            capture_output=True,
            text=True,
            **_TEXTO_SISTEMA,
            timeout=30,
        )
        if result.returncode == 0:
            log(f"Tarea antigua '{TASK_NAME_LOGON}' eliminada (ya no se usa)")
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"No se pudo eliminar la tarea antigua '{TASK_NAME_LOGON}': {exc}")


def unregister_tasks() -> None:
    """Elimina las tareas programadas del actualizador (desinstalación)."""
    if sys.platform != "win32":
        return
    for task in (TASK_NAME, TASK_NAME_LOGON):
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", task, "/F"],
                capture_output=True,
                text=True,
                **_TEXTO_SISTEMA,
                timeout=30,
            )
            if result.returncode == 0:
                log(f"Tarea '{task}' eliminada")
            else:
                log(f"Tarea '{task}' no existía o no se pudo eliminar " f"({result.returncode})")
        except (OSError, subprocess.SubprocessError) as exc:
            log(f"No se pudo eliminar la tarea '{task}': {exc}")


def relaunch_elevated_register() -> bool:
    """Relanza este mismo programa con privilegios para que registre las
    tareas (una sola confirmación de UAC) y complete la actualización."""
    if sys.platform != "win32":
        return False
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", str(self_exe()), "--register", None, 0
        )
        return bool(result > 32)
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
        log(f"Hay una versión más nueva: {tag} " f"(página: {RELEASES_PAGE})")
        return 2

    if not app_installed() and not INSTALL_IF_MISSING:
        log(
            "La aplicación no está instalada y SDEP_UPDATE_INSTALL_IF_MISSING=0; "
            "se omite la instalación"
        )
        return 0

    log(f"Actualización disponible: {last_tag or '(primera instalación)'} -> {tag}")

    asset = find_setup_asset(release["assets"])
    if asset is None:
        log("ERROR: no se encontró el instalador (Setup.exe) en la Release")
        return 1
    if not asset["url"]:
        log("ERROR: el instalador de la Release no tiene URL de descarga")
        return 1

    destino = state_dir() / "updates" / asset["name"]
    log(f"Descargando {asset['name']} " f"({asset['size'] / (1024 * 1024):.1f} MB) desde GitHub...")
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
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
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


def _gui_enabled(args: list[str]) -> bool:
    """¿Debe mostrarse la ventana de estado + bandeja del sistema?"""
    if "--no-gui" in args:
        return False
    if "--gui" in args:
        return True
    # Por defecto: ventana en los flujos interactivos; --check va en texto
    return not any(flag in args for flag in ("--check", "--register-only", "--unregister"))


def _run_with_gui(install: bool) -> int:
    """Ejecuta la comprobación/actualización mostrando la ventana de estado
    y el ícono de bandeja. Si la GUI no puede abrirse, vuelve a modo texto."""
    try:
        from updater.updater_gui import UpdaterGui
    except Exception as exc:
        log(f"No se pudo abrir la ventana del actualizador ({exc}); modo texto")
        return run_check(install=install)
    try:
        return UpdaterGui(install=install).run()
    except Exception as exc:
        log(f"La ventana del actualizador terminó con un error ({exc}); modo texto")
        return run_check(install=install)


def main() -> int:
    args = sys.argv[1:]

    if "--version" in args:
        print("SDEP_CPP5 AutoUpdater 3.0.0")
        return 0

    if "--unregister" in args:
        unregister_tasks()
        return 0

    if "--register-only" in args:
        register_tasks()
        return 0

    if "--check" in args:
        if _gui_enabled(args):
            return _run_with_gui(install=False)
        return run_check(install=False)

    if "--register" in args:
        register_tasks()
        if _gui_enabled(args):
            return _run_with_gui(install=True)
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
            log(
                f"Registrando el actualizador (cada {CHECK_INTERVAL_DAYS} días; "
                "confirmación UAC)..."
            )
            if relaunch_elevated_register():
                return 0  # el proceso elevado completa el trabajo
        if _gui_enabled(args):
            return _run_with_gui(install=True)
        return run_check(install=True)
    finally:
        release_lock()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
