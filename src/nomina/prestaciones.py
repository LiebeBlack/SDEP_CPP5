"""
Cálculo de prestaciones y beneficios proporcionales

Agrupa los conceptos que se pagan al empleado además del salario:
aguinaldo, bono vacacional, vacaciones no disfrutadas y prestaciones
acumuladas por antigüedad. Todos se calculan de forma proporcional al
tiempo de servicio transcurrido.
"""

from datetime import date
from decimal import Decimal

from .tipos import CERO, Dinero, redondear

DIAS_MES = Decimal(30)
MESES_ANO = 12
DIAS_ANO = Decimal(360)


def meses_y_dias_entre(inicio: date, fin: date) -> tuple[int, int]:
    """
    Meses y días completos transcurridos entre dos fechas

    Usa meses calendario reales (no días divididos entre 30), que es lo
    que espera un cálculo de antigüedad para prestaciones.
    """
    if fin < inicio:
        return 0, 0
    meses = (fin.year - inicio.year) * 12 + (fin.month - inicio.month)
    if fin.day < inicio.day:
        meses -= 1
    if meses < 0:
        meses = 0
    # Fecha del último aniversario mensual cumplido
    anio = inicio.year + (inicio.month - 1 + meses) // 12
    mes = (inicio.month - 1 + meses) % 12 + 1
    dia = min(inicio.day, 28) if mes == 2 else inicio.day
    try:
        aniversario = date(anio, mes, dia)
    except ValueError:
        aniversario = date(anio, mes, 28)
    dias = max(0, (fin - aniversario).days)
    return meses, dias


def antiguedad_en_anos(inicio: date, fin: date) -> Decimal:
    """
    Antigüedad expresada en años con dos decimales

    Se calcula sobre meses y días reales para que las prestaciones de
    períodos parciales queden prorrateadas correctamente.
    """
    meses, dias = meses_y_dias_entre(inicio, fin)
    return (Decimal(meses) / Decimal(MESES_ANO) + Decimal(dias) / DIAS_ANO).quantize(
        Decimal("0.01")
    )


def dias_proporcionales(dias_ano: Dinero, meses: int, dias: int = 0) -> Dinero:
    """
    Días de un beneficio anual proporcionales al tiempo servido

    Un empleado con 5 meses y 15 días de servicio acumula
    dias_ano * (5/12) + la parte diaria correspondiente.
    """
    if dias_ano <= CERO:
        return CERO
    proporcion = Decimal(meses) / Decimal(MESES_ANO) + Decimal(dias) / DIAS_ANO
    return redondear(dias_ano * proporcion)


def calcular_aguinaldo(
    salario_mensual: Dinero,
    meses_servicio: int,
    dias_servicio: int,
    dias_aguinaldo_anual: Dinero,
) -> Dinero:
    """
    Aguinaldo proporcional al tiempo servido en el año

    Equivale a los días de aguinaldo que corresponden al período,
    valorados al salario diario del empleado.
    """
    if salario_mensual <= CERO:
        return CERO
    dias = dias_proporcionales(dias_aguinaldo_anual, meses_servicio, dias_servicio)
    return redondear(dias * salario_mensual / DIAS_MES)


def calcular_bono_vacacional(
    salario_mensual: Dinero,
    meses_servicio: int,
    dias_servicio: int,
    dias_bono_anual: Dinero,
) -> Dinero:
    """Bono vacacional proporcional al tiempo servido en el año"""
    if salario_mensual <= CERO:
        return CERO
    dias = dias_proporcionales(dias_bono_anual, meses_servicio, dias_servicio)
    return redondear(dias * salario_mensual / DIAS_MES)


def calcular_vacaciones(
    salario_mensual: Dinero,
    dias_pendientes: Dinero,
) -> Dinero:
    """
    Pago de vacaciones no disfrutadas

    Se valoran los días pendientes al salario diario vigente.
    """
    if salario_mensual <= CERO or dias_pendientes <= CERO:
        return CERO
    return redondear(dias_pendientes * salario_mensual / DIAS_MES)


def calcular_prestaciones(
    salario_mensual: Dinero,
    anos_servicio: Dinero,
    dias_por_ano: Dinero,
) -> Dinero:
    """
    Prestaciones acumuladas por antigüedad

    Corresponde a los días por año de servicio valorados al salario
    diario actual del empleado.
    """
    if salario_mensual <= CERO or anos_servicio <= CERO or dias_por_ano <= CERO:
        return CERO
    dias = anos_servicio * dias_por_ano
    return redondear(dias * salario_mensual / DIAS_MES)


def calcular_indemnizacion(
    salario_mensual: Dinero,
    anos_servicio: Dinero,
    dias_por_ano: Dinero,
) -> Dinero:
    """
    Indemnización por terminación de la relación laboral

    Se calcula con el mismo criterio de días por año de servicio que
    las prestaciones, pero se registra por separado para que la
    liquidación muestre ambos conceptos.
    """
    return calcular_prestaciones(salario_mensual, anos_servicio, dias_por_ano)


def calcular_preaviso(salario_mensual: Dinero, dias_preaviso: Dinero) -> Dinero:
    """Pago del preaviso omitido, valorado en días de salario"""
    if salario_mensual <= CERO or dias_preaviso <= CERO:
        return CERO
    return redondear(dias_preaviso * salario_mensual / DIAS_MES)
