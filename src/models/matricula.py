"""
Matricula Model
Modelo de datos de las matrículas

La matrícula asigna un estudiante a un grado concreto (y, por lo tanto,
a su periodo y sección). Un estudiante puede tener una matrícula por año
escolar; retirarlo la desactiva sin borrar el historial.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel

if TYPE_CHECKING:
    from .estudiante import Estudiante
    from .grado import Grado


class Matricula(Base, BaseModel):
    """
    Modelo de matrícula

    Atributos:
        estudiante_id: Estudiante matriculado
        grado_id: Grado y sección asignados
        fecha_matricula: Fecha en que se matriculó
        activa: 1 = cursa actualmente, 0 = retirado
        observaciones: Notas adicionales
    """

    __tablename__ = "matriculas"
    __table_args__ = (
        UniqueConstraint("estudiante_id", "grado_id", name="uq_matricula_estudiante_grado"),
    )

    estudiante_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("estudiantes.id"), nullable=False, index=True
    )
    grado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grados.id"), nullable=False, index=True
    )
    fecha_matricula: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today
    )
    activa: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    estudiante: Mapped["Estudiante"] = relationship("Estudiante", back_populates="matriculas")
    grado: Mapped["Grado"] = relationship("Grado", back_populates="matriculas")

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con datos de contexto"""
        data = super().to_dict()
        data["estudiante"] = (
            self.estudiante.nombre_completo if self.estudiante is not None else None
        )
        data["grado"] = self.grado.nombre_completo if self.grado is not None else None
        return data
