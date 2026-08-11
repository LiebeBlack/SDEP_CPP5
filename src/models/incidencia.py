"""
Incidencia Model
Modelo de datos para incidencias y permisos
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Float, LargeBinary
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from .enums import TipoIncidencia, EstadoIncidencia


class Incidencia(Base, BaseModel):
    """Modelo de incidencia"""
    
    __tablename__ = "incidencias"
    
    # Relación con empleado
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False, index=True)
    
    # Datos de la incidencia
    tipo_incidencia = Column(String(50), nullable=False, index=True)
    estado = Column(String(50), nullable=False, default=EstadoIncidencia.PENDIENTE.value, index=True)
    
    # Fechas
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    fecha_solicitud = Column(Date, nullable=False, default=date.today)
    fecha_aprobacion = Column(Date, nullable=True)
    
    # Detalles
    motivo = Column(Text, nullable=False)
    descripcion = Column(Text, nullable=True)
    dias_solicitados = Column(Integer, nullable=False)
    dias_aprobados = Column(Integer, nullable=True)
    
    # Documento de soporte
    documento_soporte_nombre = Column(String(255), nullable=True)
    documento_soporte_ruta = Column(String(500), nullable=True)
    documento_soporte_binario = Column(LargeBinary, nullable=True)
    
    # Aprobación
    aprobado_por = Column(String(100), nullable=True)
    comentarios_aprobacion = Column(Text, nullable=True)
    
    # Impacto en nómina
    afecta_nominas = Column(Integer, default=1, nullable=False)
    descuento_dias = Column(Float, nullable=True)
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    empleado = relationship("Empleado", back_populates="incidencias")
    
    @property
    def duracion_dias(self):
        """Calcula la duración en días"""
        delta = self.fecha_fin - self.fecha_inicio
        return delta.days + 1  # Incluir ambos días
    
    @property
    def es_vigente(self):
        """Verifica si la incidencia está vigente actualmente"""
        hoy = date.today()
        return self.fecha_inicio <= hoy <= self.fecha_fin and self.estado == EstadoIncidencia.APROBADO.value
    
    @property
    def requiere_aprobacion(self):
        """Verifica si requiere aprobación"""
        return self.estado == EstadoIncidencia.PENDIENTE.value
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['duracion_dias'] = self.duracion_dias
        data['es_vigente'] = self.es_vigente
        data['requiere_aprobacion'] = self.requiere_aprobacion
        # No incluir contenido binario en el diccionario
        data.pop('documento_soporte_binario', None)
        return data