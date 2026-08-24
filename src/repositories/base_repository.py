"""
Base Repository
Repositorio base con operaciones CRUD comunes

Este repositorio proporciona las operaciones básicas de creación,
lectura, actualización y eliminación (CRUD) que pueden ser
utilizadas por todos los repositorios específicos.
"""

from typing import TypeVar, Type, List, Optional, Generic, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Repositorio base con operaciones CRUD
    
    Proporciona métodos genéricos para operaciones comunes de base de datos
    que pueden ser heredados por repositorios específicos.
    """
    
    def __init__(self, model: Type[T], session: Session):
        """
        Inicializa el repositorio base
        
        Args:
            model: Clase del modelo SQLAlchemy
            session: Sesión de base de datos
        """
        self.model = model
        self.session = session
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Obtiene un registro por ID
        
        Args:
            id: Identificador del registro
            
        Returns:
            Objeto del modelo o None si no existe
        """
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Obtiene todos los registros con paginación
        
        Args:
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros a retornar
            
        Returns:
            Lista de objetos del modelo
        """
        return self.session.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, obj: T) -> T:
        """
        Crea un nuevo registro
        
        Args:
            obj: Objeto del modelo a crear
            
        Returns:
            Objeto creado con ID asignado
            
        Raises:
            Exception: Si ocurre error en la creación
        """
        try:
            self.session.add(obj)
            self.session.commit()
            self.session.refresh(obj)
            return obj
        except Exception:
            self.session.rollback()
            raise
    
    def update(self, obj: T) -> T:
        """
        Actualiza un registro existente
        
        Args:
            obj: Objeto del modelo con modificaciones
            
        Returns:
            Objeto actualizado
            
        Raises:
            Exception: Si ocurre error en la actualización
        """
        try:
            self.session.commit()
            self.session.refresh(obj)
            return obj
        except Exception:
            self.session.rollback()
            raise
    
    def delete(self, id: int) -> bool:
        """
        Elimina un registro por ID
        
        Args:
            id: Identificador del registro a eliminar
            
        Returns:
            True si se eliminó, False si no existía
            
        Raises:
            Exception: Si ocurre error en la eliminación
        """
        try:
            obj = self.get_by_id(id)
            if obj:
                self.session.delete(obj)
                self.session.commit()
                return True
            return False
        except Exception:
            self.session.rollback()
            raise
    
    def count(self) -> int:
        """
        Cuenta el total de registros
        
        Returns:
            Cantidad total de registros en la tabla
        """
        return self.session.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        """
        Verifica si existe un registro por ID
        
        Args:
            id: Identificador a verificar
            
        Returns:
            True si existe, False en caso contrario
        """
        return self.session.query(self.model).filter(self.model.id == id).first() is not None
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Obtiene un registro por un campo específico"""
        return self.session.query(self.model).filter(
            getattr(self.model, field_name) == value
        ).first()
    
    def get_all_by_field(self, field_name: str, value: Any) -> List[T]:
        """Obtiene todos los registros por un campo específico"""
        return self.session.query(self.model).filter(
            getattr(self.model, field_name) == value
        ).all()
    
    def search(self, filters: dict) -> List[T]:
        """Busca registros con filtros múltiples"""
        query = self.session.query(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query.all()
    
    def search_like(self, field_name: str, value: str) -> List[T]:
        """Busca registros con coincidencia parcial"""
        return self.session.query(self.model).filter(
            getattr(self.model, field_name).like(f"%{value}%")
        ).all()