"""
Grado Repository
Repositorio para operaciones de datos de los grados y secciones
"""

import logging

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Grado, NivelEducativo
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GradoRepository(BaseRepository[Grado]):
    """Repositorio de grados con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Grado, session)

    def get_by_periodo(self, periodo_id: int) -> list[Grado]:
        """Lista los grados de un periodo, ordenados por nombre y sección"""
        try:
            return (
                self.session.query(Grado)
                .filter(Grado.periodo_id == periodo_id)
                .order_by(Grado.nombre, Grado.seccion)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar grados del periodo {periodo_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar grados del periodo {periodo_id}: {e}")
            return []

    def get_by_profesor(
        self, profesor_id: int, periodo_id: int | None = None
    ) -> list[Grado]:
        """Lista los grados asignados a un profesor (opcionalmente en un periodo)"""
        try:
            query = self.session.query(Grado).filter(Grado.profesor_id == profesor_id)
            if periodo_id is not None:
                query = query.filter(Grado.periodo_id == periodo_id)
            return query.order_by(Grado.nombre, Grado.seccion).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al listar grados del profesor {profesor_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar grados del profesor {profesor_id}: {e}")
            return []

    def get_por_nombre(self, periodo_id: int, nombre: str, seccion: str) -> Grado | None:
        """Busca un grado por periodo, nombre y sección (clave natural)"""
        try:
            return (
                self.session.query(Grado)
                .filter(
                    Grado.periodo_id == periodo_id,
                    Grado.nombre == nombre,
                    Grado.seccion == seccion,
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar el grado {nombre} {seccion}: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar el grado {nombre} {seccion}: {e}")
            return None

    def get_por_nivel(self, periodo_id: int, nivel: str | NivelEducativo) -> list[Grado]:
        """Lista los grados de un nivel dentro de un periodo"""
        try:
            nivel_val = nivel.value if hasattr(nivel, "value") else str(nivel)
            return (
                self.session.query(Grado)
                .filter(
                    Grado.periodo_id == periodo_id,
                    or_(Grado.nivel == nivel_val, Grado.nivel == nivel),
                )
                .order_by(Grado.nombre, Grado.seccion)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al listar grados del nivel {nivel}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar grados del nivel {nivel}: {e}")
            return []
