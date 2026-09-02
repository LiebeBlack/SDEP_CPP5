"""
Documento Model
Modelo de datos para documentos de empleados
"""

from datetime import date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from .enums import TipoDocumento


class Documento(Base, BaseModel):
    """Modelo de documento"""
    
    __tablename__ = "documentos"
    
    # Relación con empleado
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False, index=True)
    
    # Datos del documento
    tipo_documento = Column(String(50), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    numero_documento = Column(String(50), nullable=True)
    fecha_emision = Column(Date, nullable=True)
    fecha_vencimiento = Column(Date, nullable=True)
    
    # Datos del archivo
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tamano_bytes = Column(Integer, nullable=True)
    tipo_mime = Column(String(100), nullable=True)
    contenido_binario = Column(LargeBinary, nullable=True)
    
    # Estado y observaciones
    activo = Column(Integer, default=1, nullable=False)
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    empleado = relationship("Empleado", back_populates="documentos")
    
    @property
    def es_valido(self):
        """Verifica si el documento está activo y vigente"""
        if self.activo != 1:
            return False
        if self.fecha_vencimiento:
            try:
                venc = self.fecha_vencimiento if isinstance(self.fecha_vencimiento, date) else self.fecha_vencimiento.date()
                return date.today() <= venc
            except Exception:
                return True
        return True
    
    @property
    def dias_vencimiento(self):
        """Días restantes para vencimiento"""
        if self.fecha_vencimiento:
            try:
                venc = self.fecha_vencimiento if isinstance(self.fecha_vencimiento, date) else self.fecha_vencimiento.date()
                delta = venc - date.today()
                return delta.days
            except Exception:
                return None
        return None
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['es_valido'] = self.es_valido
        data['dias_vencimiento'] = self.dias_vencimiento
        # No incluir contenido binario en el diccionario
        data.pop('contenido_binario', None)
        return data