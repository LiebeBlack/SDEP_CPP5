"""
Motor de cálculo de nómina

Punto de entrada único del cálculo de un período de nómina. Reúne los
demás módulos del paquete (horas extra, seguridad social e ISR) y
devuelve un resultado completo y consistente, con los importes ya
redondeados a dos decimales.

Dos modalidades, según la configuración del sistema:

* PORCENTAJE: porcentajes planos sobre el salario base. Es el cálculo
  histórico del sistema, que se conserva tal cual para que ninguna
  nómina ya emitida cambie de importe.
* TRAMOS: motor completo con techos de cotización, aportes patronales
  separados y tabla progresiva de ISR sobre la base gravable.
"""

from decimal import Decimal
from typing import Any

from .horas_extra import calcular_monto_horas_extra
from .isr import calcular_isr
from .seguridad_social import calcular_seguridad_social
from .tipos import (
    CERO,
    Dinero,
    EntradaNomina,
    HorasExtra,
    ParametrosNomina,
    ResultadoNomina,
    redondear,
)


def _porcentaje(base: Dinero, porcentaje: Dinero) -> Dinero:
    """Aplica un porcentaje a una base (el porcentaje llega como 4.5 = 4.5%)"""
    if base <= CERO or porcentaje <= CERO:
        return CERO
    return redondear(base * porcentaje / Decimal(100))


def calcular_nomina(
    entrada: EntradaNomina,
    parametros: ParametrosNomina | None = None,
) -> ResultadoNomina:
    """
    Calcula el pago de un empleado para un período

    Args:
        entrada: Ingresos y descuentos del período
        parametros: Parámetros vigentes. Si no se entregan se usan los
            valores por defecto del motor (modalidad porcentual).

    Returns:
        ResultadoNomina: Desglose completo, con el neto ya calculado

    El neto nunca puede ser negativo: si los descuentos superan a los
    ingresos, el resultado se recorta a cero en lugar de generar un
    importe a cobrar, que sería un dato imposible de pagar.
    """
    parametros = parametros or ParametrosNomina()
    salario_base = redondear(entrada.salario_base)

    if entrada.prorratear and entrada.dias_periodo > 0:
        dias = max(0, min(int(entrada.dias_trabajados), int(entrada.dias_periodo)))
        salario_base = redondear(
            salario_base * Decimal(dias) / Decimal(entrada.dias_periodo)
        )

    horas: HorasExtra = entrada.horas_extra
    monto_horas_extra = (
        calcular_monto_horas_extra(
            horas,
            salario_base,
            parametros.recargo_diurno,
            parametros.recargo_nocturno,
            parametros.recargo_feriado,
            parametros.horas_jornada_diaria,
        )
        if horas.hay_horas
        else CERO
    )

    bonificaciones = redondear(entrada.bonificaciones)
    aguinaldo = redondear(entrada.aguinaldo)
    bono_vacacional = redondear(entrada.bono_vacacional)
    otras_deducciones = redondear(entrada.otras_deducciones)
    descuentos = redondear(entrada.descuentos)
    cuota_prestamo = max(CERO, redondear(entrada.cuota_prestamo))

    if parametros.usa_tramos:
        aportes = calcular_seguridad_social(
            salario_base,
            parametros.porcentaje_seguro,
            parametros.porcentaje_pension,
            parametros.techo_seguro,
            parametros.techo_pension,
            parametros.porcentaje_seguro_patronal,
            parametros.porcentaje_pension_patronal,
        )
        seguro = aportes.seguro_empleado
        pension = aportes.pension_empleado
        seguro_patronal = aportes.seguro_patronal
        pension_patronal = aportes.pension_patronal

        # La renta se calcula sobre los ingresos del período menos los
        # aportes de seguridad social, que son renta exenta.
        base_gravable = max(
            CERO,
            redondear(
                salario_base
                + monto_horas_extra
                + bonificaciones
                + aguinaldo
                + bono_vacacional
                - seguro
                - pension
            ),
        )
        impuesto, tramo = calcular_isr(base_gravable, parametros.tramos_ordenados)
    else:
        seguro = _porcentaje(salario_base, parametros.porcentaje_seguro)
        pension = _porcentaje(salario_base, parametros.porcentaje_pension)
        impuesto = _porcentaje(salario_base, parametros.porcentaje_impuesto)
        seguro_patronal = CERO
        pension_patronal = CERO
        base_gravable = salario_base
        tramo = None

    manuales = entrada.deducciones_manuales
    if manuales is not None:
        if manuales.seguro is not None:
            seguro = redondear(manuales.seguro)
        if manuales.pension is not None:
            pension = redondear(manuales.pension)
        if manuales.impuesto is not None:
            impuesto = redondear(manuales.impuesto)

    return ResultadoNomina(
        modalidad=parametros.modo.value,
        salario_base=salario_base,
        monto_horas_extra=monto_horas_extra,
        bonificaciones=bonificaciones,
        aguinaldo=aguinaldo,
        bono_vacacional=bono_vacacional,
        base_gravable=base_gravable,
        deduccion_seguro=seguro,
        deduccion_pension=pension,
        deduccion_impuesto=impuesto,
        otras_deducciones=otras_deducciones,
        descuentos=descuentos,
        deduccion_prestamo=cuota_prestamo,
        aporte_seguro_patronal=seguro_patronal,
        aporte_pension_patronal=pension_patronal,
        isr_tramo=tramo,
        horas_extra=horas,
    )


def lineas_recibo(resultado: ResultadoNomina) -> list[tuple[str, float, str]]:
    """
    Conceptos de un recibo de pago, listos para imprimir

    Returns:
        list: Tuplas (concepto, monto, tipo) donde tipo es "ingreso" o
        "deduccion". Se omiten los conceptos en cero para que el recibo
        solo muestre lo que realmente afecta al pago.
    """
    candidatos: list[tuple[str, Dinero, str]] = [
        ("Salario base", resultado.salario_base, "ingreso"),
        ("Horas extra", resultado.monto_horas_extra, "ingreso"),
        ("Bonificaciones", resultado.bonificaciones, "ingreso"),
        ("Aguinaldo", resultado.aguinaldo, "ingreso"),
        ("Bono vacacional", resultado.bono_vacacional, "ingreso"),
        ("Seguro social", resultado.deduccion_seguro, "deduccion"),
        ("Pensión", resultado.deduccion_pension, "deduccion"),
        ("Impuesto sobre la renta", resultado.deduccion_impuesto, "deduccion"),
        ("Cuota de préstamo", resultado.deduccion_prestamo, "deduccion"),
        ("Otras deducciones", resultado.otras_deducciones, "deduccion"),
        ("Descuentos", resultado.descuentos, "deduccion"),
    ]
    return [
        (concepto, float(redondear(monto)), tipo)
        for concepto, monto, tipo in candidatos
        if redondear(monto) != CERO
    ]


def resumen_costo_empleador(resultado: ResultadoNomina) -> dict[str, Any]:
    """
    Costo total del período para el empleador

    Suma el neto que recibe el empleado, los aportes que se descuentan
    de su salario (que igualmente ingresan al sistema de seguridad
    social) y los aportes patronales.
    """
    return {
        "neto_empleado": float(resultado.monto_neto),
        "deducciones_empleado": float(resultado.total_deducciones),
        "aportes_patronales": float(resultado.total_aportes_patronales),
        "costo_total": float(
            redondear(
                resultado.monto_bruto + resultado.total_aportes_patronales
            )
        ),
    }
