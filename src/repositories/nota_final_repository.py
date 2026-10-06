"""
Nota Final Repository
Repositorio para operaciones de datos de las calificaciones finales

Incluye el camino de guardado masivo de fin de año: un único executemany
y un solo commit para todo el lote, que es lo que evita la latencia de
cientos de INSERT individuales.
"""

import logging
from typing import Any

from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Estudiante, Grado, NotaFinal

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class NotaFinalRepository(BaseRepository[NotaFinal]):
    """Repositorio de notas finales con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(NotaFinal, session)

    def get_by_grado(self, grado_id: int) -> list[NotaFinal]:
        """Notas de un grado, ordenadas por estudiante y materia"""
        try:
            return (
                self.session.query(NotaFinal)
                .join(Estudiante, NotaFinal.estudiante_id == Estudiante.id)
                .filter(NotaFinal.grado_id == grado_id)
                .order_by(
                    Estudiante.apellidos,
                    Estudiante.nombres,
                    NotaFinal.materia,
                )
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar notas del grado {grado_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar notas del grado {grado_id}: {e}")
            return []

    def get_by_estudiante(
        self, estudiante_id: int, periodo_id: int | None = None
    ) -> list[NotaFinal]:
        """Notas de un estudiante (opcionalmente filtradas por periodo)"""
        try:
            query = self.session.query(NotaFinal).filter(NotaFinal.estudiante_id == estudiante_id)
            if periodo_id is not None:
                query = query.join(Grado, NotaFinal.grado_id == Grado.id).filter(
                    Grado.periodo_id == periodo_id
                )
            return query.order_by(NotaFinal.materia).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al listar notas del estudiante {estudiante_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar notas del estudiante {estudiante_id}: {e}")
            return []

    def get_una(self, estudiante_id: int, grado_id: int, materia: str) -> NotaFinal | None:
        """Busca la nota de un estudiante en una materia y grado concretos"""
        try:
            return (
                self.session.query(NotaFinal)
                .filter(
                    NotaFinal.estudiante_id == estudiante_id,
                    NotaFinal.grado_id == grado_id,
                    NotaFinal.materia == materia,
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al buscar la nota de {estudiante_id} en {materia}: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar la nota de {estudiante_id} en {materia}: {e}")
            return None

    def insertar_lote(self, filas: list[dict[str, Any]]) -> int:
        """
        Inserta varias notas en una sola transacción (executemany)

        A diferencia de ``create`` (un INSERT y un commit por nota), aquí
        todo el lote viaja en una única sentencia parametrizada y se
        confirma una sola vez, que es lo que hace viable registrar cientos
        de calificaciones al cerrar el año escolar.

        Raises:
            SQLAlchemyError: Si alguna fila viola una restricción; el lote
                completo se revierte (no quedan notas a medias).
        """
        if not filas:
            return 0
        try:
            self.session.execute(insert(NotaFinal), filas)
            self.session.commit()
            logger.info("Notas insertadas en lote: %s", len(filas))
            return len(filas)
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error al insertar el lote de notas: {e}")
            raise

    def consolidado_periodo(self, periodo_id: int) -> list[dict[str, Any]]:
        """
        Notas consolidadas de un periodo, listas para reportes

        Cada fila incluye los datos del estudiante y del grado, de modo
        que los boletines y actas no tengan que volver a consultar la base.
        """
        try:
            filas = (
                self.session.query(NotaFinal, Estudiante, Grado)
                .join(Estudiante, NotaFinal.estudiante_id == Estudiante.id)
                .join(Grado, NotaFinal.grado_id == Grado.id)
                .filter(Grado.periodo_id == periodo_id)
                .order_by(
                    Grado.nombre,
                    Grado.seccion,
                    Estudiante.apellidos,
                    Estudiante.nombres,
                    NotaFinal.materia,
                )
                .all()
            )
            return [
                {
                    "nota_id": nota.id,
                    "estudiante_id": estudiante.id,
                    "estudiante": estudiante.nombre_completo,
                    "cedula": estudiante.cedula,
                    "nivel": estudiante.nivel_valor,
                    "grado_id": grado.id,
                    "grado": grado.nombre_completo,
                    "materia": nota.materia,
                    "calificacion": float(nota.calificacion),
                    "registrado_por": nota.registrado_por,
                }
                for nota, estudiante, grado in filas
            ]
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al consolidar las notas del periodo {periodo_id}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Error inesperado al consolidar las notas del periodo {periodo_id}: {e}")
            return []
