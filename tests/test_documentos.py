"""Pruebas del servicio de documentos"""

from datetime import date, timedelta

import pytest

from src.services.documento_service import DocumentoService
from src.services.empleado_service import EmpleadoService


@pytest.fixture()
def empleado(session):
    servicio = EmpleadoService(session)
    return servicio.crear_empleado({
        "nombres": "Rosa",
        "apellidos": "Méndez",
        "cedula": "88990011",
        "tipo_empleado": "administrativo",
        "cargo": "Secretaria",
        "departamento": "Administración",
        "fecha_contratacion": date(2021, 6, 1),
        "salario_base": 900.0,
    })


def _datos_documento(empleado_id, **cambios):
    datos = {
        "empleado_id": empleado_id,
        "tipo_documento": "cedula",
        "titulo": "Cédula de identidad",
        "descripcion": "Copia digitalizada",
        "fecha_emision": date(2020, 1, 1),
        "fecha_vencimiento": date.today() + timedelta(days=100),
        "nombre_archivo": "cedula.pdf",
    }
    datos.update(cambios)
    return datos


def test_crear_documento_con_archivo(session, empleado, storage):
    servicio = DocumentoService(session)
    doc = servicio.crear_documento(
        _datos_documento(empleado.id), b"%PDF-1.4 contenido de prueba")
    assert doc.id is not None
    assert doc.ruta_archivo
    assert doc.contenido_binario == b"%PDF-1.4 contenido de prueba"
    assert doc.es_valido


def test_documento_vencido(session, empleado):
    servicio = DocumentoService(session)
    doc = servicio.crear_documento(_datos_documento(
        empleado.id,
        fecha_vencimiento=date.today() - timedelta(days=5),
    ), b"data")
    assert not doc.es_valido
    assert doc.dias_vencimiento < 0


def test_documento_inactivo_no_valido(session, empleado):
    servicio = DocumentoService(session)
    doc = servicio.crear_documento(_datos_documento(empleado.id), b"data")
    servicio.eliminar_documento(doc.id)
    session.expire_all()
    doc = servicio.obtener_documento(doc.id)
    assert doc.activo == 0
    assert not doc.es_valido


def test_listar_vencidos_y_por_vencer(session, empleado):
    servicio = DocumentoService(session)
    servicio.crear_documento(_datos_documento(
        empleado.id,
        tipo_documento="titulo",
        titulo="Título universitario",
        fecha_vencimiento=date.today() + timedelta(days=10),
    ), b"data1")
    servicio.crear_documento(_datos_documento(
        empleado.id,
        tipo_documento="certificado",
        titulo="Certificado vencido",
        fecha_vencimiento=date.today() - timedelta(days=1),
    ), b"data2")

    assert len(servicio.listar_por_vencer(30)) == 1
    assert len(servicio.listar_vencidos()) == 1


def test_actualizar_documento_y_reemplazo_archivo(session, empleado, storage):
    servicio = DocumentoService(session)
    doc = servicio.crear_documento(_datos_documento(empleado.id), b"v1")
    actualizado = servicio.actualizar_documento(
        doc.id, {"titulo": "Cédula actualizada"}, b"v2-nuevo")
    assert actualizado.titulo == "Cédula actualizada"
    assert actualizado.contenido_binario == b"v2-nuevo"


def test_obtener_archivo_desde_disco(session, empleado, storage):
    servicio = DocumentoService(session)
    doc = servicio.crear_documento(_datos_documento(empleado.id), b"bytes-de-archivo")
    contenido = servicio.obtener_archivo(doc.id)
    assert contenido == b"bytes-de-archivo"


def test_validar_campos_requeridos(session, empleado):
    servicio = DocumentoService(session)
    datos = _datos_documento(empleado.id)
    datos["titulo"] = ""
    errores = servicio.validar_datos_documento(datos)
    assert any("titulo" in e.lower() for e in errores)
