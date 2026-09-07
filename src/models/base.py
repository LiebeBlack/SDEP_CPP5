"""
Base Model
Modelo base para todos los modelos de datos

Este módulo define la clase base que todos los modelos del sistema
heredan, proporcionando campos comunes y métodos utilitarios.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow():
    """Fecha/hora UTC actual SIN zona horaria (naive).

    Sustituye a datetime.utcnow() (deprecado desde Python 3.12) y la base
    de datos guarda fechas naive, por lo que el resultado no lleva tzinfo.
    Se define aquí (y no en src.utils) porque los modelos se importan muy
    pronto en el arranque y src.utils arrastra dependencias circulares.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel:
    """
    Modelo base con campos comunes
    
    Todos los modelos del sistema heredan de esta clase, obteniendo
    automáticamente campos de identificación y auditoría.
    
    Atributos:
        id: Identificador único autoincremental
        created_at: Fecha y hora de creación del registro
        updated_at: Fecha y hora de última actualización
    """
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    
    def to_dict(self):
        """
        Convierte el modelo a diccionario
        
        Returns:
            Dict: Diccionario con todos los campos del modelo
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        """
        Representación string del modelo
        
        Returns:
            str: Representación legible del modelo
        """
        return f"<{self.__class__.__name__}(id={self.id})>"