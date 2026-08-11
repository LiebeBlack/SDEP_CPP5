"""
Base Repository
Repositorio base con operaciones CRUD comunes
"""

from typing import TypeVar, Type, List, Optional, Generic
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Repositorio base con operaciones CRUD"""
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Obtiene un registro por ID"""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Obtiene todos los registros con paginación"""
        return self.session.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, obj: T) -> T:
        """Crea un nuevo registro"""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def update(self, obj: T) -> T:
        """Actualiza un registro existente"""
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def delete(self, id: int) -> bool:
        """Elimina un registro por ID"""
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False
    
    def count(self) -> int:
        """Cuenta el total de registros"""
        return self.session.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        """Verifica si existe un registro por ID"""
        return self.session.query(self.model).filter(self.model.id == id).first() is not None
    
    def get_by_field(self, field_name: str, value: any) -> Optional[T]:
        """Obtiene un registro por un campo específico"""
        return self.session.query(self.model).filter(
            getattr(self.model, field_name) == value
        ).first()
    
    def get_all_by_field(self, field_name: str, value: any) -> List[T]:
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