"""
Prestamo Repository
Repositorio para anticipos y préstamos al empleado

Resuelve las consultas del descuento diferido: préstamos activos por
empleado, cuota a descontar en la próxima nómina, saldos pendientes y
registro de cada descuento aplicado.
"""

import logging
from datetime import date

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import EstadoPrestamo, Prestamo, TipoPrestamo

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PrestamoRepository(BaseRepository[Prestamo]):
    """Repositorio de préstamos con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Prestamo, session)

    def get_by_empleado(self, empleado_id: int) -> list[Prestamo]:
        """Préstamos de un empleado, del más reciente al más antiguo"""
        try:
            return (
                self.session.query(Prestamo)
                .filter(Prestamo.empleado_id == empleado_id)
                .order_by(Prestamo.fecha_solicitud.desc(), Prestamo.id.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo préstamos del empleado {empleado_id}: {e}")
            return []

    def get_by_estado(self, estado: str | EstadoPrestamo) -> list[Prestamo]:
        """Préstamos en un estado concreto"""
        try:
            estado_val = estado.value if hasattr(estado, "value") else str(estado)
            return (
                self.session.query(Prestamo)
                .filter(Prestamo.estado == estado_val)
                .order_by(Prestamo.fecha_solicitud.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo préstamos en estado {estado}: {e}")
            return []

    def get_activos(self, empleado_id: int | None = None) -> list[Prestamo]:
        """
        Préstamos con saldo pendiente

        Args:
            empleado_id: Si se entrega, limita el resultado a ese empleado
        """
        try:
            query = self.session.query(Prestamo).filter(
                Prestamo.estado.in_(
                    [
                        EstadoPrestamo.APROBADO.value,
                        EstadoPrestamo.ACTIVO.value,
                    ]
                ),
                Prestamo.saldo > 0,
            )
            if empleado_id is not None:
                query = query.filter(Prestamo.empleado_id == empleado_id)
            return query.order_by(Prestamo.fecha_solicitud).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo préstamos activos: {e}")
            return []

    def get_pendientes_aprobacion(self) -> list[Prestamo]:
        """Solicitudes de préstamo o anticipo a la espera de aprobación"""
        try:
            return (
                self.session.query(Prestamo)
                .filter(Prestamo.estado == EstadoPrestamo.SOLICITADO.value)
                .order_by(Prestamo.fecha_solicitud)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo préstamos por aprobar: {e}")
            return []

    def get_siguiente_a_descontar(self, empleado_id: int) -> Prestamo | None:
        """
        Préstamo al que corresponde descontar la próxima cuota

        Se atiende primero el más antiguo con cuotas pendientes, para
        cerrar las deudas en el orden en que se contrajeron.
        """
        try:
            return (
                self.session.query(Prestamo)
                .filter(
                    Prestamo.empleado_id == empleado_id,
                    Prestamo.estado.in_(
                        [
                            EstadoPrestamo.APROBADO.value,
                            EstadoPrestamo.ACTIVO.value,
                        ]
                    ),
                    Prestamo.saldo > 0,
                    Prestamo.cuotas_pagadas < Prestamo.numero_cuotas,
                )
                .order_by(Prestamo.fecha_solicitud, Prestamo.id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error buscando la cuota pendiente del empleado {empleado_id}: {e}")
            return None

    def get_saldo_total(self, empleado_id: int) -> float:
        """Saldo total pendiente de un empleado"""
        try:
            total = (
                self.session.query(func.coalesce(func.sum(Prestamo.saldo), 0))
                .filter(
                    Prestamo.empleado_id == empleado_id,
                    Prestamo.estado.in_(
                        [
                            EstadoPrestamo.APROBADO.value,
                            EstadoPrestamo.ACTIVO.value,
                        ]
                    ),
                )
                .scalar()
            )
            return round(float(total or 0.0), 2)
        except SQLAlchemyError as e:
            logger.error(f"Error calculando el saldo del empleado {empleado_id}: {e}")
            return 0.0

    def registrar_descuento(
        self, prestamo_id: int, monto: float, fecha: date | None = None
    ) -> bool:
        """
        Aplica un descuento a un préstamo y actualiza su estado

        El cálculo de cuotas y saldos vive en src/nomina/prestamos.py;
        este método solo persiste el resultado.
        """
        try:
            from src.nomina.prestamos import aplicar_descuento
            from src.nomina.tipos import a_decimal

            prestamo = self.get_by_id(prestamo_id)
            if not prestamo:
                return False

            estado = aplicar_descuento(
                saldo=a_decimal(prestamo.saldo),
                cuotas_pagadas=int(prestamo.cuotas_pagadas or 0),
                numero_cuotas=int(prestamo.numero_cuotas or 1),
                descuento=a_decimal(monto),
                fecha=fecha or date.today(),
            )
            prestamo.saldo = estado["saldo"]
            prestamo.cuotas_pagadas = estado["cuotas_pagadas"]
            prestamo.estado = estado["estado"]
            prestamo.fecha_ultimo_descuento = estado["fecha_ultimo_descuento"]
            self.session.commit()
            logger.info(
                f"Préstamo {prestamo_id}: descuento de {monto} aplicado, "
                f"saldo {prestamo.saldo}"
            )
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error registrando descuento del préstamo {prestamo_id}: {e}")
            return False

    def get_estadisticas(self) -> dict:
        """Estadísticas de préstamos y anticipos"""
        try:
            activos = self.get_activos()
            por_estado = {
                (fila[0].value if hasattr(fila[0], "value") else str(fila[0])): int(fila[1])
                for fila in self.session.query(Prestamo.estado, func.count(Prestamo.id))
                .group_by(Prestamo.estado)
                .all()
            }
            saldo_total = sum(float(prestamo.saldo or 0) for prestamo in activos)
            return {
                "total": self.count(),
                "activos": len(activos),
                "por_estado": por_estado,
                "saldo_pendiente": round(saldo_total, 2),
                "anticipos": len(
                    [
                        prestamo
                        for prestamo in activos
                        if (prestamo.tipo_valor == TipoPrestamo.ANTICIPO.value)
                    ]
                ),
            }
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de préstamos: {e}")
            return {
                "total": 0,
                "activos": 0,
                "por_estado": {},
                "saldo_pendiente": 0.0,
                "anticipos": 0,
            }

    def get_activos_con_cuota(self, empleado_id: int | None = None) -> list[Prestamo]:
        """
        Préstamos activos que aún tienen cuotas por descontar

        Es la consulta que usa la nómina para saber a quién descontarle.
        """
        try:
            return [
                prestamo
                for prestamo in self.get_activos(empleado_id)
                if int(prestamo.cuotas_pagadas or 0) < int(prestamo.numero_cuotas or 0)
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo préstamos con cuota pendiente: {e}")
            return []

    def contar_activos_empleado(self, empleado_id: int) -> int:
        """Cantidad de préstamos activos de un empleado"""
        try:
            return (
                self.session.query(func.count(Prestamo.id))
                .filter(
                    and_(
                        Prestamo.empleado_id == empleado_id,
                        Prestamo.estado.in_(
                            [
                                EstadoPrestamo.APROBADO.value,
                                EstadoPrestamo.ACTIVO.value,
                            ]
                        ),
                        Prestamo.saldo > 0,
                    )
                )
                .scalar()
                or 0
            )
        except SQLAlchemyError as e:
            logger.error(f"Error contando préstamos activos del empleado {empleado_id}: {e}")
            return 0
