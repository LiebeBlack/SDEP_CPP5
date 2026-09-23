"""
Empleado Model
Modelo de datos para empleados

Este modelo representa la información completa de un empleado en el sistema,
incluyendo datos personales, laborales, académicos y de contacto.
"""

from datetime import date
from sqlalchemy import Integer, String, Float, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, BaseModel
from .enums import TipoEmpleado, Genero, EstadoCivil

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .documento import Documento
    from .incidencia import Incidencia
    from .pago import Pago
    from .horario import Horario
    from .asistencia import Asistencia
    from .contrato import Contrato
    from .prestamo import Prestamo


class Empleado(Base, BaseModel):
    """
    Modelo de empleado

    Representa un empleado del sistema con toda su información relevante.
    Incluye datos personales, físicos, de contacto, laborales y académicos.

    Atributos:
        Datos Personales:
            nombres: Nombres del empleado
            apellidos: Apellidos del empleado
            cedula: Cédula de identidad (única)
            fecha_nacimiento: Fecha de nacimiento
            genero: Género del empleado
            estado_civil: Estado civil
            nacionalidad: Nacionalidad

        Datos Físicos:
            peso: Peso en kilogramos
            altura: Altura en centímetros
            tipo_sangre: Tipo de sangre
            foto_ruta: Ruta de la foto de perfil

        Datos de Contacto:
            telefono: Teléfono fijo
            celular: Teléfono móvil
            email: Correo electrónico
            direccion: Dirección completa
            ciudad: Ciudad de residencia
            estado: Estado/provincia
            codigo_postal: Código postal

        Datos Laborales:
            tipo_empleado: Tipo (docente, administrativo, mantenimiento)
            cargo: Cargo que desempeña
            departamento: Departamento de trabajo
            fecha_contratacion: Fecha de inicio laboral
            fecha_terminacion: Fecha de fin laboral (si aplica)
            salario_base: Salario mensual base
            activo: Estado del empleado (1=activo, 0=inactivo)

        Datos Académicos:
            nivel_educativo: Nivel educativo alcanzado
            especialidad: Especialidad profesional
            titulo_obtenido: Título obtenido

        Datos Adicionales:
            observaciones: Notas adicionales
            contacto_emergencia_nombre: Nombre de contacto de emergencia
            contacto_emergencia_telefono: Teléfono de emergencia
            contacto_emergencia_relacion: Relación con el contacto
    """

    __tablename__ = "empleados"

    # Datos personales
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    genero: Mapped[Genero | None] = mapped_column(
        SQLEnum(
            Genero,
            values_callable=lambda x: [e.value if hasattr(e, "value") else str(e) for e in x],
        ),
        nullable=True,
    )
    estado_civil: Mapped[EstadoCivil | None] = mapped_column(
        SQLEnum(
            EstadoCivil,
            values_callable=lambda x: [e.value if hasattr(e, "value") else str(e) for e in x],
        ),
        nullable=True,
    )
    nacionalidad: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Datos físicos
    peso: Mapped[float | None] = mapped_column(Float, nullable=True)
    altura: Mapped[float | None] = mapped_column(Float, nullable=True)
    tipo_sangre: Mapped[str | None] = mapped_column(String(5), nullable=True)
    foto_ruta: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Datos de contacto
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Datos laborales
    tipo_empleado: Mapped[TipoEmpleado] = mapped_column(
        SQLEnum(
            TipoEmpleado,
            values_callable=lambda x: [e.value if hasattr(e, "value") else str(e) for e in x],
        ),
        nullable=False,
        index=True,
    )
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_contratacion: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    fecha_terminacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    salario_base: Mapped[float] = mapped_column(Float, nullable=False)
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Datos académicos
    nivel_educativo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    especialidad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titulo_obtenido: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titulo_secundaria: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Datos bancarios
    institucion_bancaria: Mapped[str | None] = mapped_column(String(100), nullable=True)
    numero_cuenta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo_cuenta: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Datos de salud
    carnet_discapacidad: Mapped[str | None] = mapped_column(String(30), nullable=True)
    enfermedades_preexistentes: Mapped[str | None] = mapped_column(Text, nullable=True)
    alergias_medicamentosas: Mapped[str | None] = mapped_column(Text, nullable=True)
    alergias_alimentarias: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Datos laborales adicionales
    tipo_contratacion: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Datos familiares
    hijos: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Datos adicionales
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    contacto_emergencia_nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contacto_emergencia_telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contacto_emergencia_relacion: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relaciones
    documentos: Mapped[list["Documento"]] = relationship(
        "Documento", back_populates="empleado", cascade="all, delete-orphan"
    )
    incidencias: Mapped[list["Incidencia"]] = relationship(
        "Incidencia", back_populates="empleado", cascade="all, delete-orphan"
    )
    pagos: Mapped[list["Pago"]] = relationship(
        "Pago", back_populates="empleado", cascade="all, delete-orphan"
    )
    horarios: Mapped[list["Horario"]] = relationship(
        "Horario", back_populates="empleado", cascade="all, delete-orphan"
    )
    asistencias: Mapped[list["Asistencia"]] = relationship(
        "Asistencia", back_populates="empleado", cascade="all, delete-orphan"
    )
    contratos: Mapped[list["Contrato"]] = relationship(
        "Contrato", back_populates="empleado", cascade="all, delete-orphan"
    )
    prestamos: Mapped[list["Prestamo"]] = relationship(
        "Prestamo", back_populates="empleado", cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def edad(self):
        """Calcula la edad del empleado"""
        if self.fecha_nacimiento:
            try:
                today = date.today()
                return (
                    today.year
                    - self.fecha_nacimiento.year
                    - (
                        (today.month, today.day)
                        < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                    )
                )
            except Exception:
                return None
        return None

    @property
    def antiguedad_anos(self):
        """Calcula los años de antigüedad"""
        if self.fecha_contratacion:
            try:
                end_date = self.fecha_terminacion or date.today()
                return max(
                    0,
                    end_date.year
                    - self.fecha_contratacion.year
                    - (
                        (end_date.month, end_date.day)
                        < (self.fecha_contratacion.month, self.fecha_contratacion.day)
                    ),
                )
            except Exception:
                return 0
        return 0

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data["tipo_empleado"] = (
            self.tipo_empleado.value if hasattr(self.tipo_empleado, "value") else self.tipo_empleado
        )
        data["genero"] = self.genero.value if hasattr(self.genero, "value") else self.genero
        data["estado_civil"] = (
            self.estado_civil.value if hasattr(self.estado_civil, "value") else self.estado_civil
        )
        data["nombre_completo"] = self.nombre_completo
        data["edad"] = self.edad
        data["antiguedad_anos"] = self.antiguedad_anos
        return data
