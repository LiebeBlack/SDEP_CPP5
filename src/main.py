"""
Main Entry Point
Punto de entrada principal de la aplicación con mejoras de seguridad
"""

import io
import logging
import logging.handlers
import signal
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Configurar UTF-8 para Windows de forma segura
try:
    if sys.stdout is not None and hasattr(sys.stdout, "buffer") and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr is not None and hasattr(sys.stderr, "buffer") and sys.stderr.buffer is not None:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    logger.debug("paso de arranque ignorado", exc_info=True)

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
    logger.debug("paso de arranque ignorado", exc_info=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# El ejecutable empaquetado es de VENTANA (console=False): no hay stdout, de
# modo que un logging que solo escribe a consola no deja rastro. Un manejador
# de ARCHIVO garantiza que cualquier fallo de arranque quede registrado en
# disco y pueda diagnosticarse (SDEP_CPP5.exe "se cierra sin abrir").


def _ruta_log_arranque() -> Path:
    """Ruta del log principal, a prueba de fallos (nunca se propaga)."""
    try:
        from src.config import settings

        return Path(settings.log_file)
    except Exception:
        try:
            base = Path.home() / "SistemaGestionPersonal"
            base.mkdir(parents=True, exist_ok=True)
            return base / "app.log"
        except Exception:
            return Path.home() / "sdep_arranque.log"


def _configurar_logging() -> Path:
    """Configura logging a consola (si existe) y, sobre todo, a archivo."""
    formato = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)

    if sys.stdout is not None:
        consola = logging.StreamHandler(sys.stdout)
        consola.setFormatter(formato)
        raiz.addHandler(consola)
    else:
        raiz.addHandler(logging.NullHandler())

    ruta_log = _ruta_log_arranque()
    try:
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        archivo = logging.handlers.RotatingFileHandler(
            ruta_log, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        archivo.setFormatter(formato)
        raiz.addHandler(archivo)
    except Exception:
        raiz.debug("No se pudo abrir el archivo de log %s", ruta_log, exc_info=True)

    return ruta_log


RUTA_LOG_ARRANQUE = _configurar_logging()


# Variable global para manejo de cierre seguro
application_instance = None


def _dialogo_win32(titulo: str, mensaje: str) -> bool:
    """Muestra un diálogo nativo de Windows (user32.MessageBoxW).

    Respaldo para cuando no hay ventanas Tk disponibles. El ejecutable es de
    VENTANA (sin consola): sin un cuadro de diálogo visible, un fallo de
    arranque sería invisible y el programa parecería "cerrarse sin abrir".
    """
    # ``ctypes.windll`` solo existe en Windows; comprobarlo antes mantiene el
    # tipo correcto en los demás sistemas (y evita el error de mypy allí).
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        # MB_OK | MB_ICONERROR | MB_SETFOREGROUND | MB_SYSTEMMODAL
        banderas = 0x00000000 | 0x00000010 | 0x00010000 | 0x00001000
        ctypes.windll.user32.MessageBoxW(None, str(mensaje), str(titulo), banderas)
        return True
    except Exception:
        logger.debug("paso de arranque ignorado", exc_info=True)
        return False


def _mostrar_dialogo_error(titulo: str, mensaje: str) -> None:
    """Muestra un diálogo de error: primero con Tk, si no, con Windows."""
    try:
        from tkinter import messagebox

        messagebox.showerror(titulo, mensaje)
        return
    except Exception:
        logger.debug("paso de arranque ignorado", exc_info=True)
    _dialogo_win32(titulo, mensaje)


def _notificar_error_global(titulo: str, mensaje: str):
    """Intenta informar al usuario del error sin bloquear la consola"""
    _mostrar_dialogo_error(titulo, mensaje)


def _alerta_fatal(titulo: str, mensaje: str) -> None:
    """
    Muestra un diálogo visible ante un fallo fatal de arranque.

    El ejecutable de ventana no tiene consola: si la aplicación termina con
    ``sys.exit(1)`` sin avisar, el usuario solo ve que "no abre". Aquí se
    registra el error en el archivo de log y se muestra un cuadro de
    diálogo para que la causa nunca pase inadvertida.
    """
    try:
        logger.error("%s: %s", titulo, mensaje.replace("\n", " "))
    except Exception:
        pass
    # Tk primero y, si no hay ventanas disponibles, un diálogo nativo de
    # Windows: así el motivo del fallo nunca queda solo en el log.
    _mostrar_dialogo_error(titulo, mensaje)


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
        logger.debug("paso de arranque ignorado", exc_info=True)
    _notificar_error_global(
        "Error inesperado",
        f"Ocurrió un error no controlado:\n{exc_value}\n\n"
        "El sistema intentará continuar. Si el error persiste, "
        "contacte al administrador.",
    )


def manejar_excepcion_en_hilo(args):
    """
    Fallback para excepciones no capturadas en hilos secundarios.

    ``threading.excepthook`` recibe UN objeto ``ExceptHookArgs`` (con
    ``exc_type``, ``exc_value``, ``exc_traceback`` y ``thread``), no la
    terna que usa ``sys.excepthook``. Asignarle directamente la función
    del hilo principal hacía que el propio hook fallara con ``TypeError``
    y ocultara la excepción original.

    Además, un hilo de fondo no debe abrir un cuadro de diálogo de Tk:
    Tk no es seguro entre hilos y hacerlo puede congelar o cerrar la
    aplicación. Aquí solo se registra y se audita el fallo; la interfaz
    sigue siendo responsabilidad del hilo principal.
    """
    exc_type = getattr(args, "exc_type", None)
    exc_value = getattr(args, "exc_value", None)
    exc_traceback = getattr(args, "exc_traceback", None)
    if exc_type is None:
        return
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logger.error(
        "Excepción no capturada en el hilo %r",
        getattr(args, "thread", None),
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    try:
        from src.utils.audit_logger import get_audit_logger

        audit = get_audit_logger()
        if audit:
            audit.log_error(exc_value, context={"operation": "excepcion_hilo"})
    except Exception:
        logger.debug("paso de arranque ignorado", exc_info=True)


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

        threading.excepthook = manejar_excepcion_en_hilo
    except Exception:
        logger.debug("paso de arranque ignorado", exc_info=True)
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
            settings.logs_dir,
            settings.backups_dir,
            settings.cache_dir,
            settings.temp_dir,
        ]

        for directory in directories:
            ensure_directory_exists(directory)

        # Purga de los temporales de ejecuciones anteriores (ReportLab,
        # previsualizaciones) antes de que la aplicación empiece a escribir:
        # nadie los borraba y tmp/ crecía sin límite.
        try:
            from src.utils.document_manager import document_manager

            eliminados = document_manager.limpiar_temporales()
            if eliminados:
                logger.info("Temporales de ejecuciones anteriores eliminados: %s", eliminados)
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)

        logger.info("Entorno configurado correctamente")
        try:
            from src.utils.audit_logger import AuditEventType, get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_system_event(
                    AuditEventType.SYSTEM_START, details={"operation": "setup_environment"}
                )
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)
        return True

    except Exception as e:
        logger.error(f"Error al configurar el entorno: {str(e)}")
        try:
            from src.utils.audit_logger import get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "setup_environment"})
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)
        return False


def iniciar_servidor_sincronizacion() -> bool:
    """
    Levanta el nodo central si este equipo fue designado como servidor

    El servidor y la auto-configuración del puesto (cuentas iniciales, alta del
    dispositivo y destino de sincronización) se preparan antes de arrancar el
    agente, para que este ya encuentre la configuración escrita. Un fallo aquí
    nunca impide abrir la aplicación.
    """
    try:
        from sync_agent.servidor_embebido import (
            CLAVE_SERVIDOR_AUTO,
            ESTADO_ACTIVO,
            iniciar_servidor_embebido,
            preferencia_servidor,
        )

        preferencia = preferencia_servidor()
        if preferencia is None:
            # Instalación nueva: el nodo central se abre solo. El teléfono no
            # tiene configuración manual y necesita encontrarlo apenas arranca
            # el sistema, incluso antes de que alguien inicie sesión aquí.
            preferencia = True
            from src.config import settings as _settings

            _settings.set_config_value(CLAVE_SERVIDOR_AUTO, True)
            logger.info("Nodo central activado por primera vez en este equipo")
        if preferencia is not True:
            return False
        estado = iniciar_servidor_embebido(esperar=True)
        if estado.get("estado") == ESTADO_ACTIVO:
            logger.info(
                "Servidor central iniciado con la aplicación: %s",
                estado.get("url_red"),
            )
            return True
        logger.warning(
            "El servidor central no quedó disponible: %s",
            estado.get("error") or estado.get("estado"),
        )
        return False
    except Exception as e:
        logger.warning(f"No se pudo iniciar el servidor central: {e}")
        return False


def iniciar_sincronizacion():
    """
    Arranca el agente de sincronización en segundo plano

    Es opcional por diseño: si el equipo no está configurado, si está
    deshabilitado o si el paquete del agente no está disponible, la aplicación
    funciona igual y solo se registra el motivo. La captura de cambios se
    activa antes de arrancar el hilo, de modo que ninguna escritura del usuario
    quede fuera del journal.
    """
    try:
        from sync_agent import iniciar_agente
        from sync_agent.config import cargar

        config = cargar()
        if not config.activo:
            problemas = config.problemas()
            logger.info(
                "Sincronización inactiva en este equipo: %s",
                "; ".join(problemas) if problemas else "deshabilitada en la configuración",
            )
            return False

        from urllib.parse import urlparse

        # Si el destino es el nodo central de este mismo equipo y ese nodo no
        # está activo (el usuario lo detuvo desde la bandeja), arrancar el
        # agente solo produciría un fallo de conexión cada 30 segundos.
        if urlparse(config.url_servidor).hostname in ("127.0.0.1", "localhost", "::1"):
            from sync_agent.servidor_embebido import (
                ESTADO_DETENIDO,
                ESTADO_ERROR,
                estado_servidor_embebido,
            )

            estado_local = estado_servidor_embebido().get("estado")
            # ``ocupado`` significa que otra instancia ya está sirviendo en el
            # puerto: ese nodo sí responde y el agente puede usarlo.
            if estado_local in (ESTADO_DETENIDO, ESTADO_ERROR):
                logger.info(
                    "Sincronización local omitida: el nodo central de este equipo está detenido"
                )
                return False

        from src.config import db_config

        db_config.preparar_sincronizacion()
        db_config.activar_captura_sincronizacion()
        iniciar_agente(config)
        logger.info("Agente de sincronización iniciado")
        return True
    except Exception as e:
        logger.warning(f"No se pudo iniciar la sincronización: {e}")
        return False


def initialize_database():
    """Inicializa la base de datos con seguridad mejorada"""
    try:
        from src.config import db_config

        logger.info("Inicializando base de datos...")
        db_config.init_db()

        # Verificar estado de backups
        backup_status = db_config.get_backup_status()
        logger.info(
            f"Estado de backups: {backup_status.get('total_backups', 0)} backups disponibles"
        )

        logger.info("Base de datos inicializada correctamente")
        try:
            from src.utils.audit_logger import AuditEventType, get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_system_event(
                    AuditEventType.SYSTEM_START, details={"operation": "initialize_database"}
                )
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)
        return True

    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        try:
            from src.utils.audit_logger import get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "initialize_database"})
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)
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
                    logger.debug("paso de arranque ignorado", exc_info=True)
                logger.info("Sesión cancelada por el usuario")
                break

            # La ventana de login cierra su sesión al autenticar: se usan
            # los valores simples que copió antes de cerrarla y la ventana
            # principal vuelve a consultar el usuario en su propia sesión
            # (ver MainWindow._inicializar_sesion).
            username = login.username_autenticado or ""
            rol = login.rol_autenticado or ""
            logger.info(f"Sesión iniciada: {username} ({rol})")

            # 2. Ventana principal (con limpieza garantizada ante fallos).
            # La ventana de login se OCULTÓ al autenticar (no se destruyó):
            # se destruye aquí, DESPUÉS de que la ventana principal haya
            # arrancado, para evitar el patrón "destruir la raíz antigua
            # justo antes de crear la raíz nueva", que en algunos equipos
            # deja la segunda ventana en negro sin responder.
            app = None
            try:
                # ``preparar_servidor`` pregunta (solo la primera vez) si este
                # equipo será el nodo central y, si corresponde, lo arranca
                # antes de vincular el agente de sincronización de la ventana.
                app = MainWindow(current_user=username, preparar_servidor=True)
                try:
                    app.update()
                except Exception:
                    logger.debug("paso de arranque ignorado", exc_info=True)
            except Exception:
                # Fallback: si la construcción falló a mitad de camino,
                # liberar la sesión scoped del hilo antes de propagar.
                try:
                    from src.config import db_config

                    db_config.SessionLocal.remove()
                except Exception:
                    logger.debug("paso de arranque ignorado", exc_info=True)
                try:
                    login.destroy()
                except Exception:
                    logger.debug("paso de arranque ignorado", exc_info=True)
                raise
            try:
                login.destroy()
            except Exception:
                logger.debug("paso de arranque ignorado", exc_info=True)
            application_instance = app
            try:
                app.iniciar_bandeja_servidor()
            except Exception:
                logger.debug("No se pudo mostrar la bandeja del servidor", exc_info=True)
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
                    logger.debug("paso de arranque ignorado", exc_info=True)

            # 3. Registro de cierre de sesión en auditoría
            try:
                from src.config import db_config

                session = db_config.get_session()
                try:
                    AuthService(session).cerrar_sesion(username)
                finally:
                    db_config.close_session(session)
            except Exception:
                logger.debug("paso de arranque ignorado", exc_info=True)

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
            logger.debug("paso de arranque ignorado", exc_info=True)
        raise


def cleanup_application():
    """Limpieza segura de recursos antes de cerrar"""
    try:
        from src.config import db_config

        logger.info("Iniciando limpieza de recursos...")

        # Cerrar sesión de base de datos si existe
        if application_instance and hasattr(application_instance, "session"):
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

                habilitado = ConfiguracionRepository(session).get_valor("backup_enabled", True)
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
            from src.utils.audit_logger import AuditEventType, get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_system_event(
                    AuditEventType.SYSTEM_STOP, details={"operation": "cleanup_application"}
                )
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)

        # Liberar TODAS las conexiones del pool de la base de datos y el
        # registry de sesiones (anti-fugas de conexiones/archivos).
        # El agente se detiene ANTES: abre sus propias sesiones y no debe
        # quedar corriendo contra un pool ya cerrado.
        try:
            from sync_agent import detener_agente

            detener_agente(timeout=5.0)
            logger.info("Agente de sincronización detenido")
        except Exception as e:
            logger.warning(f"Error deteniendo el agente de sincronización: {e}")

        # El nodo central se cierra DESPUÉS del agente: así ninguna
        # sincronización en curso se queda con el puerto a medio cerrar.
        try:
            from sync_agent.servidor_embebido import detener_servidor_embebido

            detener_servidor_embebido()
            logger.info("Servidor central detenido")
        except Exception as e:
            logger.warning(f"Error deteniendo el servidor central: {e}")

        try:
            db_config.dispose()
            logger.info("Pool de conexiones de base de datos liberado")
        except Exception as e:
            logger.warning(f"Error liberando recursos de base de datos: {e}")

        logger.info("Limpieza de recursos completada")

    except Exception as e:
        logger.error(f"Error durante limpieza: {e}")
        try:
            from src.utils.audit_logger import get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_error(e, context={"operation": "cleanup_application"})
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)


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
        import src.gui.frames  # noqa: F401
        import src.gui.login_window  # noqa: F401
        import src.gui.main_window  # noqa: F401

        # El agente de sincronización es opcional en la instalación local:
        # su ausencia no debe hacer fallar la autoverificación del ejecutable.
        try:
            import sync_agent  # noqa: F401
            import sync_agent.servidor_embebido  # noqa: F401
        except ImportError:
            logger.info("Selftest: agente de sincronización no incluido (opcional)")

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
        logger.debug("paso de arranque ignorado", exc_info=True)

    logger.info("=" * 50)
    logger.info("SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA")
    logger.info("Versión Segura con Backups y Auditoría")
    logger.info("=" * 50)

    # Configurar entorno
    if not setup_environment():
        _alerta_fatal(
            "Error de arranque",
            "No se pudo preparar la carpeta de datos de la aplicación.\n\n"
            f"Detalle en el registro: {RUTA_LOG_ARRANQUE}\n\n"
            "Revise los permisos del perfil de usuario e intente de nuevo.",
        )
        sys.exit(1)

    # Inicializar base de datos
    if not initialize_database():
        _alerta_fatal(
            "Error de arranque",
            "No se pudo inicializar la base de datos.\n\n"
            f"Detalle en el registro: {RUTA_LOG_ARRANQUE}\n\n"
            "Cierre cualquier otra copia del sistema que esté abierta e "
            "intente de nuevo.",
        )
        sys.exit(1)

    # Servidor central (si este equipo quedó designado como tal) y
    # sincronización con la intranet. Ninguno de los dos bloquea el arranque.
    iniciar_servidor_sincronizacion()
    iniciar_sincronizacion()

    # Ejecutar aplicación
    try:
        run_application()
        logger.info("Aplicación finalizada correctamente")
        cleanup_application()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
        cleanup_application()
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {str(e)}", exc_info=True)
        _alerta_fatal(
            "Error fatal",
            f"La aplicación encontró un error y debe cerrarse:\n\n{e}\n\n"
            f"Detalle en el registro: {RUTA_LOG_ARRANQUE}",
        )
        cleanup_application()
        sys.exit(1)
    finally:
        # Cierra los archivos de log al terminar (anti-fuga de descriptores).
        # Va al final porque después de esto ya no se debe escribir logs.
        try:
            logging.shutdown()
        except Exception:
            logger.debug("paso de arranque ignorado", exc_info=True)


if __name__ == "__main__":
    main()
