"""
Asistencia Model
Modelo de datos del registro diario de asistencia

Almacena la jornada efectiva de cada empleado: entrada, salida, horas
trabajadas, tardanzas y horas extra clasificadas por tipo. Es la fuente
de datos del módulo de asistencia y del cálculo de horas extra que
consume la nómina.
"""

from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import TipoAsistencia, valores_sql

if TYPE_CHECKING:
    from .empleado import Empleado
    from .incidencia import Incidencia


CERO = Decimal("0.00")


class Asistencia(Base, BaseModel):
    """
    Modelo de registro de asistencia

    Un único registro por empleado y fecha, con la jornada real y las
    horas extra del día.

    Atributos:
        empleado_id: Empleado al que corresponde el registro
        fecha: Día de la jornada
        tipo: Clasificación del día (presencia, tardanza, ausencia...)
        hora_entrada: Hora real de entrada
        hora_salida: Hora real de salida
        horas_trabajadas: Horas efectivas descontando el descanso
        minutos_tardanza: Minutos de retraso sobre el horario previsto
        horas_extra_diurnas: Horas extra en jornada diurna
        horas_extra_nocturnas: Horas extra en jornada nocturna o mixta
        horas_extra_feriadas: Horas extra en día feriado
        justificada: Indica si la falta está respaldada (1 = sí)
        incidencia_id: Incidencia aprobada que justifica la ausencia
        registrado_por: Usuario que capturó el registro
        observaciones: Notas adicionales
    """

    __tablename__ = "asistencias"
    __table_args__ = (
        UniqueConstraint("empleado_id", "fecha", name="uq_asistencia_empleado_fecha"),
    )

    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tipo: Mapped[TipoAsistencia] = mapped_column(
        SQLEnum(TipoAsistencia, values_callable=valores_sql),
        nullable=False,
        default=TipoAsistencia.PRESENTE.value,
    )
    hora_entrada: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_salida: Mapped[time | None] = mapped_column(Time, nullable=True)
    horas_trabajadas: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=CERO
    )
    minutos_tardanza: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    horas_extra_diurnas: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=CERO
    )
    horas_extra_nocturnas: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=CERO
    )
    horas_extra_feriadas: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=CERO
    )
    justificada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incidencia_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("incidencias.id"), nullable=True
    )
    registrado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="asistencias")
    incidencia: Mapped["Incidencia | None"] = relationship("Incidencia")

    @property
    def tipo_valor(self) -> str:
        """Valor string del tipo de asistencia"""
        return self.tipo.value if hasattr(self.tipo, "value") else str(self.tipo)

    @property
    def total_horas_extra(self) -> Decimal:
        """Suma de todas las horas extra del día"""
        return (
            Decimal(self.horas_extra_diurnas or 0)
            + Decimal(self.horas_extra_nocturnas or 0)
            + Decimal(self.horas_extra_feriadas or 0)
        ).quantize(Decimal("0.01"))

    @property
    def es_falta(self) -> bool:
        """Indica si el registro corresponde a una inasistencia sin justificar"""
        return self.tipo_valor == TipoAsistencia.AUSENTE.value and not self.justificada

    @property
    def tiene_tardanza(self) -> bool:
        """Indica si el registro acumuló minutos de tardanza"""
        return int(self.minutos_tardanza or 0) > 0

    @property
    def tiene_horas_extra(self) -> bool:
        """Indica si el día registró horas extra"""
        return self.total_horas_extra > CERO

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["tipo"] = self.tipo_valor
        data["total_horas_extra"] = float(self.total_horas_extra)
        data["es_falta"] = self.es_falta
        data["tiene_tardanza"] = self.tiene_tardanza
        data["hora_entrada"] = self.hora_entrada.strftime("%H:%M") if self.hora_entrada else None
        data["hora_salida"] = self.hora_salida.strftime("%H:%M") if self.hora_salida else None
        return data
