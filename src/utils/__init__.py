"""
Utils Module
Utilidades y helpers de la aplicación
"""

from .helpers import (
    get_resource_path, format_date, parse_date, format_currency, parse_currency,
    format_phone_number, validate_cedula, validate_email, calculate_age,
    truncate_text, normalize_string, get_file_extension, is_valid_image_file,
    is_valid_pdf_file, format_file_size, safe_divide, clean_string,
    generate_unique_filename, ensure_directory_exists, get_timestamp, log_message
)
from .validators import (
    ValidationError, Validator, EmpleadoValidator, 
    DocumentoValidator, IncidenciaValidator, PagoValidator
)
from .document_manager import DocumentManager, document_manager
from .pdf_generator import PDFGenerator, pdf_generator
from .backup_manager import BackupManager, backup_manager, get_backup_manager
from .audit_logger import AuditLogger, audit_logger, get_audit_logger, AuditEventType
from .security import (
    SecurityValidator, PermissionChecker, SecurityLogger,
    security_validator, permission_checker, security_logger
)

__all__ = [
    "get_resource_path", "format_date", "parse_date", "format_currency", "parse_currency",
    "format_phone_number", "validate_cedula", "validate_email", "calculate_age",
    "truncate_text", "normalize_string", "get_file_extension", "is_valid_image_file",
    "is_valid_pdf_file", "format_file_size", "safe_divide", "clean_string",
    "generate_unique_filename", "ensure_directory_exists", "get_timestamp", "log_message",
    "ValidationError", "Validator", "EmpleadoValidator",
    "DocumentoValidator", "IncidenciaValidator", "PagoValidator",
    "DocumentManager", "document_manager", "PDFGenerator", "pdf_generator",
    "BackupManager", "backup_manager", "get_backup_manager",
    "AuditLogger", "audit_logger", "get_audit_logger", "AuditEventType",
    "SecurityValidator", "PermissionChecker", "SecurityLogger",
    "security_validator", "permission_checker", "security_logger"
]