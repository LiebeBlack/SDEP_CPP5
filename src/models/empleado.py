"""
Empleado Model
Modelo de datos para empleados

Este modelo representa la información completa de un empleado en el sistema,
incluyendo datos personales, laborales, académicos y de contacto.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from .enums import TipoEmpleado, Genero, EstadoCivil


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
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    cedula = Column(String(20), unique=True, nullable=False, index=True)
    fecha_nacimiento = Column(Date, nullable=True)
    genero = Column(SQLEnum(Genero, values_callable=lambda x: [e.value if hasattr(e, 'value') else str(e) for e in x]), nullable=True)
    estado_civil = Column(SQLEnum(EstadoCivil, values_callable=lambda x: [e.value if hasattr(e, 'value') else str(e) for e in x]), nullable=True)
    nacionalidad = Column(String(50), nullable=True)
    
    # Datos físicos
    peso = Column(Float, nullable=True)
    altura = Column(Float, nullable=True)
    tipo_sangre = Column(String(5), nullable=True)
    foto_ruta = Column(String(255), nullable=True)
    
    # Datos de contacto
    telefono = Column(String(20), nullable=True)
    celular = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    direccion = Column(Text, nullable=True)
    ciudad = Column(String(50), nullable=True)
    estado = Column(String(50), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    
    # Datos laborales
    tipo_empleado = Column(SQLEnum(TipoEmpleado, values_callable=lambda x: [e.value if hasattr(e, 'value') else str(e) for e in x]), nullable=False, index=True)
    cargo = Column(String(100), nullable=False)
    departamento = Column(String(100), nullable=False)
    fecha_contratacion = Column(Date, nullable=False, default=date.today)
    fecha_terminacion = Column(Date, nullable=True)
    salario_base = Column(Float, nullable=False)
    activo = Column(Integer, default=1, nullable=False)
    
    # Datos académicos
    nivel_educativo = Column(String(50), nullable=True)
    especialidad = Column(String(100), nullable=True)
    titulo_obtenido = Column(String(100), nullable=True)
    
    # Datos adicionales
    observaciones = Column(Text, nullable=True)
    contacto_emergencia_nombre = Column(String(100), nullable=True)
    contacto_emergencia_telefono = Column(String(20), nullable=True)
    contacto_emergencia_relacion = Column(String(50), nullable=True)
    
    # Relaciones
    documentos = relationship("Documento", back_populates="empleado", cascade="all, delete-orphan")
    incidencias = relationship("Incidencia", back_populates="empleado", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="empleado", cascade="all, delete-orphan")
    
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
                return today.year - self.fecha_nacimiento.year - (
                    (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
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
                return max(0, end_date.year - self.fecha_contratacion.year - (
                    (end_date.month, end_date.day) < (self.fecha_contratacion.month, self.fecha_contratacion.day)
                ))
            except Exception:
                return 0
        return 0
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['tipo_empleado'] = self.tipo_empleado.value if hasattr(self.tipo_empleado, 'value') else self.tipo_empleado
        data['genero'] = self.genero.value if hasattr(self.genero, 'value') else self.genero
        data['estado_civil'] = self.estado_civil.value if hasattr(self.estado_civil, 'value') else self.estado_civil
        data['nombre_completo'] = self.nombre_completo
        data['edad'] = self.edad
        data['antiguedad_anos'] = self.antiguedad_anos
        return data