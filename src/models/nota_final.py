"""
Nota Final Model
Modelo de datos de las calificaciones finales

Cada nota final relaciona a un estudiante con el grado que cursó, una
materia y la calificación obtenida. Cuando el periodo académico del grado
se cierra, la nota queda bloqueada: el servicio rechaza cualquier cambio
y un disparador de SQLite impide modificarla incluso por SQL directo.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel

if TYPE_CHECKING:
    from .estudiante import Estudiante
    from .grado import Grado


class NotaFinal(Base, BaseModel):
    """
    Modelo de nota final

    Atributos:
        estudiante_id: Estudiante calificado
        grado_id: Grado (y periodo) en el que se cursó la materia
        materia: Nombre de la materia
        calificacion: Calificación final dentro de la escala configurada
        registrado_por: Usuario que registró la nota (auditoría)
        observaciones: Notas adicionales
    """

    __tablename__ = "notas_finales"
    __table_args__ = (
        UniqueConstraint(
            "estudiante_id", "grado_id", "materia", name="uq_nota_estudiante_grado_materia"
        ),
    )

    estudiante_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("estudiantes.id"), nullable=False, index=True
    )
    grado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grados.id"), nullable=False, index=True
    )
    materia: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    calificacion: Mapped[float] = mapped_column(Float, nullable=False)
    registrado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    estudiante: Mapped["Estudiante"] = relationship("Estudiante", back_populates="notas")
    grado: Mapped["Grado"] = relationship("Grado", back_populates="notas")

    @property
    def periodo_id(self) -> int | None:
        """Periodo académico al que pertenece la nota (vía su grado)"""
        return self.grado.periodo_id if self.grado is not None else None

    @property
    def bloqueada(self) -> bool:
        """Indica si la nota pertenece a un periodo cerrado (inmutable)"""
        return bool(self.grado is not None and self.grado.periodo.esta_cerrado)

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con datos de contexto"""
        data = super().to_dict()
        data["estudiante"] = (
            self.estudiante.nombre_completo if self.estudiante is not None else None
        )
        data["grado"] = self.grado.nombre_completo if self.grado is not None else None
        data["periodo_id"] = self.periodo_id
        data["bloqueada"] = self.bloqueada
        return data
