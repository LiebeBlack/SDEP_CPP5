"""
Estudiante Repository
Repositorio para operaciones de datos de estudiantes
"""

import logging

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Estudiante, NivelEducativo
from .base_repository import BaseRepository
from .busqueda import normalizar_expr, normalizar_termino

logger = logging.getLogger(__name__)


class EstudianteRepository(BaseRepository[Estudiante]):
    """Repositorio de estudiantes con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Estudiante, session)

    def get_by_cedula(self, cedula: str) -> Estudiante | None:
        """Obtiene un estudiante por cédula"""
        try:
            return self.session.query(Estudiante).filter(Estudiante.cedula == cedula).first()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar estudiante por cédula {cedula}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar estudiante por cédula {cedula}: {e}")
            return None

    def get_activos(self) -> list[Estudiante]:
        """Obtiene solo los estudiantes activos, ordenados por apellido"""
        try:
            return (
                self.session.query(Estudiante)
                .filter(Estudiante.activo == 1)
                .order_by(Estudiante.apellidos, Estudiante.nombres)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar estudiantes activos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar estudiantes activos: {e}")
            return []

    def get_by_nivel(self, nivel: str | NivelEducativo) -> list[Estudiante]:
        """Obtiene los estudiantes activos de un nivel educativo"""
        try:
            nivel_val = nivel.value if hasattr(nivel, "value") else str(nivel)
            return (
                self.session.query(Estudiante)
                .filter(
                    Estudiante.activo == 1,
                    or_(Estudiante.nivel == nivel_val, Estudiante.nivel == nivel),
                )
                .order_by(Estudiante.apellidos, Estudiante.nombres)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar estudiantes del nivel {nivel}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar estudiantes del nivel {nivel}: {e}")
            return []

    def search_estudiantes(self, search_term: str) -> list[Estudiante]:
        """
        Busca estudiantes por nombre, apellido o cédula

        Insensible a mayúsculas y tildes; sin término devuelve los activos.
        """
        try:
            term = normalizar_termino(search_term.strip())
            if not term:
                return self.get_activos()
            patron = f"%{term}%"
            return (
                self.session.query(Estudiante)
                .filter(
                    Estudiante.activo == 1,
                    or_(
                        normalizar_expr(Estudiante.nombres).like(patron),
                        normalizar_expr(Estudiante.apellidos).like(patron),
                        normalizar_expr(Estudiante.cedula).like(patron),
                    ),
                )
                .order_by(Estudiante.apellidos, Estudiante.nombres)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar estudiantes con término {search_term}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar estudiantes con término {search_term}: {e}")
            return []

    def desactivar(self, id: int) -> bool:
        """Marca a un estudiante como retirado (baja lógica)"""
        try:
            estudiante = self.get_by_id(id)
            if estudiante:
                estudiante.activo = 0
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al desactivar estudiante {id}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al desactivar estudiante {id}: {e}")
            return False

    def activar(self, id: int) -> bool:
        """Reactiva a un estudiante retirado"""
        try:
            estudiante = self.get_by_id(id)
            if estudiante:
                estudiante.activo = 1
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al activar estudiante {id}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al activar estudiante {id}: {e}")
            return False

    def count_activos(self) -> int:
        """Cantidad de estudiantes activos"""
        try:
            return self.session.query(Estudiante).filter(Estudiante.activo == 1).count()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al contar estudiantes activos: {e}")
            return 0

    def get_estadisticas_por_nivel(self) -> dict:
        """Cantidad de estudiantes activos por nivel educativo"""
        try:
            stats = {nivel.value: 0 for nivel in NivelEducativo}
            for estudiante in self.get_activos():
                stats[estudiante.nivel_valor] = stats.get(estudiante.nivel_valor, 0) + 1
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por nivel: {e}")
            return {}
