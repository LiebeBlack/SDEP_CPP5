"""
Empleado Repository
Repositorio para operaciones de datos de empleados con manejo de errores mejorado
"""

import logging
from typing import Any, cast

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Empleado, TipoEmpleado

from .base_repository import BaseRepository
from .busqueda import normalizar_expr, normalizar_termino

logger = logging.getLogger(__name__)


class EmpleadoRepository(BaseRepository[Empleado]):
    """Repositorio de empleados con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Empleado, session)

    def get_by_cedula(self, cedula: str) -> Empleado | None:
        """Obtiene un empleado por cédula con manejo de errores"""
        try:
            return cast(
                Empleado | None,
                self.session.query(Empleado).filter(Empleado.cedula == cedula).first(),
            )
        except SQLAlchemyError as e:
            logger.error("Error de base de datos al buscar empleado por cédula: %s", e)
            return None
        except Exception as e:
            logger.error("Error inesperado al buscar empleado por cédula: %s", e)
            return None

    def get_by_tipo(self, tipo: str | TipoEmpleado) -> list[Empleado]:
        """Obtiene empleados por tipo con manejo de errores"""
        try:
            tipo_val = tipo.value if hasattr(tipo, "value") else str(tipo)
            return cast(
                list[Empleado],
                (
                    self.session.query(Empleado)
                    .filter(or_(Empleado.tipo_empleado == tipo_val, Empleado.tipo_empleado == tipo))
                    .all()
                ),
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados por tipo {tipo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados por tipo {tipo}: {e}")
            return []

    def get_activos(self) -> list[Empleado]:
        """Obtiene solo empleados activos con manejo de errores"""
        try:
            return cast(
                list[Empleado], self.session.query(Empleado).filter(Empleado.activo == 1).all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados activos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados activos: {e}")
            return []

    def get_by_departamento(self, departamento: str) -> list[Empleado]:
        """Obtiene empleados por departamento con manejo de errores"""
        try:
            return cast(
                list[Empleado],
                self.session.query(Empleado).filter(Empleado.departamento == departamento).all(),
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar empleados por departamento {departamento}: {e}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Error inesperado al buscar empleados por departamento {departamento}: {e}"
            )
            return []

    def search_empleados(self, search_term: str) -> list[Empleado]:
        """
        Busca empleados por nombre, apellido o cédula (insensible a mayúsculas y tildes)

        Solo devuelve empleados activos, igual que la lista principal del frame.
        """
        try:
            term = normalizar_termino(search_term.strip())
            if not term:
                return self.get_activos()
            patron = f"%{term}%"
            return cast(
                list[Empleado],
                (
                    self.session.query(Empleado)
                    .filter(
                        Empleado.activo == 1,
                        or_(
                            normalizar_expr(Empleado.nombres).like(patron),
                            normalizar_expr(Empleado.apellidos).like(patron),
                            normalizar_expr(Empleado.cedula).like(patron),
                        ),
                    )
                    .all()
                ),
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar empleados con término {search_term}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados con término {search_term}: {e}")
            return []

    def get_by_cargo(self, cargo: str) -> list[Empleado]:
        """Obtiene empleados por cargo con manejo de errores"""
        try:
            return cast(
                list[Empleado], self.session.query(Empleado).filter(Empleado.cargo == cargo).all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar empleados por cargo {cargo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleados por cargo {cargo}: {e}")
            return []

    def get_filtrados(self, filtros: dict) -> list[Empleado]:
        """Obtiene empleados con filtros múltiples y manejo de errores"""
        try:
            query = self.session.query(Empleado)

            if "tipo" in filtros and filtros["tipo"] and filtros["tipo"] != "Todos":
                tipo_val = (
                    filtros["tipo"].value
                    if hasattr(filtros["tipo"], "value")
                    else str(filtros["tipo"])
                )
                query = query.filter(
                    or_(
                        Empleado.tipo_empleado == tipo_val,
                        Empleado.tipo_empleado == filtros["tipo"],
                    )
                )

            if "departamento" in filtros and filtros["departamento"]:
                query = query.filter(Empleado.departamento == filtros["departamento"])

            if "activo" in filtros and filtros["activo"] is not None:
                # El filtro puede llegar como bool, entero o texto desde un
                # combobox/JSON; un int() crudo lanzaba ValueError y el
                # except devolvía [] (todos los empleados "desaparecían").
                activo = filtros["activo"]
                if isinstance(activo, str):
                    activo = activo.strip().lower() in {"1", "true", "si", "sí", "activo"}
                query = query.filter(Empleado.activo == (1 if activo else 0))

            if "cargo" in filtros and filtros["cargo"]:
                query = query.filter(Empleado.cargo == filtros["cargo"])

            if "busqueda" in filtros and filtros["busqueda"]:
                search = normalizar_termino(filtros["busqueda"].strip())
                if search:
                    patron = f"%{search}%"
                    query = query.filter(
                        or_(
                            normalizar_expr(Empleado.nombres).like(patron),
                            normalizar_expr(Empleado.apellidos).like(patron),
                            normalizar_expr(Empleado.cedula).like(patron),
                        )
                    )

            return cast(list[Empleado], query.all())
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
            # GROUP BY en SQL: antes se hidrataban todos los empleados
            # activos en memoria solo para contarlos.
            for tipo, total in (
                self.session.query(Empleado.tipo_empleado, func.count(Empleado.id))
                .filter(Empleado.activo == 1)
                .group_by(Empleado.tipo_empleado)
                .all()
            ):
                clave = tipo.value if hasattr(tipo, "value") else str(tipo)
                stats[clave] = stats.get(clave, 0) + int(total or 0)
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por tipo: {e}")
            return {}

    def get_estadisticas_por_departamento(self) -> dict:
        """Obtiene estadísticas de empleados por departamento con manejo de errores"""
        try:
            stats: dict[str, Any] = {}
            for departamento, total in (
                self.session.query(Empleado.departamento, func.count(Empleado.id))
                .filter(Empleado.activo == 1, Empleado.departamento.isnot(None))
                .group_by(Empleado.departamento)
                .all()
            ):
                if departamento:
                    stats[departamento] = int(total or 0)
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por departamento: {e}")
            return {}
