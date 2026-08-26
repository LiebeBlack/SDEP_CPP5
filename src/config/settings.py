"""
Settings Configuration
Configuración general de la aplicación
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Union

# Cargar variables de entorno
load_dotenv()


@dataclass
class Settings:
    """Configuración de la aplicación"""
    
    # Aplicación
    app_name: str = os.getenv("APP_NAME", "Sistema de Gestión de Personal")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Base de datos
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///personal_management.db")
    database_path: str = os.getenv("DATABASE_PATH", "personal_management.db")
    
    # Rutas de archivos
    documents_path: str = os.getenv("DOCUMENTS_PATH", "documents")
    photos_path: str = os.getenv("PHOTOS_PATH", "photos")
    exports_path: str = os.getenv("EXPORTS_PATH", "exports")
    
    # PDF
    pdf_author: str = os.getenv("PDF_AUTHOR", "Sistema de Gestión de Personal")
    pdf_title: str = os.getenv("PDF_TITLE", "Documentos Oficiales")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "app.log")
    
    # Directorio base de la aplicación
    base_dir: Path = Path(__file__).parent.parent.parent
    
    def __post_init__(self):
        """Inicializa las rutas después de la creación"""
        # Convertir rutas a absolutas
        self.documents_path = str(self.base_dir / self.documents_path)
        self.photos_path = str(self.base_dir / self.photos_path)
        self.exports_path = str(self.base_dir / self.exports_path)
        self.log_file = str(self.base_dir / self.log_file)
        
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