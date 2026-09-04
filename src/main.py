"""
Main Entry Point
Punto de entrada principal de la aplicación con mejoras de seguridad
"""

import sys
import logging
from pathlib import Path
import io
import signal

# Configurar UTF-8 para Windows de forma segura
try:
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# Asegurar que el directorio raíz esté en sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Nitidez en Windows con escalado > 100 %: debe ejecutarse ANTES de
# crear cualquier ventana Tk para evitar una UI borrosa o deformada.
try:
    from src.gui.theme import enable_windows_dpi_awareness
    enable_windows_dpi_awareness()
except Exception:
    pass

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) if sys.stdout else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


# Variable global para manejo de cierre seguro
application_instance = None


def _notificar_error_global(titulo: str, mensaje: str):
    """Intenta informar al usuario del error sin bloquear la consola"""
    try:
        from tkinter import messagebox
        messagebox.showerror(titulo, mensaje)
    except Exception:
        pass


def manejar_excepcion_no_capturada(exc_type, exc_value, exc_traceback):
    """
    Fallback global ante fallos: registra y avisa cualquier excepción
    no capturada en lugar de dejar que el programa termine en silencio.

    Registra en el log y en la auditoría y muestra un mensaje amigable;
    el programa continúa o cierra según la gravedad del error.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error(
        "Excepción no capturada",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    try:
        from src.utils.audit_logger import get_audit_logger
        audit = get_audit_logger()
        if audit:
            audit.log_error(exc_value, context={"operation": "excepcion_global"})
    except Exception:
        pass
    _notificar_error_global(
        "Error inesperado",
        f"Ocurrió un error no controlado:\n{exc_value}\n\n"
        "El sistema intentará continuar. Si el error persiste, "
        "contacte al administrador.",
    )


def instalar_manejador_excepciones():
    """
    Instala los manejadores globales de excepciones (fallback ante fallos).

    Cubre tanto el hilo principal como los hilos secundarios; la instalación
    es idempotente para no pisar manejadores previos en reejecuciones.
    """
    if getattr(sys, "_sgp_excepthook_instalado", False):
        return
    sys.excepthook = manejar_excepcion_no_capturada
    try:
        import threading
        threading.excepthook = manejar_excepcion_no_capturada
    except Exception:
        pass
    sys._sgp_excepthook_instalado = True


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
        try:
            from src.utils.audit_logger import get_audit_logger, AuditEventType
            audit = get_audit_logger()
            if audit:
                audit.log_system_event(AuditEventType.SYSTEM_START, 
                                       details={"operation": "setup_environment"})
        except Exception:
            pass
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar el entorno: {str(e)}")
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "setup_environment"})
        except Exception:
            pass
        return False


def initialize_database():
    """Inicializa la base de datos con seguridad mejorada"""
    try:
        from src.config import db_config
        
        logger.info("Inicializando base de datos...")
        db_config.init_db()
        
        # Verificar estado de backups
        backup_status = db_config.get_backup_status()
        logger.info(f"Estado de backups: {backup_status.get('total_backups', 0)} backups disponibles")
        
        logger.info("Base de datos inicializada correctamente")
        try:
            from src.utils.audit_logger import get_audit_logger, AuditEventType
            audit = get_audit_logger()
            if audit:
                audit.log_system_event(AuditEventType.SYSTEM_START, 
                                       details={"operation": "initialize_database"})
        except Exception:
            pass
        return True
        
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "initialize_database"})
        except Exception:
            pass
        return False


def run_application():
    """
    Ejecuta la aplicación GUI con sesiones de usuario

    Muestra la ventana de inicio de sesión y, tras autenticar, la ventana
    principal. Al cerrar sesión se vuelve al login; al salir se termina.
    """
    global application_instance
    try:
        from src.gui.login_window import LoginWindow
        from src.gui.main_window import MainWindow
        from src.services.auth_service import AuthService

        logger.info("Iniciando aplicación...")
        while True:
            # 1. Inicio de sesión
            login = LoginWindow()
            user = login.run()
            if user is None:
                # Sesión cancelada: la ventana sigue existiendo y se cierra
                try:
                    login.destroy()
                except Exception:
                    pass
                logger.info("Sesión cancelada por el usuario")
                break

            # Copiar a valores simples mientras el usuario sigue ligado a la
            # sesión de login; la ventana principal re-liga el objeto a su
            # propia sesión (ver MainWindow).
            username = user.username
            rol = user.rol_valor
            logger.info(f"Sesión iniciada: {username} ({rol})")

            # 2. Ventana principal (con limpieza garantizada ante fallos).
            # La ventana de login se OCULTÓ al autenticar (no se destruyó):
            # se destruye aquí, DESPUÉS de que la ventana principal haya
            # arrancado, para evitar el patrón "destruir la raíz antigua
            # justo antes de crear la raíz nueva", que en algunos equipos
            # deja la segunda ventana en negro sin responder.
            app = None
            try:
                app = MainWindow(current_user=user)
                try:
                    app.update()
                except Exception:
                    pass
            except Exception:
                # Fallback: si la construcción falló a mitad de camino,
                # liberar la sesión scoped del hilo antes de propagar.
                try:
                    from src.config import db_config
                    db_config.SessionLocal.remove()
                except Exception:
                    pass
                try:
                    login.destroy()
                except Exception:
                    pass
                raise
            try:
                login.destroy()
            except Exception:
                pass
            application_instance = app
            try:
                status = app.run()
            finally:
                # Fallback anti-fugas: la sesión de la ventana se cierra
                # siempre, incluso si la ejecución falló o se interrumpió.
                application_instance = None
                try:
                    from src.config import db_config
                    db_config.close_session(app.session)
                except Exception:
                    pass

            # 3. Registro de cierre de sesión en auditoría
            try:
                from src.config import db_config
                session = db_config.get_session()
                try:
                    AuthService(session).cerrar_sesion(username)
                finally:
                    db_config.close_session(session)
            except Exception:
                pass

            if status != "logout":
                logger.info("Aplicación finalizada")
                break

    except Exception as e:
        logger.error(f"Error al ejecutar la aplicación: {str(e)}")
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "run_application"})
        except Exception:
            pass
        raise


def cleanup_application():
    """Limpieza segura de recursos antes de cerrar"""
    global application_instance
    try:
        from src.config import db_config
        
        logger.info("Iniciando limpieza de recursos...")
        
        # Cerrar sesión de base de datos si existe
        if application_instance and hasattr(application_instance, 'session'):
            try:
                db_config.close_session(application_instance.session)
                logger.info("Sesión de base de datos cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando sesión de base de datos: {e}")
        
        # Crear backup al cerrar (si está habilitado en la configuración)
        try:
            from src.config import db_config as _db
            session = _db.get_session()
            try:
                from src.repositories import ConfiguracionRepository
                habilitado = ConfiguracionRepository(session).get_valor(
                    "backup_enabled", True)
            finally:
                _db.close_session(session)

            if not habilitado:
                logger.info("Backup al cerrar omitido (deshabilitado en configuración)")
            else:
                from src.utils.backup_manager import get_backup_manager
                backup_mgr = get_backup_manager()
                if backup_mgr:
                    backup_info = backup_mgr.create_backup("auto_shutdown", compress=True)
                    logger.info(f"Backup automático creado: {backup_info.get('name')}")
        except Exception as e:
            logger.warning(f"No se pudo crear backup al cerrar: {e}")
        
        try:
            from src.utils.audit_logger import get_audit_logger, AuditEventType
            audit = get_audit_logger()
            if audit:
                audit.log_system_event(AuditEventType.SYSTEM_STOP, 
                                       details={"operation": "cleanup_application"})
        except Exception:
            pass
        logger.info("Limpieza de recursos completada")
        
    except Exception as e:
        logger.error(f"Error durante limpieza: {e}")
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "cleanup_application"})
        except Exception:
            pass


def _selftest() -> bool:
    """
    Verificación de arranque para el ejecutable empaquetado

    Se invoca con: SistemaGestionPersonal.exe --selftest
    Valida entorno, base de datos y que los módulos GUI quedaron
    incluidos en el paquete. El código de salida indica el resultado.
    """
    try:
        if not setup_environment():
            logger.error("Selftest: falló la configuración del entorno")
            return False
        if not initialize_database():
            logger.error("Selftest: falló la inicialización de la base de datos")
            return False

        # Fuerza la importación de los módulos GUI para detectar paquetes
        # faltantes en el build (customtkinter, tkinter, etc.)
        import src.gui.login_window  # noqa: F401
        import src.gui.main_window  # noqa: F401
        import src.gui.frames  # noqa: F401

        from src.config import settings
        from src.utils.backup_manager import get_backup_manager
        get_backup_manager()
        logger.info(f"Selftest OK (v{settings.app_version})")
        return True
    except Exception as e:
        logger.error(f"Selftest: error inesperado: {e}")
        return False


def main():
    """Función principal con mejoras de seguridad"""
    # Fallback global ante excepciones no capturadas
    instalar_manejador_excepciones()

    # Modo de autoverificación para el ejecutable empaquetado
    if "--selftest" in sys.argv:
        ok = _selftest()
        sys.exit(0 if ok else 1)

    # Configurar manejadores de señales
    try:
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass
    
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