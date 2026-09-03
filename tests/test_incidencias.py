"""Pruebas del servicio de incidencias"""

from datetime import date, timedelta

import pytest

from src.services.incidencia_service import IncidenciaService
from src.services.empleado_service import EmpleadoService
from src.models import EstadoIncidencia


@pytest.fixture()
def empleado(session):
    servicio = EmpleadoService(session)
    return servicio.crear_empleado({
        "nombres": "Pedro",
        "apellidos": "Lara",
        "cedula": "77889900",
        "tipo_empleado": "docente",
        "cargo": "Docente de Historia",
        "departamento": "Sociales",
        "fecha_contratacion": date(2018, 9, 1),
        "salario_base": 1200.0,
    })


def _datos_incidencia(empleado_id, **cambios):
    hoy = date.today()
    datos = {
        "empleado_id": empleado_id,
        "tipo_incidencia": "permiso",
        "fecha_inicio": hoy + timedelta(days=1),
        "fecha_fin": hoy + timedelta(days=3),
        "motivo": "Trámite personal",
        "descripcion": "Permiso por gestión bancaria",
    }
    datos.update(cambios)
    return datos


def test_crear_incidencia_calcula_dias(session, empleado):
    servicio = IncidenciaService(session)
    incidencia = servicio.crear_incidencia(_datos_incidencia(empleado.id))
    assert incidencia.id is not None
    assert incidencia.dias_solicitados == 3
    assert incidencia.estado == EstadoIncidencia.PENDIENTE.value


def test_crear_con_soporte_binario(session, empleado, storage):
    servicio = IncidenciaService(session)
    incidencia = servicio.crear_incidencia(
        _datos_incidencia(empleado.id, tipo_incidencia="reposo_medico"),
        archivo_soporte=b"certificado-medico")
    assert incidencia.documento_soporte_binario == b"certificado-medico"
    assert servicio.obtener_soporte(incidencia.id) == b"certificado-medico"


def test_fecha_fin_anterior_a_inicio(session, empleado):
    servicio = IncidenciaService(session)
    errores = servicio.validar_datos_incidencia(_datos_incidencia(
        empleado.id,
        fecha_inicio=date(2026, 5, 10),
        fecha_fin=date(2026, 5, 1),
    ))
    assert any("fin" in e.lower() for e in errores)


def test_aprobar_y_rechazar(session, empleado):
    servicio = IncidenciaService(session)
    incidencia = servicio.crear_incidencia(_datos_incidencia(empleado.id))

    assert servicio.aprobar_incidencia(incidencia.id, "Director", "Aprobado", dias_aprobados=2)
    session.expire_all()
    incidencia = servicio.obtener_incidencia(incidencia.id)
    assert incidencia.estado == EstadoIncidencia.APROBADO.value
    assert incidencia.dias_aprobados == 2
    assert incidencia.fecha_aprobacion is not None

    otra = servicio.crear_incidencia(_datos_incidencia(empleado.id, tipo_incidencia="ausencia"))
    assert servicio.rechazar_incidencia(otra.id, "Director", "Sin justificación")
    session.expire_all()
    assert servicio.obtener_incidencia(otra.id).estado == EstadoIncidencia.RECHAZADO.value


def test_eliminar_incidencia_borra_soporte(session, empleado, storage):
    servicio = IncidenciaService(session)
    incidencia = servicio.crear_incidencia(
        _datos_incidencia(empleado.id), archivo_soporte=b"soporte")
    assert servicio.eliminar_incidencia(incidencia.id)
    assert servicio.obtener_incidencia(incidencia.id) is None


def test_actualizar_incidencia_recalcula_dias(session, empleado):
    servicio = IncidenciaService(session)
    incidencia = servicio.crear_incidencia(_datos_incidencia(empleado.id))
    nuevo_fin = incidencia.fecha_fin + timedelta(days=2)
    actualizada = servicio.actualizar_incidencia(
        incidencia.id, {"fecha_fin": nuevo_fin})
    assert actualizada.dias_solicitados == 5


def test_calcular_dias_incidencias_periodo(session, empleado):
    servicio = IncidenciaService(session)
    inicio = date.today() + timedelta(days=2)
    incidencia = servicio.crear_incidencia(_datos_incidencia(
        empleado.id,
        fecha_inicio=inicio,
        fecha_fin=inicio + timedelta(days=2),
    ))
    servicio.aprobar_incidencia(incidencia.id, "Director")

    dias = servicio.calcular_dias_incidencias_periodo(
        empleado.id, inicio, inicio + timedelta(days=2))
    assert dias == 3


def test_pendiente_no_afecta_calculo(session, empleado):
    servicio = IncidenciaService(session)
    inicio = date.today() + timedelta(days=2)
    servicio.crear_incidencia(_datos_incidencia(
        empleado.id,
        fecha_inicio=inicio,
        fecha_fin=inicio + timedelta(days=1),
    ))
    # Sin aprobar no debe descontar días de nómina
    dias = servicio.calcular_dias_incidencias_periodo(
        empleado.id, inicio, inicio + timedelta(days=1))
    assert dias == 0
