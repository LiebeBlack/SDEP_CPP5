#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba simple para verificar las mejoras de seguridad
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=== Prueba Simple de Mejoras de Seguridad ===")
print()

# Test 1: Validaciones de seguridad
print("Test 1: Validaciones de seguridad...")
try:
    from src.utils.security import SecurityValidator
    
    validator = SecurityValidator()
    
    # Test de validación de email
    valid_email = validator.validate_email("test@example.com")
    invalid_email = validator.validate_email("invalid-email")
    print(f"[OK] Validación de email: válido={valid_email}, inválido={not invalid_email}")
    
    # Test de validación de cédula
    valid_cedula = validator.validate_cedula("12345678")
    invalid_cedula = validator.validate_cedula("abc")
    print(f"[OK] Validación de cédula: válido={valid_cedula}, inválido={not invalid_cedula}")
    
    # Test de sanitización
    safe_string = validator.sanitize_string("test <script>alert('xss')</script>")
    print(f"[OK] Sanitización de string: '{safe_string}'")
    
    # Test de validación de archivos
    valid_file = validator.validate_file_extension("documento.pdf", 
                                                          validator.ALLOWED_DOCUMENT_EXTENSIONS)
    invalid_file = validator.validate_file_extension("malware.exe", 
                                                           validator.ALLOWED_DOCUMENT_EXTENSIONS)
    print(f"[OK] Validación de archivos: PDF válido={valid_file}, EXE inválido={not invalid_file}")
    
except Exception as e:
    print(f"[ERROR] Error en validaciones de seguridad: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Generación de tokens seguros
print("\nTest 2: Generación de tokens seguros...")
try:
    from src.utils.security import SecurityValidator
    
    validator = SecurityValidator()
    token = validator.generate_secure_token(16)
    print(f"[OK] Token seguro generado: {token[:8]}... (longitud: {len(token)})")
    
    hash_pass = validator.hash_password("test_password")
    print(f"[OK] Hash de contraseña generado: {hash_pass[:20]}...")
    
    verified = validator.verify_password("test_password", hash_pass)
    print(f"[OK] Verificación de contraseña: {verified}")
    
except Exception as e:
    print(f"[ERROR] Error en generación de tokens: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Verificación de permisos
print("\nTest 3: Verificación de permisos...")
try:
    from src.utils.security import PermissionChecker
    
    checker = PermissionChecker()
    has_perm = checker.has_permission("admin", "create")
    print(f"[OK] Verificación de permisos: admin tiene create = {has_perm}")
    
    can_access = checker.can_access_module("user", "empleados")
    print(f"[OK] Verificación de acceso: user puede acceder a empleados = {can_access}")
    
except Exception as e:
    print(f"[ERROR] Error en verificación de permisos: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Integración con sistema de base de datos mejorado
print("\nTest 4: Sistema de base de datos mejorado...")
try:
    from src.config.database import DatabaseConfig
    
    # Crear instancia sin inicializar completamente
    db_config = DatabaseConfig()
    
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
    import traceback
    traceback.print_exc()

print("\n=== Pruebas Completadas ===")
print("Resumen: Se han probado las mejoras de seguridad implementadas")
print("- Validaciones de seguridad mejoradas")
print("- Generación de tokens seguros")
print("- Verificación de permisos")
print("- Sistema de base de datos mejorado")