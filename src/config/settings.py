"""
Settings Configuration
Configuración general de la aplicación
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    """Configuración de la aplicación"""
    
    def __init__(self):
        # Directorio base de la aplicación
        self.base_dir = Path(__file__).parent.parent.parent
        
        # Aplicación
        self.app_name = os.getenv("APP_NAME", "Sistema de Gestión de Personal")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Base de datos
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///personal_management.db")
        self.database_path = os.getenv("DATABASE_PATH", "personal_management.db")
        
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