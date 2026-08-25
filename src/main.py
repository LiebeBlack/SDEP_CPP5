"""
Main Entry Point
Punto de entrada principal de la aplicación
"""

import sys
import os
import logging
from pathlib import Path

# Asegurar que el directorio raíz esté en sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Configura el entorno de la aplicación"""
    try:
        # Asegurar que los directorios necesarios existan
        from src.config import settings
        from src.utils.helpers import ensure_directory_exists
        
        directories = [
            settings.documents_path,
            settings.photos_path,
            settings.exports_path
        ]
        
        for directory in directories:
            ensure_directory_exists(directory)
        
        logger.info("Entorno configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar el entorno: {str(e)}")
        return False


def initialize_database():
    """Inicializa la base de datos"""
    try:
        from src.config import db_config
        
        logger.info("Inicializando base de datos...")
        db_config.init_db()
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        return False


def run_application():
    """Ejecuta la aplicación GUI"""
    try:
        from src.gui.main_window import MainWindow
        
        logger.info("Iniciando aplicación...")
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logger.error(f"Error al ejecutar la aplicación: {str(e)}")
        raise


def main():
    """Función principal"""
    logger.info("=" * 50)
    logger.info("SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA")
    logger.info("=" * 50)
    
    # Configurar entorno
    if not setup_environment():
        logger.error("No se pudo configurar el entorno. Saliendo...")
        sys.exit(1)
    
    # Inicializar base de datos
    if not initialize_database():
        logger.error("No se pudo inicializar la base de datos. Saliendo...")
        sys.exit(1)
    
    # Ejecutar aplicación
    try:
        run_application()
        logger.info("Aplicación finalizada correctamente")
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()