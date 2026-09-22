"""
Incidencia Model
Modelo de datos para incidencias y permisos
"""

from datetime import date
from sqlalchemy import Integer, String, Text, Date, ForeignKey, Float, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, BaseModel
from .enums import EstadoIncidencia

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .empleado import Empleado


class Incidencia(Base, BaseModel):
    """Modelo de incidencia"""

    __tablename__ = "incidencias"

    # Relación con empleado
    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )

    # Datos de la incidencia
    tipo_incidencia: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EstadoIncidencia.PENDIENTE.value, index=True
    )

    # Fechas
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_solicitud: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    fecha_aprobacion: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Detalles
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    dias_solicitados: Mapped[int] = mapped_column(Integer, nullable=False)
    dias_aprobados: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Documento de soporte
    documento_soporte_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    documento_soporte_ruta: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documento_soporte_binario: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Aprobación
    aprobado_por: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comentarios_aprobacion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Impacto en nómina
    afecta_nominas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    descuento_dias: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Observaciones
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="incidencias")

    @property
    def duracion_dias(self):
        """Calcula la duración en días"""
        if self.fecha_inicio and self.fecha_fin:
            try:
                ini = (
                    self.fecha_inicio
                    if isinstance(self.fecha_inicio, date)
                    else self.fecha_inicio.date()
                )
                fin = self.fecha_fin if isinstance(self.fecha_fin, date) else self.fecha_fin.date()
                delta = fin - ini
                return max(0, delta.days + 1)
            except Exception:
                return self.dias_solicitados or 0
        return self.dias_solicitados or 0

    @property
    def es_vigente(self):
        """Verifica si la incidencia está vigente actualmente"""
        if self.fecha_inicio and self.fecha_fin:
            try:
                hoy = date.today()
                ini = (
                    self.fecha_inicio
                    if isinstance(self.fecha_inicio, date)
                    else self.fecha_inicio.date()
                )
                fin = self.fecha_fin if isinstance(self.fecha_fin, date) else self.fecha_fin.date()
                return ini <= hoy <= fin and self.estado == EstadoIncidencia.APROBADO.value
            except Exception:
                return False
        return False

    @property
    def requiere_aprobacion(self):
        """Verifica si requiere aprobación"""
        return self.estado == EstadoIncidencia.PENDIENTE.value

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data["duracion_dias"] = self.duracion_dias
        data["es_vigente"] = self.es_vigente
        data["requiere_aprobacion"] = self.requiere_aprobacion
        # No incluir contenido binario en el diccionario
        data.pop("documento_soporte_binario", None)
        return data
