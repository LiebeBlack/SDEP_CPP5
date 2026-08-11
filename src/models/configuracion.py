"""
Configuracion Model
Modelo de datos para configuración del sistema
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float
from .base import Base, BaseModel


class Configuracion(Base, BaseModel):
    """Modelo de configuración del sistema"""
    
    __tablename__ = "configuraciones"
    
    # Datos de configuración
    clave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    descripcion = Column(Text, nullable=True)
    tipo_dato = Column(String(20), nullable=False, default="string")
    
    # Metadatos
    categoria = Column(String(50), nullable=True, index=True)
    editable = Column(Integer, default=1, nullable=False)
    
    @property
    def valor_typed(self):
        """Retorna el valor con el tipo de dato correcto"""
        if self.valor is None:
            return None
        
        if self.tipo_dato == "int":
            return int(self.valor)
        elif self.tipo_dato == "float":
            return float(self.valor)
        elif self.tipo_dato == "bool":
            return self.valor.lower() in ("true", "1", "yes", "on")
        else:
            return self.valor
    
    def set_valor(self, valor):
        """Establece el valor convirtiéndolo al tipo correcto"""
        if valor is None:
            self.valor = None
        elif self.tipo_dato == "bool":
            self.valor = "true" if valor else "false"
        else:
            self.valor = str(valor)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        data = super().to_dict()
        data['valor_typed'] = self.valor_typed
        return data