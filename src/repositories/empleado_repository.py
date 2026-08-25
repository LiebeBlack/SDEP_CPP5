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
        tipo_val = tipo.value if hasattr(tipo, 'value') else str(tipo)
        return self.session.query(Empleado).filter(
            or_(
                Empleado.tipo_empleado == tipo_val,
                Empleado.tipo_empleado == tipo
            )
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
        term = search_term.strip()
        return self.session.query(Empleado).filter(
            or_(
                Empleado.nombres.like(f"%{term}%"),
                Empleado.apellidos.like(f"%{term}%"),
                Empleado.cedula.like(f"%{term}%")
            )
        ).all()
    
    def get_by_cargo(self, cargo: str) -> List[Empleado]:
        """Obtiene empleados por cargo"""
        return self.session.query(Empleado).filter(Empleado.cargo == cargo).all()
    
    def get_filtrados(self, filtros: dict) -> List[Empleado]:
        """Obtiene empleados con filtros múltiples"""
        query = self.session.query(Empleado)
        
        if "tipo" in filtros and filtros["tipo"] and filtros["tipo"] != "Todos":
            tipo_val = filtros["tipo"].value if hasattr(filtros["tipo"], 'value') else str(filtros["tipo"])
            query = query.filter(
                or_(
                    Empleado.tipo_empleado == tipo_val,
                    Empleado.tipo_empleado == filtros["tipo"]
                )
            )
        
        if "departamento" in filtros and filtros["departamento"]:
            query = query.filter(Empleado.departamento == filtros["departamento"])
        
        if "activo" in filtros and filtros["activo"] is not None:
            query = query.filter(Empleado.activo == int(filtros["activo"]))
        
        if "cargo" in filtros and filtros["cargo"]:
            query = query.filter(Empleado.cargo == filtros["cargo"])
        
        if "busqueda" in filtros and filtros["busqueda"]:
            search = filtros["busqueda"].strip()
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
        stats = {t.value: 0 for t in TipoEmpleado}
        empleados = self.get_activos()
        for empleado in empleados:
            t = empleado.tipo_empleado.value if hasattr(empleado.tipo_empleado, 'value') else str(empleado.tipo_empleado)
            stats[t] = stats.get(t, 0) + 1
        return stats
    
    def get_estadisticas_por_departamento(self) -> dict:
        """Obtiene estadísticas de empleados por departamento"""
        stats = {}
        empleados = self.get_activos()
        for empleado in empleados:
            dept = empleado.departamento
            if dept:
                stats[dept] = stats.get(dept, 0) + 1
        return stats