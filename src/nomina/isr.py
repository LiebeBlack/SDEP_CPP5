"""
Cálculo del impuesto sobre la renta (ISR)

Implementa la tabla progresiva por tramos: cada tramo tiene una cuota
fija y una tasa que se aplica sobre el excedente del límite inferior.
El módulo es puro: recibe la base gravable y los tramos, y devuelve el
impuesto con su explicación.
"""

from decimal import Decimal
from typing import Sequence

from .tipos import CERO, Dinero, TramoISR, redondear


def tramo_aplicable(base: Dinero, tramos: Sequence[TramoISR]) -> TramoISR | None:
    """
    Tramo en el que cae una base gravable

    Si la base está por debajo del primer tramo devuelve None (renta no
    gravada). Si la base excede el último tramo se devuelve el último,
    que es el que no tiene límite superior.
    """
    if base <= CERO or not tramos:
        return None
    ordenados = sorted(tramos, key=lambda tramo: tramo.limite_inferior)
    seleccionado: TramoISR | None = None
    for tramo in ordenados:
        if tramo.aplica_a(base):
            seleccionado = tramo
    return seleccionado


def calcular_isr(base: Dinero, tramos: Sequence[TramoISR]) -> tuple[Dinero, str | None]:
    """
    Impuesto a retener sobre una base gravable

    Args:
        base: Base gravable del período (ingresos menos aportes exentos)
        tramos: Tabla progresiva vigente

    Returns:
        tuple: (impuesto retenido, descripción del tramo aplicado o None)

    El impuesto nunca puede superar la base: si la configuración de los
    tramos es inconsistente, se recorta al 100% de la base en lugar de
    generar un neto negativo.
    """
    if base <= CERO:
        return CERO, None
    tramo = tramo_aplicable(base, tramos)
    if tramo is None:
        return CERO, None
    impuesto = tramo.calcular(base)
    if impuesto > base:
        impuesto = redondear(base)
    return impuesto, tramo.descripcion()


def calcular_isr_anual(
    ingresos_anuales: Dinero,
    tramos: Sequence[TramoISR],
    retenido_acumulado: Dinero = CERO,
) -> Dinero:
    """
    Ajuste anual del ISR

    Compara el impuesto que corresponde a la renta anual con lo que ya
    se retuvo mes a mes. Un resultado positivo indica que falta retener;
    uno negativo, que hay un saldo a favor del empleado.
    """
    impuesto_anual, _ = calcular_isr(ingresos_anuales, tramos)
    return redondear(impuesto_anual - max(CERO, retenido_acumulado))


def calcular_tasa_efectiva(base: Dinero, tramos: Sequence[TramoISR]) -> Decimal:
    """
    Tasa efectiva del impuesto sobre una base gravable

    Es el porcentaje real que representa el impuesto dentro de la base,
    útil para los reportes de nómina (no es la tasa marginal del tramo).
    """
    if base <= CERO:
        return CERO
    impuesto, _ = calcular_isr(base, tramos)
    return (impuesto / base * Decimal(100)).quantize(Decimal("0.01"))
