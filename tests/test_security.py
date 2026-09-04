"""Pruebas del módulo de seguridad (security.py)"""

import pytest

from src.utils.security import (
    SecurityValidator,
    PermissionChecker,
    SecurityLogger,
)


class TestSecurityValidator:
    def test_validate_pattern_email_ok(self):
        assert SecurityValidator.validate_pattern("ana@example.com", "email")

    def test_validate_pattern_email_mal(self):
        assert not SecurityValidator.validate_pattern("ana@", "email")

    def test_validate_pattern_numeric(self):
        assert SecurityValidator.validate_pattern("12345", "numeric")
        assert not SecurityValidator.validate_pattern("12a45", "numeric")

    def test_validate_pattern_desconocido(self):
        assert not SecurityValidator.validate_pattern("x", "no_existe")

    def test_validate_pattern_no_string(self):
        assert not SecurityValidator.validate_pattern(123, "numeric")

    def test_sanitize_string_elimina_peligrosos(self):
        assert SecurityValidator.sanitize_string("<b>'x'</b>") == "bx/b"

    def test_sanitize_string_trunca(self):
        assert len(SecurityValidator.sanitize_string("a" * 2000, 50)) == 50

    def test_sanitize_string_none(self):
        assert SecurityValidator.sanitize_string(None) == ""

    def test_sanitize_string_no_str(self):
        assert SecurityValidator.sanitize_string(42) == "42"

    def test_validate_email_vacio_ok(self):
        assert SecurityValidator.validate_email("")

    def test_validate_email_invalido(self):
        assert not SecurityValidator.validate_email("correo@")

    def test_validate_phone_ok(self):
        assert SecurityValidator.validate_phone("0412-123-4567")

    def test_validate_phone_vacio_ok(self):
        assert SecurityValidator.validate_phone("")

    def test_validate_cedula_ok(self):
        assert SecurityValidator.validate_cedula("12-345-678")

    def test_validate_cedula_vacia(self):
        assert not SecurityValidator.validate_cedula("")

    def test_validate_filename_ok(self):
        assert SecurityValidator.validate_filename("planilla_2026.pdf")

    def test_validate_filename_inseguro(self):
        assert not SecurityValidator.validate_filename("planilla<>.pdf")

    def test_validate_file_extension_ok(self):
        assert SecurityValidator.validate_file_extension(
            "foto.JPG", SecurityValidator.ALLOWED_IMAGE_EXTENSIONS)

    def test_validate_file_extension_no(self):
        assert not SecurityValidator.validate_file_extension(
            "doc.pdf", SecurityValidator.ALLOWED_IMAGE_EXTENSIONS)

    def test_validate_file_extension_vacio(self):
        assert not SecurityValidator.validate_file_extension(
            "", SecurityValidator.ALLOWED_IMAGE_EXTENSIONS)

    def test_validate_file_size_ok(self):
        assert SecurityValidator.validate_file_size(1024)

    def test_validate_file_size_cero(self):
        assert not SecurityValidator.validate_file_size(0)

    def test_validate_file_size_excede(self):
        assert not SecurityValidator.validate_file_size(60 * 1024 * 1024)

    def test_validate_numeric_range_ok(self):
        assert SecurityValidator.validate_numeric_range(5, 1, 10)

    def test_validate_numeric_range_fuera(self):
        assert not SecurityValidator.validate_numeric_range(15, 1, 10)

    def test_validate_numeric_range_invalido(self):
        assert not SecurityValidator.validate_numeric_range("abc")

    def test_sanitize_sql_input_elimina_comillas(self):
        assert "'" not in SecurityValidator.sanitize_sql_input("o'hara")

    def test_sanitize_sql_input_elimina_palabras(self):
        assert "DROP" not in SecurityValidator.sanitize_sql_input("DROP TABLE x")

    def test_sanitize_sql_input_none(self):
        assert SecurityValidator.sanitize_sql_input(None) == ""

    def test_sanitize_sql_input_numerico(self):
        assert SecurityValidator.sanitize_sql_input(42) == "42"

    def test_generate_secure_token(self):
        token = SecurityValidator.generate_secure_token(16)
        assert len(token) == 32  # 16 bytes en hex
        assert token != SecurityValidator.generate_secure_token(16)


class TestPassword:
    def test_hash_password_formato(self):
        h = SecurityValidator.hash_password("clave-segura")
        partes = h.split("$")
        assert partes[0] == "pbkdf2"
        assert partes[1] == str(SecurityValidator.PBKDF2_ITERATIONS)
        assert len(partes[2]) == 32  # salt de 16 bytes en hex
        assert len(partes[3]) == 64  # sha256 en hex

    def test_hash_password_unicidad_sal(self):
        h1 = SecurityValidator.hash_password("misma-clave")
        h2 = SecurityValidator.hash_password("misma-clave")
        assert h1 != h2

    def test_verify_password_ok(self):
        h = SecurityValidator.hash_password("clave-segura")
        assert SecurityValidator.verify_password("clave-segura", h)

    def test_verify_password_incorrecta(self):
        h = SecurityValidator.hash_password("clave-segura")
        assert not SecurityValidator.verify_password("otra", h)

    def test_verify_password_hash_legado(self):
        import hashlib
        salt = "salt123"
        valor = hashlib.sha256(("clave" + salt).encode()).hexdigest()
        assert SecurityValidator.verify_password("clave", f"{salt}${valor}")

    def test_verify_password_malformado(self):
        assert not SecurityValidator.verify_password("clave", "sin-formato")

    def test_verify_password_vacio(self):
        assert not SecurityValidator.verify_password("clave", "")


class TestIntegridad:
    def test_validate_data_integrity_ok(self):
        errores = SecurityValidator.validate_data_integrity(
            {"a": "x", "b": 1}, ["a", "b"])
        assert errores == []

    def test_validate_data_integrity_faltante(self):
        errores = SecurityValidator.validate_data_integrity(
            {"a": "x"}, ["a", "b"])
        assert any("b" in e for e in errores)

    def test_validate_data_integrity_vacio(self):
        errores = SecurityValidator.validate_data_integrity(
            {"a": "  "}, ["a"])
        assert any("vacío" in e for e in errores)

    def test_sanitize_input_data_string(self):
        datos = SecurityValidator.sanitize_input_data(
            {"nombre": "<Ana>"}, {"nombre": "string"})
        assert datos["nombre"] == "Ana"

    def test_sanitize_input_data_numeric(self):
        datos = SecurityValidator.sanitize_input_data(
            {"monto": "1500,25"}, {"monto": "numeric"})
        assert datos["monto"] == 1500.25

    def test_sanitize_input_data_email(self):
        datos = SecurityValidator.sanitize_input_data(
            {"correo": "  ANA@EXAMPLE.COM "}, {"correo": "email"})
        assert datos["correo"] == "ana@example.com"

    def test_sanitize_input_data_phone(self):
        datos = SecurityValidator.sanitize_input_data(
            {"tel": "0412-123-45-67"}, {"tel": "phone"})
        assert datos["tel"] == "0412-123-45-67"

    def test_sanitize_input_data_none(self):
        datos = SecurityValidator.sanitize_input_data(
            {"campo": None}, {"campo": "string"})
        assert datos["campo"] is None

    def test_sanitize_input_data_error(self):
        datos = SecurityValidator.sanitize_input_data(
            {"monto": "no-numero"}, {"monto": "numeric"})
        assert datos["monto"] is None


class TestCheckFileSecurity:
    def test_archivo_seguro(self):
        resultado = SecurityValidator.check_file_security(
            "planilla.pdf", 1024, "application/pdf")
        assert resultado["safe"] is True
        assert resultado["errors"] == []

    def test_archivo_nombre_invalido(self):
        resultado = SecurityValidator.check_file_security(
            "planilla<>.pdf", 1024)
        assert resultado["safe"] is False

    def test_archivo_extension_no_permitida(self):
        resultado = SecurityValidator.check_file_security("virus.exe", 1024)
        assert resultado["safe"] is False
        assert any("Extensión" in e for e in resultado["errors"])

    def test_archivo_tamano_excesivo(self):
        resultado = SecurityValidator.check_file_security(
            "doc.pdf", 60 * 1024 * 1024)
        assert resultado["safe"] is False

    def test_mime_inusual_advierte(self):
        resultado = SecurityValidator.check_file_security(
            "doc.pdf", 1024, "application/x-msdownload")
        assert resultado["safe"] is True
        assert len(resultado["warnings"]) == 1


class TestPermissionChecker:
    def test_admin_permisos(self):
        assert PermissionChecker.has_permission("admin", "config")
        assert PermissionChecker.has_permission("admin", "restore")

    def test_manager_permisos(self):
        assert PermissionChecker.has_permission("manager", "create")
        assert not PermissionChecker.has_permission("manager", "config")

    def test_usuario_permisos(self):
        assert PermissionChecker.has_permission("user", "read")
        assert not PermissionChecker.has_permission("user", "delete")

    def test_viewer_permisos(self):
        assert PermissionChecker.has_permission("viewer", "read")
        assert not PermissionChecker.has_permission("viewer", "report")

    def test_rol_desconocido(self):
        assert not PermissionChecker.has_permission("invitado", "read")

    def test_can_access_module(self):
        assert PermissionChecker.can_access_module("admin", "configuracion")
        assert PermissionChecker.can_access_module("user", "empleados")
        assert not PermissionChecker.can_access_module("user", "nomina")
        assert not PermissionChecker.can_access_module("viewer", "incidencias")


class TestSecurityLogger:
    def test_log_event_auth_failure(self, db_config):
        SecurityLogger.log_security_event(
            "auth_failure", {"usuario": "anonimo"}, "WARNING")

    def test_log_event_permission_denied(self, db_config):
        SecurityLogger.log_security_event(
            "permission_denied", {"modulo": "nomina"})

    def test_log_event_sospechoso(self, db_config):
        SecurityLogger.log_security_event(
            "suspicious", {"detalle": "acceso raro"})

    def test_log_event_tipo_desconocido(self, db_config):
        # Tipos no mapeados caen en SECURITY_SUSPICIOUS sin excepción
        SecurityLogger.log_security_event("otro", {})