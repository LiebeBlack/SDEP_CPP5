"""
Cálculo de anticipos y préstamos

Resuelve la cuota, el plan de pagos, el descuento aplicable en cada
nómina y el estado del préstamo después de cada descuento. Todo el
cálculo es puro: la persistencia la hace el servicio correspondiente.
"""

from datetime import date
from decimal import Decimal, ROUND_DOWN
from typing import Any

from src.models.enums import EstadoPrestamo, TipoPrestamo

from .tipos import CERO, Dinero, redondear


def calcular_monto_cuota(monto: Dinero, numero_cuotas: int) -> Dinero:
    """
    Cuota teórica de un préstamo

    Se calcula hacia abajo (ROUND_DOWN) para que la suma de las cuotas
    nunca exceda el monto prestado; la diferencia se cobra en la última
    cuota mediante el saldo, que es la fuente de verdad del descuento.
    """
    if monto <= CERO or numero_cuotas <= 0:
        return CERO
    cuota = (monto / Decimal(numero_cuotas)).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    return cuota


def plan_de_pagos(
    monto: Dinero,
    numero_cuotas: int,
    fecha_primer_descuento: date | None = None,
) -> list[dict[str, Any]]:
    """
    Plan de amortización cuota por cuota

    La última cuota absorbe el redondeo pendiente, de modo que la suma
    del plan sea exactamente igual al monto otorgado.
    """
    if monto <= CERO or numero_cuotas <= 0:
        return []
    cuota = calcular_monto_cuota(monto, numero_cuotas)
    plan: list[dict[str, Any]] = []
    saldo = redondear(monto)
    for numero in range(1, numero_cuotas + 1):
        es_ultima = numero == numero_cuotas
        descuento = saldo if es_ultima else cuota
        saldo = redondear(saldo - descuento)
        plan.append(
            {
                "numero": numero,
                "fecha": fecha_primer_descuento,
                "monto": float(descuento),
                "saldo": float(saldo),
            }
        )
    return plan


def cuota_a_descontar(saldo: Dinero, monto_cuota: Dinero) -> Dinero:
    """
    Descuento real de una cuota

    Nunca descuenta más que el saldo pendiente: si el saldo es menor que
    la cuota pactada, el préstamo se cierra con ese último descuento.
    """
    if saldo <= CERO:
        return CERO
    if monto_cuota <= CERO:
        return redondear(saldo)
    return redondear(min(saldo, monto_cuota))


def calcular_descuento(
    saldo: Dinero,
    monto_cuota: Dinero,
    neto_disponible: Dinero,
    max_porcentaje: Dinero,
) -> Dinero:
    """
    Descuento de préstamo aplicable a una nómina

    Respeta dos límites: el saldo pendiente y el porcentaje máximo del
    neto que la institución puede retener por este concepto. Si el neto
    no alcanza para la cuota completa, se descuenta lo que permite el
    tope en lugar de dejar el pago en cero.
    """
    if neto_disponible <= CERO or saldo <= CERO:
        return CERO
    tope = CERO
    if max_porcentaje > CERO:
        tope = redondear(neto_disponible * max_porcentaje / Decimal(100))
    disponible = max(CERO, min(saldo, neto_disponible)) if tope <= CERO else tope
    return redondear(min(cuota_a_descontar(saldo, monto_cuota), disponible))


def estado_tras_descuento(saldo: Dinero) -> str:
    """Estado que corresponde a un préstamo según su saldo restante"""
    if saldo <= CERO:
        return EstadoPrestamo.PAGADO.value
    return EstadoPrestamo.ACTIVO.value


def aplicar_descuento(
    saldo: Dinero,
    cuotas_pagadas: int,
    numero_cuotas: int,
    descuento: Dinero,
    fecha: date | None = None,
) -> dict[str, Any]:
    """
    Estado del préstamo después de aplicar un descuento

    Returns:
        dict: saldo, cuotas_pagadas, estado y fecha del descuento, listo
        para volcar en el modelo Prestamo.
    """
    nuevo_saldo = redondear(max(CERO, saldo - descuento))
    nuevas_cuotas = cuotas_pagadas + (1 if descuento > CERO else 0)
    if nuevo_saldo <= CERO:
        nuevas_cuotas = max(nuevas_cuotas, numero_cuotas)
    return {
        "saldo": float(nuevo_saldo),
        "cuotas_pagadas": nuevas_cuotas,
        "estado": estado_tras_descuento(nuevo_saldo),
        "fecha_ultimo_descuento": fecha,
    }


def validar_solicitud(
    monto: Dinero,
    numero_cuotas: int,
    max_cuotas: int = 24,
    salario_mensual: Dinero = CERO,
    max_porcentaje: Dinero = Decimal("30.0"),
) -> list[str]:
    """
    Valida una solicitud de anticipo o préstamo

    Returns:
        list[str]: Errores encontrados (lista vacía si la solicitud es
        válida). Los mensajes están redactados para mostrarse al usuario.
    """
    errores: list[str] = []

    if monto <= CERO:
        errores.append("El monto debe ser mayor que cero")
    if numero_cuotas <= 0:
        errores.append("El número de cuotas debe ser mayor que cero")
    elif max_cuotas > 0 and numero_cuotas > max_cuotas:
        errores.append(f"El número de cuotas no puede superar {max_cuotas}")

    if monto > CERO and numero_cuotas > 0 and salario_mensual > CERO and max_porcentaje > CERO:
        cuota = calcular_monto_cuota(monto, numero_cuotas)
        tope = redondear(salario_mensual * max_porcentaje / Decimal(100))
        if cuota > tope:
            errores.append(
                f"La cuota ({cuota:.2f}) supera el {max_porcentaje:.0f}% del salario "
                f"({tope:.2f}). Aumente el número de cuotas."
            )

    return errores


def monto_maximo_otorgable(
    salario_mensual: Dinero,
    numero_cuotas: int,
    max_porcentaje: Dinero = Decimal("30.0"),
) -> Dinero:
    """Monto máximo que puede otorgarse sin superar el tope de descuento"""
    if salario_mensual <= CERO or numero_cuotas <= 0 or max_porcentaje <= CERO:
        return CERO
    cuota_maxima = redondear(salario_mensual * max_porcentaje / Decimal(100))
    return redondear(cuota_maxima * Decimal(numero_cuotas))


def etiqueta_tipo(tipo: str) -> str:
    """Nombre legible del tipo de operación"""
    return "Anticipo" if tipo == TipoPrestamo.ANTICIPO.value else "Préstamo"
