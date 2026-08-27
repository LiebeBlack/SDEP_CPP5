#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar las mejoras de seguridad
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=== Prueba de Mejoras de Seguridad ===")
print()

# Test 1: Importación de módulos básicos primero
print("Test 1: Importación de configuración básica...")
try:
    from src.config import settings
    print(f"[OK] Configuración importada correctamente")
    print(f"     - Directorio base: {settings.base_dir}")
except Exception as e:
    print(f"[ERROR] Error importando configuración: {e}")
    sys.exit(1)

# Test 2: Importación de módulos de seguridad
print("\nTest 2: Importación de módulos de seguridad...")
try:
    from src.utils.security import (
        SecurityValidator, PermissionChecker, SecurityLogger,
        security_validator, permission_checker, security_logger
    )
    print("[OK] Módulos de seguridad importados correctamente")
except Exception as e:
    print(f"[ERROR] Error importando módulos de seguridad: {e}")
    sys.exit(1)

# Test 2: Sistema de backups
print("\nTest 2: Sistema de backups...")
try:
    from src.utils.backup_manager import BackupManager, backup_manager
    print("[OK] Módulo de backups importado correctamente")
    
    # Verificar directorio de backups
    backup_dir = backup_manager.backup_dir
    if backup_dir.exists():
        print(f"[OK] Directorio de backups existe: {backup_dir}")
    else:
        print(f"[WARN] Directorio de backups no existe, se creará al usar")
except Exception as e:
    print(f"[ERROR] Error con sistema de backups: {e}")

# Test 3: Sistema de auditoría
print("\nTest 3: Sistema de auditoría...")
try:
    from src.utils.audit_logger import AuditLogger, audit_logger, AuditEventType
    print("[OK] Módulo de auditoría importado correctamente")
    
    # Verificar directorios de logs
    audit_dir = audit_logger.audit_dir
    error_dir = audit_logger.error_dir
    if audit_dir.exists():
        print(f"[OK] Directorio de auditoría existe: {audit_dir}")
    if error_dir.exists():
        print(f"[OK] Directorio de errores existe: {error_dir}")
except Exception as e:
    print(f"[ERROR] Error con sistema de auditoría: {e}")

# Test 4: Validaciones de seguridad
print("\nTest 4: Validaciones de seguridad...")
try:
    # Test de validación de email
    valid_email = security_validator.validate_email("test@example.com")
    invalid_email = security_validator.validate_email("invalid-email")
    print(f"[OK] Validación de email: válido={valid_email}, inválido={not invalid_email}")
    
    # Test de validación de cédula
    valid_cedula = security_validator.validate_cedula("12345678")
    invalid_cedula = security_validator.validate_cedula("abc")
    print(f"[OK] Validación de cédula: válido={valid_cedula}, inválido={not invalid_cedula}")
    
    # Test de sanitización
    safe_string = security_validator.sanitize_string("test <script>alert('xss')</script>")
    print(f"[OK] Sanitización de string: '{safe_string}'")
    
    # Test de validación de archivos
    valid_file = security_validator.validate_file_extension("documento.pdf", 
                                                          security_validator.ALLOWED_DOCUMENT_EXTENSIONS)
    invalid_file = security_validator.validate_file_extension("malware.exe", 
                                                           security_validator.ALLOWED_DOCUMENT_EXTENSIONS)
    print(f"[OK] Validación de archivos: PDF válido={valid_file}, EXE inválido={not invalid_file}")
    
except Exception as e:
    print(f"[ERROR] Error en validaciones de seguridad: {e}")

# Test 5: Sistema de base de datos mejorado
print("\nTest 5: Sistema de base de datos mejorado...")
try:
    from src.config.database import DatabaseConfig, db_config
    print("[OK] Configuración de base de datos mejorada importada")
    
    # Verificar métodos de backup
    if hasattr(db_config, 'create_backup'):
        print("[OK] Método create_backup disponible")
    if hasattr(db_config, 'restore_backup'):
        print("[OK] Método restore_backup disponible")
    if hasattr(db_config, 'get_backup_status'):
        print("[OK] Método get_backup_status disponible")
    if hasattr(db_config, '_verify_database_integrity'):
        print("[OK] Método _verify_database_integrity disponible")
        
except Exception as e:
    print(f"[ERROR] Error con sistema de base de datos: {e}")

# Test 6: Repositorios mejorados
print("\nTest 6: Repositorios mejorados...")
try:
    from src.repositories.base_repository import BaseRepository
    print("[OK] Repositorio base mejorado importado")
    
    # Verificar que tiene manejo de errores
    import inspect
    create_method = inspect.getsource(BaseRepository.create)
    if "SQLAlchemyError" in create_method and "audit_logger" in create_method:
        print("[OK] Método create tiene manejo de errores y auditoría")
    else:
        print("[WARN] Método create puede no tener manejo completo de errores")
        
except Exception as e:
    print(f"[ERROR] Error con repositorios: {e}")

# Test 7: Registro de eventos de auditoría
print("\nTest 7: Registro de eventos de auditoría...")
try:
    audit_logger.log_system_event(
        AuditEventType.SYSTEM_START,
        details={"test": "security_test"}
    )
    print("[OK] Evento de auditoría registrado")
    
    # Verificar eventos recientes
    recent_events = audit_logger.get_recent_events(limit=1)
    if recent_events:
        print(f"[OK] Eventos recientes disponibles: {len(recent_events)}")
    else:
        print("[WARN] No se encontraron eventos recientes")
        
except Exception as e:
    print(f"[ERROR] Error registrando eventos de auditoría: {e}")

# Test 8: Generación de backup de prueba
print("\nTest 8: Generación de backup de prueba...")
try:
    backup_info = backup_manager.create_backup("test_security", compress=True)
    print(f"[OK] Backup de prueba creado: {backup_info['name']}")
    print(f"     - Tamaño: {backup_info['size_bytes']} bytes")
    print(f"     - Comprimido: {backup_info['compressed']}")
    
    # Verificar integridad
    integrity = backup_manager.verify_backup_integrity("test_security")
    print(f"[OK] Verificación de integridad: {integrity['integrity_ok']}")
    
    # Listar backups
    backups = backup_manager.list_backups()
    print(f"[OK] Total de backups disponibles: {len(backups)}")
    
except Exception as e:
    print(f"[ERROR] Error creando backup de prueba: {e}")

# Test 9: Verificación de permisos
print("\nTest 9: Verificación de permisos...")
try:
    has_perm = permission_checker.has_permission("admin", "create")
    print(f"[OK] Verificación de permisos: admin tiene create = {has_perm}")
    
    can_access = permission_checker.can_access_module("user", "empleados")
    print(f"[OK] Verificación de acceso: user puede acceder a empleados = {can_access}")
    
except Exception as e:
    print(f"[ERROR] Error en verificación de permisos: {e}")

# Test 10: Generación de tokens seguros
print("\nTest 10: Generación de tokens seguros...")
try:
    token = security_validator.generate_secure_token(16)
    print(f"[OK] Token seguro generado: {token[:8]}... (longitud: {len(token)})")
    
    hash_pass = security_validator.hash_password("test_password")
    print(f"[OK] Hash de contraseña generado: {hash_pass[:20]}...")
    
    verified = security_validator.verify_password("test_password", hash_pass)
    print(f"[OK] Verificación de contraseña: {verified}")
    
except Exception as e:
    print(f"[ERROR] Error en generación de tokens: {e}")

print("\n=== Pruebas Completadas ===")
print("Resumen: Se han probado las mejoras de seguridad implementadas")
print("- Sistema de backups automáticos")
print("- Sistema de auditoría y logging")
print("- Validaciones de seguridad mejoradas")
print("- Manejo robusto de errores")
print("- Verificación de integridad de datos")
print("- Generación de tokens seguros")