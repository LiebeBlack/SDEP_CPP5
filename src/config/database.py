"""
Database Configuration
Configuración de base de datos SQLite
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

from src.models import Base

# Cargar variables de entorno
load_dotenv()


class DatabaseConfig:
    """Configuración de base de datos"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///personal_management.db")
        self.database_path = os.getenv("DATABASE_PATH", "personal_management.db")
        self.echo = os.getenv("DEBUG", "False").lower() == "true"
        
        # Crear directorio de datos si no existe
        self._ensure_data_directory()
        
        # Configurar engine
        self.engine = self._create_engine()
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
        
    def _ensure_data_directory(self):
        """Asegura que el directorio de datos exista"""
        db_path = Path(self.database_path)
        if db_path.parent != Path('.'):
            db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_engine(self):
        """Crea el engine de SQLAlchemy"""
        # Configuración específica para SQLite
        connect_args = {"check_same_thread": False}
        
        engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            poolclass=StaticPool,
            echo=self.echo
        )
        
        return engine
    
    def create_tables(self):
        """Crea todas las tablas en la base de datos"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Elimina todas las tablas de la base de datos"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Retorna una sesión de base de datos"""
        session = self.SessionLocal()
        try:
            return session
        except Exception as e:
            session.close()
            raise e
    
    def close_session(self, session):
        """Cierra una sesión de base de datos"""
        try:
            session.close()
        except Exception:
            pass
        finally:
            self.SessionLocal.remove()
    
    def init_db(self):
        """Inicializa la base de datos con tablas y datos básicos"""
        self.create_tables()
        self._seed_initial_data()
    
    def _seed_initial_data(self):
        """Inserta datos iniciales de configuración"""
        from src.models.configuracion import Configuracion
        
        session = self.get_session()
        try:
            # Verificar si ya existen configuraciones
            existing = session.query(Configuracion).first()
            if existing:
                return
            
            # Configuraciones iniciales
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
            ]
            
            session.add_all(configuraciones)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)


# Instancia global de configuración de base de datos
db_config = DatabaseConfig()


def get_db():
    """Retorna una sesión de base de datos (para dependency injection)"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        db_config.close_session(session)