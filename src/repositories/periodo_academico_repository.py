"""
Periodo Academico Repository
Repositorio para operaciones de datos de los periodos académicos
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import EstadoPeriodoAcademico, PeriodoAcademico
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PeriodoAcademicoRepository(BaseRepository[PeriodoAcademico]):
    """Repositorio de periodos académicos con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(PeriodoAcademico, session)

    def get_by_nombre(self, nombre: str) -> PeriodoAcademico | None:
        """Obtiene un periodo por su nombre (año escolar)"""
        try:
            return (
                self.session.query(PeriodoAcademico)
                .filter(PeriodoAcademico.nombre == nombre)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar periodo {nombre}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar periodo {nombre}: {e}")
            return None

    def get_ordenados(self, descendente: bool = True) -> list[PeriodoAcademico]:
        """Lista los periodos del más reciente al más antiguo (o al revés)"""
        try:
            orden = PeriodoAcademico.nombre.desc() if descendente else PeriodoAcademico.nombre
            return self.session.query(PeriodoAcademico).order_by(orden).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar periodos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar periodos: {e}")
            return []

    def get_abiertos(self) -> list[PeriodoAcademico]:
        """Lista los periodos abiertos (admiten registrar notas)"""
        try:
            return (
                self.session.query(PeriodoAcademico)
                .filter(PeriodoAcademico.estado == EstadoPeriodoAcademico.ABIERTO.value)
                .order_by(PeriodoAcademico.nombre.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar periodos abiertos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar periodos abiertos: {e}")
            return []

    def get_ultimo_abierto(self) -> PeriodoAcademico | None:
        """Periodo abierto más reciente (el año escolar en curso)"""
        try:
            return (
                self.session.query(PeriodoAcademico)
                .filter(PeriodoAcademico.estado == EstadoPeriodoAcademico.ABIERTO.value)
                .order_by(PeriodoAcademico.nombre.desc())
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar el periodo en curso: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar el periodo en curso: {e}")
            return None
