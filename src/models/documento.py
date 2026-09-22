"""
Documento Model
Modelo de datos para documentos de empleados
"""

from datetime import date
from sqlalchemy import Integer, String, Text, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, BaseModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .empleado import Empleado


class Documento(Base, BaseModel):
    """Modelo de documento"""

    __tablename__ = "documentos"

    # Relación con empleado
    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )

    # Datos del documento
    tipo_documento: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_emision: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Datos del archivo
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    tamano_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contenido_binario: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Estado y observaciones
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="documentos")

    @property
    def es_valido(self):
        """Verifica si el documento está activo y vigente"""
        if self.activo != 1:
            return False
        if self.fecha_vencimiento:
            try:
                venc = (
                    self.fecha_vencimiento
                    if isinstance(self.fecha_vencimiento, date)
                    else self.fecha_vencimiento.date()
                )
                return date.today() <= venc
            except Exception:
                return True
        return True

    @property
    def dias_vencimiento(self):
        """Días restantes para vencimiento"""
        if self.fecha_vencimiento:
            try:
                venc = (
                    self.fecha_vencimiento
                    if isinstance(self.fecha_vencimiento, date)
                    else self.fecha_vencimiento.date()
                )
                delta = venc - date.today()
                return delta.days
            except Exception:
                return None
        return None

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data["es_valido"] = self.es_valido
        data["dias_vencimiento"] = self.dias_vencimiento
        # No incluir contenido binario en el diccionario
        data.pop("contenido_binario", None)
        return data
