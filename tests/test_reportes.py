"""Pruebas de reportes y exportación (PDF, CSV y Excel)"""

import csv
import os
from datetime import date

import pytest

from src.models import TipoEmpleado
from src.services.empleado_service import EmpleadoService
from src.utils.exporter import exportar_archivo, escribir_csv, escribir_xlsx
from src.utils.pdf_generator import PDFGenerator


def _datos_empleado(cedula="99999999-1", **cambios):
    datos = {
        "nombres": "María",
        "apellidos": "Fernández",
        "cedula": cedula,
        "fecha_nacimiento": date(1988, 3, 22),
        "genero": "femenino",
        "estado_civil": "casado",
        "tipo_empleado": TipoEmpleado.ADMINISTRATIVO.value,
        "cargo": "Coordinadora de Recursos Humanos",
        "departamento": "Recursos Humanos",
        "fecha_contratacion": date(2019, 6, 3),
        "salario_base": 1850.0,
        "email": "maria.fernandez@example.com",
        "telefono": "7777-0000",
    }
    datos.update(cambios)
    return datos


@pytest.fixture()
def empleado_completo(session):
    """Empleado con todos los campos opcionales poblados"""
    servicio = EmpleadoService(session)
    datos = _datos_empleado(
        tipo_contratacion="indefinido",
        titulo_secundaria="Bachiller General",
        titulo_obtenido="Licenciatura en Administración",
        institucion_bancaria="Banco Agrícola",
        numero_cuenta="123456789",
        tipo_cuenta="ahorro",
        enfermedades_preexistentes="Asma controlada",
        alergias_medicamentosas="Penicilina",
        hijos="Luis (8 años, cédula pendiente)\nAna (5 años)",
    )
    return servicio.crear_empleado(datos)


# --- Ficha del empleado (PDF) ---

def test_generar_ficha_empleado_pdf(session, empleado_completo, tmp_path):
    salida = str(tmp_path / "ficha.pdf")
    resultado = PDFGenerator().generate_ficha_empleado(empleado_completo, salida)
    assert resultado == salida
    assert os.path.getsize(salida) > 3000
    with open(salida, "rb") as archivo:
        assert archivo.read(5) == b"%PDF-"


def test_generar_ficha_empleado_minima(session, tmp_path):
    """La ficha funciona aunque casi todos los campos opcionales estén vacíos"""
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado(cedula="11111111-1"))
    salida = str(tmp_path / "ficha_minima.pdf")
    PDFGenerator().generate_ficha_empleado(empleado, salida)
    assert os.path.getsize(salida) > 2000


def test_generar_ficha_estado_inactivo(session, tmp_path):
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado(cedula="22222222-1"))
    empleado.activo = 0
    session.commit()
    session.refresh(empleado)
    assert empleado.activo == 0
    salida = str(tmp_path / "ficha_inactivo.pdf")
    PDFGenerator().generate_ficha_empleado(empleado, salida)
    assert os.path.exists(salida)


# --- Planilla de nómina (PDF) ---

def _filas_planilla():
    return [
        {
            "nombre_empleado": "Ana Gómez",
            "cedula": "12345678-1",
            "cargo": "Docente de Matemáticas",
            "salario_base": 1500.0,
            "bonificaciones": 100.0,
            "horas_extra": 50.0,
            "deduccion_seguro": 45.0,
            "deduccion_pension": 108.75,
            "deduccion_impuesto": 60.0,
            "otras_deducciones": 0.0,
            "descuentos": 20.0,
            "monto_neto": 1416.25,
            "periodo_inicio": date(2026, 8, 1),
            "periodo_fin": date(2026, 8, 31),
        },
        {
            "nombre_empleado": "Luis Pérez",
            "cedula": "87654321-2",
            "cargo": "Conserje",
            "salario_base": 700.0,
            "bonificaciones": 0.0,
            "horas_extra": 0.0,
            "deduccion_seguro": 21.0,
            "deduccion_pension": 50.75,
            "deduccion_impuesto": 0.0,
            "otras_deducciones": 0.0,
            "descuentos": 0.0,
            "monto_neto": 628.25,
            "periodo_inicio": date(2026, 8, 1),
            "periodo_fin": date(2026, 8, 31),
        },
    ]


def test_generar_planilla_pdf(session, tmp_path):
    salida = str(tmp_path / "planilla.pdf")
    resultado = PDFGenerator().generate_reporte_nomina(
        _filas_planilla(), salida, titulo_periodo="Periodo: 01/08/2026 a 31/08/2026")
    assert resultado == salida
    assert os.path.getsize(salida) > 1500
    with open(salida, "rb") as archivo:
        assert archivo.read(5) == b"%PDF-"


def test_generar_planilla_sin_pagos_error(session, tmp_path):
    with pytest.raises(ValueError):
        PDFGenerator().generate_reporte_nomina([], str(tmp_path / "vacia.pdf"))


def test_planilla_con_empleado_real(session, empleado_completo, tmp_path):
    """Una fila armada desde un empleado real de la BD genera el PDF"""
    filas = [{
        "nombre_empleado": empleado_completo.nombre_completo,
        "cedula": empleado_completo.cedula,
        "cargo": empleado_completo.cargo,
        "salario_base": float(empleado_completo.salario_base),
        "bonificaciones": 0.0,
        "horas_extra": 0.0,
        "deduccion_seguro": 55.5,
        "deduccion_pension": 134.13,
        "deduccion_impuesto": 0.0,
        "otras_deducciones": 0.0,
        "descuentos": 0.0,
        "monto_neto": 1660.37,
    }]
    salida = str(tmp_path / "planilla_empleado.pdf")
    PDFGenerator().generate_reporte_nomina(filas, salida)
    assert os.path.getsize(salida) > 2000


# --- Exportación CSV / Excel ---

@pytest.fixture()
def filas_exportacion():
    return [
        {"Cédula": "00000000-1", "Nombre": "María José", "Salario Mensual": 1200.5},
        {"Cédula": "00000000-2", "Nombre": "José Gómez", "Salario Mensual": 900.25},
    ]


def test_exportar_csv_utf8(filas_exportacion, tmp_path):
    salida = str(tmp_path / "listado.csv")
    escribir_csv(filas_exportacion, salida)
    with open(salida, encoding="utf-8-sig") as archivo:
        leido = list(csv.reader(archivo, delimiter=";"))
    assert leido[0] == ["Cédula", "Nombre", "Salario Mensual"]
    assert leido[1] == ["00000000-1", "María José", "1200.5"]
    assert leido[2] == ["00000000-2", "José Gómez", "900.25"]


def test_exportar_xlsx(filas_exportacion, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    salida = str(tmp_path / "listado.xlsx")
    escribir_xlsx(filas_exportacion, salida)
    pagina = openpyxl.load_workbook(salida).active
    assert [celda.value for celda in pagina[1]] == ["Cédula", "Nombre", "Salario Mensual"]
    assert pagina["B2"].value == "María José"
    assert pagina["B3"].value == "José Gómez"
    assert pagina["C2"].value == 1200.5
    assert pagina["C2"].number_format == "#,##0.00"


def test_exportar_archivo_despacha_por_extension(filas_exportacion, tmp_path):
    csv_path = str(tmp_path / "a.csv")
    xlsx_path = str(tmp_path / "b.xlsx")
    assert exportar_archivo(filas_exportacion, csv_path) == csv_path
    assert exportar_archivo(filas_exportacion, xlsx_path) == xlsx_path
    assert os.path.exists(csv_path) and os.path.exists(xlsx_path)


def test_exportar_archivo_errores(tmp_path):
    with pytest.raises(ValueError):
        exportar_archivo([], str(tmp_path / "vacio.xlsx"))
    with pytest.raises(ValueError):
        exportar_archivo([{"a": 1}], str(tmp_path / "no_soportado.txt"))


def test_exportar_xlsx_sanea_caracteres_control(tmp_path):
    salida = str(tmp_path / "sucio.xlsx")
    escribir_xlsx([{"Dato": "valor\x01sucio"}], salida)
    openpyxl = pytest.importorskip("openpyxl")
    pagina = openpyxl.load_workbook(salida).active
    assert pagina["A2"].value == "valor sucio"
