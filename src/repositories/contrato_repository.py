"""
Contrato Repository
Repositorio para los contratos laborales

Resuelve las consultas del ciclo de vida contractual: contrato vigente
de un empleado, contratos por vencer, vencidos, historial y
estadísticas por tipo y estado.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Contrato, EstadoContrato, TipoContrato

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

DIAS_UMBRAL_DEFECTO = 30


class ContratoRepository(BaseRepository[Contrato]):
    """Repositorio de contratos con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Contrato, session)

    def get_by_empleado(self, empleado_id: int) -> list[Contrato]:
        """Historial de contratos de un empleado, del más reciente al más antiguo"""
        try:
            return (
                self.session.query(Contrato)
                .filter(Contrato.empleado_id == empleado_id)
                .order_by(Contrato.fecha_inicio.desc(), Contrato.id.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo contratos del empleado {empleado_id}: {e}")
            return []

    def get_by_numero(self, numero: str) -> Contrato | None:
        """Contrato por su número único"""
        try:
            return (
                self.session.query(Contrato)
                .filter(Contrato.numero == numero)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error buscando el contrato {numero}: {e}")
            return None

    def get_vigente(self, empleado_id: int) -> Contrato | None:
        """
        Contrato vigente de un empleado

        Se considera vigente el contrato sin fecha de fin o con fecha de
        fin no vencida, siempre que no esté terminado.
        """
        try:
            hoy = date.today()
            return (
                self.session.query(Contrato)
                .filter(
                    Contrato.empleado_id == empleado_id,
                    Contrato.estado != EstadoContrato.TERMINADO.value,
                    or_(Contrato.fecha_fin.is_(None), Contrato.fecha_fin >= hoy),
                )
                .order_by(Contrato.fecha_inicio.desc())
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo el contrato vigente del empleado {empleado_id}: {e}")
            return None

    def get_vigentes(self) -> list[Contrato]:
        """Todos los contratos vigentes del sistema"""
        try:
            hoy = date.today()
            return (
                self.session.query(Contrato)
                .filter(
                    Contrato.estado != EstadoContrato.TERMINADO.value,
                    or_(Contrato.fecha_fin.is_(None), Contrato.fecha_fin >= hoy),
                )
                .order_by(Contrato.fecha_fin.is_(None), Contrato.fecha_fin)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo contratos vigentes: {e}")
            return []

    def get_by_estado(self, estado: str | EstadoContrato) -> list[Contrato]:
        """Contratos en un estado concreto"""
        try:
            estado_val = estado.value if hasattr(estado, "value") else str(estado)
            return (
                self.session.query(Contrato)
                .filter(Contrato.estado == estado_val)
                .order_by(Contrato.fecha_inicio.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo contratos en estado {estado}: {e}")
            return []

    def get_por_vencer(self, dias: int = DIAS_UMBRAL_DEFECTO) -> list[Contrato]:
        """
        Contratos que vencen dentro del umbral

        Solo incluye contratos con fecha de fin, aún no terminados y cuya
        fecha de fin cae entre hoy y hoy + días.
        """
        try:
            hoy = date.today()
            limite = hoy + timedelta(days=max(0, int(dias)))
            return (
                self.session.query(Contrato)
                .filter(
                    Contrato.estado != EstadoContrato.TERMINADO.value,
                    Contrato.fecha_fin.isnot(None),
                    Contrato.fecha_fin >= hoy,
                    Contrato.fecha_fin <= limite,
                )
                .order_by(Contrato.fecha_fin)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo contratos por vencer: {e}")
            return []

    def get_vencidos(self, hasta: date | None = None) -> list[Contrato]:
        """Contratos cuya fecha de fin ya pasó y siguen sin terminarse"""
        try:
            referencia = hasta or date.today()
            return (
                self.session.query(Contrato)
                .filter(
                    Contrato.estado != EstadoContrato.TERMINADO.value,
                    Contrato.fecha_fin.isnot(None),
                    Contrato.fecha_fin < referencia,
                )
                .order_by(Contrato.fecha_fin)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo contratos vencidos: {e}")
            return []

    def get_ultimo(self, empleado_id: int) -> Contrato | None:
        """Último contrato registrado para un empleado (para renovaciones)"""
        try:
            return (
                self.session.query(Contrato)
                .filter(Contrato.empleado_id == empleado_id)
                .order_by(Contrato.fecha_inicio.desc(), Contrato.id.desc())
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo el último contrato del empleado {empleado_id}: {e}")
            return None

    def get_estadisticas(self) -> dict:
        """Estadísticas de contratos por estado y tipo"""
        try:
            por_estado = {
                (fila[0].value if hasattr(fila[0], "value") else str(fila[0])): int(fila[1])
                for fila in self.session.query(Contrato.estado, func.count(Contrato.id))
                .group_by(Contrato.estado)
                .all()
            }
            por_tipo = {
                (fila[0].value if hasattr(fila[0], "value") else str(fila[0])): int(fila[1])
                for fila in self.session.query(Contrato.tipo, func.count(Contrato.id))
                .group_by(Contrato.tipo)
                .all()
            }
            vigentes = len(self.get_vigentes())
            return {
                "total": self.count(),
                "por_estado": por_estado,
                "por_tipo": por_tipo,
                "vigentes": vigentes,
                "indefinidos": por_tipo.get(TipoContrato.INDEFINIDO.value, 0),
            }
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de contratos: {e}")
            return {"total": 0, "por_estado": {}, "por_tipo": {}, "vigentes": 0, "indefinidos": 0}

    def contar_activos_por_empleado(self, empleado_id: int) -> int:
        """Cantidad de contratos no terminados de un empleado"""
        try:
            return (
                self.session.query(func.count(Contrato.id))
                .filter(
                    and_(
                        Contrato.empleado_id == empleado_id,
                        Contrato.estado != EstadoContrato.TERMINADO.value,
                    )
                )
                .scalar()
                or 0
            )
        except SQLAlchemyError as e:
            logger.error(f"Error contando contratos del empleado {empleado_id}: {e}")
            return 0
