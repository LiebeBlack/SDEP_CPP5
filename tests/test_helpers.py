"""Pruebas de las funciones auxiliares (helpers.py)"""

import os
from datetime import date, datetime

from src.utils import helpers


class TestFechas:
    def test_format_date_none(self):
        assert helpers.format_date(None) == ""

    def test_format_date_date(self):
        assert helpers.format_date(date(2026, 1, 5)) == "05/01/2026"

    def test_format_date_datetime(self):
        assert helpers.format_date(datetime(2026, 1, 5, 10, 30)) == "05/01/2026"

    def test_format_date_str(self):
        assert helpers.format_date("05/01/2026") == "05/01/2026"

    def test_format_date_str_invalida(self):
        assert helpers.format_date("no-fecha") == "no-fecha"

    def test_format_date_vacia(self):
        assert helpers.format_date("   ") == ""

    def test_format_date_otro_tipo(self):
        assert helpers.format_date(123) == "123"

    def test_format_date_personalizado(self):
        assert helpers.format_date(date(2026, 1, 5), "%Y-%m-%d") == "2026-01-05"

    def test_parse_date_none(self):
        assert helpers.parse_date(None) is None

    def test_parse_date_dd_mm_yyyy(self):
        assert helpers.parse_date("05/01/2026") == date(2026, 1, 5)

    def test_parse_date_iso(self):
        assert helpers.parse_date("2026-01-05") == date(2026, 1, 5)

    def test_parse_date_guiones(self):
        assert helpers.parse_date("05-01-2026") == date(2026, 1, 5)

    def test_parse_date_puntos(self):
        assert helpers.parse_date("05.01.2026") == date(2026, 1, 5)

    def test_parse_date_datetime(self):
        assert helpers.parse_date(datetime(2026, 1, 5, 8, 0)) == date(2026, 1, 5)

    def test_parse_date_date(self):
        assert helpers.parse_date(date(2026, 1, 5)) == date(2026, 1, 5)

    def test_parse_date_invalida(self):
        assert helpers.parse_date("31/02/2026") is None

    def test_parse_date_vacia(self):
        assert helpers.parse_date("") is None


class TestMoneda:
    def test_format_currency(self):
        assert helpers.format_currency(1234.5) == "$1,234.50"

    def test_format_currency_none(self):
        assert helpers.format_currency(None) == "$0.00"

    def test_format_currency_invalido(self):
        assert helpers.format_currency("abc") == "$0.00"

    def test_format_currency_simbolo(self):
        assert helpers.format_currency(10, "€") == "€10.00"

    def test_parse_currency(self):
        assert helpers.parse_currency("$1,234.50") == 1234.5

    def test_parse_currency_sin_simbolo(self):
        assert helpers.parse_currency("100.5") == 100.5

    def test_parse_currency_invalido(self):
        assert helpers.parse_currency("abc") is None


class TestTelefono:
    def test_format_phone_10(self):
        assert helpers.format_phone_number("0412123456") == "(041) 212-3456"

    def test_format_phone_7(self):
        assert helpers.format_phone_number("1234567") == "123-4567"

    def test_format_phone_vacio(self):
        assert helpers.format_phone_number("") == ""

    def test_format_phone_con_caracteres(self):
        # Limpia símbolos no numéricos antes de formatear
        assert helpers.format_phone_number("(0412) 123-456") == "(041) 212-3456"

    def test_format_phone_longitud_otra(self):
        assert helpers.format_phone_number("123") == "123"


class TestValidaciones:
    def test_validate_cedula_ok(self):
        assert helpers.validate_cedula("12345678")

    def test_validate_cedula_con_guiones(self):
        assert helpers.validate_cedula("12-345-678")

    def test_validate_cedula_corta(self):
        assert not helpers.validate_cedula("123")

    def test_validate_cedula_con_letras(self):
        assert not helpers.validate_cedula("1234abc")

    def test_validate_cedula_vacia(self):
        assert not helpers.validate_cedula("")

    def test_validate_email_ok(self):
        assert helpers.validate_email("ana@example.com")

    def test_validate_email_vacio(self):
        assert helpers.validate_email("")

    def test_validate_email_sin_dominio(self):
        assert not helpers.validate_email("ana@example")

    def test_validate_email_sin_arroba(self):
        assert not helpers.validate_email("ana.example.com")


class TestTexto:
    def test_calculate_age(self):
        assert helpers.calculate_age(date(1990, 1, 1)) == date.today().year - 1990

    def test_calculate_age_cumpleanos_pendiente(self):
        # Nacido ayer => edad 0
        from datetime import timedelta
        assert helpers.calculate_age(date.today() - timedelta(days=1)) == 0

    def test_calculate_age_none(self):
        assert helpers.calculate_age(None) == 0

    def test_truncate_text_corto(self):
        assert helpers.truncate_text("hola", 10) == "hola"

    def test_truncate_text_largo(self):
        assert helpers.truncate_text("abcdefghij", 8) == "abcde..."

    def test_truncate_text_vacio(self):
        assert helpers.truncate_text("") == ""

    def test_normalize_string(self):
        assert helpers.normalize_string("  ana   pérez ") == "ANA PÉREZ"

    def test_normalize_string_vacio(self):
        assert helpers.normalize_string("") == ""

    def test_clean_string(self):
        assert helpers.clean_string("<script>alert('x')</script>") == "scriptalertx/script"

    def test_clean_string_vacio(self):
        assert helpers.clean_string("") == ""


class TestArchivos:
    def test_get_file_extension(self):
        assert helpers.get_file_extension("doc.pdf") == ".pdf"

    def test_get_file_extension_sin_punto(self):
        assert helpers.get_file_extension("doc") == ""

    def test_is_valid_image_file(self):
        assert helpers.is_valid_image_file("foto.png")
        assert not helpers.is_valid_image_file("doc.pdf")

    def test_is_valid_pdf_file(self):
        assert helpers.is_valid_pdf_file("doc.pdf")
        assert not helpers.is_valid_pdf_file("foto.png")

    def test_format_file_size_bytes(self):
        assert helpers.format_file_size(500) == "500.00 B"

    def test_format_file_size_kb(self):
        assert helpers.format_file_size(2048) == "2.00 KB"

    def test_format_file_size_grande(self):
        assert helpers.format_file_size(3 * 1024 * 1024 * 1024) == "3.00 GB"

    def test_generate_unique_filename(self):
        nombre = helpers.generate_unique_filename("doc.pdf")
        assert nombre.endswith(".pdf")
        assert nombre != helpers.generate_unique_filename("doc.pdf")

    def test_ensure_directory_exists(self, tmp_path):
        destino = str(tmp_path / "nuevo" / "sub")
        assert helpers.ensure_directory_exists(destino)
        assert os.path.isdir(destino)

    def test_get_timestamp_formato(self):
        ts = helpers.get_timestamp()
        assert len(ts) == 15  # YYYYMMDD_HHMMSS
        assert "_" in ts


class TestNumeros:
    def test_safe_divide_normal(self):
        assert helpers.safe_divide(10, 2) == 5.0

    def test_safe_divide_cero(self):
        assert helpers.safe_divide(10, 0) == 0.0

    def test_safe_divide_none(self):
        assert helpers.safe_divide(10, None) == 0.0

    def test_safe_divide_tipo_error(self):
        assert helpers.safe_divide("a", "b") == 0.0

    def test_safe_divide_default(self):
        assert helpers.safe_divide(10, 0, 99) == 99


class TestMisc:
    def test_get_resource_path(self):
        assert helpers.get_resource_path("assets/logo.png").endswith("logo.png")

    def test_log_message(self, capsys):
        helpers.log_message("mensaje de prueba", "WARNING")
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out
        assert "mensaje de prueba" in captured.out

    def test_mantener_y_quitar_ventana_al_frente(self):
        class VentanaFake:
            def __init__(self):
                self.atributos = {}
                self.pendientes = []

            def attributes(self, *args):
                if len(args) == 1:
                    return self.atributos.get(args[0])
                self.atributos[args[0]] = args[1]

            def after(self, ms, callback):
                self.pendientes.append((ms, callback))
                return len(self.pendientes)

        ventana = VentanaFake()
        helpers.mantener_ventana_al_frente(ventana)
        assert ventana.atributos.get("-topmost") is True
        assert len(ventana.pendientes) == 1
        # Ejecutar el callback programado (quita el topmost)
        ventana.pendientes[0][1]()
        assert ventana.atributos.get("-topmost") is False