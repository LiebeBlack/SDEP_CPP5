"""
Periodo Academico Model
Modelo de datos de los periodos académicos (años escolares)

Cada periodo representa un año escolar (por ejemplo 2025-2026). Mientras
está ABIERTO se pueden registrar y corregir notas; al CERRARLO las notas
de todos sus grados quedan bloqueadas y solo se consultan.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import EstadoPeriodoAcademico, valores_sql

if TYPE_CHECKING:
    from .grado import Grado


class PeriodoAcademico(Base, BaseModel):
    """
    Modelo de periodo académico

    Atributos:
        nombre: Identificación del año escolar (único, ej. "2025-2026")
        fecha_inicio / fecha_fin: Vigencia del año escolar
        estado: ABIERTO (permite registrar notas) o CERRADO (inmutable)
        cerrado_en: Fecha/hora en que se cerró el periodo
        cerrado_por: Usuario que realizó el cierre
        observaciones: Notas adicionales
    """

    __tablename__ = "periodos_academicos"

    nombre: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoPeriodoAcademico] = mapped_column(
        SQLEnum(EstadoPeriodoAcademico, values_callable=valores_sql),
        nullable=False,
        default=EstadoPeriodoAcademico.ABIERTO.value,
        index=True,
    )
    cerrado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cerrado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    grados: Mapped[list["Grado"]] = relationship(
        "Grado", back_populates="periodo", cascade="all, delete-orphan"
    )

    @property
    def estado_valor(self) -> str:
        """Valor string del estado del periodo"""
        return self.estado.value if hasattr(self.estado, "value") else str(self.estado)

    @property
    def esta_cerrado(self) -> bool:
        """Indica si el periodo está cerrado (notas inmutables)"""
        return self.estado_valor == EstadoPeriodoAcademico.CERRADO.value

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["estado"] = self.estado_valor
        data["esta_cerrado"] = self.esta_cerrado
        return data
