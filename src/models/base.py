"""
Base Model
Modelo base para todos los modelos de datos

Este módulo define la clase base que todos los modelos del sistema
heredan, proporcionando campos comunes y métodos utilitarios.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
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