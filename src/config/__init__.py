"""
Config Module
Configuración de la aplicación
"""

# settings debe inicializarse antes que database: la instancia de
# DatabaseConfig resuelve su ruta a partir de settings en tiempo de import.
from .settings import Settings, settings
from .database import DatabaseConfig, db_config, get_db

__all__ = [
    "DatabaseConfig", "db_config", "get_db",
    "Settings", "settings"
]