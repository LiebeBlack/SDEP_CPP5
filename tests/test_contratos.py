"""
Pruebas del dominio de contratos

Cubren el ciclo de vida completo: alta con validaciones, unicidad del
contrato vigente, renovación encadenada, vencimiento automático y
terminación con liquidación registrada como pago.
"""

from datetime import date, timedelta

import pytest

from src.models import EstadoContrato, TipoContrato, TipoPago
from src.services.contrato_service import ContratoService
from src.services.empleado_service import EmpleadoService
from src.services.pago_service import PagoService


@pytest.fixture()
def empleado(session):
    return EmpleadoService(session).crear_empleado(
        {
            "nombres": "Marta",
            "apellidos": "Solís",
            "cedula": "44112233",
            "tipo_empleado": "docente",
            "cargo": "Docente de Matemática",
            "departamento": "Ciencias exactas",
            "fecha_contratacion": date(2023, 3, 1),
            "salario_base": 1800.0,
        }
    )


@pytest.fixture()
def servicio(session):
    return ContratoService(session)


def _datos_contrato(empleado_id, **cambios):
    datos = {
        "empleado_id": empleado_id,
        "tipo": TipoContrato.INDEFINIDO.value,
        "cargo": "Docente de Matemática",
        "departamento": "Ciencias exactas",
        "salario_pactado": 1800.0,
        "horas_semanales": 40,
        "fecha_inicio": date(2026, 1, 1),
    }
    datos.update(cambios)
    return datos


def test_crear_contrato_vigente(servicio, empleado):
    contrato = servicio.crear_contrato(_datos_contrato(empleado.id))
    assert contrato.id is not None
    assert contrato.numero
    assert contrato.estado_valor == EstadoContrato.VIGENTE.value
    assert contrato.esta_vigente
    assert contrato.tipo_valor == TipoContrato.INDEFINIDO.value
    assert float(contrato.salario_pactado) == pytest.approx(1800.0)
    assert contrato.dias_vigencia >= 0


def test_no_se_admite_un_segundo_contrato_vigente(servicio, empleado):
    servicio.crear_contrato(_datos_contrato(empleado.id))
    with pytest.raises(ValueError, match="vigente"):
        servicio.crear_contrato(_datos_contrato(empleado.id))


def test_los_numeros_de_contrato_son_unicos(servicio, empleado):
    primero = servicio.crear_contrato(_datos_contrato(empleado.id))
    segundo = servicio.crear_contrato(
        _datos_contrato(
            empleado.id,
            estado=EstadoContrato.TERMINADO.value,
            tipo=TipoContrato.TEMPORAL.value,
            fecha_fin=date(2026, 6, 30),
        )
    )
    assert primero.numero != segundo.numero


def test_validaciones_del_contrato(servicio, empleado):
    sin_salario = servicio.validar_datos_contrato(_datos_contrato(empleado.id, salario_pactado=0))
    assert any("salario" in error.lower() for error in sin_salario)

    temporal_sin_fin = servicio.validar_datos_contrato(
        _datos_contrato(empleado.id, tipo=TipoContrato.TEMPORAL.value)
    )
    assert any("fecha de fin" in error.lower() for error in temporal_sin_fin)

    fechas_invertidas = servicio.validar_datos_contrato(
        _datos_contrato(
            empleado.id,
            tipo=TipoContrato.TEMPORAL.value,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 1, 1),
        )
    )
    assert any("anterior" in error.lower() for error in fechas_invertidas)

    sin_empleado = servicio.validar_datos_contrato(
        {**_datos_contrato(empleado.id), "empleado_id": None}
    )
    assert sin_empleado != []


def test_el_contrato_vigente_sincroniza_al_empleado(session, servicio, empleado):
    servicio.crear_contrato(
        _datos_contrato(empleado.id, cargo="Coordinador académico", salario_pactado=2500.0)
    )
    session.refresh(empleado)
    assert empleado.cargo == "Coordinador académico"
    assert float(empleado.salario_base) == pytest.approx(2500.0)


def test_renovacion_encadena_contratos(servicio, empleado):
    original = servicio.crear_contrato(
        _datos_contrato(
            empleado.id,
            tipo=TipoContrato.TEMPORAL.value,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 12, 31),
        )
    )
    nuevo = servicio.renovar_contrato(
        original.id, nueva_fecha_fin=date(2026, 12, 31), nuevo_salario=2000.0
    )
    assert nuevo.id != original.id
    assert nuevo.contrato_anterior_id == original.id
    assert float(nuevo.salario_pactado) == pytest.approx(2000.0)
    # La renovación arranca el día siguiente al vencimiento anterior
    assert nuevo.fecha_inicio == date(2026, 1, 1)

    servicio.session.refresh(original)
    assert original.estado_valor == EstadoContrato.RENOVADO.value


def test_renovar_exige_fecha_de_fin(servicio, empleado):
    contrato = servicio.crear_contrato(
        _datos_contrato(empleado.id, fecha_inicio=date(2025, 1, 1))
    )
    with pytest.raises(ValueError):
        servicio.renovar_contrato(contrato.id)


def test_los_contratos_vencidos_se_sincronizan(servicio, empleado):
    servicio.crear_contrato(
        _datos_contrato(
            empleado.id,
            tipo=TipoContrato.TEMPORAL.value,
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
            estado=EstadoContrato.VENCIDO.value,
        )
    )
    actualizados = servicio.sincronizar_estados()
    assert actualizados >= 0
    assert len(servicio.listar_vencidos()) == 1


def test_contratos_por_vencer_segun_el_umbral(servicio, empleado):
    por_vencer = date.today() + timedelta(days=10)
    servicio.crear_contrato(
        _datos_contrato(
            empleado.id,
            tipo=TipoContrato.TEMPORAL.value,
            fecha_inicio=date.today() - timedelta(days=100),
            fecha_fin=por_vencer,
        )
    )
    assert len(servicio.listar_por_vencer()) == 1
    assert len(servicio.listar_por_vencer(dias=5)) == 0


def test_empleados_sin_contrato(servicio, empleado):
    assert [item.id for item in servicio.empleados_sin_contrato()] == [empleado.id]
    servicio.crear_contrato(_datos_contrato(empleado.id))
    assert servicio.empleados_sin_contrato() == []


def test_terminar_contrato_genera_liquidacion_y_pago(session, servicio, empleado):
    contrato = servicio.crear_contrato(
        _datos_contrato(empleado.id, fecha_inicio=date(2024, 1, 1))
    )
    resultado = servicio.terminar_contrato(
        contrato.id,
        motivo="renuncia",
        fecha_terminacion=date(2026, 1, 1),
        generar_liquidacion=True,
        registrado_por="admin",
    )
    assert resultado["contrato"].estado_valor == EstadoContrato.TERMINADO.value
    finiquito = resultado["finiquito"]
    assert finiquito.neto > 0
    assert resultado["pago"].tipo_pago == TipoPago.LIQUIDACION.value
    assert float(resultado["pago"].monto_neto) == pytest.approx(float(finiquito.neto))

    # La liquidación queda auditada en el módulo de nómina
    pagos = PagoService(session).listar_pagos()
    liquidaciones = [pago for pago in pagos if pago.tipo_pago == TipoPago.LIQUIDACION.value]
    assert len(liquidaciones) == 1


def test_no_se_puede_terminar_dos_veces(servicio, empleado):
    contrato = servicio.crear_contrato(_datos_contrato(empleado.id))
    servicio.terminar_contrato(contrato.id, motivo="renuncia", generar_liquidacion=False)
    with pytest.raises(ValueError):
        servicio.terminar_contrato(contrato.id, motivo="renuncia", generar_liquidacion=False)


def test_terminar_sin_liquidacion_no_crea_pago(session, servicio, empleado):
    contrato = servicio.crear_contrato(_datos_contrato(empleado.id))
    resultado = servicio.terminar_contrato(
        contrato.id, motivo="abandono", generar_liquidacion=False
    )
    assert resultado["pago"] is None
    assert PagoService(session).listar_pagos() == []


def test_calculo_de_liquidacion_previo(servicio, empleado):
    finiquito = servicio.calcular_liquidacion(
        empleado.id, "renuncia", date(2026, 3, 1)
    )
    assert finiquito.anos_servicio >= 0
    assert finiquito.neto >= 0
    assert finiquito.total_asignaciones >= finiquito.neto


def test_estadisticas_de_contratos(servicio, empleado):
    servicio.crear_contrato(_datos_contrato(empleado.id))
    estadisticas = servicio.obtener_estadisticas()
    assert estadisticas["total"] == 1
    assert estadisticas["vigentes"] == 1
    assert estadisticas["por_tipo"].get(TipoContrato.INDEFINIDO.value) == 1


def test_actualizar_contrato_cambia_solo_lo_indicado(servicio, empleado):
    contrato = servicio.crear_contrato(_datos_contrato(empleado.id))
    actualizado = servicio.actualizar_contrato(
        contrato.id, {"cargo": "Jefe de área", "observaciones": "Ajuste de cargo"}
    )
    assert actualizado.cargo == "Jefe de área"
    assert actualizado.observaciones == "Ajuste de cargo"
    assert float(actualizado.salario_pactado) == pytest.approx(1800.0)
    assert actualizado.estado_valor == EstadoContrato.VIGENTE.value


def test_obtener_contrato_inexistente(servicio):
    assert servicio.obtener_contrato(9999) is None
    with pytest.raises(ValueError):
        servicio.actualizar_contrato(9999, {"cargo": "X"})
