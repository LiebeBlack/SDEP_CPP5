"""
Security Module
Módulo de seguridad con validaciones y sanitización de datos

Este módulo proporciona:
- Validación de datos de entrada
- Sanitización de strings y archivos
- Verificación de permisos
- Protección contra inyección SQL
- Validación de tipos de archivos
- Gestión de contraseñas seguras
"""

import re
import os
import hashlib
import secrets
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validador de seguridad para datos de entrada"""
    
    # Patrones de validación
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\d\s\-\+\(\)]{7,20}$',
        'cedula': r'^[\d\-]{5,20}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'numeric': r'^[\d]+$',
        'safe_string': r'^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚñÑ]+$',
        'filename': r'^[a-zA-Z0-9_\-\.]+$',
    }
    
    # Extensiones de archivos permitidas
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.rtf'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate_pattern(cls, value: str, pattern_name: str) -> bool:
        """
        Valida un string contra un patrón específico
        
        Args:
            value: String a validar
            pattern_name: Nombre del patrón a usar
            
        Returns:
            True si el valor coincide con el patrón
        """
        if not value or not isinstance(value, str):
            return False
            
        pattern = cls.PATTERNS.get(pattern_name)
        if not pattern:
            logger.warning(f"Patrón desconocido: {pattern_name}")
            return False
            
        return bool(re.match(pattern, value.strip()))
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitiza un string para prevenir inyecciones
        
        Args:
            value: String a sanitizar
            max_length: Longitud máxima permitida
            
        Returns:
            String sanitizado
        """
        if not value:
            return ""
            
        if not isinstance(value, str):
            value = str(value)
        
        # Eliminar caracteres peligrosos
        sanitized = re.sub(r'[<>"\']', '', value)
        
        # Truncar si es muy largo
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Valida formato de email"""
        if not email:
            return True  # Email opcional
        return cls.validate_pattern(email, 'email')
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Valida formato de teléfono"""
        if not phone:
            return True  # Teléfono opcional
        return cls.validate_pattern(phone, 'phone')
    
    @classmethod
    def validate_cedula(cls, cedula: str) -> bool:
        """Valida formato de cédula"""
        if not cedula:
            return False
        return cls.validate_pattern(cedula, 'cedula')
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Valida que un nombre de archivo sea seguro"""
        if not filename:
            return False
        return cls.validate_pattern(filename, 'filename')
    
    @classmethod
    def validate_file_extension(cls, filename: str, allowed_extensions: set) -> bool:
        """
        Valida que un archivo tenga una extensión permitida
        
        Args:
            filename: Nombre del archivo
            allowed_extensions: Conjunto de extensiones permitidas
            
        Returns:
            True si la extensión es permitida
        """
        if not filename:
            return False
            
        ext = Path(filename).suffix.lower()
        return ext in allowed_extensions
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size: int = None) -> bool:
        """
        Valida que un archivo no exceda el tamaño máximo
        
        Args:
            file_size: Tamaño del archivo en bytes
            max_size: Tamaño máximo permitido (default: MAX_FILE_SIZE)
            
        Returns:
            True si el tamaño es válido
        """
        max_size = max_size or cls.MAX_FILE_SIZE
        return 0 < file_size <= max_size
    
    @classmethod
    def validate_numeric_range(cls, value: Union[int, float], 
                              min_val: Optional[float] = None, 
                              max_val: Optional[float] = None) -> bool:
        """
        Valida que un número esté en un rango específico
        
        Args:
            value: Valor numérico a validar
            min_val: Valor mínimo permitido
            max_val: Valor máximo permitido
            
        Returns:
            True si el valor está en el rango
        """
        try:
            num_value = float(value)
            
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
                
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def sanitize_sql_input(cls, value: Any) -> str:
        """
        Sanitiza input para prevenir inyección SQL básica
        
        Nota: Esto no reemplaza el uso de parámetros en queries SQL
        """
        if value is None:
            return ""
            
        if isinstance(value, (int, float)):
            return str(value)
            
        if not isinstance(value, str):
            value = str(value)
        
        # Eliminar caracteres SQL peligrosos
        sanitized = re.sub(r"[';\"\\]", '', value)
        sanitized = re.sub(r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """
        Genera un token seguro aleatorio
        
        Args:
            length: Longitud del token
            
        Returns:
            Token seguro en hexadecimal
        """
        return secrets.token_hex(length)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hashea una contraseña de forma segura
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        # Usar SHA-256 con salt (en producción usar bcrypt o argon2)
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            password: Contraseña en texto plano
            password_hash: Hash almacenado
            
        Returns:
            True si la contraseña es correcta
        """
        try:
            salt, hash_value = password_hash.split('$')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return secrets.compare_digest(computed_hash, hash_value)
        except Exception:
            return False
    
    @classmethod
    def validate_data_integrity(cls, data: Dict, required_fields: List[str]) -> List[str]:
        """
        Valida integridad de datos de entrada
        
        Args:
            data: Diccionario de datos a validar
            required_fields: Lista de campos requeridos
            
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Campo requerido faltante: {field}")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Campo requerido vacío: {field}")
        
        return errors
    
    @classmethod
    def sanitize_input_data(cls, data: Dict, field_types: Dict[str, str]) -> Dict:
        """
        Sanitiza datos de entrada según tipos específicos
        
        Args:
            data: Diccionario de datos a sanitizar
            field_types: Diccionario de {campo: tipo} donde tipo puede ser:
                'string', 'numeric', 'email', 'phone', 'safe_string'
                
        Returns:
            Diccionario con datos sanitizados
        """
        sanitized = {}
        
        for field, value in data.items():
            field_type = field_types.get(field, 'string')
            
            if value is None:
                sanitized[field] = None
                continue
            
            try:
                if field_type == 'string':
                    sanitized[field] = cls.sanitize_string(str(value))
                elif field_type == 'numeric':
                    sanitized[field] = float(str(value).replace(',', '.'))
                elif field_type == 'email':
                    sanitized[field] = cls.sanitize_string(str(value)).lower()
                elif field_type == 'phone':
                    sanitized[field] = re.sub(r'[^\d\+\-\(\)]', '', str(value))
                elif field_type == 'safe_string':
                    sanitized[field] = cls.sanitize_string(str(value))
                else:
                    sanitized[field] = cls.sanitize_string(str(value))
            except Exception as e:
                logger.warning(f"Error sanitizando campo {field}: {e}")
                sanitized[field] = None
        
        return sanitized
    
    @classmethod
    def check_file_security(cls, filename: str, file_size: int, 
                          content_type: Optional[str] = None) -> Dict:
        """
        Verifica seguridad de un archivo
        
        Args:
            filename: Nombre del archivo
            file_size: Tamaño del archivo
            content_type: Tipo MIME del archivo (opcional)
            
        Returns:
            Dict con resultados de verificación
        """
        result = {
            'safe': True,
            'errors': [],
            'warnings': []
        }
        
        # Validar nombre de archivo
        if not cls.validate_filename(filename):
            result['safe'] = False
            result['errors'].append("Nombre de archivo inválido")
        
        # Validar extensión
        ext = Path(filename).suffix.lower()
        all_allowed = cls.ALLOWED_IMAGE_EXTENSIONS | cls.ALLOWED_DOCUMENT_EXTENSIONS
        if ext not in all_allowed:
            result['safe'] = False
            result['errors'].append(f"Extensión no permitida: {ext}")
        
        # Validar tamaño
        if not cls.validate_file_size(file_size):
            result['safe'] = False
            result['errors'].append(f"Tamaño de archivo excede el máximo permitido")
        
        # Validar tipo MIME si se proporciona
        if content_type:
            if not content_type.startswith(('image/', 'application/pdf', 'text/')):
                result['warnings'].append(f"Tipo MIME inusual: {content_type}")
        
        return result


class PermissionChecker:
    """Verificador de permisos de usuario"""
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        """
        Verifica si un usuario tiene un permiso específico
        
        Args:
            user_role: Rol del usuario
            required_permission: Permiso requerido
            
        Returns:
            True si tiene el permiso
        """
        # Mapeo de roles a permisos
        role_permissions = {
            'admin': ['create', 'read', 'update', 'delete', 'config', 'backup', 'restore'],
            'manager': ['create', 'read', 'update', 'delete', 'report'],
            'user': ['read', 'update_own'],
            'viewer': ['read']
        }
        
        user_permissions = role_permissions.get(user_role, [])
        return required_permission in user_permissions
    
    @staticmethod
    def can_access_module(user_role: str, module: str) -> bool:
        """
        Verifica si un usuario puede acceder a un módulo específico
        
        Args:
            user_role: Rol del usuario
            module: Nombre del módulo
            
        Returns:
            True si puede acceder
        """
        module_access = {
            'admin': ['empleados', 'documentos', 'incidencias', 'nomina', 'configuracion', 'reportes'],
            'manager': ['empleados', 'documentos', 'incidencias', 'nomina', 'reportes'],
            'user': ['empleados', 'documentos', 'incidencias'],
            'viewer': ['empleados', 'documentos']
        }
        
        allowed_modules = module_access.get(user_role, [])
        return module in allowed_modules


class SecurityLogger:
    """Logger de eventos de seguridad"""
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict, severity: str = "INFO"):
        """
        Registra un evento de seguridad
        
        Args:
            event_type: Tipo de evento
            details: Detalles del evento
            severity: Severidad (INFO, WARNING, ERROR)
        """
        from src.utils.audit_logger import audit_logger, AuditEventType
        
        event_type_map = {
            'auth_failure': AuditEventType.SECURITY_AUTH_FAILURE,
            'permission_denied': AuditEventType.SECURITY_PERMISSION_DENIED,
            'suspicious': AuditEventType.SECURITY_SUSPICIOUS
        }
        
        audit_event = event_type_map.get(event_type, AuditEventType.SECURITY_SUSPICIOUS)
        
        audit_logger.log_event(
            event_type=audit_event,
            entity_type="security",
            details=details,
            success=(severity == "INFO")
        )


# Instancias globales
security_validator = SecurityValidator()
permission_checker = PermissionChecker()
security_logger = SecurityLogger()