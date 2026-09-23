"""
Prestamo Model
Modelo de datos de anticipos y préstamos al empleado

Registra los montos entregados al empleado y su descuento por cuotas
en la nómina, junto con el saldo pendiente. Es la base del descuento
diferido que aplica el motor de nómina en cada período.
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import EstadoPrestamo, TipoPrestamo, valores_sql

if TYPE_CHECKING:
    from .empleado import Empleado


CERO = Decimal("0.00")


class Prestamo(Base, BaseModel):
    """
    Modelo de anticipo o préstamo al empleado

    Atributos:
        empleado_id: Empleado que recibe el monto
        tipo: Anticipo (de una sola cuota) o préstamo (varias cuotas)
        estado: Estado dentro del ciclo de aprobación y pago
        monto: Monto total otorgado
        numero_cuotas: Cantidad de cuotas pactadas
        monto_cuota: Valor de cada cuota
        cuotas_pagadas: Cuotas ya descontadas en nómina
        saldo: Saldo pendiente de descuento
        fecha_solicitud: Fecha de la solicitud
        fecha_aprobacion: Fecha de aprobación
        fecha_primer_descuento: Fecha del primer descuento en nómina
        fecha_ultimo_descuento: Fecha del último descuento aplicado
        motivo: Razón de la solicitud
        aprobado_por: Usuario que aprobó la operación
        observaciones: Notas adicionales
    """

    __tablename__ = "prestamos"

    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoPrestamo] = mapped_column(
        SQLEnum(TipoPrestamo, values_callable=valores_sql),
        nullable=False,
        default=TipoPrestamo.PRESTAMO.value,
    )
    estado: Mapped[EstadoPrestamo] = mapped_column(
        SQLEnum(EstadoPrestamo, values_callable=valores_sql),
        nullable=False,
        default=EstadoPrestamo.SOLICITADO.value,
        index=True,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    numero_cuotas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    monto_cuota: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=CERO)
    cuotas_pagadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saldo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=CERO)
    fecha_solicitud: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    fecha_aprobacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_primer_descuento: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_ultimo_descuento: Mapped[date | None] = mapped_column(Date, nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprobado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="prestamos")

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------
    @property
    def tipo_valor(self) -> str:
        """Valor string del tipo de operación"""
        return self.tipo.value if hasattr(self.tipo, "value") else str(self.tipo)

    @property
    def estado_valor(self) -> str:
        """Valor string del estado"""
        return self.estado.value if hasattr(self.estado, "value") else str(self.estado)

    @property
    def cuotas_pendientes(self) -> int:
        """Cuotas que faltan por descontar"""
        return max(0, int(self.numero_cuotas or 0) - int(self.cuotas_pagadas or 0))

    @property
    def monto_pagado(self) -> Decimal:
        """Monto ya descontado en nómina"""
        pagado = Decimal(self.monto or 0) - Decimal(self.saldo or 0)
        return max(CERO, pagado).quantize(Decimal("0.01"))

    @property
    def porcentaje_pagado(self) -> float:
        """Porcentaje del monto ya descontado"""
        total = Decimal(self.monto or 0)
        if total <= CERO:
            return 0.0
        return round(float(self.monto_pagado / total * 100), 2)

    @property
    def esta_activo(self) -> bool:
        """Indica si el préstamo está aprobado y con saldo pendiente"""
        return self.estado_valor in (
            EstadoPrestamo.APROBADO.value,
            EstadoPrestamo.ACTIVO.value,
        ) and Decimal(self.saldo or 0) > CERO

    @property
    def se_puede_descontar(self) -> bool:
        """Indica si corresponde aplicar una cuota en la próxima nómina"""
        return self.esta_activo and self.cuotas_pendientes > 0

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["tipo"] = self.tipo_valor
        data["estado"] = self.estado_valor
        data["cuotas_pendientes"] = self.cuotas_pendientes
        data["monto_pagado"] = float(self.monto_pagado)
        data["porcentaje_pagado"] = self.porcentaje_pagado
        data["esta_activo"] = self.esta_activo
        return data
