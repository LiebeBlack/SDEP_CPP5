"""
Cálculo de horas extra

Convierte las horas extra registradas en asistencia (diurnas,
nocturnas y feriadas) al monto a pagar, aplicando el recargo de cada
tipo sobre el valor de la hora ordinaria del empleado.
"""

from decimal import Decimal

from .tipos import CERO, Dinero, HorasExtra, redondear

# Días que se consideran base de un mes de remuneración
DIAS_MES = Decimal(30)
# Semanas promedio de un mes (52 semanas / 12 meses)
SEMANAS_MES = Decimal("4.3333")


def valor_hora_ordinaria(
    salario_mensual: Dinero,
    horas_jornada_diaria: Dinero = Decimal(8),
    dias_mes: Decimal = DIAS_MES,
) -> Dinero:
    """
    Valor de una hora ordinaria de trabajo

    Se deriva del salario mensual dividiéndolo entre los días del mes y
    las horas de la jornada diaria, que es el criterio habitual cuando
    el contrato no pacta un valor hora propio.
    """
    if salario_mensual <= CERO or horas_jornada_diaria <= CERO or dias_mes <= CERO:
        return CERO
    return redondear(salario_mensual / dias_mes / horas_jornada_diaria)


def valor_hora_por_jornada(
    salario_mensual: Dinero,
    horas_semanales: int = 40,
) -> Dinero:
    """
    Valor de la hora ordinaria a partir de la jornada semanal pactada

    Se usa cuando el contrato define horas semanales (por ejemplo 30 o
    44) y se quiere que el valor hora respete esa jornada real.
    """
    if salario_mensual <= CERO or horas_semanales <= 0:
        return CERO
    horas_mes = Decimal(horas_semanales) * SEMANAS_MES
    if horas_mes <= CERO:
        return CERO
    return redondear(salario_mensual / horas_mes)


def monto_por_recargo(horas: Dinero, valor_hora: Dinero, recargo: Dinero) -> Dinero:
    """
    Monto de una cantidad de horas extra con su recargo

    El recargo llega como número (25 = 25%), igual que se configura.
    """
    if horas <= CERO or valor_hora <= CERO:
        return CERO
    factor = Decimal(1) + (max(CERO, recargo) / Decimal(100))
    return redondear(horas * valor_hora * factor)


def calcular_monto_horas_extra(
    horas: HorasExtra,
    salario_mensual: Dinero,
    recargo_diurno: Dinero,
    recargo_nocturno: Dinero,
    recargo_feriado: Dinero,
    horas_jornada_diaria: Dinero = Decimal(8),
) -> Dinero:
    """
    Monto total de las horas extra de un período

    Aplica el recargo correspondiente a cada tipo de hora y devuelve la
    suma. El detalle por tipo se conserva en el modelo de pago, de modo
    que el recibo pueda mostrar el desglose.
    """
    if not horas.hay_horas:
        return CERO
    valor_hora = valor_hora_ordinaria(salario_mensual, horas_jornada_diaria)
    return redondear(
        monto_por_recargo(horas.diurnas, valor_hora, recargo_diurno)
        + monto_por_recargo(horas.nocturnas, valor_hora, recargo_nocturno)
        + monto_por_recargo(horas.feriadas, valor_hora, recargo_feriado)
    )


def desglose_horas_extra(
    horas: HorasExtra,
    salario_mensual: Dinero,
    recargo_diurno: Dinero,
    recargo_nocturno: Dinero,
    recargo_feriado: Dinero,
    horas_jornada_diaria: Dinero = Decimal(8),
) -> dict[str, float]:
    """
    Detalle por tipo de hora extra con su monto

    Alimenta el recibo de pago y los reportes de nómina.
    """
    valor_hora = valor_hora_ordinaria(salario_mensual, horas_jornada_diaria)
    return {
        "valor_hora": float(valor_hora),
        "horas_diurnas": float(redondear(horas.diurnas)),
        "monto_diurnas": float(monto_por_recargo(horas.diurnas, valor_hora, recargo_diurno)),
        "horas_nocturnas": float(redondear(horas.nocturnas)),
        "monto_nocturnas": float(
            monto_por_recargo(horas.nocturnas, valor_hora, recargo_nocturno)
        ),
        "horas_feriadas": float(redondear(horas.feriadas)),
        "monto_feriadas": float(
            monto_por_recargo(horas.feriadas, valor_hora, recargo_feriado)
        ),
    }
