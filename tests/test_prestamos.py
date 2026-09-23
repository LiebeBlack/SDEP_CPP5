"""
Pruebas del dominio de anticipos y préstamos

Verifican el ciclo completo (solicitud, aprobación o rechazo, descuento
por cuotas y cierre), el tope de descuento sobre el salario y la
protección del neto del empleado al aplicar la cuota en la nómina.
"""

from datetime import date

import pytest

from src.models import EstadoPrestamo, TipoPrestamo
from src.services.empleado_service import EmpleadoService
from src.services.prestamo_service import PrestamoService


@pytest.fixture()
def empleado(session):
    return EmpleadoService(session).crear_empleado(
        {
            "nombres": "Andrés",
            "apellidos": "Núñez",
            "cedula": "22334455",
            "tipo_empleado": "mantenimiento",
            "cargo": "Conserje",
            "departamento": "Servicios generales",
            "fecha_contratacion": date(2022, 5, 1),
            "salario_base": 1000.0,
        }
    )


@pytest.fixture()
def servicio(session):
    return PrestamoService(session)


def _solicitud(empleado_id, **cambios):
    datos = {
        "empleado_id": empleado_id,
        "tipo": TipoPrestamo.PRESTAMO.value,
        "monto": 600.0,
        "numero_cuotas": 6,
        "motivo": "Reparación de vivienda",
    }
    datos.update(cambios)
    return datos


def test_solicitar_prestamo_queda_pendiente(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    assert prestamo.id is not None
    assert prestamo.estado_valor == EstadoPrestamo.SOLICITADO.value
    assert float(prestamo.saldo) == pytest.approx(600.0)
    assert float(prestamo.monto_cuota) == pytest.approx(100.0)
    assert int(prestamo.cuotas_pagadas) == 0
    assert float(prestamo.porcentaje_pagado) == pytest.approx(0.0)
    assert not prestamo.esta_activo


def test_el_anticipo_es_de_una_sola_cuota(servicio, empleado):
    prestamo = servicio.solicitar(
        _solicitud(empleado.id, tipo=TipoPrestamo.ANTICIPO.value, numero_cuotas=5)
    )
    assert int(prestamo.numero_cuotas) == 1
    assert float(prestamo.monto_cuota) == pytest.approx(600.0)


def test_validacion_del_tope_de_descuento(servicio, empleado):
    # Cuota de 600 sobre un salario de 1000 supera el 30% permitido
    errores = servicio.validar_datos_prestamo(
        _solicitud(empleado.id, monto=600.0, numero_cuotas=1)
    )
    assert any("supera" in error for error in errores)

    assert servicio.validar_datos_prestamo(_solicitud(empleado.id)) == []


def test_validacion_de_datos_incompletos(servicio):
    assert servicio.validar_datos_prestamo({}) != []
    assert servicio.validar_datos_prestamo(
        {"empleado_id": 9999, "monto": 100, "numero_cuotas": 2}
    ) != []


def test_solicitar_con_datos_invalidos_lanza_error(servicio, empleado):
    with pytest.raises(ValueError):
        servicio.solicitar(_solicitud(empleado.id, monto=0))
    with pytest.raises(ValueError):
        servicio.solicitar({**_solicitud(empleado.id), "empleado_id": 9999})


def test_aprobar_deja_el_prestamo_listo_para_descontar(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    aprobado = servicio.aprobar(prestamo.id, aprobado_por="admin")
    assert aprobado.estado_valor == EstadoPrestamo.ACTIVO.value
    assert aprobado.fecha_aprobacion is not None
    assert aprobado.aprobado_por == "admin"
    assert aprobado.esta_activo
    assert aprobado.se_puede_descontar

    pendiente = servicio.cuota_pendiente(empleado.id)
    assert pendiente is not None
    assert pendiente[0].id == prestamo.id
    assert float(pendiente[1]) == pytest.approx(100.0)


def test_no_se_aprueba_dos_veces(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    servicio.aprobar(prestamo.id, aprobado_por="admin")
    with pytest.raises(ValueError):
        servicio.aprobar(prestamo.id, aprobado_por="admin")


def test_rechazar_cierra_la_solicitud(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    rechazado = servicio.rechazar(prestamo.id, motivo="Sin disponibilidad")
    assert rechazado.estado_valor == EstadoPrestamo.CANCELADO.value
    assert rechazado.observaciones == "Sin disponibilidad"
    assert servicio.cuota_pendiente(empleado.id) is None


def test_plan_de_pagos_cuadra_con_el_monto(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    plan = servicio.plan_de_pagos(prestamo.id)
    assert len(plan) == 6
    assert sum(cuota["monto"] for cuota in plan) == pytest.approx(600.0)
    assert plan[-1]["saldo"] == pytest.approx(0.0)


def test_descuentos_amortizan_el_saldo_hasta_cerrarlo(session, servicio, empleado):
    prestamo = servicio.solicitar(
        _solicitud(empleado.id, monto=300.0, numero_cuotas=3)
    )
    servicio.aprobar(prestamo.id, aprobado_por="admin")

    for _ in range(3):
        assert servicio.registrar_descuento(prestamo.id, 100.0, date(2026, 1, 28))
        session.expire_all()

    actualizado = servicio.obtener_prestamo(prestamo.id)
    assert float(actualizado.saldo) == pytest.approx(0.0)
    assert int(actualizado.cuotas_pagadas) == 3
    assert actualizado.estado_valor == EstadoPrestamo.PAGADO.value
    assert servicio.saldo_total(empleado.id) == pytest.approx(0.0)
    assert servicio.cuota_pendiente(empleado.id) is None


def test_descuento_para_pago_respeta_el_tope_sobre_el_neto(servicio, empleado):
    prestamo = servicio.solicitar(
        _solicitud(empleado.id, monto=270.0, numero_cuotas=3)
    )
    servicio.aprobar(prestamo.id, aprobado_por="admin")

    encontrado, monto = servicio.descuento_para_pago(empleado.id, neto_estimado=1000.0)
    assert encontrado is not None
    assert float(monto) <= 300.0  # 30% del neto
    assert float(monto) > 0


def test_monto_maximo_otorgable_por_salario(servicio, empleado):
    assert servicio.monto_maximo(empleado.id, 2) == pytest.approx(600.0)
    assert servicio.saldo_total(empleado.id) == pytest.approx(0.0)


def test_listados_por_estado(session, servicio, empleado):
    pendiente = servicio.solicitar(_solicitud(empleado.id))
    assert len(servicio.listar_pendientes_aprobacion()) == 1

    servicio.aprobar(pendiente.id, aprobado_por="admin")
    assert servicio.listar_pendientes_aprobacion() == []
    activos = servicio.listar_activos()
    assert [item.id for item in activos] == [pendiente.id]

    otro_empleado = EmpleadoService(session).crear_empleado(
        {
            "nombres": "Rosa",
            "apellidos": "Ibarra",
            "cedula": "66778899",
            "tipo_empleado": "docente",
            "cargo": "Docente de Arte",
            "departamento": "Artes",
            "fecha_contratacion": date(2024, 1, 15),
            "salario_base": 1400.0,
        }
    )
    otro = servicio.solicitar(_solicitud(otro_empleado.id, monto=120.0, numero_cuotas=2))
    servicio.rechazar(otro.id, motivo="Duplicado")
    assert len(servicio.listar_por_estado(EstadoPrestamo.CANCELADO.value)) == 1
    assert len(servicio.listar_por_empleado(otro_empleado.id)) == 1
    assert len(servicio.listar_prestamos()) == 2


def test_sincronizar_estados_actualiza_el_estado_vigente(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    servicio.aprobar(prestamo.id, aprobado_por="admin")
    cambios = servicio.sincronizar_estados()
    assert cambios >= 0
    assert servicio.obtener_prestamo(prestamo.id).estado_valor in (
        EstadoPrestamo.APROBADO.value,
        EstadoPrestamo.ACTIVO.value,
    )


def test_estadisticas_de_la_cartera(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    servicio.aprobar(prestamo.id, aprobado_por="admin")
    estadisticas = servicio.obtener_estadisticas()
    assert estadisticas["total"] == 1
    assert estadisticas["activos"] == 1
    assert estadisticas["saldo_pendiente"] == pytest.approx(600.0)


def test_actualizar_prestamo_permite_reprogramar(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    actualizado = servicio.actualizar_prestamo(
        prestamo.id, {"numero_cuotas": 4, "observaciones": "Reprogramado"}
    )
    assert int(actualizado.numero_cuotas) == 4
    assert float(actualizado.monto_cuota) == pytest.approx(150.0)
    assert actualizado.observaciones == "Reprogramado"


def test_cancelar_un_prestamo_activo(servicio, empleado):
    prestamo = servicio.solicitar(_solicitud(empleado.id))
    servicio.aprobar(prestamo.id, aprobado_por="admin")
    cancelado = servicio.cancelar(prestamo.id, motivo="Pagado por otra vía")
    assert cancelado.estado_valor == EstadoPrestamo.CANCELADO.value
    assert not cancelado.esta_activo
