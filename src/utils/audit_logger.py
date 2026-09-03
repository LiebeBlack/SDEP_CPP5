"""
Audit Logger
Sistema de auditoría y logging de eventos del sistema

Este módulo proporciona funcionalidades para:
- Registro de auditoría de todas las operaciones críticas
- Logging estructurado con múltiples niveles
- Separación de logs por tipo de evento
- Exportación de logs para análisis
- Alertas sobre eventos sospechosos
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Tipos de eventos de auditoría"""
    # Operaciones de datos
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_READ = "data_read"
    
    # Operaciones de usuario
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_ACCESS = "user_access"
    
    # Operaciones de sistema
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    
    # Operaciones de seguridad
    SECURITY_AUTH_FAILURE = "security_auth_failure"
    SECURITY_PERMISSION_DENIED = "security_permission_denied"
    SECURITY_SUSPICIOUS = "security_suspicious"
    
    # Operaciones de configuración
    CONFIG_CHANGE = "config_change"
    CONFIG_ACCESS = "config_access"


class AuditLogger:
    """Sistema de auditoría y logging"""
    
    def __init__(self):
        """Inicializa el sistema de auditoría"""
        # Importar settings aquí para evitar problemas de inicialización
        from src.config import settings
        
        self.audit_dir = Path(settings.base_dir) / "logs" / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_dir = Path(settings.base_dir) / "logs" / "errors"
        self.error_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar loggers
        self._setup_loggers()
        
        # Registros en memoria para alertas
        self.recent_events = []
        self.max_recent_events = 100

        # Cache de la configuración 'audit_enabled'
        self._audit_enabled = True
        self._audit_cache_ts = None

    def _auditoria_habilitada(self) -> bool:
        """
        Verifica (con caché) si la auditoría está habilitada en la configuración
        """
        import time
        try:
            now = time.monotonic()
            if self._audit_cache_ts is None or now - self._audit_cache_ts > 60:
                self._audit_cache_ts = now
                self._audit_enabled = True
                from src.config import db_config
                from src.models.configuracion import Configuracion
                session = db_config.get_session()
                try:
                    config = session.query(Configuracion).filter(
                        Configuracion.clave == "audit_enabled").first()
                    if config is not None and config.valor is not None:
                        self._audit_enabled = str(config.valor).strip().lower() in (
                            "true", "1", "yes", "on", "si", "verdadero")
                finally:
                    db_config.close_session(session)
        except Exception:
            # Si no se puede consultar, se mantiene el último valor conocido
            pass
        return self._audit_enabled
    
    def _setup_loggers(self):
        """Configura los diferentes loggers"""
        # Logger de auditoría
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.setLevel(logging.INFO)
        
        audit_handler = logging.FileHandler(
            self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        audit_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.audit_logger.addHandler(audit_handler)
        
        # Logger de errores
        self.error_logger = logging.getLogger("errors")
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.FileHandler(
            self.error_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
        # Logger de seguridad
        self.security_logger = logging.getLogger("security")
        self.security_logger.setLevel(logging.WARNING)
        
        security_handler = logging.FileHandler(
            self.audit_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.security_logger.addHandler(security_handler)
    
    def log_event(self, event_type: AuditEventType, 
                  entity_type: str, 
                  entity_id: Optional[int] = None,
                  user: Optional[str] = None,
                  details: Optional[Dict] = None,
                  ip_address: Optional[str] = None,
                  success: bool = True,
                  error_message: Optional[str] = None,
                  force: bool = False):
        """
        Registra un evento de auditoría
        
        Args:
            event_type: Tipo de evento
            entity_type: Tipo de entidad afectada
            entity_id: ID de la entidad (si aplica)
            user: Usuario que realizó la acción
            details: Detalles adicionales del evento
            ip_address: Dirección IP del usuario
            success: Si la operación fue exitosa
            error_message: Mensaje de error si falló
            force: Registrar aunque la auditoría esté deshabilitada
        """
        if not force and not self._auditoria_habilitada():
            return

        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user": user or "system",
            "ip_address": ip_address,
            "success": success,
            "error_message": error_message,
            "details": details or {}
        }
        
        # Determinar nivel de log
        log_level = logging.INFO if success else logging.ERROR
        
        # Registrar en el logger apropiado
        if event_type in [AuditEventType.SECURITY_AUTH_FAILURE, 
                         AuditEventType.SECURITY_PERMISSION_DENIED,
                         AuditEventType.SECURITY_SUSPICIOUS]:
            self.security_logger.log(log_level, json.dumps(event_data, ensure_ascii=False))
        elif not success:
            self.error_logger.log(log_level, json.dumps(event_data, ensure_ascii=False))
        else:
            self.audit_logger.log(log_level, json.dumps(event_data, ensure_ascii=False))
        
        # Guardar en memoria
        self._add_to_recent_events(event_data)
        
        # Verificar patrones sospechosos
        self._check_suspicious_patterns(event_data)
    
    def log_error(self, error: Exception, 
                  context: Optional[Dict] = None,
                  user: Optional[str] = None):
        """
        Registra un error con contexto completo
        
        Args:
            error: Excepción ocurrida
            context: Contexto adicional del error
            user: Usuario afectado
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user": user or "system"
        }
        
        self.error_logger.error(json.dumps(error_data, ensure_ascii=False))
        
        # También registrar como evento de auditoría
        self.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            entity_type="system",
            details={"error": error_data},
            success=False,
            error_message=str(error)
        )
    
    def log_data_operation(self, operation: str, 
                          entity_type: str,
                          entity_id: Optional[int] = None,
                          user: Optional[str] = None,
                          data: Optional[Dict] = None,
                          changes: Optional[Dict] = None):
        """
        Registra operaciones de datos CRUD
        
        Args:
            operation: Tipo de operación (create, update, delete, read)
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            user: Usuario que realizó la operación
            data: Datos involucrados
            changes: Cambios realizados (para updates)
        """
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
            "read": AuditEventType.DATA_READ
        }
        
        event_type = event_type_map.get(operation, AuditEventType.DATA_READ)
        
        details = {
            "operation": operation,
            "data": data or {},
            "changes": changes or {}
        }
        
        self.log_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            details=details
        )
    
    def log_system_event(self, event_type: AuditEventType,
                        details: Optional[Dict] = None):
        """
        Registra eventos del sistema
        
        Args:
            event_type: Tipo de evento de sistema
            details: Detalles del evento
        """
        self.log_event(
            event_type=event_type,
            entity_type="system",
            details=details
        )
    
    def _add_to_recent_events(self, event_data: Dict):
        """Agrega evento a la lista de eventos recientes"""
        self.recent_events.append(event_data)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
    
    def _check_suspicious_patterns(self, event_data: Dict):
        """Verifica patrones de actividad sospechosa"""
        # Verificar múltiples fallos de autenticación
        if event_data["event_type"] == AuditEventType.SECURITY_AUTH_FAILURE.value:
            recent_failures = [
                e for e in self.recent_events 
                if e["event_type"] == AuditEventType.SECURITY_AUTH_FAILURE.value
                and e["user"] == event_data["user"]
            ]
            
            if len(recent_failures) >= 5:
                self.security_logger.warning(
                    f"Múltiples fallos de autenticación para usuario: {event_data['user']}"
                )
        
        # Verificar operaciones masivas
        if event_data["event_type"] == AuditEventType.DATA_DELETE.value:
            recent_deletes = [
                e for e in self.recent_events 
                if e["event_type"] == AuditEventType.DATA_DELETE.value
                and e["user"] == event_data["user"]
            ]
            
            if len(recent_deletes) >= 10:
                self.security_logger.warning(
                    f"Actividad sospechosa: múltiples eliminaciones por usuario: {event_data['user']}"
                )
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """
        Obtiene eventos recientes
        
        Args:
            limit: Número máximo de eventos a retornar
            
        Returns:
            Lista de eventos recientes
        """
        return self.recent_events[-limit:]
    
    def get_events_by_type(self, event_type: AuditEventType, 
                          hours: int = 24) -> List[Dict]:
        """
        Obtiene eventos de un tipo específico
        
        Args:
            event_type: Tipo de evento a buscar
            hours: Número de horas hacia atrás
            
        Returns:
            Lista de eventos del tipo especificado
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        return [
            event for event in self.recent_events
            if event["event_type"] == event_type.value
            and datetime.fromisoformat(event["timestamp"]).timestamp() > cutoff
        ]
    
    def get_user_activity(self, user: str, hours: int = 24) -> List[Dict]:
        """
        Obtiene actividad de un usuario específico
        
        Args:
            user: Usuario a buscar
            hours: Número de horas hacia atrás
            
        Returns:
            Lista de eventos del usuario
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        return [
            event for event in self.recent_events
            if event["user"] == user
            and datetime.fromisoformat(event["timestamp"]).timestamp() > cutoff
        ]
    
    def export_audit_log(self, start_date: str, end_date: str, 
                        output_file: Optional[str] = None) -> str:
        """
        Exporta logs de auditoría a un archivo JSON
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            output_file: Nombre del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo exportado
        """
        import json as _json

        if not output_file:
            output_file = f"audit_export_{start_date}_{end_date}.json"
        
        from src.config import settings
        output_path = Path(settings.base_dir) / "exports" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Recolectar eventos de los archivos diarios dentro del rango
        eventos = []
        try:
            patron = "audit_*.log"
            for archivo in sorted(self.audit_dir.glob(patron)):
                fecha_archivo = archivo.stem.split("_")[-1]  # YYYYMMDD
                if len(fecha_archivo) != 8:
                    continue
                fecha_iso = f"{fecha_archivo[:4]}-{fecha_archivo[4:6]}-{fecha_archivo[6:]}"
                if start_date <= fecha_iso <= end_date:
                    with open(archivo, "r", encoding="utf-8") as f:
                        for linea in f:
                            linea = linea.strip()
                            if not linea:
                                continue
                            # El formato es: fecha - nivel - JSON
                            partes = linea.split(" - ", 2)
                            if len(partes) == 3:
                                try:
                                    eventos.append(_json.loads(partes[2]))
                                except ValueError:
                                    continue
        except Exception as e:
            logger.error(f"Error exportando auditoría: {e}")

        with open(output_path, "w", encoding="utf-8") as f:
            _json.dump(eventos, f, ensure_ascii=False, indent=2)

        logger.info(f"Auditoría exportada: {len(eventos)} eventos → {output_path}")
        return str(output_path)
    
    def get_security_summary(self, hours: int = 24) -> Dict:
        """
        Obtiene un resumen de eventos de seguridad
        
        Args:
            hours: Número de horas hacia atrás
            
        Returns:
            Diccionario con estadísticas de seguridad
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        security_events = [
            event for event in self.recent_events
            if event["event_type"] in [
                AuditEventType.SECURITY_AUTH_FAILURE.value,
                AuditEventType.SECURITY_PERMISSION_DENIED.value,
                AuditEventType.SECURITY_SUSPICIOUS.value
            ]
            and datetime.fromisoformat(event["timestamp"]).timestamp() > cutoff
        ]
        
        return {
            "total_security_events": len(security_events),
            "auth_failures": len([e for e in security_events if e["event_type"] == AuditEventType.SECURITY_AUTH_FAILURE.value]),
            "permission_denied": len([e for e in security_events if e["event_type"] == AuditEventType.SECURITY_PERMISSION_DENIED.value]),
            "suspicious_activities": len([e for e in security_events if e["event_type"] == AuditEventType.SECURITY_SUSPICIOUS.value]),
            "affected_users": list(set([e["user"] for e in security_events if e["user"] != "system"]))
        }


# Instancia global del logger de auditoría
audit_logger = AuditLogger()

def get_audit_logger():
    """Retorna la instancia del logger de auditoría"""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger()
    return audit_logger