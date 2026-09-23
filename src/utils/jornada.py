"""
Utilidades de jornada laboral

Cálculos puros sobre horarios y marcas de entrada/salida: horas
trabajadas, tardanzas y clasificación de las horas extra según el tipo
de jornada y si el día es feriado o de descanso.

No accede a la base de datos ni a la interfaz, de modo que cada regla
de negocio puede probarse por separado.
"""

from datetime import date, time
from decimal import Decimal

from src.models.enums import TipoJornada
from src.nomina.tipos import CERO, HorasExtra, redondear

MINUTOS_HORA = 60
DIAS_DESCANSO_POR_DEFECTO = (5, 6)  # sábado y domingo


def minutos_entre(inicio: time, fin: time) -> int:
    """
    Minutos transcurridos entre dos horas

    Si la hora de fin es menor o igual a la de inicio se asume un turno
    que cruza la medianoche (22:00 a 06:00 son 8 horas, no 16 negativas).
    """
    if inicio is None or fin is None:
        return 0
    inicio_min = inicio.hour * MINUTOS_HORA + inicio.minute
    fin_min = fin.hour * MINUTOS_HORA + fin.minute
    if fin_min <= inicio_min:
        fin_min += 24 * MINUTOS_HORA
    return fin_min - inicio_min


def calcular_horas_trabajadas(
    hora_entrada: time | None,
    hora_salida: time | None,
    descanso_minutos: int = 0,
) -> Decimal:
    """Horas efectivas trabajadas, descontando el descanso"""
    if hora_entrada is None or hora_salida is None:
        return CERO
    minutos = minutos_entre(hora_entrada, hora_salida) - max(0, int(descanso_minutos))
    return redondear(Decimal(max(0, minutos)) / MINUTOS_HORA)


def calcular_minutos_tardanza(
    hora_entrada: time | None,
    hora_prevista: time | None,
    tolerancia_minutos: int = 0,
) -> int:
    """
    Minutos de tardanza sobre la hora prevista de entrada

    La tolerancia se descuenta del retraso: llegar dentro del margen no
    cuenta como tardanza. Llegar antes devuelve cero, nunca negativo.
    """
    if hora_entrada is None or hora_prevista is None:
        return 0
    retraso = (
        (hora_entrada.hour - hora_prevista.hour) * MINUTOS_HORA
        + (hora_entrada.minute - hora_prevista.minute)
    )
    return max(0, retraso - max(0, int(tolerancia_minutos)))


def es_fin_de_semana(fecha: date, dias_descanso: tuple[int, ...] = DIAS_DESCANSO_POR_DEFECTO) -> bool:
    """Indica si la fecha cae en un día de descanso configurado"""
    if not dias_descanso:
        return False
    return fecha.weekday() in dias_descanso


def es_feriado(fecha: date, feriados: object) -> bool:
    """
    Indica si la fecha está marcada como feriado

    Acepta una colección de fechas o textos ISO; los valores que no se
    puedan interpretar simplemente se ignoran.
    """
    if not feriados:
        return False
    if isinstance(feriados, str):
        return fecha.isoformat() in feriados
    if isinstance(feriados, (list, tuple, set, frozenset)):
        for valor in feriados:
            if str(valor).strip()[:10] == fecha.isoformat():
                return True
    return False


def clasificar_horas_extra(
    horas_trabajadas: Decimal,
    horas_previstas: Decimal,
    tipo_jornada: str = TipoJornada.DIURNA.value,
    dia_feriado: bool = False,
    dia_descanso: bool = False,
) -> HorasExtra:
    """
    Clasifica las horas extra del día según su recargo

    Un feriado o día de descanso laborado se paga como hora feriada
    (recargo del 100%); el resto se reparte entre nocturna y diurna
    según la jornada del horario.
    """
    if horas_previstas <= CERO:
        # Sin jornada prevista (feriado o descanso) todo lo trabajado es extra
        horas_extra = redondear(horas_trabajadas)
    else:
        horas_extra = redondear(max(CERO, horas_trabajadas - horas_previstas))
    if horas_extra <= CERO:
        return HorasExtra()

    if dia_feriado or dia_descanso:
        return HorasExtra(feriadas=horas_extra)
    if tipo_jornada == TipoJornada.NOCTURNA.value or tipo_jornada == TipoJornada.MIXTA.value:
        return HorasExtra(nocturnas=horas_extra)
    return HorasExtra(diurnas=horas_extra)


def tipo_segun_horas(
    horas_trabajadas: Decimal,
    minutos_tardanza: int,
) -> str:
    """
    Tipo de asistencia que corresponde a una jornada

    Sin horas trabajadas la jornada queda como ausencia; con retraso se
    marca como tardanza y, en el caso normal, como presencia.
    """
    from src.models import TipoAsistencia

    if horas_trabajadas <= CERO:
        return TipoAsistencia.AUSENTE.value
    if minutos_tardanza > 0:
        return TipoAsistencia.TARDANZA.value
    return TipoAsistencia.PRESENTE.value


def parsear_hora(valor: object, por_defecto: time | None = None) -> time | None:
    """
    Convierte a time un valor de hora de cualquier procedencia

    Acepta time, texto "HH:MM" (con o sin segundos) y texto ISO con hora.
    Devuelve el valor por defecto si no se puede interpretar.
    """
    if valor is None or valor == "":
        return por_defecto
    if isinstance(valor, time):
        return valor
    texto = str(valor).strip()
    if "T" in texto:
        texto = texto.split("T", 1)[1]
    partes = texto.split(":")
    try:
        hora = int(partes[0])
        minuto = int(partes[1]) if len(partes) > 1 else 0
    except (TypeError, ValueError, IndexError):
        return por_defecto
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        return por_defecto
    return time(hour=hora, minute=minuto)


def formatear_hora(valor: time | None) -> str:
    """Hora en formato HH:MM para mostrar en pantalla"""
    if valor is None:
        return ""
    return valor.strftime("%H:%M")


def formatear_minutos(minutos: int) -> str:
    """Minutos expresados como 'Xh Ym' para mostrar en pantalla"""
    total = max(0, int(minutos))
    return f"{total // MINUTOS_HORA}h {total % MINUTOS_HORA:02d}m"
