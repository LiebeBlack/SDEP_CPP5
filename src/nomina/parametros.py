"""
Carga de parámetros del motor de nómina

Traduce los parámetros guardados en la configuración del sistema a la
estructura tipada que consumen los cálculos. Incluye los valores por
defecto y la validación, de modo que una configuración incompleta o mal
capturada nunca rompa la nómina: se usa el valor por defecto y se avisa.
"""

import json
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any

from src.models.enums import ModoCalculoNomina

from .tipos import CERO, Dinero, ParametrosNomina, TramoISR, a_decimal

# Valores por defecto del motor. Se usan cuando la clave no existe en la
# configuración (por ejemplo, en una instalación que aún no se sembró) y
# son deliberadamente conservadores: sin aporte patronal inventado y en
# modalidad porcentual, que es el cálculo histórico del sistema.
VALORES_POR_DEFECTO: dict[str, Any] = {
    "modo_calculo_nomina": ModoCalculoNomina.PORCENTAJE.value,
    "porcentaje_seguro": 4.5,
    "porcentaje_pension": 5.0,
    "porcentaje_impuesto": 0.0,
    "techo_seguro": 0.0,
    "techo_pension": 0.0,
    "porcentaje_seguro_patronal": 0.0,
    "porcentaje_pension_patronal": 0.0,
    "isr_tramos": [],
    "horas_jornada_diaria": 8,
    "recargo_hora_extra_diurna": 25.0,
    "recargo_hora_extra_nocturna": 50.0,
    "recargo_hora_extra_feriada": 100.0,
    "dias_aguinaldo": 15,
    "dias_bono_vacacional": 15,
    "dias_prestaciones_por_ano": 30,
    "dias_preaviso": 30,
    "max_porcentaje_cuota_prestamo": 30.0,
    "salario_minimo": 0.0,
}


def construir_tramos(valor: Any) -> tuple[TramoISR, ...]:
    """
    Construye la tabla de tramos de ISR desde la configuración

    Acepta la lista ya deserializada o el texto JSON tal como se guarda
    en la base de datos. Cualquier entrada inválida se descarta en lugar
    de abortar el cálculo, porque la nómina debe poder ejecutarse aunque
    la tabla esté a medio configurar.
    """
    if valor in (None, "", "[]"):
        return ()
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except json.JSONDecodeError:
            return ()
    if not isinstance(valor, (list, tuple)):
        return ()
    tramos: list[TramoISR] = []
    for entrada in valor:
        if isinstance(entrada, Mapping):
            tramo = TramoISR.desde_dict(dict(entrada))
            if tramo.tasa > CERO or tramo.cuota_fija > CERO or tramo.limite_inferior > CERO:
                tramos.append(tramo)
    return tuple(tramos)


def cargar_parametros(valores: Mapping[str, Any] | None = None) -> ParametrosNomina:
    """
    Construye los parámetros del motor a partir de un mapeo clave -> valor

    Args:
        valores: Valores vigentes (normalmente leídos de la configuración).
            Las claves ausentes toman su valor por defecto.
    """
    datos = dict(VALORES_POR_DEFECTO)
    if valores:
        datos.update({clave: valor for clave, valor in valores.items() if valor is not None})

    modo_valor = str(datos["modo_calculo_nomina"]).strip().lower()
    modo = (
        ModoCalculoNomina.TRAMOS
        if modo_valor == ModoCalculoNomina.TRAMOS.value
        else ModoCalculoNomina.PORCENTAJE
    )

    return ParametrosNomina(
        modo=modo,
        porcentaje_seguro=a_decimal(datos["porcentaje_seguro"]),
        porcentaje_pension=a_decimal(datos["porcentaje_pension"]),
        porcentaje_impuesto=a_decimal(datos["porcentaje_impuesto"]),
        techo_seguro=a_decimal(datos["techo_seguro"]),
        techo_pension=a_decimal(datos["techo_pension"]),
        porcentaje_seguro_patronal=a_decimal(datos["porcentaje_seguro_patronal"]),
        porcentaje_pension_patronal=a_decimal(datos["porcentaje_pension_patronal"]),
        tramos_isr=construir_tramos(datos["isr_tramos"]),
        horas_jornada_diaria=a_decimal(datos["horas_jornada_diaria"], Decimal(8)),
        recargo_diurno=a_decimal(datos["recargo_hora_extra_diurna"]),
        recargo_nocturno=a_decimal(datos["recargo_hora_extra_nocturna"]),
        recargo_feriado=a_decimal(datos["recargo_hora_extra_feriada"]),
        dias_aguinaldo=a_decimal(datos["dias_aguinaldo"]),
        dias_bono_vacacional=a_decimal(datos["dias_bono_vacacional"]),
        dias_prestaciones_por_ano=a_decimal(datos["dias_prestaciones_por_ano"]),
        dias_preaviso=a_decimal(datos["dias_preaviso"]),
        max_porcentaje_cuota_prestamo=a_decimal(datos["max_porcentaje_cuota_prestamo"]),
        salario_minimo=a_decimal(datos["salario_minimo"]),
    )


def cargar_parametros_desde(obtener: Callable[[str, Any], Any]) -> ParametrosNomina:
    """
    Construye los parámetros leyendo cada clave con la función recibida

    Args:
        obtener: Función que recibe (clave, valor_por_defecto) y devuelve el
            valor vigente. Normalmente es ConfiguracionService.obtener_valor.
    """
    valores: dict[str, Any] = {}
    for clave, por_defecto in VALORES_POR_DEFECTO.items():
        try:
            valores[clave] = obtener(clave, por_defecto)
        except (KeyError, TypeError, ValueError):
            valores[clave] = por_defecto
    return cargar_parametros(valores)


def validar_parametros(parametros: ParametrosNomina) -> list[str]:
    """
    Revisa la coherencia de los parámetros configurados

    Returns:
        list[str]: Descripción de cada problema encontrado (lista vacía si
        todo es válido). Lo usa la pantalla de Configuración para avisar
        antes de que un cálculo salga mal.
    """
    errores: list[str] = []

    for nombre, valor in (
        ("porcentaje_seguro", parametros.porcentaje_seguro),
        ("porcentaje_pension", parametros.porcentaje_pension),
        ("porcentaje_impuesto", parametros.porcentaje_impuesto),
        ("porcentaje_seguro_patronal", parametros.porcentaje_seguro_patronal),
        ("porcentaje_pension_patronal", parametros.porcentaje_pension_patronal),
    ):
        if valor < CERO or valor > Decimal(100):
            errores.append(f"{nombre}: debe estar entre 0 y 100 (valor actual {valor})")

    if parametros.horas_jornada_diaria <= CERO:
        errores.append("horas_jornada_diaria: debe ser mayor que 0")

    if parametros.max_porcentaje_cuota_prestamo < CERO:
        errores.append("max_porcentaje_cuota_prestamo: no puede ser negativo")

    tramos = parametros.tramos_ordenados
    if parametros.usa_tramos and not tramos:
        errores.append("isr_tramos: la modalidad por tramos requiere una tabla configurada")

    anterior: TramoISR | None = None
    for tramo in tramos:
        if tramo.limite_superior is not None and tramo.limite_superior < tramo.limite_inferior:
            errores.append(f"isr_tramos: tramo inválido {tramo.descripcion()}")
        if anterior is not None:
            fin_anterior = anterior.limite_superior
            if fin_anterior is not None and tramo.limite_inferior < fin_anterior:
                errores.append(
                    "isr_tramos: los tramos se solapan entre "
                    f"{anterior.descripcion()} y {tramo.descripcion()}"
                )
        anterior = tramo

    return errores


def porcentaje_efectivo(base: Dinero, monto: Dinero) -> Decimal:
    """Porcentaje que representa un monto dentro de una base (para reportes)"""
    if base <= CERO:
        return CERO
    return (monto / base * Decimal(100)).quantize(Decimal("0.01"))
