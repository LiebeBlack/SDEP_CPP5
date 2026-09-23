"""
Pruebas del motor de cálculo de nómina

El motor es código puro (no toca la base de datos ni la interfaz), así que
estas pruebas fijan las fórmulas: modalidad porcentual histórica, tabla
progresiva de ISR, topes de seguridad social, horas extra con recargo,
prorrateo, prestaciones y amortización de préstamos.
"""

from datetime import date
from decimal import Decimal

import pytest

from src.models.enums import ModoCalculoNomina
from src.nomina import (
    CERO,
    DeduccionesManuales,
    EntradaFiniquito,
    EntradaNomina,
    HorasExtra,
    ParametrosNomina,
    TramoISR,
    a_decimal,
    antiguedad_en_anos,
    aplicar_descuento,
    calcular_aguinaldo,
    calcular_finiquito,
    calcular_isr,
    calcular_isr_anual,
    calcular_monto_cuota,
    calcular_monto_horas_extra,
    calcular_nomina,
    calcular_preaviso,
    calcular_prestaciones,
    calcular_seguridad_social,
    calcular_tasa_efectiva,
    calcular_vacaciones,
    cargar_parametros,
    construir_tramos,
    cuota_a_descontar,
    dias_vacaciones_pendientes,
    lineas_recibo,
    monto_maximo_otorgable,
    plan_de_pagos,
    redondear,
    resumen_costo_empleador,
    tramo_aplicable,
    validar_parametros,
    validar_solicitud,
    valor_hora_ordinaria,
    valor_hora_por_jornada,
)

TRAMOS_ISR = (
    TramoISR(
        limite_inferior=Decimal("0.00"),
        limite_superior=Decimal("1000.00"),
        tasa=CERO,
        cuota_fija=CERO,
    ),
    TramoISR(
        limite_inferior=Decimal("1000.00"),
        limite_superior=None,
        tasa=Decimal("10.0"),
        cuota_fija=CERO,
    ),
)

PARAMETROS_TRAMOS = ParametrosNomina(
    modo=ModoCalculoNomina.TRAMOS,
    porcentaje_seguro=Decimal("4.5"),
    porcentaje_pension=Decimal("5.0"),
    tramos_isr=TRAMOS_ISR,
)


# ----------------------------------------------------------------------
# Conversión y redondeo
# ----------------------------------------------------------------------
def test_a_decimal_acepta_formatos_reales():
    assert a_decimal(None) == CERO
    assert a_decimal("") == CERO
    assert a_decimal(1500) == Decimal("1500")
    assert a_decimal(1500.5) == Decimal("1500.5")
    assert a_decimal("1,234.56") == Decimal("1234.56")
    assert a_decimal("1.234,56") == Decimal("1234.56")
    assert a_decimal("no es número", Decimal("7")) == Decimal("7")


def test_redondeo_comercial_sube_el_medio_centavo():
    assert redondear("0.005") == Decimal("0.01")
    assert redondear("0.004") == Decimal("0.00")
    assert redondear("10.565") == Decimal("10.57")


# ----------------------------------------------------------------------
# Modalidad porcentual (cálculo histórico del sistema)
# ----------------------------------------------------------------------
def test_modalidad_porcentual_reproduce_el_calculo_historico():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("2000.00"),
            bonificaciones=Decimal("100.00"),
            horas_extra=HorasExtra(),
        )
    )
    # 4.5% de seguro y 5% de pensión sobre el salario base
    assert resultado.deduccion_seguro == Decimal("90.00")
    assert resultado.deduccion_pension == Decimal("100.00")
    assert resultado.deduccion_impuesto == CERO
    assert resultado.monto_bruto == Decimal("2100.00")
    assert resultado.monto_neto == Decimal("1910.00")
    assert resultado.modalidad == ModoCalculoNomina.PORCENTAJE.value
    assert resultado.isr_tramo is None


def test_el_neto_nunca_es_negativo():
    resultado = calcular_nomina(
        EntradaNomina(salario_base=Decimal("100.00"), descuentos=Decimal("9999.00"))
    )
    assert resultado.monto_neto == CERO
    assert resultado.total_deducciones > resultado.total_ingresos


def test_las_deducciones_manuales_mandan_sobre_el_calculo():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("2000.00"),
            deducciones_manuales=DeduccionesManuales(
                seguro=Decimal("12.34"),
                pension=Decimal("56.78"),
                impuesto=Decimal("10.00"),
            ),
        )
    )
    assert resultado.deduccion_seguro == Decimal("12.34")
    assert resultado.deduccion_pension == Decimal("56.78")
    assert resultado.deduccion_impuesto == Decimal("10.00")
    assert resultado.monto_neto == Decimal("1920.88")


def test_prorrateo_por_dias_trabajados():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("3000.00"),
            dias_trabajados=15,
            dias_periodo=30,
            prorratear=True,
        )
    )
    assert resultado.salario_base == Decimal("1500.00")
    # Los aportes se calculan sobre el salario efectivamente devengado
    assert resultado.deduccion_seguro == Decimal("67.50")


def test_prorrateo_con_dias_invalidos_no_rompe_el_calculo():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("3000.00"),
            dias_trabajados=90,
            dias_periodo=30,
            prorratear=True,
        )
    )
    assert resultado.salario_base == Decimal("3000.00")


def test_aguinaldo_y_bono_entran_al_bruto_y_a_las_deducciones():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("1000.00"),
            aguinaldo=Decimal("500.00"),
            bono_vacacional=Decimal("250.00"),
        )
    )
    assert resultado.monto_bruto == Decimal("1750.00")
    assert resultado.deduccion_seguro == Decimal("45.00")
    assert resultado.monto_neto == Decimal("1655.00")


def test_la_cuota_del_prestamo_se_descuenta_del_neto():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("1000.00"),
            cuota_prestamo=Decimal("100.00"),
        )
    )
    assert resultado.deduccion_prestamo == Decimal("100.00")
    assert resultado.monto_neto == Decimal("805.00")
    assert resultado.to_dict()["deduccion_prestamo"] == 100.0


# ----------------------------------------------------------------------
# Modalidad por tramos
# ----------------------------------------------------------------------
def test_tramos_calculan_isr_sobre_la_base_gravable():
    resultado = calcular_nomina(
        EntradaNomina(salario_base=Decimal("2000.00")), PARAMETROS_TRAMOS
    )
    # Base gravable = 2000 - 90 (seguro) - 100 (pensión) = 1810
    assert resultado.base_gravable == Decimal("1810.00")
    # Excedente sobre 1000 al 10% = 81.00
    assert resultado.deduccion_impuesto == Decimal("81.00")
    assert resultado.isr_tramo is not None
    assert resultado.monto_neto == Decimal("1729.00")


def test_tramo_aplicable_elige_el_rango_correcto():
    assert tramo_aplicable(Decimal("500.00"), TRAMOS_ISR) is TRAMOS_ISR[0]
    assert tramo_aplicable(Decimal("1500.00"), TRAMOS_ISR) is TRAMOS_ISR[1]
    assert tramo_aplicable(CERO, TRAMOS_ISR) is None
    assert tramo_aplicable(Decimal("100.00"), ()) is None


def test_el_impuesto_nunca_supera_la_base():
    tramos = (
        TramoISR(
            limite_inferior=CERO,
            limite_superior=None,
            tasa=Decimal("150.0"),
            cuota_fija=CERO,
        ),
    )
    impuesto, _ = calcular_isr(Decimal("100.00"), tramos)
    assert impuesto == Decimal("100.00")


def test_ajuste_anual_del_isr_detecta_saldo_a_favor():
    tramos = (
        TramoISR(
            limite_inferior=CERO,
            limite_superior=None,
            tasa=Decimal("10.0"),
            cuota_fija=CERO,
        ),
    )
    # Renta anual 12000 -> 1200 de impuesto; si se retuvieron 1500 sobra 300
    assert calcular_isr_anual(Decimal("12000.00"), tramos, Decimal("1500.00")) == Decimal(
        "-300.00"
    )
    assert calcular_tasa_efectiva(Decimal("12000.00"), tramos) == Decimal("10.0000")


def test_seguridad_social_aplica_techos_de_cotizacion():
    aportes = calcular_seguridad_social(
        salario=Decimal("1000.00"),
        porcentaje_seguro=Decimal("5.0"),
        porcentaje_pension=Decimal("5.0"),
        techo_seguro=Decimal("500.00"),
        techo_pension=CERO,
        porcentaje_seguro_patronal=Decimal("8.0"),
    )
    assert aportes.base_seguro == Decimal("500.00")
    assert aportes.seguro_empleado == Decimal("25.00")
    assert aportes.base_pension == Decimal("1000.00")
    assert aportes.pension_empleado == Decimal("50.00")
    assert aportes.seguro_patronal == Decimal("40.00")
    assert aportes.total_empleado == Decimal("75.00")
    assert aportes.total_patronal == Decimal("40.00")
    assert aportes.costo_total == Decimal("115.00")


def test_los_aportes_patronales_no_bajan_el_neto():
    parametros = ParametrosNomina(
        modo=ModoCalculoNomina.TRAMOS,
        porcentaje_seguro_patronal=Decimal("8.0"),
        porcentaje_pension_patronal=Decimal("5.0"),
        tramos_isr=TRAMOS_ISR,
    )
    resultado = calcular_nomina(EntradaNomina(salario_base=Decimal("1000.00")), parametros)
    assert resultado.total_aportes_patronales == Decimal("130.00")
    # 1000 - 45 - 50 = 905, sin descontar los aportes del patrono
    assert resultado.monto_neto == Decimal("905.00")


# ----------------------------------------------------------------------
# Horas extra
# ----------------------------------------------------------------------
def test_valor_de_la_hora_ordinaria():
    assert valor_hora_ordinaria(Decimal("2400.00"), Decimal(8)) == Decimal("10.00")
    assert valor_hora_ordinaria(CERO, Decimal(8)) == CERO
    assert valor_hora_por_jornada(Decimal("1733.32"), 40) == Decimal("10.00")


def test_horas_extra_con_recargos_por_tipo():
    monto = calcular_monto_horas_extra(
        HorasExtra(diurnas=Decimal(2), nocturnas=Decimal(2), feriadas=Decimal(1)),
        salario_mensual=Decimal("2400.00"),
        recargo_diurno=Decimal("25.0"),
        recargo_nocturno=Decimal("50.0"),
        recargo_feriado=Decimal("100.0"),
        horas_jornada_diaria=Decimal(8),
    )
    # 2*10*1.25 + 2*10*1.50 + 1*10*2.00 = 25 + 30 + 20
    assert monto == Decimal("75.00")


def test_horas_extra_en_la_nomina_y_en_el_recibo():
    resultado = calcular_nomina(
        EntradaNomina(
            salario_base=Decimal("2400.00"),
            horas_extra=HorasExtra(diurnas=Decimal(2)),
        )
    )
    assert resultado.monto_horas_extra == Decimal("25.00")
    assert resultado.horas_extra.total == Decimal("2.00")
    conceptos = {concepto for concepto, _, _ in lineas_recibo(resultado)}
    assert "Horas extra" in conceptos
    assert resultado.to_dict()["horas_extra_diurnas"] == 2.0


def test_sin_horas_extra_el_monto_es_cero():
    assert (
        calcular_monto_horas_extra(HorasExtra(), Decimal("2400.00"), *[Decimal(0)] * 3)
        == CERO
    )


# ----------------------------------------------------------------------
# Prestaciones, aguinaldo y finiquito
# ----------------------------------------------------------------------
def test_antiguedad_en_anos_usa_meses_y_dias_calendario():
    assert antiguedad_en_anos(date(2020, 1, 1), date(2022, 1, 1)) == Decimal("2.00")
    # 15 días de servicio: 15/360 de año, redondeado a dos decimales
    assert antiguedad_en_anos(date(2024, 1, 1), date(2024, 1, 16)) == Decimal("0.04")
    assert antiguedad_en_anos(date(2024, 1, 1), date(2023, 1, 1)) == CERO


def test_aguinaldo_bono_y_prestaciones_proporcionales():
    assert calcular_aguinaldo(Decimal("3000.00"), 6, 0, Decimal(15)) == Decimal("750.00")
    assert calcular_vacaciones(Decimal("3000.00"), Decimal(15)) == Decimal("1500.00")
    assert calcular_prestaciones(Decimal("3000.00"), Decimal(2), Decimal(30)) == Decimal(
        "6000.00"
    )
    assert calcular_preaviso(Decimal("3000.00"), Decimal(30)) == Decimal("3000.00")
    # Sin salario no hay importe que pagar
    assert calcular_aguinaldo(CERO, 12, 0, Decimal(15)) == CERO


def test_finiquito_de_dos_anos_incluye_todos_los_conceptos():
    finiquito = calcular_finiquito(
        EntradaFiniquito(
            salario_mensual=Decimal("3000.00"),
            fecha_ingreso=date(2024, 1, 1),
            fecha_egreso=date(2026, 1, 1),
            dias_vacaciones_pendientes=Decimal(15),
            anticipos_pendientes=Decimal("500.00"),
            motivo="renuncia",
        ),
        ParametrosNomina(),
    )
    assert finiquito.anos_servicio == Decimal("2.0000")
    assert finiquito.prestaciones == Decimal("6000.00")
    assert finiquito.anticipos == Decimal("500.00")
    assert finiquito.total_asignaciones > CERO
    assert finiquito.neto == finiquito.total_asignaciones - finiquito.total_deducciones
    assert finiquito.to_dict()["motivo"] == "renuncia"


def test_finiquito_sin_fecha_de_ingreso_no_inventa_prestaciones():
    finiquito = calcular_finiquito(
        EntradaFiniquito(
            salario_mensual=Decimal("3000.00"),
            fecha_ingreso=None,
            fecha_egreso=date(2026, 1, 1),
            anticipos_pendientes=Decimal("100.00"),
        )
    )
    assert finiquito.prestaciones == CERO
    assert finiquito.anticipos == Decimal("100.00")
    assert finiquito.neto == CERO


def test_dias_de_vacaciones_pendientes_por_antiguedad():
    dias = dias_vacaciones_pendientes(
        salario_mensual=Decimal("3000.00"),
        dias_vacaciones_anuales=Decimal(15),
        fecha_ingreso=date(2025, 1, 1),
        fecha_egreso=date(2025, 7, 1),
        dias_ya_disfrutados=Decimal(5),
    )
    assert dias > CERO


# ----------------------------------------------------------------------
# Préstamos
# ----------------------------------------------------------------------
def test_cuota_redondea_hacia_abajo_para_no_cobrar_de_mas():
    assert calcular_monto_cuota(Decimal("1000.00"), 3) == Decimal("333.33")
    assert calcular_monto_cuota(Decimal("1000.00"), 0) == CERO


def test_plan_de_pagos_suma_exactamente_el_monto():
    plan = plan_de_pagos(Decimal("1000.00"), 3, date(2026, 1, 15))
    assert len(plan) == 3
    assert sum(cuota["monto"] for cuota in plan) == pytest.approx(1000.0)
    assert plan[-1]["saldo"] == pytest.approx(0.0)
    assert plan[0]["fecha"] == date(2026, 1, 15)
    assert plan_de_pagos(CERO, 3) == []


def test_la_ultima_cuota_no_excede_el_saldo():
    assert cuota_a_descontar(Decimal("50.00"), Decimal("100.00")) == Decimal("50.00")
    assert cuota_a_descontar(Decimal("500.00"), Decimal("100.00")) == Decimal("100.00")


def test_aplicar_descuento_cierra_el_prestamo_cuando_llega_a_cero():
    parcial = aplicar_descuento(
        saldo=Decimal("500.00"),
        cuotas_pagadas=0,
        numero_cuotas=5,
        descuento=Decimal("100.00"),
        fecha=date(2026, 1, 30),
    )
    assert parcial["saldo"] == 400.0
    assert parcial["cuotas_pagadas"] == 1
    assert parcial["estado"] == "activo"
    assert parcial["fecha_ultimo_descuento"] == date(2026, 1, 30)

    final = aplicar_descuento(
        saldo=Decimal("100.00"),
        cuotas_pagadas=4,
        numero_cuotas=5,
        descuento=Decimal("100.00"),
        fecha=date(2026, 2, 28),
    )
    assert final["saldo"] == 0.0
    assert final["cuotas_pagadas"] == 5
    assert final["estado"] == "pagado"


def test_validacion_de_solicitud_por_tope_salarial():
    # Cuota del 40% del salario: supera el tope del 30%
    errores = validar_solicitud(
        monto=Decimal("3600.00"),
        numero_cuotas=3,
        max_cuotas=24,
        salario_mensual=Decimal("3000.00"),
        max_porcentaje=Decimal("30.0"),
    )
    assert any("supera" in error for error in errores)

    sin_errores = validar_solicitud(
        monto=Decimal("1000.00"),
        numero_cuotas=6,
        max_cuotas=24,
        salario_mensual=Decimal("3000.00"),
    )
    assert sin_errores == []

    assert validar_solicitud(CERO, 0) != []
    assert validar_solicitud(Decimal("100.00"), 99, max_cuotas=24) != []


def test_monto_maximo_otorgable_respeta_el_tope():
    assert monto_maximo_otorgable(Decimal("3000.00"), 10) == Decimal("9000.00")
    assert monto_maximo_otorgable(CERO, 10) == CERO


# ----------------------------------------------------------------------
# Parámetros y utilidades de presentación
# ----------------------------------------------------------------------
def test_parametros_por_defecto_son_conservadores():
    parametros = cargar_parametros({})
    assert parametros.modo == ModoCalculoNomina.PORCENTAJE
    assert parametros.porcentaje_seguro == Decimal("4.5")
    assert parametros.tramos_isr == ()
    assert not parametros.usa_tramos


def test_construir_tramos_acepta_json_y_descarta_basura():
    tramos = construir_tramos(
        '[{"limite_inferior": 0, "limite_superior": 1000, "tasa": 5, "cuota_fija": 0},'
        ' {"limite_inferior": 1000, "limite_superior": null, "tasa": 10, "cuota_fija": 50}]'
    )
    assert len(tramos) == 2
    assert tramos[1].limite_superior is None
    assert tramos[1].cuota_fija == Decimal("50")
    assert construir_tramos("no es json") == ()
    assert construir_tramos([{"basura": 1}]) == ()


def test_validar_parametros_avisa_de_configuraciones_incoherentes():
    # Los valores por defecto son coherentes: el motor nunca debe frenar
    # el cálculo de la nómina por una configuración sin sembrar.
    assert validar_parametros(ParametrosNomina()) == []
    # Pero la modalidad por tramos exige una tabla configurada
    assert validar_parametros(
        ParametrosNomina(modo=ModoCalculoNomina.TRAMOS)
    ) != []
    assert validar_parametros(
        ParametrosNomina(porcentaje_seguro=Decimal("150.0"))
    ) != []
    parametros = ParametrosNomina(
        modo=ModoCalculoNomina.TRAMOS,
        porcentaje_seguro=Decimal("4.5"),
        porcentaje_pension=Decimal("5.0"),
        tramos_isr=TRAMOS_ISR,
    )
    assert validar_parametros(parametros) == []

    desordenados = ParametrosNomina(
        modo=ModoCalculoNomina.TRAMOS,
        tramos_isr=tuple(reversed(TRAMOS_ISR)),
    )
    assert desordenados.tramos_ordenados[0].limite_inferior == CERO


def test_resumen_del_costo_para_el_empleador():
    resultado = calcular_nomina(
        EntradaNomina(salario_base=Decimal("2000.00")), PARAMETROS_TRAMOS
    )
    resumen = resumen_costo_empleador(resultado)
    assert resumen["neto_empleado"] == 1729.0
    assert resumen["deducciones_empleado"] == 271.0
    assert resumen["costo_total"] > resumen["neto_empleado"]
