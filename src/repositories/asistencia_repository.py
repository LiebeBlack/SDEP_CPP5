"""
Asistencia Repository
Repositorio para el registro diario de asistencia

Concentra las consultas del módulo de asistencia: registros por
empleado y período, faltas, tardanzas y los totales de horas que
consume el cálculo de la nómina.
"""

import logging
from datetime import date

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Asistencia, TipoAsistencia

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AsistenciaRepository(BaseRepository[Asistencia]):
    """Repositorio de asistencias con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Asistencia, session)

    def get_by_empleado(
        self,
        empleado_id: int,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[Asistencia]:
        """Registros de un empleado, opcionalmente acotados a un rango de fechas"""
        try:
            query = self.session.query(Asistencia).filter(
                Asistencia.empleado_id == empleado_id
            )
            if desde is not None:
                query = query.filter(Asistencia.fecha >= desde)
            if hasta is not None:
                query = query.filter(Asistencia.fecha <= hasta)
            return query.order_by(Asistencia.fecha.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo asistencia del empleado {empleado_id}: {e}")
            return []

    def get_registro(self, empleado_id: int, fecha: date) -> Asistencia | None:
        """Registro de un empleado en una fecha concreta (o None)"""
        try:
            return (
                self.session.query(Asistencia)
                .filter(
                    and_(
                        Asistencia.empleado_id == empleado_id,
                        Asistencia.fecha == fecha,
                    )
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error buscando asistencia del {fecha} del empleado {empleado_id}: {e}")
            return None

    def get_by_periodo(self, desde: date, hasta: date) -> list[Asistencia]:
        """Registros de todos los empleados en un período"""
        try:
            return (
                self.session.query(Asistencia)
                .filter(and_(Asistencia.fecha >= desde, Asistencia.fecha <= hasta))
                .order_by(Asistencia.fecha.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo asistencias del período {desde} - {hasta}: {e}")
            return []

    def get_by_fecha(self, fecha: date) -> list[Asistencia]:
        """Registros de todos los empleados en una fecha"""
        try:
            return (
                self.session.query(Asistencia)
                .filter(Asistencia.fecha == fecha)
                .order_by(Asistencia.empleado_id)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo asistencias del {fecha}: {e}")
            return []

    def get_por_tipo(
        self, tipo: str | TipoAsistencia, desde: date | None = None, hasta: date | None = None
    ) -> list[Asistencia]:
        """Registros de un tipo concreto de asistencia"""
        try:
            tipo_val = tipo.value if hasattr(tipo, "value") else str(tipo)
            query = self.session.query(Asistencia).filter(Asistencia.tipo == tipo_val)
            if desde is not None:
                query = query.filter(Asistencia.fecha >= desde)
            if hasta is not None:
                query = query.filter(Asistencia.fecha <= hasta)
            return query.order_by(Asistencia.fecha.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo asistencias de tipo {tipo}: {e}")
            return []

    def get_faltas(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        solo_injustificadas: bool = False,
    ) -> list[Asistencia]:
        """Faltas registradas en un período"""
        try:
            query = self.session.query(Asistencia).filter(
                Asistencia.tipo == TipoAsistencia.AUSENTE.value
            )
            if solo_injustificadas:
                query = query.filter(Asistencia.justificada == 0)
            if desde is not None:
                query = query.filter(Asistencia.fecha >= desde)
            if hasta is not None:
                query = query.filter(Asistencia.fecha <= hasta)
            return query.order_by(Asistencia.fecha.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo faltas del período: {e}")
            return []

    def get_totales_periodo(self, empleado_id: int, desde: date, hasta: date) -> dict:
        """
        Totales de un empleado en un período

        Devuelve en una sola consulta todo lo que necesita la nómina:
        horas trabajadas, horas extra por tipo, tardanzas y faltas.
        """
        try:
            fila = (
                self.session.query(
                    func.coalesce(func.sum(Asistencia.horas_trabajadas), 0),
                    func.coalesce(func.sum(Asistencia.horas_extra_diurnas), 0),
                    func.coalesce(func.sum(Asistencia.horas_extra_nocturnas), 0),
                    func.coalesce(func.sum(Asistencia.horas_extra_feriadas), 0),
                    func.coalesce(func.sum(Asistencia.minutos_tardanza), 0),
                    func.count(Asistencia.id),
                )
                .filter(
                    and_(
                        Asistencia.empleado_id == empleado_id,
                        Asistencia.fecha >= desde,
                        Asistencia.fecha <= hasta,
                    )
                )
                .first()
            )
            faltas = (
                self.session.query(func.count(Asistencia.id))
                .filter(
                    and_(
                        Asistencia.empleado_id == empleado_id,
                        Asistencia.fecha >= desde,
                        Asistencia.fecha <= hasta,
                        Asistencia.tipo == TipoAsistencia.AUSENTE.value,
                        Asistencia.justificada == 0,
                    )
                )
                .scalar()
            )
            if fila is None:
                return self._totales_vacios()
            return {
                "horas_trabajadas": round(float(fila[0] or 0), 2),
                "horas_extra_diurnas": round(float(fila[1] or 0), 2),
                "horas_extra_nocturnas": round(float(fila[2] or 0), 2),
                "horas_extra_feriadas": round(float(fila[3] or 0), 2),
                "minutos_tardanza": int(fila[4] or 0),
                "dias_registrados": int(fila[5] or 0),
                "faltas_injustificadas": int(faltas or 0),
            }
        except SQLAlchemyError as e:
            logger.error(
                f"Error obteniendo totales de asistencia del empleado {empleado_id}: {e}"
            )
            return self._totales_vacios()

    @staticmethod
    def _totales_vacios() -> dict:
        """Totales en cero, para cuando no hay registros o falla la consulta"""
        return {
            "horas_trabajadas": 0.0,
            "horas_extra_diurnas": 0.0,
            "horas_extra_nocturnas": 0.0,
            "horas_extra_feriadas": 0.0,
            "minutos_tardanza": 0,
            "dias_registrados": 0,
            "faltas_injustificadas": 0,
        }

    def get_ultimo_registro(self, empleado_id: int) -> Asistencia | None:
        """Último registro de asistencia de un empleado"""
        try:
            return (
                self.session.query(Asistencia)
                .filter(Asistencia.empleado_id == empleado_id)
                .order_by(Asistencia.fecha.desc())
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo el último registro del empleado {empleado_id}: {e}")
            return None

    def get_empleados_con_registro(self, fecha: date) -> set[int]:
        """IDs de los empleados que ya tienen registro en una fecha"""
        try:
            filas = (
                self.session.query(Asistencia.empleado_id)
                .filter(Asistencia.fecha == fecha)
                .distinct()
                .all()
            )
            return {int(fila[0]) for fila in filas}
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo empleados con registro del {fecha}: {e}")
            return set()

    def get_estadisticas(self, desde: date | None = None, hasta: date | None = None) -> dict:
        """Estadísticas agregadas de asistencia del período consultado"""
        try:
            query = self.session.query(
                Asistencia.tipo, func.count(Asistencia.id)
            ).group_by(Asistencia.tipo)
            if desde is not None:
                query = query.filter(Asistencia.fecha >= desde)
            if hasta is not None:
                query = query.filter(Asistencia.fecha <= hasta)
            por_tipo = {
                (fila[0].value if hasattr(fila[0], "value") else str(fila[0])): int(fila[1])
                for fila in query.all()
            }
            total = sum(por_tipo.values())
            faltas = por_tipo.get(TipoAsistencia.AUSENTE.value, 0)
            return {
                "total_registros": total,
                "por_tipo": por_tipo,
                "faltas": faltas,
                "ausentismo_porcentaje": round(faltas / total * 100, 2) if total else 0.0,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de asistencia: {e}")
            return {"total_registros": 0, "por_tipo": {}, "faltas": 0, "ausentismo_porcentaje": 0.0}
