"""
Pago Model
Modelo de datos para pagos y nómina
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Float, Numeric
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from .enums import TipoPago, MetodoPago


class Pago(Base, BaseModel):
    """Modelo de pago"""
    
    __tablename__ = "pagos"
    
    # Relación con empleado
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False, index=True)
    
    # Datos del pago
    tipo_pago = Column(String(50), nullable=False, index=True)
    metodo_pago = Column(String(50), nullable=False, default=MetodoPago.TRANSFERENCIA.value)
    
    # Periodo
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    fecha_pago = Column(Date, nullable=False, default=date.today)
    
    # Montos
    monto_bruto = Column(Numeric(10, 2), nullable=False)
    monto_neto = Column(Numeric(10, 2), nullable=False)
    descuentos = Column(Numeric(10, 2), default=0.00)
    bonificaciones = Column(Numeric(10, 2), default=0.00)
    horas_extra = Column(Numeric(10, 2), default=0.00)
    
    # Desglose de pagos
    salario_base = Column(Numeric(10, 2), nullable=False)
    deduccion_seguro = Column(Numeric(10, 2), default=0.00)
    deduccion_pension = Column(Numeric(10, 2), default=0.00)
    deduccion_impuesto = Column(Numeric(10, 2), default=0.00)
    otras_deducciones = Column(Numeric(10, 2), default=0.00)
    
    # Detalles adicionales
    descripcion = Column(Text, nullable=True)
    referencia_pago = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Estado
    pagado = Column(Integer, default=0, nullable=False)
    fecha_registro_pago = Column(Date, nullable=True)
    
    # Relaciones
    empleado = relationship("Empleado", back_populates="pagos")
    
    @property
    def dias_trabajados(self):
        """Calcula los días trabajados en el periodo"""
        delta = self.periodo_fin - self.periodo_inicio
        return delta.days + 1
    
    @property
    def salario_diario(self):
        """Calcula el salario diario"""
        if self.dias_trabajados > 0:
            return float(self.salario_base) / 30.0  # Asumiendo mes de 30 días
        return 0.0
    
    @property
    def total_deducciones(self):
        """Calcula el total de deducciones"""
        return float(self.deduccion_seguro) + float(self.deduccion_pension) + \
               float(self.deduccion_impuesto) + float(self.otras_deducciones)
    
    @property
    def total_ingresos(self):
        """Calcula el total de ingresos"""
        return float(self.salario_base) + float(self.bonificaciones) + float(self.horas_extra)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['dias_trabajados'] = self.dias_trabajados
        data['salario_diario'] = self.salario_diario
        data['total_deducciones'] = self.total_deducciones
        data['total_ingresos'] = self.total_ingresos
        return data