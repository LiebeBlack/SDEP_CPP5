"""Pruebas del servicio de pagos y nómina"""

from datetime import date, timedelta

import pytest

from src.services.pago_service import PagoService
from src.services.empleado_service import EmpleadoService
from src.models import Pago, TipoPago, MetodoPago


@pytest.fixture()
def empleado(session):
    servicio = EmpleadoService(session)
    return servicio.crear_empleado({
        "nombres": "Carlos",
        "apellidos": "Ruiz",
        "cedula": "55500112",
        "tipo_empleado": "docente",
        "cargo": "Docente de Física",
        "departamento": "Ciencias",
        "fecha_contratacion": date(2019, 3, 1),
        "salario_base": 2000.0,
    })


def _pago_base(empleado_id, **cambios):
    datos = {
        "empleado_id": empleado_id,
        "tipo_pago": TipoPago.SALARIO_BASE.value,
        "periodo_inicio": date(2026, 1, 1),
        "periodo_fin": date(2026, 1, 31),
        "salario_base": 2000.0,
        "bonificaciones": 100.0,
        "horas_extra": 50.0,
        "descuentos": 0.0,
        "metodo_pago": MetodoPago.TRANSFERENCIA.value,
    }
    datos.update(cambios)
    return datos


def test_crear_pago_con_deducciones(session, empleado):
    servicio = PagoService(session)
    pago = servicio.crear_pago(_pago_base(empleado.id))
    assert pago.monto_bruto == pytest.approx(2150.0)
    # 4.5% seguro + 5% pensión sobre 2000 (base de los porcentajes)
    esperado_seguro = round(2000 * 0.045, 2)
    esperado_pension = round(2000 * 0.05, 2)
    assert pago.deduccion_seguro == pytest.approx(esperado_seguro)
    assert pago.deduccion_pension == pytest.approx(esperado_pension)
    assert pago.monto_neto == pytest.approx(round(2150 - esperado_seguro - esperado_pension, 2))
    assert not pago.pagado


def test_neto_nunca_negativo(session, empleado):
    servicio = PagoService(session)
    pago = servicio.crear_pago(_pago_base(empleado.id, descuentos=100000.0))
    assert pago.monto_neto == pytest.approx(0.0)


def test_validacion_fechas_periodo(session, empleado):
    servicio = PagoService(session)
    errores = servicio.validar_datos_pago(_pago_base(
        empleado.id,
        periodo_inicio=date(2026, 2, 1),
        periodo_fin=date(2026, 1, 1),
    ))
    assert any("fecha fin" in e.lower() for e in errores)


def test_marcar_pagado_y_pendiente(session, empleado):
    servicio = PagoService(session)
    pago = servicio.crear_pago(_pago_base(empleado.id))
    assert servicio.marcar_pagado(pago.id)
    session.expire_all()
    assert servicio.obtener_pago(pago.id).pagado == 1
    assert servicio.marcar_pendiente(pago.id)
    session.expire_all()
    assert servicio.obtener_pago(pago.id).pagado == 0


def test_actualizar_pago_recalcula(session, empleado):
    servicio = PagoService(session)
    pago = servicio.crear_pago(_pago_base(empleado.id))
    actualizado = servicio.actualizar_pago(pago.id, {"bonificaciones": 300.0})
    assert float(actualizado.monto_bruto) == pytest.approx(2300.0)


def test_generar_nomina_empleado(session, empleado):
    servicio = PagoService(session)
    pago = servicio.generar_nominas_empleado(
        empleado.id, date(2026, 2, 1), date(2026, 2, 28))
    # Proporcional al mes comercial de 30 días (28 días hábiles del periodo)
    assert float(pago.salario_base) == pytest.approx(round(2000 / 30 * 28, 2))


def test_generar_nomina_periodo_duplicada(session, empleado):
    servicio = PagoService(session)
    servicio.generar_nominas_empleado(empleado.id, date(2026, 3, 1), date(2026, 3, 31))
    with pytest.raises(ValueError):
        servicio.generar_nominas_empleado(empleado.id, date(2026, 3, 1), date(2026, 3, 31))


def test_estadisticas_y_resumen(session, empleado):
    servicio = PagoService(session)
    servicio.crear_pago(_pago_base(empleado.id))
    stats = servicio.obtener_estadisticas()
    assert stats["total"] == 1
    assert stats["pendientes"] == 1
    resumen = servicio.obtener_resumen_periodo(date(2026, 1, 1), date(2026, 1, 31))
    assert resumen["cantidad_pagos"] == 1
    assert resumen["total_neto"] > 0
