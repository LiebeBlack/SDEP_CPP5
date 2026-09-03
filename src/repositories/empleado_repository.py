"""
Empleado Repository
Repositorio para operaciones de datos de empleados con manejo de errores mejorado
"""

from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.models import Empleado, TipoEmpleado
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


# Pares para búsqueda insensible a mayúsculas y tildes (SQLite LIKE no
# normaliza caracteres acentuados: "gomez" debe encontrar "Gómez").
_ACENTOS = [
    ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
    ("ü", "u"), ("ñ", "n"),
]


def _normalizar_expr(col):
    """Expresión SQL que pasa una columna a minúsculas sin tildes"""
    expr = func.lower(col)
    for acento, plano in _ACENTOS:
        expr = func.replace(expr, acento, plano)
    return expr


def _normalizar_termino(termino: str) -> str:
    """Normaliza un término de búsqueda: minúsculas y sin tildes"""
    texto = termino.lower()
    for acento, plano in _ACENTOS:
        texto = texto.replace(acento, plano)
    return texto


class EmpleadoRepository(BaseRepository[Empleado]):
    """Repositorio de empleados con manejo robusto de errores"""
    
    def __init__(self, session: Session):
        super().__init__(Empleado, session)
    
    def get_by_cedula(self, cedula: str) -> Optional[Empleado]:
        """Obtiene un empleado por cédula con manejo de errores"""
        try:
            return self.session.query(Empleado).filter(Empleado.cedula == cedula).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleado por cédula {cedula}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleado por cédula {cedula}: {e}")
            return None
    
    def get_by_tipo(self, tipo: Union[str, TipoEmpleado]) -> List[Empleado]:
        """Obtiene empleados por tipo con manejo de errores"""
        try:
            tipo_val = tipo.value if hasattr(tipo, 'value') else str(tipo)
            return self.session.query(Empleado).filter(
                or_(
                    Empleado.tipo_empleado == tipo_val,
                    Empleado.tipo_empleado == tipo
                )
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados por tipo {tipo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados por tipo {tipo}: {e}")
            return []
    
    def get_activos(self) -> List[Empleado]:
        """Obtiene solo empleados activos con manejo de errores"""
        try:
            return self.session.query(Empleado).filter(Empleado.activo == 1).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados activos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados activos: {e}")
            return []
    
    def get_by_departamento(self, departamento: str) -> List[Empleado]:
        """Obtiene empleados por departamento con manejo de errores"""
        try:
            return self.session.query(Empleado).filter(
                Empleado.departamento == departamento
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados por departamento {departamento}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados por departamento {departamento}: {e}")
            return []
    
    def search_empleados(self, search_term: str) -> List[Empleado]:
        """
        Busca empleados por nombre, apellido o cédula (insensible a mayúsculas y tildes)

        Solo devuelve empleados activos, igual que la lista principal del frame.
        """
        try:
            term = _normalizar_termino(search_term.strip())
            if not term:
                return self.get_activos()
            patron = f"%{term}%"
            return self.session.query(Empleado).filter(
                Empleado.activo == 1,
                or_(
                    _normalizar_expr(Empleado.nombres).like(patron),
                    _normalizar_expr(Empleado.apellidos).like(patron),
                    _normalizar_expr(Empleado.cedula).like(patron),
                ),
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados con término {search_term}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados con término {search_term}: {e}")
            return []
    
    def get_by_cargo(self, cargo: str) -> List[Empleado]:
        """Obtiene empleados por cargo con manejo de errores"""
        try:
            return self.session.query(Empleado).filter(Empleado.cargo == cargo).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados por cargo {cargo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados por cargo {cargo}: {e}")
            return []
    
    def get_filtrados(self, filtros: dict) -> List[Empleado]:
        """Obtiene empleados con filtros múltiples y manejo de errores"""
        try:
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
                search = _normalizar_termino(filtros["busqueda"].strip())
                if search:
                    patron = f"%{search}%"
                    query = query.filter(
                        or_(
                            _normalizar_expr(Empleado.nombres).like(patron),
                            _normalizar_expr(Empleado.apellidos).like(patron),
                            _normalizar_expr(Empleado.cedula).like(patron),
                        )
                    )
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados con filtros: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados con filtros: {e}")
            return []
    
    def desactivar(self, id: int) -> bool:
        """Desactiva un empleado con manejo de errores"""
        try:
            empleado = self.get_by_id(id)
            if empleado:
                empleado.activo = 0
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al desactivar empleado {id}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al desactivar empleado {id}: {e}")
            return False
    
    def activar(self, id: int) -> bool:
        """Activa un empleado con manejo de errores"""
        try:
            empleado = self.get_by_id(id)
            if empleado:
                empleado.activo = 1
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al activar empleado {id}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al activar empleado {id}: {e}")
            return False
    
    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de empleados por tipo con manejo de errores"""
        try:
            stats = {t.value: 0 for t in TipoEmpleado}
            empleados = self.get_activos()
            for empleado in empleados:
                t = empleado.tipo_empleado.value if hasattr(empleado.tipo_empleado, 'value') else str(empleado.tipo_empleado)
                stats[t] = stats.get(t, 0) + 1
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por tipo: {e}")
            return {}
    
    def get_estadisticas_por_departamento(self) -> dict:
        """Obtiene estadísticas de empleados por departamento con manejo de errores"""
        try:
            stats = {}
            empleados = self.get_activos()
            for empleado in empleados:
                dept = empleado.departamento
                if dept:
                    stats[dept] = stats.get(dept, 0) + 1
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por departamento: {e}")
            return {}