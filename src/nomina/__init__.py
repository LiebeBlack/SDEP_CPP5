"""
Motor de cálculo de nómina

Paquete de cálculo puro: no accede a la base de datos ni a la interfaz,
de modo que cada fórmula puede probarse y auditarse por separado. Los
servicios de la aplicación lo usan pasándole los datos ya cargados.

Uso típico:

    from src.nomina import EntradaNomina, HorasExtra, calcular_nomina

    resultado = calcular_nomina(
        EntradaNomina(salario_base=Decimal("1500.00")),
        parametros,
    )
    resultado.monto_neto
"""

from .finiquito import calcular_finiquito, dias_vacaciones_pendientes, resumen_liquidacion
from .horas_extra import (
    calcular_monto_horas_extra,
    desglose_horas_extra,
    valor_hora_ordinaria,
    valor_hora_por_jornada,
)
from .isr import calcular_isr, calcular_isr_anual, calcular_tasa_efectiva, tramo_aplicable
from .motor import calcular_nomina, lineas_recibo, resumen_costo_empleador
from .parametros import (
    VALORES_POR_DEFECTO,
    cargar_parametros,
    cargar_parametros_desde,
    construir_tramos,
    validar_parametros,
)
from .prestaciones import (
    antiguedad_en_anos,
    calcular_aguinaldo,
    calcular_bono_vacacional,
    calcular_indemnizacion,
    calcular_preaviso,
    calcular_prestaciones,
    calcular_vacaciones,
    meses_y_dias_entre,
)
from .prestamos import (
    aplicar_descuento,
    calcular_descuento,
    calcular_monto_cuota,
    cuota_a_descontar,
    monto_maximo_otorgable,
    plan_de_pagos,
    validar_solicitud,
)
from .seguridad_social import (
    AportesSeguridadSocial,
    base_afectada,
    calcular_aporte,
    calcular_seguridad_social,
)
from .tipos import (
    CERO,
    CENTAVO,
    DeduccionesManuales,
    Dinero,
    EntradaFiniquito,
    EntradaNomina,
    HorasExtra,
    ParametrosNomina,
    ResultadoFiniquito,
    ResultadoNomina,
    TramoISR,
    a_decimal,
    redondear,
)

__all__ = [
    # Tipos
    "CERO",
    "CENTAVO",
    "DeduccionesManuales",
    "Dinero",
    "EntradaFiniquito",
    "EntradaNomina",
    "HorasExtra",
    "ParametrosNomina",
    "ResultadoFiniquito",
    "ResultadoNomina",
    "TramoISR",
    "AportesSeguridadSocial",
    "a_decimal",
    "redondear",
    # Parámetros
    "VALORES_POR_DEFECTO",
    "cargar_parametros",
    "cargar_parametros_desde",
    "construir_tramos",
    "validar_parametros",
    # Cálculos
    "calcular_nomina",
    "calcular_finiquito",
    "calcular_isr",
    "calcular_isr_anual",
    "calcular_tasa_efectiva",
    "tramo_aplicable",
    "calcular_seguridad_social",
    "calcular_aporte",
    "base_afectada",
    "calcular_monto_horas_extra",
    "desglose_horas_extra",
    "valor_hora_ordinaria",
    "valor_hora_por_jornada",
    "calcular_aguinaldo",
    "calcular_bono_vacacional",
    "calcular_vacaciones",
    "calcular_prestaciones",
    "calcular_indemnizacion",
    "calcular_preaviso",
    "antiguedad_en_anos",
    "meses_y_dias_entre",
    "dias_vacaciones_pendientes",
    "resumen_liquidacion",
    "calcular_monto_cuota",
    "plan_de_pagos",
    "cuota_a_descontar",
    "calcular_descuento",
    "aplicar_descuento",
    "validar_solicitud",
    "monto_maximo_otorgable",
    "lineas_recibo",
    "resumen_costo_empleador",
]
