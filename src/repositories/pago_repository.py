"""
Pago Repository
Repositorio para operaciones de datos de pagos
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import date, datetime

from src.models import Pago, TipoPago, MetodoPago
from .base_repository import BaseRepository


class PagoRepository(BaseRepository[Pago]):
    """Repositorio de pagos"""
    
    def __init__(self, session: Session):
        super().__init__(Pago, session)
    
    def get_by_empleado(self, empleado_id: int) -> List[Pago]:
        """Obtiene pagos de un empleado"""
        return self.session.query(Pago).filter(
            Pago.empleado_id == empleado_id
        ).all()
    
    def get_by_tipo(self, tipo: str) -> List[Pago]:
        """Obtiene pagos por tipo"""
        return self.session.query(Pago).filter(
            Pago.tipo_pago == tipo
        ).all()
    
    def get_by_metodo(self, metodo: str) -> List[Pago]:
        """Obtiene pagos por método de pago"""
        return self.session.query(Pago).filter(
            Pago.metodo_pago == metodo
        ).all()
    
    def get_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Pago]:
        """Obtiene pagos en un periodo"""
        return self.session.query(Pago).filter(
            and_(
                Pago.periodo_inicio >= fecha_inicio,
                Pago.periodo_fin <= fecha_fin
            )
        ).all()
    
    def get_by_empleado_periodo(self, empleado_id: int, fecha_inicio: date, fecha_fin: date) -> List[Pago]:
        """Obtiene pagos de un empleado en un periodo"""
        return self.session.query(Pago).filter(
            and_(
                Pago.empleado_id == empleado_id,
                Pago.periodo_inicio >= fecha_inicio,
                Pago.periodo_fin <= fecha_fin
            )
        ).all()
    
    def get_pagados(self) -> List[Pago]:
        """Obtiene pagos ya realizados"""
        return self.session.query(Pago).filter(Pago.pagado == 1).all()
    
    def get_pendientes(self) -> List[Pago]:
        """Obtiene pagos pendientes"""
        return self.session.query(Pago).filter(Pago.pagado == 0).all()
    
    def get_pendientes_by_empleado(self, empleado_id: int) -> List[Pago]:
        """Obtiene pagos pendientes de un empleado"""
        return self.session.query(Pago).filter(
            and_(
                Pago.empleado_id == empleado_id,
                Pago.pagado == 0
            )
        ).all()
    
    def marcar_pagado(self, id: int) -> bool:
        """Marca un pago como realizado"""
        pago = self.get_by_id(id)
        if pago:
            pago.pagado = 1
            pago.fecha_registro_pago = date.today()
            self.session.commit()
            return True
        return False
    
    def marcar_pendiente(self, id: int) -> bool:
        """Marca un pago como pendiente"""
        pago = self.get_by_id(id)
        if pago:
            pago.pagado = 0
            pago.fecha_registro_pago = None
            self.session.commit()
            return True
        return False
    
    def get_total_by_empleado(self, empleado_id: int) -> float:
        """Obtiene el total de pagos de un empleado"""
        result = self.session.query(func.sum(Pago.monto_neto)).filter(
            Pago.empleado_id == empleado_id
        ).first()
        return float(result[0] or 0.0)
    
    def get_total_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> float:
        """Obtiene el total de pagos en un periodo"""
        result = self.session.query(func.sum(Pago.monto_neto)).filter(
            and_(
                Pago.periodo_inicio >= fecha_inicio,
                Pago.periodo_fin <= fecha_fin
            )
        ).first()
        return float(result[0] or 0.0)
    
    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de pagos por tipo"""
        stats = {}
        pagos = self.get_all()
        for pago in pagos:
            tipo = pago.tipo_pago
            stats[tipo] = stats.get(tipo, 0) + 1
        return stats
    
    def get_estadisticas_por_metodo(self) -> dict:
        """Obtiene estadísticas de pagos por método"""
        stats = {}
        pagos = self.get_all()
        for pago in pagos:
            metodo = pago.metodo_pago
            stats[metodo] = stats.get(metodo, 0) + 1
        return stats
    
    def get_ultimo_pago_empleado(self, empleado_id: int) -> Optional[Pago]:
        """Obtiene el último pago de un empleado"""
        return self.session.query(Pago).filter(
            Pago.empleado_id == empleado_id
        ).order_by(Pago.fecha_pago.desc()).first()