"""Pruebas de los validadores de datos (validators.py)"""

from datetime import date

import pytest

from src.utils.validators import (
    ValidationError,
    Validator,
    EmpleadoValidator,
    DocumentoValidator,
    IncidenciaValidator,
    PagoValidator,
)


# --- Validator base ---

class TestValidatorBase:
    def test_validate_required_ok(self):
        Validator.validate_required("texto", "campo")

    def test_validate_required_none(self):
        with pytest.raises(ValidationError):
            Validator.validate_required(None, "campo")

    def test_validate_required_vacio(self):
        with pytest.raises(ValidationError):
            Validator.validate_required("   ", "campo")

    def test_validate_type_ok(self):
        Validator.validate_type(42, int, "campo")

    def test_validate_type_error(self):
        with pytest.raises(ValidationError):
            Validator.validate_type("42", int, "campo")

    def test_validate_length_ok(self):
        Validator.validate_length("abc", 1, 5, "campo")

    def test_validate_length_min(self):
        with pytest.raises(ValidationError):
            Validator.validate_length("a", 2, 5, "campo")

    def test_validate_length_max(self):
        with pytest.raises(ValidationError):
            Validator.validate_length("abcdef", 1, 5, "campo")

    def test_validate_range_ok(self):
        Validator.validate_range(5, 0, 10, "campo")

    def test_validate_range_fuera(self):
        with pytest.raises(ValidationError):
            Validator.validate_range(11, 0, 10, "campo")

    def test_validate_positive_ok(self):
        Validator.validate_positive(3.5, "campo")

    def test_validate_positive_cero(self):
        with pytest.raises(ValidationError):
            Validator.validate_positive(0, "campo")


# --- EmpleadoValidator ---

class TestEmpleadoValidator:
    def test_datos_validos(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "Ana", "apellidos": "Pérez", "cedula": "12345678",
            "tipo_empleado": "docente", "cargo": "Profesor",
            "departamento": "Académico", "salario_base": 1500.0,
        })
        assert errores == []

    def test_campos_requeridos_faltantes(self):
        errores = EmpleadoValidator.validate_datos_empleado({})
        assert any("nombres" in e for e in errores)
        assert any("salario_base" in e for e in errores)

    def test_cedula_con_letras(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12ab345",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100,
        })
        assert any("solo números" in e for e in errores)

    def test_cedula_corta(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "123",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100,
        })
        assert any("5 y 20" in e for e in errores)

    def test_salario_no_numerico(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12345678",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": "abc",
        })
        assert any("número válido" in e for e in errores)

    def test_email_invalido(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12345678",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100, "email": "correo-sin-arroba",
        })
        assert any("email" in e for e in errores)

    def test_fecha_nacimiento_futura(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12345678",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100,
            "fecha_nacimiento": "01/01/2100",
        })
        assert any("futura" in e for e in errores)

    def test_fecha_contratacion_futura(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12345678",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100,
            "fecha_contratacion": "01/01/2100",
        })
        assert any("contratación no puede ser futura" in e for e in errores)

    def test_fecha_nacimiento_objeto_date_pasada(self):
        errores = EmpleadoValidator.validate_datos_empleado({
            "nombres": "A", "apellidos": "B", "cedula": "12345678",
            "tipo_empleado": "x", "cargo": "y", "departamento": "z",
            "salario_base": 100,
            "fecha_nacimiento": date(1990, 5, 1),
        })
        assert errores == []


# --- DocumentoValidator ---

class TestDocumentoValidator:
    def test_datos_validos(self):
        errores = DocumentoValidator.validate_datos_documento({
            "empleado_id": 1, "tipo_documento": "titulo", "titulo": "Título",
        })
        assert errores == []

    def test_campos_requeridos(self):
        errores = DocumentoValidator.validate_datos_documento({})
        assert any("empleado_id" in e for e in errores)
        assert any("titulo" in e for e in errores)

    def test_empleado_id_invalido(self):
        errores = DocumentoValidator.validate_datos_documento({
            "empleado_id": "abc", "tipo_documento": "x", "titulo": "T",
        })
        assert any("entero válido" in e for e in errores)

    def test_empleado_id_no_positivo(self):
        errores = DocumentoValidator.validate_datos_documento({
            "empleado_id": 0, "tipo_documento": "x", "titulo": "T",
        })
        assert any("positivo" in e for e in errores)

    def test_archivo_demasiado_grande(self):
        errores = DocumentoValidator.validate_datos_documento({
            "empleado_id": 1, "tipo_documento": "x", "titulo": "T",
            "tamano_bytes": 60 * 1024 * 1024,
        })
        assert any("50MB" in e for e in errores)


# --- IncidenciaValidator ---

class TestIncidenciaValidator:
    def test_datos_validos(self):
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "01/01/2026", "fecha_fin": "03/01/2026",
            "motivo": "Trámite personal",
        })
        assert errores == []

    def test_fecha_fin_anterior_a_inicio(self):
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "05/01/2026", "fecha_fin": "03/01/2026",
            "motivo": "M",
        })
        assert any("anterior a la fecha inicio" in e for e in errores)

    def test_fechas_formato_invalido(self):
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "no-es-fecha", "fecha_fin": "tampoco",
            "motivo": "M",
        })
        assert any("formato válido" in e for e in errores)

    def test_dias_solicitados_negativos(self):
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "01/01/2026", "fecha_fin": "02/01/2026",
            "motivo": "M", "dias_solicitados": -3,
        })
        assert any("mayores a 0" in e for e in errores)

    def test_dias_solicitados_excesivos(self):
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "01/01/2026", "fecha_fin": "02/01/2026",
            "motivo": "M", "dias_solicitados": 400,
        })
        assert any("365" in e for e in errores)

    def test_dias_solicitados_no_entero_no_falla(self):
        # El validador ignora valores no convertibles para días
        errores = IncidenciaValidator.validate_datos_incidencia({
            "empleado_id": 1, "tipo_incidencia": "permiso",
            "fecha_inicio": "01/01/2026", "fecha_fin": "02/01/2026",
            "motivo": "M", "dias_solicitados": "muchos",
        })
        assert not any("días" in e for e in errores)


# --- PagoValidator ---

class TestPagoValidator:
    def test_datos_validos(self):
        errores = PagoValidator.validate_datos_pago({
            "empleado_id": 1, "tipo_pago": "mensual",
            "periodo_inicio": "01/01/2026", "periodo_fin": "31/01/2026",
            "salario_base": 1500.0,
        })
        assert errores == []

    def test_periodo_invertido(self):
        errores = PagoValidator.validate_datos_pago({
            "empleado_id": 1, "tipo_pago": "mensual",
            "periodo_inicio": "31/01/2026", "periodo_fin": "01/01/2026",
            "salario_base": 1500.0,
        })
        assert any("anterior a la fecha inicio" in e for e in errores)

    def test_neto_mayor_que_bruto(self):
        errores = PagoValidator.validate_datos_pago({
            "empleado_id": 1, "tipo_pago": "mensual",
            "periodo_inicio": "01/01/2026", "periodo_fin": "31/01/2026",
            "salario_base": 1500.0,
            "monto_bruto": 1000, "monto_neto": 1200,
        })
        assert any("neto no puede ser mayor" in e for e in errores)

    def test_bruto_neto_validos(self):
        errores = PagoValidator.validate_datos_pago({
            "empleado_id": 1, "tipo_pago": "mensual",
            "periodo_inicio": "01/01/2026", "periodo_fin": "31/01/2026",
            "salario_base": 1500.0,
            "monto_bruto": 1000, "monto_neto": 950,
        })
        assert errores == []