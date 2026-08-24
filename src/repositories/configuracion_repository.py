"""
Configuracion Repository
Repositorio para operaciones de datos de configuración
"""

from typing import List, Optional, Any
from sqlalchemy.orm import Session

from src.models import Configuracion
from .base_repository import BaseRepository


class ConfiguracionRepository(BaseRepository[Configuracion]):
    """Repositorio de configuración"""
    
    def __init__(self, session: Session):
        super().__init__(Configuracion, session)
    
    def get_by_clave(self, clave: str) -> Optional[Configuracion]:
        """Obtiene una configuración por clave"""
        return self.session.query(Configuracion).filter(
            Configuracion.clave == clave
        ).first()
    
    def get_by_categoria(self, categoria: str) -> List[Configuracion]:
        """Obtiene configuraciones por categoría"""
        return self.session.query(Configuracion).filter(
            Configuracion.categoria == categoria
        ).all()
    
    def get_editables(self) -> List[Configuracion]:
        """Obtiene configuraciones editables"""
        return self.session.query(Configuracion).filter(
            Configuracion.editable == 1
        ).all()
    
    def set_valor(self, clave: str, valor: Any) -> bool:
        """Establece el valor de una configuración"""
        config = self.get_by_clave(clave)
        if config:
            try:
                config.set_valor(valor)
                self.session.commit()
                return True
            except Exception:
                self.session.rollback()
                return False
        return False
    
    def get_valor(self, clave: str, default=None):
        """Obtiene el valor de una configuración"""
        config = self.get_by_clave(clave)
        if config:
            return config.valor_typed
        return default
    
    def get_valor_typed(self, clave: str, default=None):
        """Obtiene el valor tipado de una configuración"""
        config = self.get_by_clave(clave)
        if config:
            return config.valor_typed
        return default
    
    def get_configuraciones_dict(self) -> dict:
        """Obtiene todas las configuraciones como diccionario"""
        configs = self.get_all()
        return {config.clave: config.valor_typed for config in configs}
    
    def get_configuraciones_categoria(self, categoria: str) -> dict:
        """Obtiene configuraciones de una categoría como diccionario"""
        configs = self.get_by_categoria(categoria)
        return {config.clave: config.valor_typed for config in configs}