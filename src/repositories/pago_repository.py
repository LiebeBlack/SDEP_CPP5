import logging
from datetime import date

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from src.models import MetodoPago, Pago, TipoPago

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PagoRepository(BaseRepository[Pago]):
    """Repositorio de pagos"""

    def __init__(self, session: Session):
        super().__init__(Pago, session)

    def get_by_empleado(self, empleado_id: int) -> list[Pago]:
        """Obtiene pagos de un empleado"""
        return (
            self.session.query(Pago)
            .filter(Pago.empleado_id == empleado_id)
            .order_by(Pago.periodo_inicio.desc())
            .all()
        )

    def get_by_tipo(self, tipo: str | TipoPago) -> list[Pago]:
        """Obtiene pagos por tipo"""
        tipo_val = tipo.value if hasattr(tipo, "value") else str(tipo)
        return (
            self.session.query(Pago)
            .filter(or_(Pago.tipo_pago == tipo_val, Pago.tipo_pago == tipo))
            .all()
        )

    def get_by_metodo(self, metodo: str | MetodoPago) -> list[Pago]:
        """Obtiene pagos por método de pago"""
        metodo_val = metodo.value if hasattr(metodo, "value") else str(metodo)
        return (
            self.session.query(Pago)
            .filter(or_(Pago.metodo_pago == metodo_val, Pago.metodo_pago == metodo))
            .all()
        )

    def get_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> list[Pago]:
        """Obtiene pagos en un periodo"""
        return (
            self.session.query(Pago)
            .filter(and_(Pago.periodo_inicio <= fecha_fin, Pago.periodo_fin >= fecha_inicio))
            .order_by(Pago.periodo_inicio.desc())
            .all()
        )

    def get_by_empleado_periodo(
        self, empleado_id: int, fecha_inicio: date, fecha_fin: date
    ) -> list[Pago]:
        """Obtiene pagos de un empleado en un periodo"""
        return (
            self.session.query(Pago)
            .filter(
                and_(
                    Pago.empleado_id == empleado_id,
                    Pago.periodo_inicio <= fecha_fin,
                    Pago.periodo_fin >= fecha_inicio,
                )
            )
            .all()
        )

    def get_pagados(self) -> list[Pago]:
        """Obtiene pagos ya realizados"""
        return (
            self.session.query(Pago)
            .filter(Pago.pagado == 1)
            .order_by(Pago.periodo_inicio.desc())
            .all()
        )

    def get_pendientes(self) -> list[Pago]:
        """Obtiene pagos pendientes"""
        return (
            self.session.query(Pago)
            .filter(Pago.pagado == 0)
            .order_by(Pago.periodo_inicio.desc())
            .all()
        )

    def get_pendientes_by_empleado(self, empleado_id: int) -> list[Pago]:
        """Obtiene pagos pendientes de un empleado"""
        return (
            self.session.query(Pago)
            .filter(and_(Pago.empleado_id == empleado_id, Pago.pagado == 0))
            .order_by(Pago.periodo_inicio.desc())
            .all()
        )

    def marcar_pagado(self, id: int) -> bool:
        """Marca un pago como realizado con manejo de errores"""
        try:
            pago = self.get_by_id(id)
            if pago:
                pago.pagado = 1
                pago.fecha_registro_pago = date.today()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al marcar pago {id} como pagado: {e}")
            return False

    def marcar_pendiente(self, id: int) -> bool:
        """Marca un pago como pendiente con manejo de errores"""
        try:
            pago = self.get_by_id(id)
            if pago:
                pago.pagado = 0
                pago.fecha_registro_pago = None
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al marcar pago {id} como pendiente: {e}")
            return False

    def get_total_by_empleado(self, empleado_id: int) -> float:
        """Obtiene el total de pagos de un empleado"""
        row = (
            self.session.query(func.sum(Pago.monto_neto))
            .filter(Pago.empleado_id == empleado_id)
            .first()
        )
        total = row[0] if row is not None else None
        return round(float(total or 0.0), 2)

    def get_total_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> float:
        """Obtiene el total de pagos en un periodo"""
        row = (
            self.session.query(func.sum(Pago.monto_neto))
            .filter(and_(Pago.periodo_inicio <= fecha_fin, Pago.periodo_fin >= fecha_inicio))
            .first()
        )
        total = row[0] if row is not None else None
        return round(float(total or 0.0), 2)

    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de pagos por tipo

        El conteo se agrega en SQL (GROUP BY): antes se cargaban todas las
        filas en memoria —y solo las primeras 100, por el límite por
        defecto de get_all— para contarlas.
        """
        stats = {t.value: 0 for t in TipoPago}
        filas = (
            self.session.query(Pago.tipo_pago, func.count(Pago.id)).group_by(Pago.tipo_pago).all()
        )
        for tipo, total in filas:
            clave = tipo.value if hasattr(tipo, "value") else str(tipo)
            stats[clave] = stats.get(clave, 0) + int(total or 0)
        return stats

    def get_estadisticas_por_metodo(self) -> dict:
        """Obtiene estadísticas de pagos por método (agregado en SQL)"""
        stats = {m.value: 0 for m in MetodoPago}
        filas = (
            self.session.query(Pago.metodo_pago, func.count(Pago.id))
            .group_by(Pago.metodo_pago)
            .all()
        )
        for metodo, total in filas:
            clave = metodo.value if hasattr(metodo, "value") else str(metodo)
            stats[clave] = stats.get(clave, 0) + int(total or 0)
        return stats

    def get_ultimo_pago_empleado(self, empleado_id: int) -> Pago | None:
        """Obtiene el último pago de un empleado"""
        return (
            self.session.query(Pago)
            .filter(Pago.empleado_id == empleado_id)
            .order_by(Pago.fecha_pago.desc(), Pago.id.desc())
            .first()
        )
