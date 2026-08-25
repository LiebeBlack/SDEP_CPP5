from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
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
        ).order_by(Pago.periodo_inicio.desc()).all()
    
    def get_by_tipo(self, tipo: Union[str, TipoPago]) -> List[Pago]:
        """Obtiene pagos por tipo"""
        tipo_val = tipo.value if hasattr(tipo, 'value') else str(tipo)
        return self.session.query(Pago).filter(
            or_(
                Pago.tipo_pago == tipo_val,
                Pago.tipo_pago == tipo
            )
        ).all()
    
    def get_by_metodo(self, metodo: Union[str, MetodoPago]) -> List[Pago]:
        """Obtiene pagos por método de pago"""
        metodo_val = metodo.value if hasattr(metodo, 'value') else str(metodo)
        return self.session.query(Pago).filter(
            or_(
                Pago.metodo_pago == metodo_val,
                Pago.metodo_pago == metodo
            )
        ).all()
    
    def get_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Pago]:
        """Obtiene pagos en un periodo"""
        return self.session.query(Pago).filter(
            and_(
                Pago.periodo_inicio <= fecha_fin,
                Pago.periodo_fin >= fecha_inicio
            )
        ).order_by(Pago.periodo_inicio.desc()).all()
    
    def get_by_empleado_periodo(self, empleado_id: int, fecha_inicio: date, fecha_fin: date) -> List[Pago]:
        """Obtiene pagos de un empleado en un periodo"""
        return self.session.query(Pago).filter(
            and_(
                Pago.empleado_id == empleado_id,
                Pago.periodo_inicio <= fecha_fin,
                Pago.periodo_fin >= fecha_inicio
            )
        ).all()
    
    def get_pagados(self) -> List[Pago]:
        """Obtiene pagos ya realizados"""
        return self.session.query(Pago).filter(Pago.pagado == 1).order_by(Pago.periodo_inicio.desc()).all()
    
    def get_pendientes(self) -> List[Pago]:
        """Obtiene pagos pendientes"""
        return self.session.query(Pago).filter(Pago.pagado == 0).order_by(Pago.periodo_inicio.desc()).all()
    
    def get_pendientes_by_empleado(self, empleado_id: int) -> List[Pago]:
        """Obtiene pagos pendientes de un empleado"""
        return self.session.query(Pago).filter(
            and_(
                Pago.empleado_id == empleado_id,
                Pago.pagado == 0
            )
        ).order_by(Pago.periodo_inicio.desc()).all()
    
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
        return round(float(result[0] or 0.0), 2)
    
    def get_total_by_periodo(self, fecha_inicio: date, fecha_fin: date) -> float:
        """Obtiene el total de pagos en un periodo"""
        result = self.session.query(func.sum(Pago.monto_neto)).filter(
            and_(
                Pago.periodo_inicio <= fecha_fin,
                Pago.periodo_fin >= fecha_inicio
            )
        ).first()
        return round(float(result[0] or 0.0), 2)
    
    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de pagos por tipo"""
        stats = {t.value: 0 for t in TipoPago}
        pagos = self.get_all()
        for pago in pagos:
            tipo = pago.tipo_pago.value if hasattr(pago.tipo_pago, 'value') else str(pago.tipo_pago)
            stats[tipo] = stats.get(tipo, 0) + 1
        return stats
    
    def get_estadisticas_por_metodo(self) -> dict:
        """Obtiene estadísticas de pagos por método"""
        stats = {m.value: 0 for m in MetodoPago}
        pagos = self.get_all()
        for pago in pagos:
            metodo = pago.metodo_pago.value if hasattr(pago.metodo_pago, 'value') else str(pago.metodo_pago)
            stats[metodo] = stats.get(metodo, 0) + 1
        return stats
    
    def get_ultimo_pago_empleado(self, empleado_id: int) -> Optional[Pago]:
        """Obtiene el último pago de un empleado"""
        return self.session.query(Pago).filter(
            Pago.empleado_id == empleado_id
        ).order_by(Pago.fecha_pago.desc(), Pago.id.desc()).first()