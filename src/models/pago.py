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
        if self.periodo_inicio and self.periodo_fin:
            try:
                ini = self.periodo_inicio if isinstance(self.periodo_inicio, date) else self.periodo_inicio.date()
                fin = self.periodo_fin if isinstance(self.periodo_fin, date) else self.periodo_fin.date()
                delta = fin - ini
                return max(0, delta.days + 1)
            except Exception:
                return 0
        return 0
    
    @property
    def salario_diario(self):
        """Calcula el salario diario"""
        if self.dias_trabajados > 0 and self.salario_base:
            try:
                return round(float(self.salario_base) / 30.0, 2)
            except Exception:
                return 0.0
        return 0.0
    
    @property
    def total_deducciones(self):
        """Calcula el total de deducciones"""
        return round(
            float(self.deduccion_seguro or 0) +
            float(self.deduccion_pension or 0) +
            float(self.deduccion_impuesto or 0) +
            float(self.otras_deducciones or 0) +
            float(self.descuentos or 0),
            2
        )
    
    @property
    def total_ingresos(self):
        """Calcula el total de ingresos"""
        return round(
            float(self.salario_base or 0) +
            float(self.bonificaciones or 0) +
            float(self.horas_extra or 0),
            2
        )
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['dias_trabajados'] = self.dias_trabajados
        data['salario_diario'] = self.salario_diario
        data['total_deducciones'] = self.total_deducciones
        data['total_ingresos'] = self.total_ingresos
        return data