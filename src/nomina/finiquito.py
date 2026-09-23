"""
Cálculo de liquidaciones y finiquitos

Determina lo que corresponde pagar a un empleado que cesa funciones:
prestaciones acumuladas, indemnización, preaviso, vacaciones y
beneficios proporcionales, menos los anticipos pendientes.
"""

from datetime import date, datetime
from decimal import Decimal

from .prestaciones import (
    antiguedad_en_anos,
    calcular_aguinaldo,
    calcular_bono_vacacional,
    calcular_indemnizacion,
    calcular_preaviso,
    calcular_prestaciones,
    calcular_vacaciones,
    dias_proporcionales,
    meses_y_dias_entre,
)
from .tipos import (
    CERO,
    Dinero,
    EntradaFiniquito,
    ParametrosNomina,
    ResultadoFiniquito,
    redondear,
)

DIAS_MES = Decimal(30)
MESES_ANO = 12

# Motivos de egreso en los que no procede el pago del preaviso
MOTIVOS_SIN_PREAVISO = ("renuncia", "renuncia voluntaria", "jubilacion", "jubilación")


def _como_fecha(valor: object) -> date | None:
    """
    Convierte a date un valor de fecha de cualquier procedencia

    Acepta date, datetime y texto ISO (con o sin hora), que son las
    formas en que la interfaz y la base de datos entregan las fechas.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date()
        except ValueError:
            continue
    return None


def calcular_finiquito(
    entrada: EntradaFiniquito,
    parametros: ParametrosNomina | None = None,
) -> ResultadoFiniquito:
    """
    Liquidación completa de un empleado

    Args:
        entrada: Salario y fechas de la relación laboral
        parametros: Parámetros vigentes (días de prestaciones, preaviso,
            aguinaldo y bono vacacional)

    Returns:
        ResultadoFiniquito: Desglose de asignaciones y deducciones con el
        neto a pagar.
    """
    parametros = parametros or ParametrosNomina()
    salario = redondear(entrada.salario_mensual)
    ingreso = _como_fecha(entrada.fecha_ingreso)
    egreso = _como_fecha(entrada.fecha_egreso) or date.today()

    if ingreso is None or salario <= CERO:
        return ResultadoFiniquito(
            motivo=entrada.motivo,
            anticipos=redondear(entrada.anticipos_pendientes),
            otras_deducciones=redondear(entrada.otras_deducciones),
        )

    if egreso < ingreso:
        egreso = ingreso

    meses, dias = meses_y_dias_entre(ingreso, egreso)
    anos = antiguedad_en_anos(ingreso, egreso)
    meses_del_ano_en_curso = meses % MESES_ANO
    dias_del_ano_en_curso = dias if meses_del_ano_en_curso or meses == 0 else 0

    prestaciones = calcular_prestaciones(
        salario, anos, parametros.dias_prestaciones_por_ano
    )
    indemnizacion = calcular_indemnizacion(
        salario, anos, parametros.dias_prestaciones_por_ano
    )

    motivo = (entrada.motivo or "").strip().lower()
    aplica_preaviso = motivo not in MOTIVOS_SIN_PREAVISO
    preaviso = (
        calcular_preaviso(salario, parametros.dias_preaviso) if aplica_preaviso else CERO
    )

    vacaciones = calcular_vacaciones(salario, entrada.dias_vacaciones_pendientes)
    bono_vacacional = calcular_bono_vacacional(
        salario,
        meses_del_ano_en_curso,
        dias_del_ano_en_curso,
        parametros.dias_bono_vacacional,
    )

    if entrada.dias_utilidades_pendientes > CERO:
        aguinaldo = calcular_vacaciones(salario, entrada.dias_utilidades_pendientes)
    else:
        aguinaldo = calcular_aguinaldo(
            salario,
            meses_del_ano_en_curso,
            dias_del_ano_en_curso,
            parametros.dias_aguinaldo,
        )

    return ResultadoFiniquito(
        anos_servicio=anos,
        meses_servicio=meses,
        dias_servicio=dias,
        prestaciones=prestaciones,
        indemnizacion=indemnizacion,
        preaviso=preaviso,
        vacaciones=vacaciones,
        bono_vacacional=bono_vacacional,
        aguinaldo=aguinaldo,
        anticipos=redondear(entrada.anticipos_pendientes),
        otras_deducciones=redondear(entrada.otras_deducciones),
        motivo=entrada.motivo,
    )


def dias_vacaciones_pendientes(
    salario_mensual: Dinero,
    dias_vacaciones_anuales: Dinero,
    fecha_ingreso: date,
    fecha_egreso: date,
    dias_ya_disfrutados: Dinero = CERO,
    anos_servicio: Dinero | None = None,
) -> Dinero:
    """
    Días de vacaciones pendientes al momento del egreso

    Se acumulan los días del año en curso de forma proporcional y se
    suman los que quedaron de años anteriores sin disfrutar. El derecho
    a vacaciones se genera a partir del año completo de servicio.
    """
    if dias_vacaciones_anuales <= CERO:
        return CERO
    _, dias = meses_y_dias_entre(fecha_ingreso, fecha_egreso)
    meses_servicio, _ = meses_y_dias_entre(fecha_ingreso, fecha_egreso)
    if anos_servicio is None:
        anos_servicio = antiguedad_en_anos(fecha_ingreso, fecha_egreso)

    meses_del_ano_en_curso = meses_servicio % MESES_ANO
    acumulados = dias_proporcionales(
        dias_vacaciones_anuales, meses_del_ano_en_curso, dias
    )
    anos_completos = Decimal(int(anos_servicio))
    pendientes = acumulados + (dias_vacaciones_anuales * anos_completos) - dias_ya_disfrutados
    return redondear(max(CERO, pendientes))


def resumen_liquidacion(resultado: ResultadoFiniquito) -> list[tuple[str, float]]:
    """
    Conceptos de la liquidación listos para imprimir en el recibo

    Returns:
        list: Tuplas (concepto, monto) con los conceptos distintos de cero.
    """
    conceptos: list[tuple[str, Dinero]] = [
        ("Prestaciones acumuladas", resultado.prestaciones),
        ("Indemnización", resultado.indemnizacion),
        ("Preaviso", resultado.preaviso),
        ("Vacaciones no disfrutadas", resultado.vacaciones),
        ("Bono vacacional", resultado.bono_vacacional),
        ("Aguinaldo", resultado.aguinaldo),
        ("Anticipos pendientes (-)", resultado.anticipos),
        ("Otras deducciones (-)", resultado.otras_deducciones),
    ]
    return [
        (concepto, float(redondear(monto)))
        for concepto, monto in conceptos
        if redondear(monto) != CERO
    ]
