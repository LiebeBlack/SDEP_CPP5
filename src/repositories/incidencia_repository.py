from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date
import logging

from src.models import Incidencia, TipoIncidencia, EstadoIncidencia
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class IncidenciaRepository(BaseRepository[Incidencia]):
    """Repositorio de incidencias"""

    def __init__(self, session: Session):
        super().__init__(Incidencia, session)

    def get_by_empleado(self, empleado_id: int) -> list[Incidencia]:
        """Obtiene incidencias de un empleado"""
        return (
            self.session.query(Incidencia)
            .filter(Incidencia.empleado_id == empleado_id)
            .order_by(Incidencia.fecha_inicio.desc())
            .all()
        )

    def get_by_tipo(self, tipo: str | TipoIncidencia) -> list[Incidencia]:
        """Obtiene incidencias por tipo"""
        tipo_val = tipo.value if hasattr(tipo, "value") else str(tipo)
        return (
            self.session.query(Incidencia)
            .filter(or_(Incidencia.tipo_incidencia == tipo_val, Incidencia.tipo_incidencia == tipo))
            .all()
        )

    def get_by_estado(self, estado: str | EstadoIncidencia) -> list[Incidencia]:
        """Obtiene incidencias por estado"""
        estado_val = estado.value if hasattr(estado, "value") else str(estado)
        return (
            self.session.query(Incidencia)
            .filter(or_(Incidencia.estado == estado_val, Incidencia.estado == estado))
            .all()
        )

    def get_by_empleado_y_tipo(
        self, empleado_id: int, tipo: str | TipoIncidencia
    ) -> list[Incidencia]:
        """Obtiene incidencias de un empleado por tipo"""
        tipo_val = tipo.value if hasattr(tipo, "value") else str(tipo)
        return (
            self.session.query(Incidencia)
            .filter(
                and_(
                    Incidencia.empleado_id == empleado_id,
                    or_(Incidencia.tipo_incidencia == tipo_val, Incidencia.tipo_incidencia == tipo),
                )
            )
            .all()
        )

    def get_pendientes(self) -> list[Incidencia]:
        """Obtiene incidencias pendientes de aprobación"""
        return (
            self.session.query(Incidencia)
            .filter(Incidencia.estado == EstadoIncidencia.PENDIENTE.value)
            .all()
        )

    def get_vigentes(self) -> list[Incidencia]:
        """Obtiene incidencias vigentes actualmente"""
        hoy = date.today()
        return (
            self.session.query(Incidencia)
            .filter(
                and_(
                    Incidencia.fecha_inicio <= hoy,
                    Incidencia.fecha_fin >= hoy,
                    Incidencia.estado == EstadoIncidencia.APROBADO.value,
                )
            )
            .all()
        )

    def get_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> list[Incidencia]:
        """Obtiene incidencias en un periodo de tiempo"""
        return (
            self.session.query(Incidencia)
            .filter(
                and_(Incidencia.fecha_inicio <= fecha_fin, Incidencia.fecha_fin >= fecha_inicio)
            )
            .all()
        )

    def get_by_empleado_periodo(
        self, empleado_id: int, fecha_inicio: date, fecha_fin: date
    ) -> list[Incidencia]:
        """Obtiene incidencias de un empleado en un periodo"""
        return (
            self.session.query(Incidencia)
            .filter(
                and_(
                    Incidencia.empleado_id == empleado_id,
                    Incidencia.fecha_inicio <= fecha_fin,
                    Incidencia.fecha_fin >= fecha_inicio,
                )
            )
            .all()
        )

    def aprobar(
        self,
        id: int,
        aprobado_por: str,
        comentarios: str | None = None,
        dias_aprobados: int | None = None,
    ) -> bool:
        """Aprueba una incidencia con manejo de errores"""
        try:
            incidencia = self.get_by_id(id)
            if incidencia:
                incidencia.estado = EstadoIncidencia.APROBADO.value
                incidencia.aprobado_por = aprobado_por
                incidencia.fecha_aprobacion = date.today()
                incidencia.comentarios_aprobacion = comentarios
                if dias_aprobados is not None and dias_aprobados > 0:
                    incidencia.dias_aprobados = dias_aprobados
                else:
                    incidencia.dias_aprobados = incidencia.dias_solicitados
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al aprobar incidencia {id}: {e}")
            return False

    def rechazar(self, id: int, rechazado_por: str, comentarios: str | None = None) -> bool:
        """Rechaza una incidencia con manejo de errores"""
        try:
            incidencia = self.get_by_id(id)
            if incidencia:
                incidencia.estado = EstadoIncidencia.RECHAZADO.value
                incidencia.aprobado_por = rechazado_por
                incidencia.fecha_aprobacion = date.today()
                incidencia.comentarios_aprobacion = comentarios
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al rechazar incidencia {id}: {e}")
            return False

    def completar(self, id: int) -> bool:
        """Marca una incidencia como completada con manejo de errores"""
        try:
            incidencia = self.get_by_id(id)
            if incidencia:
                incidencia.estado = EstadoIncidencia.COMPLETADO.value
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al completar incidencia {id}: {e}")
            return False

    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de incidencias por tipo

        El conteo se agrega en SQL (GROUP BY): antes se cargaban todas las
        filas en memoria —y solo las primeras 100, por el límite por
        defecto de get_all— para contarlas.
        """
        stats = {t.value: 0 for t in TipoIncidencia}
        filas = (
            self.session.query(Incidencia.tipo_incidencia, func.count(Incidencia.id))
            .group_by(Incidencia.tipo_incidencia)
            .all()
        )
        for tipo, total in filas:
            clave = tipo.value if hasattr(tipo, "value") else str(tipo)
            stats[clave] = stats.get(clave, 0) + int(total or 0)
        return stats

    def get_estadisticas_por_estado(self) -> dict:
        """Obtiene estadísticas de incidencias por estado (agregado en SQL)"""
        stats = {e.value: 0 for e in EstadoIncidencia}
        filas = (
            self.session.query(Incidencia.estado, func.count(Incidencia.id))
            .group_by(Incidencia.estado)
            .all()
        )
        for estado, total in filas:
            clave = estado.value if hasattr(estado, "value") else str(estado)
            stats[clave] = stats.get(clave, 0) + int(total or 0)
        return stats
