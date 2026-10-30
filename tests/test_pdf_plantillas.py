"""Pruebas de los valores derivados y el catálogo de campos de plantilla.

Cubren lo que el teléfono muestra como «datos que se completarán»: montos en
letras, fechas en palabras, antigüedad y el catálogo que decide si un marcador
`{{campo}}` se sustituye o se imprime tal cual.
"""

import os
from datetime import date
from importlib import import_module

import pytest
from reportlab.platypus import Table

from src.models import TipoEmpleado
from src.services.empleado_service import EmpleadoService
from src.utils.pdf_generator import (
    CAMPOS_PLANTILLA,
    PDFGenerator,
    _antiguedad_legible,
    _fecha_larga,
    campos_desconocidos,
    monto_en_letras,
)

# `src.utils.pdf_generator` es también el nombre de la instancia exportada por el
# paquete, así que el módulo se resuelve por importlib para parchearlo de verdad.
modulo_pdf = import_module("src.utils.pdf_generator")


@pytest.mark.parametrize(
    ("monto", "esperado"),
    [
        (0, "CERO BOLÍVARES CON 00/100"),
        (21, "VEINTIÚN BOLÍVARES CON 00/100"),
        (100, "CIEN BOLÍVARES CON 00/100"),
        (1850, "MIL OCHOCIENTOS CINCUENTA BOLÍVARES CON 00/100"),
        (1015.25, "MIL QUINCE BOLÍVARES CON 25/100"),
        (1_000_000, "UN MILLÓN BOLÍVARES CON 00/100"),
    ],
)
def test_monto_en_letras(monto, esperado):
    assert monto_en_letras(monto) == esperado


def test_monto_en_letras_redondea_los_centimos_del_borde():
    """99,999 se redondea a 100,00 y no debe imprimir «CON 100/100»."""
    assert monto_en_letras(99.999) == "CIEN BOLÍVARES CON 00/100"


def test_monto_en_letras_ignora_valores_invalidos():
    assert monto_en_letras(None) == ""
    assert monto_en_letras(-5) == ""
    assert monto_en_letras("no es un número") == ""


def test_fecha_larga():
    assert _fecha_larga(date(2026, 10, 30)) == "30 de octubre de 2026"
    assert _fecha_larga("2019-06-03") == "3 de junio de 2019"
    assert _fecha_larga("") == ""
    assert _fecha_larga("sin fecha") == "sin fecha"


def test_antiguedad_legible():
    assert _antiguedad_legible(date(2019, 6, 3), date(2026, 10, 30)) == "7 años y 4 meses"
    assert _antiguedad_legible(date(2026, 1, 15), date(2026, 10, 30)) == "9 meses"
    assert _antiguedad_legible(date(2026, 10, 1), date(2026, 10, 30)) == "menos de un mes"
    assert _antiguedad_legible(None) == ""


def test_catalogo_incluye_los_campos_derivados():
    """El aviso de «campos no reconocidos» no debe marcar los campos nuevos."""
    assert campos_desconocidos("{{salario_letras}} {{ciudad}} {{antiguedad}}") == []
    assert campos_desconocidos("{{campo_inventado}}") == ["campo_inventado"]
    assert "salario_letras" in CAMPOS_PLANTILLA
    assert "fecha_emision_larga" in CAMPOS_PLANTILLA


@pytest.fixture()
def empleado_constancia(session):
    """Empleado con datos personales y laborales completos."""
    servicio = EmpleadoService(session)
    return servicio.crear_empleado(
        {
            "nombres": "Ana",
            "apellidos": "Pérez",
            "cedula": "12345678",
            "fecha_nacimiento": date(1990, 4, 12),
            "genero": "femenino",
            "estado_civil": "soltero",
            "nacionalidad": "Venezolana",
            "telefono": "0212-5550000",
            "celular": "0414-5550000",
            "email": "ana.perez@example.com",
            "direccion": "Av. Principal, casa 4",
            "ciudad": "Caracas",
            "estado": "Distrito Capital",
            "tipo_empleado": TipoEmpleado.ADMINISTRATIVO.value,
            "cargo": "Analista",
            "departamento": "Administración",
            "fecha_contratacion": date(2019, 6, 3),
            "salario_base": 1850.0,
        }
    )


PLANTILLA_DERIVADOS = """# Constancia de ingresos

{{institucion}} certifica que **{{nombre_completo}}**, cédula **{{cedula}}**, con
{{edad}} de edad, labora como {{cargo}} desde {{fecha_contratacion}} con una
antigüedad de {{antiguedad}}, devengando **{{salario}}** ({{salario_letras}}).

Se expide en {{ciudad}}, el {{fecha_emision_larga}}."""


def test_generar_constancia_con_campos_derivados(session, empleado_constancia, tmp_path):
    salida = str(tmp_path / "constancia.pdf")
    resultado = PDFGenerator().generate_constancia_plantilla(
        empleado_constancia,
        PLANTILLA_DERIVADOS,
        salida,
        "CONSTANCIA DE INGRESOS",
    )
    assert resultado == salida
    assert os.path.getsize(salida) > 1500
    with open(salida, "rb") as archivo:
        assert archivo.read(5) == b"%PDF-"


class _DocumentoCapturado:
    """Sustituto de ``SimpleDocTemplate`` que guarda la historia sin maquetar.

    Permite comprobar qué se imprime (y qué se omite) sin extraer texto del PDF.
    """

    def __init__(self, *args, **kwargs):
        self.story = []

    def build(self, story):
        self.story = list(story)


def _historia(monkeypatch, empleado, plantilla, titulo):
    capturado = _DocumentoCapturado()
    monkeypatch.setattr(modulo_pdf, "SimpleDocTemplate", lambda *a, **k: capturado)
    modulo_pdf.PDFGenerator().generate_constancia_plantilla(
        empleado, plantilla, "constancia.pdf", titulo
    )
    return capturado.story


def test_titulo_no_se_imprime_dos_veces(monkeypatch, empleado_constancia):
    """La cabecera ya lleva el título: el «#» que abre la plantilla se omite."""
    historia = _historia(
        monkeypatch,
        empleado_constancia,
        PLANTILLA_DERIVADOS,
        "CONSTANCIA DE INGRESOS",
    )
    textos = [p.getPlainText() for p in historia if hasattr(p, "getPlainText")]
    apariciones = sum(1 for texto in textos if "constancia de ingresos" in texto.lower())
    assert apariciones == 1
    # El cuerpo sigue completo: omitir el título no recorta el documento.
    assert any("Analista" in texto for texto in textos)


def test_encabezado_distinto_al_titulo_se_conserva(monkeypatch, empleado_constancia):
    """Si el encabezado no repite el título, es contenido y no se toca."""
    historia = _historia(
        monkeypatch,
        empleado_constancia,
        "# Datos complementarios\n\nTexto del cuerpo.",
        "CONSTANCIA DE TRABAJO",
    )
    textos = [p.getPlainText() for p in historia if hasattr(p, "getPlainText")]
    assert any("Datos complementarios" in texto for texto in textos)


def test_plantilla_con_firma_propia_no_añade_otra(monkeypatch, empleado_constancia):
    historia = _historia(
        monkeypatch,
        empleado_constancia,
        "Cuerpo.\n\nFirma autorizada: ______________",
        "CONSTANCIA DE TRABAJO",
    )
    assert not any(isinstance(bloque, Table) for bloque in historia)


def test_plantilla_sin_firma_añade_el_bloque_institucional(monkeypatch, empleado_constancia):
    historia = _historia(
        monkeypatch,
        empleado_constancia,
        "Cuerpo de la constancia, sin bloque de cierre.",
        "CONSTANCIA DE TRABAJO",
    )
    assert sum(1 for bloque in historia if isinstance(bloque, Table)) == 1


def test_titulo_derivado_del_markdown():
    """Sin título explícito, el nodo usa el primer encabezado de la plantilla."""
    from sync_agent.api_acciones import _titulo_de_markdown

    assert _titulo_de_markdown("# Constancia de ingresos\n\nTexto") == "Constancia de ingresos"
    assert _titulo_de_markdown("## Con antigüedad") == "Con antigüedad"
    assert _titulo_de_markdown("Sin encabezado") == ""
    assert _titulo_de_markdown("") == ""
    assert _titulo_de_markdown("# " + "x" * 200) == "x" * 120


def test_plantilla_vacia_se_rechaza(empleado_constancia, tmp_path):
    with pytest.raises(ValueError):
        PDFGenerator().generate_constancia_plantilla(
            empleado_constancia,
            "   ",
            str(tmp_path / "vacia.pdf"),
        )
