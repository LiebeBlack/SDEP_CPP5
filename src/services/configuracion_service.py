"""
Configuración Service
Servicio de lógica de negocio para configuración

Este servicio gestiona la configuración del sistema, permitiendo
almacenar y recuperar parámetros configurables por categoría.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from src.models import Configuracion
from src.repositories import ConfiguracionRepository


class ConfiguracionService:
    """
    Servicio de gestión de configuración
    
    Administra los parámetros configurables del sistema organizados
    por categorías (general, nómina, recursos_humanos), permitiendo
    su recuperación y actualización de forma tipada.
    """
    
    def __init__(self, session: Session):
        """
        Inicializa el servicio de configuración
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.repository = ConfiguracionRepository(session)
    
    def crear_configuracion(self, datos: Dict) -> Configuracion:
        """Crea una nueva configuración"""
        # Verificar que la clave no exista
        if self.repository.get_by_clave(datos["clave"]):
            raise ValueError("Ya existe una configuración con esta clave")
        
        configuracion = Configuracion(
            clave=datos["clave"],
            valor=datos.get("valor"),
            descripcion=datos.get("descripcion"),
            tipo_dato=datos.get("tipo_dato", "string"),
            categoria=datos.get("categoria"),
            editable=datos.get("editable", 1)
        )
        
        valor_to_set = datos.get("valor")
        if valor_to_set is not None:
            configuracion.set_valor(valor_to_set)
        return self.repository.create(configuracion)
    
    def actualizar_configuracion(self, configuracion_id: int, datos: Dict) -> Configuracion:
        """Actualiza una configuración existente"""
        configuracion = self.repository.get_by_id(configuracion_id)
        if not configuracion:
            raise ValueError("Configuración no encontrada")
        
        # Si se actualiza la clave, verificar que no exista
        if "clave" in datos and datos["clave"] != configuracion.clave:
            if self.repository.get_by_clave(datos["clave"]):
                raise ValueError("Ya existe una configuración con esta clave")
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(configuracion, campo):
                if campo == "valor":
                    if valor is not None:
                        configuracion.set_valor(valor)
                else:
                    setattr(configuracion, campo, valor)
        
        return self.repository.update(configuracion)
    
    def eliminar_configuracion(self, configuracion_id: int) -> bool:
        """Elimina una configuración"""
        return self.repository.delete(configuracion_id)
    
    def obtener_configuracion(self, configuracion_id: int) -> Optional[Configuracion]:
        """Obtiene una configuración por ID"""
        return self.repository.get_by_id(configuracion_id)
    
    def obtener_por_clave(self, clave: str) -> Optional[Configuracion]:
        """Obtiene una configuración por clave"""
        return self.repository.get_by_clave(clave)
    
    def obtener_valor(self, clave: str, default=None):
        """Obtiene el valor de una configuración"""
        return self.repository.get_valor(clave, default)
    
    def establecer_valor(self, clave: str, valor: Union[str, int, float, bool]) -> bool:
        """Establece el valor de una configuración"""
        return self.repository.set_valor(clave, valor)
    
    def listar_por_categoria(self, categoria: str) -> List[Configuracion]:
        """Lista configuraciones por categoría"""
        return self.repository.get_by_categoria(categoria)
    
    def listar_editables(self) -> List[Configuracion]:
        """Lista configuraciones editables"""
        return self.repository.get_editables()
    
    def obtener_todas_dict(self) -> Dict:
        """Obtiene todas las configuraciones como diccionario"""
        return self.repository.get_configuraciones_dict()
    
    def obtener_categoria_dict(self, categoria: str) -> Dict:
        """Obtiene configuraciones de una categoría como diccionario"""
        return self.repository.get_configuraciones_categoria(categoria)
    
    def obtener_configuracion_general(self) -> Dict:
        """Obtiene configuraciones generales de la institución"""
        return self.obtener_categoria_dict("general")
    
    def obtener_configuracion_nomina(self) -> Dict:
        """Obtiene configuraciones de nómina"""
        return self.obtener_categoria_dict("nomina")
    
    def obtener_configuracion_recursos_humanos(self) -> Dict:
        """Obtiene configuraciones de recursos humanos"""
        return self.obtener_categoria_dict("recursos_humanos")
    
    def validar_datos_configuracion(self, datos: Dict) -> List[str]:
        """Valida los datos de una configuración"""
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["clave", "tipo_dato"]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "tipo_dato" in datos:
            tipos_validos = ["string", "int", "float", "bool"]
            if datos["tipo_dato"] not in tipos_validos:
                errores.append(f"El tipo de dato debe ser uno de: {', '.join(tipos_validos)}")
        
        return errores