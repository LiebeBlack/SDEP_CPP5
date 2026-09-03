"""
Settings Configuration
Configuración general de la aplicación
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Nombre de la carpeta de datos cuando la app está instalada en Windows
APP_DATA_DIR_NAME = "SistemaGestionPersonal"

APP_VERSION_DEFAULT = "1.0.3"


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
    """
    override = os.getenv("SGP_BASE_DIR")
    if override:
        return Path(override).resolve()
    if getattr(sys, "frozen", False):
        local_data = os.getenv("LOCALAPPDATA")
        if local_data:
            return Path(local_data) / APP_DATA_DIR_NAME
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


class Settings:
    """Configuración de la aplicación"""

    def __init__(self):
        # Directorio base de la aplicación
        self.base_dir = _resolve_base_dir()

        # Aplicación
        self.app_name = os.getenv("APP_NAME", "Sistema de Gestión de Personal")
        self.app_version = os.getenv("APP_VERSION", APP_VERSION_DEFAULT)
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
        
        # PDF
        self.pdf_author = os.getenv("PDF_AUTHOR", "Sistema de Gestión de Personal")
        self.pdf_title = os.getenv("PDF_TITLE", "Documentos Oficiales")
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = str(self.base_dir / os.getenv("LOG_FILE", "app.log"))
        
        # Crear directorios necesarios
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Asegura que los directorios necesarios existan"""
        directories = [
            self.documents_path,
            self.photos_path,
            self.exports_path,
            Path(self.log_file).parent
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
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