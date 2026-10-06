"""
Grado Model
Modelo de datos de los grados y secciones

Cada grado pertenece a un periodo académico y tiene un nivel, un nombre
(por ejemplo "1er Año") y una sección (por ejemplo "A"). El profesor
asignado es el único docente autorizado a registrar notas de ese grado;
un administrador o gestor puede hacerlo en cualquier grado.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import NivelEducativo, valores_sql

if TYPE_CHECKING:
    from .matricula import Matricula
    from .nota_final import NotaFinal
    from .periodo_academico import PeriodoAcademico
    from .usuario import Usuario


class Grado(Base, BaseModel):
    """
    Modelo de grado o sección

    Atributos:
        periodo_id: Periodo académico al que pertenece el grado
        nivel: Nivel educativo (Inicial o Secundaria)
        nombre: Nombre del grado (ej. "1er Año", "3er Grado")
        seccion: Letra o código de la sección (ej. "A")
        profesor_id: Usuario docente asignado al grado (None = sin asignar)
        observaciones: Notas adicionales
    """

    __tablename__ = "grados"
    __table_args__ = (
        UniqueConstraint("periodo_id", "nombre", "seccion", name="uq_grado_periodo_nombre_seccion"),
    )

    periodo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("periodos_academicos.id"), nullable=False, index=True
    )
    nivel: Mapped[NivelEducativo] = mapped_column(
        SQLEnum(NivelEducativo, values_callable=valores_sql),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    seccion: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    profesor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    periodo: Mapped["PeriodoAcademico"] = relationship("PeriodoAcademico", back_populates="grados")
    profesor: Mapped["Usuario | None"] = relationship("Usuario")
    matriculas: Mapped[list["Matricula"]] = relationship(
        "Matricula", back_populates="grado", cascade="all, delete-orphan"
    )
    notas: Mapped[list["NotaFinal"]] = relationship(
        "NotaFinal", back_populates="grado", cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self) -> str:
        """Grado con su sección (ej. "1er Año A")"""
        return f"{self.nombre} {self.seccion}".strip()

    @property
    def nivel_valor(self) -> str:
        """Valor string del nivel educativo"""
        return self.nivel.value if hasattr(self.nivel, "value") else str(self.nivel)

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["nivel"] = self.nivel_valor
        data["nombre_completo"] = self.nombre_completo
        data["profesor"] = (
            self.profesor.nombre_completo or self.profesor.username
            if self.profesor is not None
            else None
        )
        return data
