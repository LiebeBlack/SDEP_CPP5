"""
Database Configuration
Configuración de base de datos SQLite

La ruta de la base de datos se resuelve siempre a partir de
settings.database_path (absoluta y única), evitando la creación de
archivos .db duplicados según el directorio de trabajo.
"""

import logging
from pathlib import Path
from typing import Optional, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from src.models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuración de la base de datos SQLite"""

    def __init__(self):
        from src.config import settings

        # Ruta absoluta y única de la base de datos
        self.database_path = settings.database_path
        self.database_url = settings.database_url
        self.echo = settings.debug

        self._ensure_data_directory()

        self.engine = self._create_engine()
        self.SessionFactory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        self.SessionLocal = scoped_session(self.SessionFactory)

        logger.info(f"Base de datos configurada: {self.database_path}")

    def _safe_log_error(self, error: Exception, context: Dict = None):
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(error, context=context)
        except Exception:
            pass

    def _safe_log_event(self, event_type, details: Dict = None):
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_system_event(event_type, details=details)
        except Exception:
            pass

    def _ensure_data_directory(self):
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_engine(self):
        try:
            engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False, "timeout": 30},
                echo=self.echo,
                pool_pre_ping=True,
            )
            logger.info("Engine de base de datos creado exitosamente")
            return engine
        except Exception as e:
            logger.error(f"Error creando engine de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "create_engine"})
            raise

    def create_tables(self):
        """Crea todas las tablas que aún no existan"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tablas de base de datos verificadas exitosamente")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creando tablas: {e}")
            self._safe_log_error(e, context={"operation": "create_tables"})
            raise

    def drop_tables(self):
        """Elimina todas las tablas de la base de datos con backup previo"""
        try:
            try:
                from src.utils.backup_manager import get_backup_manager
                backup_mgr = get_backup_manager()
                backup_info = backup_mgr.create_backup("pre_drop_tables", compress=True)
                logger.info(f"Backup creado antes de eliminar tablas: {backup_info.get('name')}")
            except Exception as e:
                logger.warning(f"No se pudo crear backup antes de eliminar tablas: {e}")

            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Tablas de base de datos eliminadas")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error eliminando tablas: {e}")
            self._safe_log_error(e, context={"operation": "drop_tables"})
            raise

    def get_session(self):
        """
        Retorna una sesión de base de datos ligada al registry scoped

        La misma sesión se reutiliza dentro del hilo hasta que se cierra
        con close_session(). Es la opción por defecto para operaciones
        puntuales (auditoría, configuración, etc.).
        """
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"Error obteniendo sesión de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "get_session"})
            raise

    def new_session(self):
        """
        Retorna una sesión independiente y no gestionada por el registry

        Las sesiones scoped se cierran en cascada (SessionLocal.remove),
        invalidando cualquier objeto que estuvieran cargando. Una ventana
        de larga duración (MainWindow) necesita una sesión propia que
        sobreviva a esas operaciones.
        """
        return self.SessionFactory()

    def close_session(self, session):
        """Cierra una sesión de base de datos de forma segura"""
        if session is not None:
            try:
                session.close()
            except Exception as e:
                logger.warning(f"Error cerrando sesión de base de datos: {e}")
        try:
            self.SessionLocal.remove()
        except Exception as e:
            logger.warning(f"Error removiendo sesión: {e}")

    def init_db(self):
        """Inicializa la base de datos: tablas, verificación y datos semilla"""
        try:
            logger.info("Inicializando base de datos...")
            self.create_tables()
            self._check_integrity()
            self._seed_initial_data()
            self._seed_initial_user()

            # Crear backup inicial una sola vez (si la BD es nueva)
            from pathlib import Path as _Path
            db_file = _Path(self.database_path)
            if not db_file.exists() or db_file.stat().st_size == 0:
                try:
                    from src.utils.backup_manager import get_backup_manager
                    get_backup_manager().create_backup("initial_setup", compress=True)
                except Exception as e:
                    logger.warning(f"No se pudo crear backup inicial: {e}")

            logger.info("Base de datos inicializada exitosamente")
            try:
                from src.utils.audit_logger import AuditEventType
                self._safe_log_event(AuditEventType.SYSTEM_START, details={"operation": "init_db"})
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            self._safe_log_error(e, context={"operation": "init_db"})
            raise

    def _check_integrity(self):
        """Ejecuta PRAGMA quick_check y registra advertencias sin abortar"""
        db_path = Path(self.database_path)
        if not db_path.exists():
            return
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("PRAGMA quick_check")).scalar()
            if result and result != "ok":
                logger.warning(f"Integridad de base de datos: {result}")
            else:
                logger.info("Integridad de base de datos verificada (ok)")
        except Exception as e:
            logger.warning(f"No se pudo verificar la integridad de la base de datos: {e}")

    def _seed_initial_data(self):
        """Inserta la configuración inicial del sistema si no existe"""
        from src.models.configuracion import Configuracion

        session = self.get_session()
        try:
            if session.query(Configuracion).first() is not None:
                return

            configuraciones = [
                Configuracion(clave="nombre_institucion", valor="Institución Educativa",
                              descripcion="Nombre de la institución educativa",
                              tipo_dato="string", categoria="general"),
                Configuracion(clave="ruc", valor="", descripcion="RUC de la institución",
                              tipo_dato="string", categoria="general"),
                Configuracion(clave="direccion", valor="", descripcion="Dirección de la institución",
                              tipo_dato="string", categoria="general"),
                Configuracion(clave="telefono", valor="", descripcion="Teléfono de la institución",
                              tipo_dato="string", categoria="general"),
                Configuracion(clave="email", valor="", descripcion="Email de la institución",
                              tipo_dato="string", categoria="general"),
                Configuracion(clave="porcentaje_seguro", valor="4.5",
                              descripcion="Porcentaje de deducción por seguro social",
                              tipo_dato="float", categoria="nomina"),
                Configuracion(clave="porcentaje_pension", valor="5.0",
                              descripcion="Porcentaje de deducción por pensión",
                              tipo_dato="float", categoria="nomina"),
                Configuracion(clave="porcentaje_impuesto", valor="0.0",
                              descripcion="Porcentaje de deducción por impuesto",
                              tipo_dato="float", categoria="nomina"),
                Configuracion(clave="salario_minimo", valor="130.0",
                              descripcion="Salario mínimo mensual",
                              tipo_dato="float", categoria="nomina"),
                Configuracion(clave="dias_vacaciones_anual", valor="15",
                              descripcion="Días de vacaciones anuales",
                              tipo_dato="int", categoria="recursos_humanos"),
                Configuracion(clave="horas_laborales_semana", valor="40",
                              descripcion="Horas laborales semanales",
                              tipo_dato="int", categoria="recursos_humanos"),
                Configuracion(clave="backup_enabled", valor="true",
                              descripcion="Habilitar backups automáticos",
                              tipo_dato="bool", categoria="seguridad"),
                Configuracion(clave="backup_interval_hours", valor="24",
                              descripcion="Intervalo de backups en horas",
                              tipo_dato="int", categoria="seguridad"),
                Configuracion(clave="audit_enabled", valor="true",
                              descripcion="Habilitar auditoría de eventos",
                              tipo_dato="bool", categoria="seguridad"),
            ]
            session.add_all(configuraciones)
            session.commit()
            logger.info(f"Configuraciones iniciales insertadas: {len(configuraciones)}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error insertando configuraciones iniciales: {e}")
            self._safe_log_error(e, context={"operation": "seed_initial_data"})
            raise
        finally:
            self.close_session(session)

    def _seed_initial_user(self):
        """Crea el usuario administrador por defecto en el primer arranque"""
        session = self.get_session()
        try:
            from src.models import Usuario
            if session.query(Usuario).count() > 0:
                return
            from src.services.auth_service import ensure_default_admin
            ensure_default_admin(session)
        except Exception as e:
            logger.warning(f"No se pudo crear el usuario inicial: {e}")
        finally:
            self.close_session(session)

    def create_backup(self, backup_name: Optional[str] = None) -> Dict:
        """Crea un backup de la base de datos"""
        try:
            from src.utils.backup_manager import get_backup_manager
            return get_backup_manager().create_backup(backup_name)
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            self._safe_log_error(e, context={"operation": "create_backup"})
            raise

    def restore_backup(self, backup_name: str) -> bool:
        """Restaura un backup de la base de datos"""
        try:
            from src.utils.backup_manager import get_backup_manager
            result = get_backup_manager().restore_backup(backup_name)
            try:
                from src.utils.audit_logger import AuditEventType
                self._safe_log_event(AuditEventType.SYSTEM_RESTORE, details={"backup_name": backup_name})
            except Exception:
                pass
            return result
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            self._safe_log_error(e, context={"operation": "restore_backup", "backup_name": backup_name})
            raise

    def get_backup_status(self) -> Dict:
        """Obtiene el estado del sistema de backups"""
        try:
            from src.utils.backup_manager import get_backup_manager
            backup_mgr = get_backup_manager()
            backups = backup_mgr.list_backups()
            return {
                "total_backups": len(backups),
                "latest_backup": backups[0] if backups else None,
                "backup_enabled": True,
                "database_path": str(Path(self.database_path).absolute()),
                "backup_directory": str(backup_mgr.backup_dir.absolute()),
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado de backups: {e}")
            return {"error": str(e)}


# Instancia global de configuración de base de datos
db_config = DatabaseConfig()


def get_db():
    """Retorna una sesión de base de datos (para dependency injection)"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        db_config.close_session(session)
