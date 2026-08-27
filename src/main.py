"""
Main Entry Point
Punto de entrada principal de la aplicación con mejoras de seguridad
"""

import sys
import os
import logging
from pathlib import Path
import io
import signal

# Configurar UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Asegurar que el directorio raíz esté en sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# Variable global para manejo de cierre seguro
application_instance = None


def signal_handler(signum, frame):
    """Manejador de señales para cierre seguro"""
    logger.info(f"Señal {signum} recibida, iniciando cierre seguro...")
    if application_instance:
        try:
            cleanup_application()
        except Exception as e:
            logger.error(f"Error durante cierre seguro: {e}")
    sys.exit(0)


def setup_environment():
    """Configura el entorno de la aplicación con verificación de seguridad"""
    try:
        from src.config import settings
        from src.utils.helpers import ensure_directory_exists
        from src.utils.audit_logger import audit_logger, AuditEventType
        
        # Asegurar que los directorios necesarios existan
        directories = [
            settings.documents_path,
            settings.photos_path,
            settings.exports_path,
            str(Path(settings.base_dir) / "logs"),
            str(Path(settings.base_dir) / "backups")
        ]
        
        for directory in directories:
            ensure_directory_exists(directory)
        
        logger.info("Entorno configurado correctamente")
        audit_logger.log_system_event(AuditEventType.SYSTEM_START, 
                                     details={"operation": "setup_environment"})
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar el entorno: {str(e)}")
        from src.utils.audit_logger import audit_logger
        audit_logger.log_error(e, context={"operation": "setup_environment"})
        return False


def initialize_database():
    """Inicializa la base de datos con seguridad mejorada"""
    try:
        from src.config import db_config
        from src.utils.audit_logger import audit_logger, AuditEventType
        
        logger.info("Inicializando base de datos...")
        db_config.init_db()
        
        # Verificar estado de backups
        backup_status = db_config.get_backup_status()
        logger.info(f"Estado de backups: {backup_status.get('total_backups', 0)} backups disponibles")
        
        logger.info("Base de datos inicializada correctamente")
        audit_logger.log_system_event(AuditEventType.SYSTEM_START, 
                                     details={"operation": "initialize_database"})
        return True
        
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        from src.utils.audit_logger import audit_logger
        audit_logger.log_error(e, context={"operation": "initialize_database"})
        return False


def run_application():
    """Ejecuta la aplicación GUI con manejo de errores mejorado"""
    global application_instance
    try:
        from src.gui.main_window import MainWindow
        from src.utils.audit_logger import audit_logger, AuditEventType
        
        logger.info("Iniciando aplicación...")
        app = MainWindow()
        application_instance = app
        
        audit_logger.log_system_event(AuditEventType.SYSTEM_START, 
                                     details={"operation": "run_application"})
        
        app.run()
        
    except Exception as e:
        logger.error(f"Error al ejecutar la aplicación: {str(e)}")
        from src.utils.audit_logger import audit_logger
        audit_logger.log_error(e, context={"operation": "run_application"})
        raise


def cleanup_application():
    """Limpieza segura de recursos antes de cerrar"""
    global application_instance
    try:
        from src.config import db_config
        from src.utils.audit_logger import audit_logger, AuditEventType
        from src.utils.backup_manager import backup_manager
        
        logger.info("Iniciando limpieza de recursos...")
        
        # Cerrar sesión de base de datos si existe
        if application_instance and hasattr(application_instance, 'session'):
            try:
                db_config.close_session(application_instance.session)
                logger.info("Sesión de base de datos cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando sesión de base de datos: {e}")
        
        # Crear backup al cerrar (si está habilitado)
        try:
            backup_info = backup_manager.create_backup("auto_shutdown", compress=True)
            logger.info(f"Backup automático creado: {backup_info['name']}")
        except Exception as e:
            logger.warning(f"No se pudo crear backup al cerrar: {e}")
        
        audit_logger.log_system_event(AuditEventType.SYSTEM_STOP, 
                                     details={"operation": "cleanup_application"})
        logger.info("Limpieza de recursos completada")
        
    except Exception as e:
        logger.error(f"Error durante limpieza: {e}")
        from src.utils.audit_logger import audit_logger
        audit_logger.log_error(e, context={"operation": "cleanup_application"})


def main():
    """Función principal con mejoras de seguridad"""
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA")
    logger.info("Versión Segura con Backups y Auditoría")
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
        cleanup_application()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
        cleanup_application()
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {str(e)}")
        cleanup_application()
        sys.exit(1)


if __name__ == "__main__":
    main()