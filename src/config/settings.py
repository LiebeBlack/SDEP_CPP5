"""
Settings Configuration
Configuración general de la aplicación

Todas las rutas de datos (base de datos, documentos, fotos, exportaciones,
caché, temporales, logs, respaldos y config.json) se resuelven SIEMPRE
contra un directorio base escribible por el usuario, de modo que el
software funciona en cualquier cuenta de Windows sin privilegios de
administrador, sin importar dónde se haya instalado el ejecutable.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Nombre de la carpeta de datos cuando la app está instalada en Windows
APP_DATA_DIR_NAME = "SistemaGestionPersonal"

APP_VERSION_DEFAULT = "2.79"

# Información de compilación incrustada en el build (generada por build.py
# o por el CI como src/config/build_info.py). En desarrollo, sin ese archivo,
# se lee la versión desde VERSION en la raíz del repositorio.
try:
    from . import build_info as _build_info  # generado en el build
except ImportError:  # pragma: no cover - depende del entorno de build
    _build_info = None


def _version_desarrollo() -> str:
    """Versión desde el archivo VERSION de la raíz (modo desarrollo)."""
    try:
        ruta = Path(__file__).resolve().parents[2] / "VERSION"
        return ruta.read_text(encoding="utf-8").strip() or ""
    except OSError:
        return ""


def _build_info_incrustado():
    """Devuelve (versión, commit, fecha) incrustados en el build."""
    if _build_info is None:
        return "", "", ""
    return (
        getattr(_build_info, "BUILD_VERSION", "") or "",
        getattr(_build_info, "BUILD_COMMIT", "") or "",
        getattr(_build_info, "BUILD_DATE", "") or "",
    )


def _es_dir_escribible(ruta: Path) -> bool:
    """Verifica que un directorio exista y permita escribir (probe real)"""
    try:
        ruta.mkdir(parents=True, exist_ok=True)
        prueba = ruta / ".sgp_prueba_escritura"
        prueba.write_text("ok", encoding="utf-8")
        prueba.unlink()
        return True
    except (OSError, PermissionError):
        return False


def _resolve_base_dir() -> Path:
    """
    Resuelve el directorio base de la aplicación (dónde viven los datos)

    Prioridad:
      1. SGP_BASE_DIR: ruta explícita (modo portable o pruebas).
      2. Ejecutable empaquetado (PyInstaller): %LOCALAPPDATA%/... si
         está disponible. Una app instalada en "Program Files" no puede
         escribir junto al ejecutable; los datos del usuario van al
         perfil de Windows.
      3. Desarrollo: la raíz del repositorio.

    Si el directorio elegido no es escribible (permisos, unidad de solo
    lectura, etc.), se cae a la carpeta personal del usuario y, en última
    instancia, al directorio temporal del sistema: el arranque NUNCA
    debe fallar por una ruta sin permisos.
    """
    override = os.getenv("SGP_BASE_DIR")
    if override:
        base = Path(override).resolve()
    elif getattr(sys, "frozen", False):
        local_data = os.getenv("LOCALAPPDATA")
        if local_data:
            base = Path(local_data) / APP_DATA_DIR_NAME
        else:
            base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent.parent.parent

    if _es_dir_escribible(base):
        return base

    # Fallback por permisos: carpeta del usuario o temp del sistema
    for candidato in (
        Path.home() / APP_DATA_DIR_NAME,
        Path(tempfile.gettempdir()) / APP_DATA_DIR_NAME,
    ):
        if _es_dir_escribible(candidato):
            return candidato
    return Path(tempfile.gettempdir()) / APP_DATA_DIR_NAME


class Settings:
    """Configuración de la aplicación"""

    def __init__(self):
        # Directorio base de la aplicación (siempre escribible)
        self.base_dir = _resolve_base_dir()

        # Aplicación
        self.app_name = os.getenv("APP_NAME", "Sistema de Gestión de Personal")
        version_incrustada, self.build_commit, self.build_date = _build_info_incrustado()
        if not version_incrustada and not getattr(sys, "frozen", False):
            version_incrustada = _version_desarrollo()
        # Prioridad: variable de entorno > versión incrustada en el build >
        # archivo VERSION (desarrollo) > constante por defecto.
        self.app_version = (
            os.getenv("APP_VERSION") or version_incrustada or APP_VERSION_DEFAULT
        )
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Base de datos
        db_env_path = os.getenv("DATABASE_PATH", "personal_management.db")
        if os.path.isabs(db_env_path):
            self.database_path = db_env_path
        else:
            self.database_path = str(self.base_dir / db_env_path)
        
        db_env_url = os.getenv("DATABASE_URL")
        if db_env_url:
            self.database_url = db_env_url
        else:
            # Normalizar slashes para URL de SQLite en Windows
            db_posix = Path(self.database_path).as_posix()
            self.database_url = f"sqlite:///{db_posix}"
        
        # Rutas de archivos (inicializar como absolutas)
        self.documents_path = str(self.base_dir / os.getenv("DOCUMENTS_PATH", "documents"))
        self.photos_path = str(self.base_dir / os.getenv("PHOTOS_PATH", "photos"))
        self.exports_path = str(self.base_dir / os.getenv("EXPORTS_PATH", "exports"))
        
        # Estructura limpia y aislada en la carpeta del usuario:
        # caché, temporales, logs, respaldos y configuración local
        self.cache_dir = str(self.base_dir / os.getenv("CACHE_DIR", "cache"))
        self.temp_dir = str(self.base_dir / os.getenv("TEMP_DIR", "tmp"))
        self.logs_dir = str(self.base_dir / "logs")
        self.backups_dir = str(self.base_dir / "backups")
        self.config_path = str(self.base_dir / os.getenv("CONFIG_FILE", "config.json"))
        
        # PDF
        self.pdf_author = os.getenv("PDF_AUTHOR", "Sistema de Gestión de Personal")
        self.pdf_title = os.getenv("PDF_TITLE", "Documentos Oficiales")
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = str(self.base_dir / os.getenv("LOG_FILE", "app.log"))
        
        # Crear directorios necesarios (nunca aborta el arranque)
        self._ensure_directories()
        
        # Aislar los archivos temporales de la aplicación (ReportLab,
        # CustomTkinter, PIL, etc.) en tmp/ dentro de la carpeta de datos
        # del usuario, en lugar de TEMP del sistema compartido.
        try:
            tempfile.tempdir = self.temp_dir
        except Exception:
            pass
    
    def _ensure_directories(self):
        """Asegura que los directorios necesarios existan sin abortar"""
        directorios = [
            self.documents_path,
            self.photos_path,
            self.exports_path,
            self.cache_dir,
            self.temp_dir,
            self.logs_dir,
            self.backups_dir,
            str(Path(self.config_path).parent),
            str(Path(self.log_file).parent),
        ]
        
        for directorio in directorios:
            try:
                Path(directorio).mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                print(f"ADVERTENCIA: no se pudo crear el directorio {directorio}")
    
    # ------------------------------------------------------------------
    # Configuración local del usuario (config.json)
    # ------------------------------------------------------------------
    def load_config_json(self) -> dict:
        """
        Carga config.json con recuperación automática

        Si el archivo está corrupto (JSON inválido, escritura a medias),
        se aparta como .corrupto y se devuelve un diccionario vacío para
        que la aplicación arranque con los valores por defecto.
        """
        ruta = Path(self.config_path)
        try:
            if ruta.exists():
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                if isinstance(datos, dict):
                    return datos
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            self._apartar_config_corrupto()
        return {}

    def _apartar_config_corrupto(self):
        """Aparta un config.json corrupto para no perder el archivo original"""
        ruta = Path(self.config_path)
        try:
            if ruta.exists():
                ruta.rename(ruta.with_suffix(".json.corrupto"))
        except OSError:
            pass

    def save_config_json(self, datos: dict) -> bool:
        """
        Guarda config.json de forma atómica

        Escribe primero un archivo temporal y lo renombra (os.replace),
        de modo que un corte de energía a mitad de escritura nunca deja
        un config.json a medias.
        """
        ruta = Path(self.config_path)
        temporal = ruta.with_suffix(".json.tmp")
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            temporal.write_text(
                json.dumps(datos, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temporal, ruta)
            return True
        except (OSError, PermissionError):
            try:
                if temporal.exists():
                    temporal.unlink()
            except OSError:
                pass
            return False

    def get_config_value(self, clave: str, default=None):
        """Lee un valor de config.json (None si no existe)"""
        return self.load_config_json().get(clave, default)

    def set_config_value(self, clave: str, valor) -> bool:
        """Escribe un valor en config.json de forma atómica"""
        datos = self.load_config_json()
        datos[clave] = valor
        return self.save_config_json(datos)

    def get_document_path(self, filename: str) -> str:
        """Retorna la ruta completa para un documento"""
        return str(Path(self.documents_path) / filename)
    
    def get_photo_path(self, filename: str) -> str:
        """Retorna la ruta completa para una foto"""
        return str(Path(self.photos_path) / filename)
    
    def get_export_path(self, filename: str) -> str:
        """Retorna la ruta completa para un archivo exportado"""
        return str(Path(self.exports_path) / filename)


# Instancia global de configuración
settings = Settings()