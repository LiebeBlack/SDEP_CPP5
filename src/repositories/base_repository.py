"""
Base Repository
Repositorio base con operaciones CRUD comunes

Este repositorio proporciona las operaciones básicas de creación,
lectura, actualización y eliminación (CRUD) que pueden ser
utilizadas por todos los repositorios específicos.
"""

from typing import TypeVar, Type, List, Optional, Generic, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import logging

from src.utils.audit_logger import get_audit_logger

T = TypeVar('T')

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """
    Repositorio base con operaciones CRUD
    
    Proporciona métodos genéricos para operaciones comunes de base de datos
    que pueden ser heredados por repositorios específicos.
    Incluye manejo robusto de errores y auditoría de operaciones.
    """
    
    def __init__(self, model: Type[T], session: Session):
        """
        Inicializa el repositorio base
        
        Args:
            model: Clase del modelo SQLAlchemy
            session: Sesión de base de datos
        """
        self.model = model
        self.session = session
        self._model_name = model.__name__ if hasattr(model, '__name__') else str(model)

    def _log_data_operation(self, operation: str, entity_id: Any = None, data: Any = None, changes: Dict = None, success: bool = True):
        """Helper seguro para registrar auditoría de datos sin lanzar excepciones"""
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_data_operation(
                    operation=operation,
                    entity_type=self._model_name,
                    entity_id=entity_id,
                    data=data,
                    changes=changes,
                    success=success
                )
        except Exception:
            pass

    def _log_audit_error(self, error: Exception, context: Dict = None):
        """Helper seguro para registrar errores en la auditoría sin lanzar excepciones"""
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_error(error, context=context)
        except Exception:
            pass
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Obtiene un registro por ID con manejo de errores
        
        Args:
            id: Identificador del registro
            
        Returns:
            Objeto del modelo o None si no existe
        """
        try:
            result = self.session.query(self.model).filter(self.model.id == id).first()
            if result:
                self._log_data_operation("read", entity_id=id, data={"result": "found"})
            else:
                self._log_data_operation("read", entity_id=id, data={"result": "not_found"}, success=False)
            return result
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al obtener {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "get_by_id", "entity_id": id})
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "get_by_id", "entity_id": id})
            return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Obtiene todos los registros con paginación y manejo de errores
        
        Args:
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros a retornar
            
        Returns:
            Lista de objetos del modelo
        """
        try:
            result = self.session.query(self.model).offset(skip).limit(limit).all()
            self._log_data_operation("read", data={"skip": skip, "limit": limit, "count": len(result)})
            return result
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al obtener {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_all", "skip": skip, "limit": limit})
            return []
        except Exception as e:
            logger.error(f"Error inesperado al obtener {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_all", "skip": skip, "limit": limit})
            return []
    
    def create(self, obj: T) -> T:
        """
        Crea un nuevo registro con manejo robusto de errores y auditoría
        
        Args:
            obj: Objeto del modelo a crear
            
        Returns:
            Objeto creado con ID asignado
            
        Raises:
            IntegrityError: Si viola restricciones de integridad
            SQLAlchemyError: Si ocurre error de base de datos
            Exception: Si ocurre error general
        """
        try:
            self.session.add(obj)
            self.session.commit()
            self.session.refresh(obj)
            
            # Registrar auditoría de creación exitosa
            obj_id = getattr(obj, 'id', None)
            obj_data = obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)
            self._log_data_operation("create", entity_id=obj_id, data=obj_data)
            
            logger.info(f"{self._model_name} creado exitosamente con ID {obj_id}")
            return obj
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error de integridad al crear {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "create", "entity": str(obj)})
            raise ValueError("Error de integridad: el registro viola restricciones únicas") from e
            
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Error operacional al crear {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "create", "entity": str(obj)})
            raise
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al crear {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "create", "entity": str(obj)})
            raise
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al crear {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "create", "entity": str(obj)})
            raise
    
    def update(self, obj: T) -> T:
        """
        Actualiza un registro existente con manejo robusto de errores y auditoría
        
        Args:
            obj: Objeto del modelo con modificaciones
            
        Returns:
            Objeto actualizado
            
        Raises:
            IntegrityError: Si viola restricciones de integridad
            SQLAlchemyError: Si ocurre error de base de datos
            Exception: Si ocurre error general
        """
        try:
            self.session.commit()
            self.session.refresh(obj)
            
            # Registrar auditoría de actualización
            obj_id = getattr(obj, 'id', None)
            new_data = obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)
            self._log_data_operation(
                operation="update",
                entity_id=obj_id,
                data=new_data
            )
            
            logger.info(f"{self._model_name} actualizado exitosamente con ID {obj_id}")
            return obj
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error de integridad al actualizar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "update", "entity_id": getattr(obj, 'id', None)})
            raise ValueError("Error de integridad: la actualización viola restricciones") from e
            
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Error operacional al actualizar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "update", "entity_id": getattr(obj, 'id', None)})
            raise
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al actualizar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "update", "entity_id": getattr(obj, 'id', None)})
            raise
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al actualizar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "update", "entity_id": getattr(obj, 'id', None)})
            raise
    
    def delete(self, id: int) -> bool:
        """
        Elimina un registro por ID con manejo robusto de errores y auditoría
        
        Args:
            id: Identificador del registro a eliminar
            
        Returns:
            True si se eliminó, False si no existía
            
        Raises:
            SQLAlchemyError: Si ocurre error de base de datos
            Exception: Si ocurre error general
        """
        try:
            obj = self.get_by_id(id)
            if not obj:
                logger.warning(f"{self._model_name} con ID {id} no encontrado para eliminación")
                return False
            
            # Guardar datos antes de eliminar para auditoría
            deleted_data = obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)
            
            self.session.delete(obj)
            self.session.commit()
            
            # Registrar auditoría de eliminación
            self._log_data_operation(
                operation="delete",
                entity_id=id,
                data=deleted_data
            )
            
            logger.info(f"{self._model_name} eliminado exitosamente con ID {id}")
            return True
            
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Error operacional al eliminar {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "delete", "entity_id": id})
            raise
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al eliminar {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "delete", "entity_id": id})
            raise
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al eliminar {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "delete", "entity_id": id})
            raise
    
    def _calculate_changes(self, original: Dict, new: Dict) -> Dict:
        """Calcula los cambios entre dos diccionarios"""
        changes = {}
        if not original or not new:
            return changes
        for key, new_value in new.items():
            if key not in original or original[key] != new_value:
                changes[key] = {
                    "old": original.get(key),
                    "new": new_value
                }
        return changes
    
    def count(self) -> int:
        """
        Cuenta el total de registros con manejo de errores
        
        Returns:
            Cantidad total de registros en la tabla
        """
        try:
            return self.session.query(self.model).count()
        except OperationalError as e:
            logger.error(f"Error de base de datos al contar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "count"})
            return 0
        except Exception as e:
            logger.error(f"Error inesperado al contar {self._model_name}: {e}")
            self._log_audit_error(e, context={"operation": "count"})
            return 0
    
    def exists(self, id: int) -> bool:
        """
        Verifica si existe un registro por ID con manejo de errores
        
        Args:
            id: Identificador a verificar
            
        Returns:
            True si existe, False en caso contrario
        """
        try:
            return self.session.query(self.model).filter(self.model.id == id).first() is not None
        except OperationalError as e:
            logger.error(f"Error de base de datos al verificar existencia de {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "exists", "entity_id": id})
            return False
        except Exception as e:
            logger.error(f"Error inesperado al verificar existencia de {self._model_name} ID {id}: {e}")
            self._log_audit_error(e, context={"operation": "exists", "entity_id": id})
            return False
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Obtiene un registro por un campo específico con manejo de errores
        
        Args:
            field_name: Nombre del campo a buscar
            value: Valor a buscar
            
        Returns:
            Objeto del modelo o None si no existe
        """
        try:
            if not hasattr(self.model, field_name):
                logger.warning(f"Campo {field_name} no existe en {self._model_name}")
                return None
                
            result = self.session.query(self.model).filter(
                getattr(self.model, field_name) == value
            ).first()
            
            return result
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al buscar {self._model_name} por {field_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_by_field", "field": field_name, "value": str(value)})
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar {self._model_name} por {field_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_by_field", "field": field_name, "value": str(value)})
            return None
    
    def get_all_by_field(self, field_name: str, value: Any) -> List[T]:
        """
        Obtiene todos los registros por un campo específico con manejo de errores
        
        Args:
            field_name: Nombre del campo a buscar
            value: Valor a buscar
            
        Returns:
            Lista de objetos del modelo
        """
        try:
            if not hasattr(self.model, field_name):
                logger.warning(f"Campo {field_name} no existe en {self._model_name}")
                return []
                
            result = self.session.query(self.model).filter(
                getattr(self.model, field_name) == value
            ).all()
            
            return result
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al buscar {self._model_name} por {field_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_all_by_field", "field": field_name, "value": str(value)})
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar {self._model_name} por {field_name}: {e}")
            self._log_audit_error(e, context={"operation": "get_all_by_field", "field": field_name, "value": str(value)})
            return []
    
    def search(self, filters: dict) -> List[T]:
        """
        Busca registros con filtros múltiples y manejo de errores
        
        Args:
            filters: Diccionario de campos y valores a filtrar
            
        Returns:
            Lista de objetos del modelo
        """
        try:
            query = self.session.query(self.model)
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
                else:
                    logger.warning(f"Campo {field} no existe en {self._model_name}")
            
            return query.all()
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al buscar {self._model_name} con filtros: {e}")
            self._log_audit_error(e, context={"operation": "search", "filters": str(filters)})
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar {self._model_name} con filtros: {e}")
            self._log_audit_error(e, context={"operation": "search", "filters": str(filters)})
            return []
    
    def search_like(self, field_name: str, value: str) -> List[T]:
        """
        Busca registros con coincidencia parcial y manejo de errores
        
        Args:
            field_name: Nombre del campo a buscar
            value: Valor parcial a buscar
            
        Returns:
            Lista de objetos del modelo
        """
        try:
            if not hasattr(self.model, field_name):
                logger.warning(f"Campo {field_name} no existe en {self._model_name}")
                return []
                
            result = self.session.query(self.model).filter(
                getattr(self.model, field_name).like(f"%{value}%")
            ).all()
            
            return result
            
        except OperationalError as e:
            logger.error(f"Error de base de datos al buscar {self._model_name} con LIKE: {e}")
            self._log_audit_error(e, context={"operation": "search_like", "field": field_name, "value": value})
            return []
        except Exception as e:
            logger.error(f"Error inesperado al buscar {self._model_name} con LIKE: {e}")
            self._log_audit_error(e, context={"operation": "search_like", "field": field_name, "value": value})
            return []