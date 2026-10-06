"""
Estudiante Model
Modelo de datos para estudiantes

Representa la información personal de un estudiante de la institución y
su nivel educativo actual (Inicial o Secundaria). El grado y la sección
que cursa en un año escolar se registran en la tabla de matrículas.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import Genero, NivelEducativo, valores_sql

if TYPE_CHECKING:
    from .matricula import Matricula
    from .nota_final import NotaFinal


class Estudiante(Base, BaseModel):
    """
    Modelo de estudiante

    Atributos:
        nombres / apellidos: Nombre completo del estudiante
        cedula: Documento de identidad (único cuando existe; en el nivel
            Inicial puede registrarse sin cédula)
        fecha_nacimiento: Fecha de nacimiento
        genero: Género del estudiante
        nivel: Nivel educativo actual (Inicial o Secundaria)
        representante: Nombre del representante legal
        telefono / telefono_representante: Teléfonos de contacto
        email / direccion: Datos de contacto
        observaciones: Notas adicionales
        activo: 1 = activo, 0 = retirado
    """

    __tablename__ = "estudiantes"

    # Datos personales
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    cedula: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    genero: Mapped[Genero | None] = mapped_column(
        SQLEnum(Genero, values_callable=valores_sql), nullable=True
    )
    nivel: Mapped[NivelEducativo] = mapped_column(
        SQLEnum(NivelEducativo, values_callable=valores_sql),
        nullable=False,
        index=True,
    )

    # Datos de contacto
    representante: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefono_representante: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Datos adicionales
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)

    # Relaciones
    matriculas: Mapped[list["Matricula"]] = relationship(
        "Matricula", back_populates="estudiante", cascade="all, delete-orphan"
    )
    notas: Mapped[list["NotaFinal"]] = relationship(
        "NotaFinal", back_populates="estudiante", cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self) -> str:
        """Nombre completo del estudiante"""
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def nivel_valor(self) -> str:
        """Valor string del nivel educativo"""
        return self.nivel.value if hasattr(self.nivel, "value") else str(self.nivel)

    @property
    def edad(self) -> int | None:
        """Edad cumplida del estudiante (None si no hay fecha de nacimiento)"""
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        return (
            hoy.year
            - self.fecha_nacimiento.year
            - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["nivel"] = self.nivel_valor
        genero = self.genero
        data["genero"] = genero.value if genero is not None and hasattr(genero, "value") else genero
        data["nombre_completo"] = self.nombre_completo
        data["edad"] = self.edad
        return data
