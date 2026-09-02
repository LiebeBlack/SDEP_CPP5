"""
Database Configuration
Configuración de base de datos SQLite con mejoras de seguridad y backups

Este módulo proporciona:
- Configuración robusta de base de datos
- Manejo de errores mejorado
- Integración con sistema de backups
- Verificación de integridad
- Logging de operaciones
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from dotenv import load_dotenv

from src.models import Base

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuración de base de datos con mejoras de seguridad"""
    
    def __init__(self):
        """Inicializa la configuración de base de datos"""
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///personal_management.db")
        self.database_path = os.getenv("DATABASE_PATH", "personal_management.db")
        self.echo = os.getenv("DEBUG", "False").lower() == "true"
        
        # Crear directorio de datos si no existe
        self._ensure_data_directory()
        
        # Configurar engine con seguridad mejorada
        self.engine = self._create_engine()
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
        
        logger.info("Configuración de base de datos inicializada")

    def _safe_log_error(self, error: Exception, context: Dict = None):
        """Helper para registrar errores en audit_logger sin lanzar excepciones"""
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_error(error, context=context)
        except Exception:
            pass

    def _safe_log_event(self, event_type, details: Dict = None):
        """Helper para registrar eventos de sistema sin lanzar excepciones"""
        try:
            from src.utils.audit_logger import get_audit_logger
            audit = get_audit_logger()
            if audit:
                audit.log_system_event(event_type, details=details)
        except Exception:
            pass
        
    def _ensure_data_directory(self):
        """Asegura que el directorio de datos exista"""
        try:
            db_path = Path(self.database_path)
            if db_path.parent != Path('.'):
                db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directorio de datos creado/verificado: {db_path.parent}")
        except Exception as e:
            logger.error(f"Error creando directorio de datos: {e}")
            self._safe_log_error(e, context={"operation": "ensure_data_directory"})
            raise
    
    def _create_engine(self):
        """Crea el engine de SQLAlchemy con configuración segura"""
        try:
            connect_args = {
                "check_same_thread": False,
                "timeout": 30
            }
            
            engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                echo=self.echo,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            logger.info("Engine de base de datos creado exitosamente")
            return engine
            
        except Exception as e:
            logger.error(f"Error creando engine de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "create_engine"})
            raise
    
    def create_tables(self):
        """Crea todas las tablas en la base de datos con manejo de errores"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tablas de base de datos creadas exitosamente")
            
            try:
                from src.utils.audit_logger import AuditEventType
                self._safe_log_event(AuditEventType.SYSTEM_START, details={"operation": "create_tables"})
            except Exception:
                pass
                
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creando tablas: {e}")
            self._safe_log_error(e, context={"operation": "create_tables"})
            raise
        except Exception as e:
            logger.error(f"Error inesperado creando tablas: {e}")
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
            
            try:
                from src.utils.audit_logger import AuditEventType
                self._safe_log_event(AuditEventType.SYSTEM_STOP, details={"operation": "drop_tables"})
            except Exception:
                pass
                
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error eliminando tablas: {e}")
            self._safe_log_error(e, context={"operation": "drop_tables"})
            raise
        except Exception as e:
            logger.error(f"Error inesperado eliminando tablas: {e}")
            self._safe_log_error(e, context={"operation": "drop_tables"})
            raise
    
    def get_session(self):
        """Retorna una sesión de base de datos con manejo de errores"""
        try:
            session = self.SessionLocal()
            return session
        except Exception as e:
            logger.error(f"Error obteniendo sesión de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "get_session"})
            raise
    
    def close_session(self, session):
        """Cierra una sesión de base de datos de forma segura"""
        try:
            if session:
                session.close()
        except Exception as e:
            logger.warning(f"Error cerrando sesión de base de datos: {e}")
        finally:
            try:
                self.SessionLocal.remove()
            except Exception as e:
                logger.warning(f"Error removiendo sesión: {e}")
    
    def init_db(self):
        """Inicializa la base de datos con tablas y datos básicos"""
        try:
            logger.info("Inicializando base de datos...")
            
            # Siempre llamar create_tables para asegurar que todas las tablas existan
            self.create_tables()
            
            # Sembrar datos iniciales
            self._seed_initial_data()
            
            # Crear backup inicial
            try:
                from src.utils.backup_manager import get_backup_manager
                backup_mgr = get_backup_manager()
                backup_mgr.create_backup("initial_setup", compress=True)
                logger.info("Backup inicial creado exitosamente")
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
    
    def _verify_database_integrity(self) -> bool:
        """Verifica la integridad de la base de datos existente"""
        try:
            db_path = Path(self.database_path)
            if not db_path.exists():
                return False
            
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            return len(tables) > 0
            
        except Exception as e:
            logger.warning(f"Error verificando integridad de base de datos: {e}")
            return False
    
    def _seed_initial_data(self):
        """Inserta datos iniciales de configuración con manejo de errores"""
        from src.models.configuracion import Configuracion
        
        session = self.get_session()
        try:
            existing = session.query(Configuracion).first()
            if existing:
                logger.info("Configuraciones iniciales ya existen")
                return
            
            configuraciones = [
                Configuracion(
                    clave="nombre_institucion",
                    valor="Institución Educativa",
                    descripcion="Nombre de la institución educativa",
                    tipo_dato="string",
                    categoria="general"
                ),
                Configuracion(
                    clave="ruc",
                    valor="",
                    descripcion="RUC de la institución",
                    tipo_dato="string",
                    categoria="general"
                ),
                Configuracion(
                    clave="direccion",
                    valor="",
                    descripcion="Dirección de la institución",
                    tipo_dato="string",
                    categoria="general"
                ),
                Configuracion(
                    clave="telefono",
                    valor="",
                    descripcion="Teléfono de la institución",
                    tipo_dato="string",
                    categoria="general"
                ),
                Configuracion(
                    clave="email",
                    valor="",
                    descripcion="Email de la institución",
                    tipo_dato="string",
                    categoria="general"
                ),
                Configuracion(
                    clave="porcentaje_seguro",
                    valor="4.5",
                    descripcion="Porcentaje de deducción por seguro social",
                    tipo_dato="float",
                    categoria="nomina"
                ),
                Configuracion(
                    clave="porcentaje_pension",
                    valor="5.0",
                    descripcion="Porcentaje de deducción por pensión",
                    tipo_dato="float",
                    categoria="nomina"
                ),
                Configuracion(
                    clave="porcentaje_impuesto",
                    valor="0.0",
                    descripcion="Porcentaje de deducción por impuesto",
                    tipo_dato="float",
                    categoria="nomina"
                ),
                Configuracion(
                    clave="salario_minimo",
                    valor="130.0",
                    descripcion="Salario mínimo mensual",
                    tipo_dato="float",
                    categoria="nomina"
                ),
                Configuracion(
                    clave="dias_vacaciones_anual",
                    valor="15",
                    descripcion="Días de vacaciones anuales",
                    tipo_dato="int",
                    categoria="recursos_humanos"
                ),
                Configuracion(
                    clave="horas_laborales_semana",
                    valor="40",
                    descripcion="Horas laborales semanales",
                    tipo_dato="int",
                    categoria="recursos_humanos"
                ),
                Configuracion(
                    clave="backup_enabled",
                    valor="true",
                    descripcion="Habilitar backups automáticos",
                    tipo_dato="bool",
                    categoria="seguridad"
                ),
                Configuracion(
                    clave="backup_interval_hours",
                    valor="24",
                    descripcion="Intervalo de backups en horas",
                    tipo_dato="int",
                    categoria="seguridad"
                ),
                Configuracion(
                    clave="audit_enabled",
                    valor="true",
                    descripcion="Habilitar auditoría de eventos",
                    tipo_dato="bool",
                    categoria="seguridad"
                ),
            ]
            
            session.add_all(configuraciones)
            session.commit()
            
            logger.info(f"Configuraciones iniciales insertadas: {len(configuraciones)} registros")
            
            try:
                from src.utils.audit_logger import get_audit_logger
                audit_log = get_audit_logger()
                if audit_log:
                    audit_log.log_data_operation(
                        operation="create",
                        entity_type="configuracion",
                        data={"count": len(configuraciones)}
                    )
            except Exception:
                pass
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error insertando configuraciones iniciales: {e}")
            self._safe_log_error(e, context={"operation": "seed_initial_data"})
            raise
        finally:
            self.close_session(session)
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict:
        """
        Crea un backup de la base de datos
        
        Args:
            backup_name: Nombre personalizado para el backup
            
        Returns:
            Dict con información del backup
        """
        try:
            from src.utils.backup_manager import get_backup_manager
            backup_mgr = get_backup_manager()
            return backup_mgr.create_backup(backup_name)
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            self._safe_log_error(e, context={"operation": "create_backup"})
            raise
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restaura un backup de la base de datos
        
        Args:
            backup_name: Nombre del backup a restaurar
            
        Returns:
            True si la restauración fue exitosa
        """
        try:
            from src.utils.backup_manager import get_backup_manager
            backup_mgr = get_backup_manager()
            result = backup_mgr.restore_backup(backup_name)
            
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
        """
        Obtiene el estado del sistema de backups
        
        Returns:
            Dict con información del estado de backups
        """
        try:
            from src.utils.backup_manager import get_backup_manager
            backup_mgr = get_backup_manager()
            backups = backup_mgr.list_backups()
            return {
                "total_backups": len(backups),
                "latest_backup": backups[0] if backups else None,
                "backup_enabled": True,
                "database_path": str(Path(self.database_path).absolute()),
                "backup_directory": str(backup_mgr.backup_dir.absolute())
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