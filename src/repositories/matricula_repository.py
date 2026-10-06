"""
Matricula Repository
Repositorio para operaciones de datos de las matrículas
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Estudiante, Grado, Matricula

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MatriculaRepository(BaseRepository[Matricula]):
    """Repositorio de matrículas con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Matricula, session)

    def get_by_grado(self, grado_id: int, solo_activas: bool = True) -> list[Matricula]:
        """Lista las matrículas de un grado, ordenadas por apellido del estudiante"""
        try:
            query = (
                self.session.query(Matricula)
                .join(Estudiante, Matricula.estudiante_id == Estudiante.id)
                .filter(Matricula.grado_id == grado_id)
            )
            if solo_activas:
                query = query.filter(Matricula.activa == 1)
            return query.order_by(Estudiante.apellidos, Estudiante.nombres).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar matrículas del grado {grado_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar matrículas del grado {grado_id}: {e}")
            return []

    def get_by_estudiante(self, estudiante_id: int, solo_activas: bool = True) -> list[Matricula]:
        """Lista las matrículas de un estudiante (historial por año escolar)"""
        try:
            query = self.session.query(Matricula).filter(Matricula.estudiante_id == estudiante_id)
            if solo_activas:
                query = query.filter(Matricula.activa == 1)
            return (
                query.join(Grado, Matricula.grado_id == Grado.id)
                .order_by(Grado.nombre, Grado.seccion)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al listar matrículas del estudiante {estudiante_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Error inesperado al listar matrículas del estudiante {estudiante_id}: {e}"
            )
            return []

    def get_activa_en_periodo(self, estudiante_id: int, periodo_id: int) -> Matricula | None:
        """
        Matrícula activa de un estudiante dentro de un periodo

        Un estudiante cursa un solo grado por año escolar; esta consulta es
        la que valida esa regla al matricular.
        """
        try:
            return (
                self.session.query(Matricula)
                .join(Grado, Matricula.grado_id == Grado.id)
                .filter(
                    Matricula.estudiante_id == estudiante_id,
                    Matricula.activa == 1,
                    Grado.periodo_id == periodo_id,
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar la matrícula activa del estudiante "
                f"{estudiante_id}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Error inesperado al buscar la matrícula activa del estudiante "
                f"{estudiante_id}: {e}"
            )
            return None

    def desactivar(self, matricula_id: int) -> bool:
        """Retira al estudiante del grado sin borrar el registro"""
        try:
            matricula = self.get_by_id(matricula_id)
            if matricula:
                matricula.activa = 0
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al retirar la matrícula {matricula_id}: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al retirar la matrícula {matricula_id}: {e}")
            return False

    def count_activas(self, grado_id: int | None = None) -> int:
        """Cantidad de matrículas activas (de un grado o de todo el sistema)"""
        try:
            query = self.session.query(Matricula).filter(Matricula.activa == 1)
            if grado_id is not None:
                query = query.filter(Matricula.grado_id == grado_id)
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al contar el grado {grado_id}: {e}")
            return 0
