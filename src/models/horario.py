"""
Horario Model
Modelo de datos de los horarios de trabajo

Define la jornada semanal de cada empleado. Es la base para detectar
tardanzas, calcular las horas trabajadas y clasificar las horas extra
que después alimentan el motor de nómina.
"""

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import TipoJornada, valores_sql

if TYPE_CHECKING:
    from .empleado import Empleado


# Días de la semana según datetime.date.weekday() (0 = lunes)
NOMBRES_DIA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}


def nombre_dia(dia_semana: int) -> str:
    """Nombre legible de un día de la semana (0 = lunes)"""
    try:
        return NOMBRES_DIA.get(int(dia_semana), f"Día {dia_semana}")
    except (TypeError, ValueError):
        return f"Día {dia_semana}"


class Horario(Base, BaseModel):
    """
    Modelo de horario de trabajo

    Un registro por empleado y día de la semana, con la jornada
    asignada, el descanso y la tolerancia de llegada.

    Atributos:
        empleado_id: Empleado al que pertenece el horario
        dia_semana: Día de la semana (0 = lunes, 6 = domingo)
        hora_inicio: Hora de entrada prevista
        hora_fin: Hora de salida prevista
        descanso_minutos: Minutos de descanso no computables
        tolerancia_minutos: Margen antes de considerar tardanza
        tipo_jornada: Diurna, nocturna o mixta (define el recargo)
        activo: Estado del horario (1 = vigente)
        observaciones: Notas adicionales
    """

    __tablename__ = "horarios"
    __table_args__ = (
        UniqueConstraint("empleado_id", "dia_semana", name="uq_horario_empleado_dia"),
    )

    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    descanso_minutos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tolerancia_minutos: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    tipo_jornada: Mapped[TipoJornada] = mapped_column(
        SQLEnum(TipoJornada, values_callable=valores_sql),
        nullable=False,
        default=TipoJornada.DIURNA.value,
    )
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    observaciones: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="horarios")

    @property
    def minutos_jornada(self) -> int:
        """
        Minutos netos de jornada, descontando el descanso

        Si la hora de fin es anterior o igual a la de inicio se asume un
        turno nocturno que cruza la medianoche (por ejemplo 22:00-06:00).
        """
        if self.hora_inicio is None or self.hora_fin is None:
            return 0
        inicio = self.hora_inicio.hour * 60 + self.hora_inicio.minute
        fin = self.hora_fin.hour * 60 + self.hora_fin.minute
        if fin <= inicio:
            fin += 24 * 60
        return max(0, fin - inicio - int(self.descanso_minutos or 0))

    @property
    def horas_jornada(self) -> float:
        """Horas netas de jornada del día"""
        return round(self.minutos_jornada / 60.0, 2)

    @property
    def dia_nombre(self) -> str:
        """Nombre del día de la semana"""
        return nombre_dia(self.dia_semana)

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["tipo_jornada"] = (
            self.tipo_jornada.value
            if hasattr(self.tipo_jornada, "value")
            else self.tipo_jornada
        )
        data["dia_nombre"] = self.dia_nombre
        data["minutos_jornada"] = self.minutos_jornada
        data["horas_jornada"] = self.horas_jornada
        data["hora_inicio"] = self.hora_inicio.strftime("%H:%M") if self.hora_inicio else None
        data["hora_fin"] = self.hora_fin.strftime("%H:%M") if self.hora_fin else None
        return data
