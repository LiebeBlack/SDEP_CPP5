"""
Pago Model
Modelo de datos para pagos y nómina
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Text, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, BaseModel
from .enums import MetodoPago

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .empleado import Empleado
    from .prestamo import Prestamo


class Pago(Base, BaseModel):
    """Modelo de pago"""

    __tablename__ = "pagos"

    # Relación con empleado
    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )

    # Datos del pago
    tipo_pago: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metodo_pago: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MetodoPago.TRANSFERENCIA.value
    )

    # Periodo
    periodo_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_fin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    # Montos
    monto_bruto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    monto_neto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    descuentos: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    bonificaciones: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    horas_extra: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    # Desglose de pagos
    salario_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deduccion_seguro: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    deduccion_pension: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    deduccion_impuesto: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    otras_deducciones: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    # Desglose del motor de nómina
    modalidad_calculo: Mapped[str] = mapped_column(
        String(20), default="porcentaje", nullable=False
    )
    base_gravable: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    horas_extra_diurnas: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    horas_extra_nocturnas: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    horas_extra_feriadas: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    deduccion_prestamo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    aguinaldo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    bono_vacacional: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    aporte_seguro_patronal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    aporte_pension_patronal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    isr_tramo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prestamo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("prestamos.id"), nullable=True
    )

    # Detalles adicionales
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    referencia_pago: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Estado
    pagado: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fecha_registro_pago: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="pagos")
    prestamo: Mapped["Prestamo | None"] = relationship("Prestamo")

    @property
    def dias_trabajados(self):
        """Calcula los días trabajados en el periodo"""
        if self.periodo_inicio and self.periodo_fin:
            try:
                ini = (
                    self.periodo_inicio
                    if isinstance(self.periodo_inicio, date)
                    else self.periodo_inicio.date()
                )
                fin = (
                    self.periodo_fin
                    if isinstance(self.periodo_fin, date)
                    else self.periodo_fin.date()
                )
                delta = fin - ini
                return max(0, delta.days + 1)
            except Exception:
                return 0
        return 0

    @property
    def salario_diario(self):
        """Calcula el salario diario"""
        if self.dias_trabajados > 0 and self.salario_base:
            try:
                return round(float(self.salario_base) / 30.0, 2)
            except Exception:
                return 0.0
        return 0.0

    @property
    def total_deducciones(self):
        """Calcula el total de deducciones"""
        return round(
            float(self.deduccion_seguro or 0)
            + float(self.deduccion_pension or 0)
            + float(self.deduccion_impuesto or 0)
            + float(self.otras_deducciones or 0)
            + float(self.descuentos or 0)
            + float(self.deduccion_prestamo or 0),
            2,
        )

    @property
    def total_ingresos(self):
        """Calcula el total de ingresos"""
        return round(
            float(self.salario_base or 0)
            + float(self.bonificaciones or 0)
            + float(self.horas_extra or 0)
            + float(self.aguinaldo or 0)
            + float(self.bono_vacacional or 0),
            2,
        )

    @property
    def total_aportes_patronales(self):
        """Aportes a cargo del patrono (no descontados del empleado)"""
        return round(
            float(self.aporte_seguro_patronal or 0)
            + float(self.aporte_pension_patronal or 0),
            2,
        )

    @property
    def desglose_horas_extra(self) -> dict:
        """Detalle de las horas extra del período por tipo"""
        return {
            "diurnas": float(self.horas_extra_diurnas or 0),
            "nocturnas": float(self.horas_extra_nocturnas or 0),
            "feriadas": float(self.horas_extra_feriadas or 0),
            "monto": float(self.horas_extra or 0),
        }

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data["dias_trabajados"] = self.dias_trabajados
        data["salario_diario"] = self.salario_diario
        data["total_deducciones"] = self.total_deducciones
        data["total_ingresos"] = self.total_ingresos
        data["total_aportes_patronales"] = self.total_aportes_patronales
        data["desglose_horas_extra"] = self.desglose_horas_extra
        return data
