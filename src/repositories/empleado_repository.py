"""
Empleado Repository
Repositorio para operaciones de datos de empleados
"""

from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from src.models import Empleado, TipoEmpleado
from .base_repository import BaseRepository


class EmpleadoRepository(BaseRepository[Empleado]):
    """Repositorio de empleados"""
    
    def __init__(self, session: Session):
        super().__init__(Empleado, session)
    
    def get_by_cedula(self, cedula: str) -> Optional[Empleado]:
        """Obtiene un empleado por cédula"""
        return self.session.query(Empleado).filter(Empleado.cedula == cedula).first()
    
    def get_by_tipo(self, tipo: Union[str, TipoEmpleado]) -> List[Empleado]:
        """Obtiene empleados por tipo"""
        if isinstance(tipo, str):
            return self.session.query(Empleado).filter(
                Empleado.tipo_empleado == tipo
            ).all()
        return self.session.query(Empleado).filter(
            Empleado.tipo_empleado == tipo.value
        ).all()
    
    def get_activos(self) -> List[Empleado]:
        """Obtiene solo empleados activos"""
        return self.session.query(Empleado).filter(Empleado.activo == 1).all()
    
    def get_by_departamento(self, departamento: str) -> List[Empleado]:
        """Obtiene empleados por departamento"""
        return self.session.query(Empleado).filter(
            Empleado.departamento == departamento
        ).all()
    
    def search_empleados(self, search_term: str) -> List[Empleado]:
        """Busca empleados por nombre, apellido o cédula"""
        return self.session.query(Empleado).filter(
            or_(
                Empleado.nombres.like(f"%{search_term}%"),
                Empleado.apellidos.like(f"%{search_term}%"),
                Empleado.cedula.like(f"%{search_term}%")
            )
        ).all()
    
    def get_by_cargo(self, cargo: str) -> List[Empleado]:
        """Obtiene empleados por cargo"""
        return self.session.query(Empleado).filter(Empleado.cargo == cargo).all()
    
    def get_filtrados(self, filtros: dict) -> List[Empleado]:
        """Obtiene empleados con filtros múltiples"""
        query = self.session.query(Empleado)
        
        if "tipo" in filtros:
            query = query.filter(Empleado.tipo_empleado == filtros["tipo"])
        
        if "departamento" in filtros:
            query = query.filter(Empleado.departamento == filtros["departamento"])
        
        if "activo" in filtros:
            query = query.filter(Empleado.activo == filtros["activo"])
        
        if "cargo" in filtros:
            query = query.filter(Empleado.cargo == filtros["cargo"])
        
        if "busqueda" in filtros:
            search = filtros["busqueda"]
            query = query.filter(
                or_(
                    Empleado.nombres.like(f"%{search}%"),
                    Empleado.apellidos.like(f"%{search}%"),
                    Empleado.cedula.like(f"%{search}%")
                )
            )
        
        return query.all()
    
    def desactivar(self, id: int) -> bool:
        """Desactiva un empleado"""
        empleado = self.get_by_id(id)
        if empleado:
            empleado.activo = 0
            self.session.commit()
            return True
        return False
    
    def activar(self, id: int) -> bool:
        """Activa un empleado"""
        empleado = self.get_by_id(id)
        if empleado:
            empleado.activo = 1
            self.session.commit()
            return True
        return False
    
    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de empleados por tipo"""
        stats = {}
        for tipo in TipoEmpleado:
            count = self.session.query(Empleado).filter(
                Empleado.tipo_empleado == tipo.value,
                Empleado.activo == 1
            ).count()
            stats[tipo.value] = count
        return stats
    
    def get_estadisticas_por_departamento(self) -> dict:
        """Obtiene estadísticas de empleados por departamento"""
        stats = {}
        empleados = self.get_activos()
        for empleado in empleados:
            dept = empleado.departamento
            stats[dept] = stats.get(dept, 0) + 1
        return stats