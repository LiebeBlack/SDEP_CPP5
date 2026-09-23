"""
Pruebas de las utilidades de jornada laboral

Son cálculos puros sobre horas: turnos que cruzan la medianoche, descuento
del descanso, tolerancia de entrada, clasificación de horas extra y
reconocimiento de feriados y días de descanso.
"""

from datetime import date, time
from decimal import Decimal

import pytest

from src.utils.jornada import (
    DIAS_DESCANSO_POR_DEFECTO,
    calcular_horas_trabajadas,
    calcular_minutos_tardanza,
    clasificar_horas_extra,
    es_fin_de_semana,
    es_feriado,
    formatear_hora,
    formatear_minutos,
    minutos_entre,
    parsear_hora,
    tipo_segun_horas,
)

SABADO = date(2026, 1, 10)
DOMINGO = date(2026, 1, 11)
LUNES = date(2026, 1, 5)


def test_minutos_entre_turnos_del_dia_y_nocturnos():
    assert minutos_entre(time(7, 0), time(15, 0)) == 480
    assert minutos_entre(time(7, 15), time(7, 45)) == 30
    # Un turno que termina igual o antes del inicio cruza la medianoche
    assert minutos_entre(time(22, 0), time(6, 0)) == 480
    assert minutos_entre(time(8, 0), time(8, 0)) == 1440


def test_minutos_entre_sin_horas_devuelve_cero():
    assert minutos_entre(None, time(8, 0)) == 0
    assert minutos_entre(time(8, 0), None) == 0


def test_horas_trabajadas_descuentan_el_descanso():
    assert calcular_horas_trabajadas(time(8, 0), time(17, 0), 60) == Decimal("8.00")
    assert calcular_horas_trabajadas(time(8, 0), time(8, 30)) == Decimal("0.50")
    # El descanso no puede dejar horas negativas
    assert calcular_horas_trabajadas(time(8, 0), time(8, 10), 60) == Decimal("0.00")
    assert calcular_horas_trabajadas(None, time(8, 0)) == Decimal("0.00")


def test_tardanza_respeta_la_tolerancia():
    assert calcular_minutos_tardanza(time(7, 25), time(7, 0), 10) == 15
    assert calcular_minutos_tardanza(time(7, 5), time(7, 0), 10) == 0
    assert calcular_minutos_tardanza(time(6, 50), time(7, 0), 10) == 0
    assert calcular_minutos_tardanza(None, time(7, 0)) == 0


def test_fin_de_semana_con_dias_de_descanso_configurables():
    assert es_fin_de_semana(SABADO)
    assert es_fin_de_semana(DOMINGO)
    assert not es_fin_de_semana(LUNES)
    # Una jornada de lunes a viernes con descanso solo el domingo
    assert not es_fin_de_semana(SABADO, (6,))
    assert es_fin_de_semana(DOMINGO, (6,))
    assert DIAS_DESCANSO_POR_DEFECTO == (5, 6)


def test_feriados_desde_lista_o_json():
    assert es_feriado(date(2026, 9, 15), ["2026-09-15"])
    assert es_feriado(date(2026, 9, 15), '["2026-09-15", "2026-12-25"]')
    assert not es_feriado(date(2026, 9, 16), ["2026-09-15"])
    assert not es_feriado(date(2026, 9, 15), None)


def test_horas_extra_por_tipo_de_jornada():
    diurna = clasificar_horas_extra(Decimal(10), Decimal(8), "diurna")
    assert diurna.diurnas == Decimal("2.00")
    assert diurna.nocturnas == Decimal("0.00")

    nocturna = clasificar_horas_extra(Decimal(9), Decimal(8), "nocturna")
    assert nocturna.nocturnas == Decimal("1.00")

    mixta = clasificar_horas_extra(Decimal(9), Decimal(8), "mixta")
    assert mixta.nocturnas == Decimal("1.00")


def test_feriado_o_descanso_laborado_es_hora_feriada():
    # En un feriado o día de descanso no hay jornada prevista que cumplir:
    # el llamador pasa 0 y todo lo trabajado se paga como hora feriada.
    feriado = clasificar_horas_extra(
        Decimal(6), Decimal(0), "diurna", dia_feriado=True
    )
    assert feriado.feriadas == Decimal("6.00")
    assert feriado.total == Decimal("6.00")

    descanso = clasificar_horas_extra(
        Decimal(4), Decimal(0), "diurna", dia_descanso=True
    )
    assert descanso.feriadas == Decimal("4.00")


def test_sin_exceso_de_horas_no_hay_extra():
    sin_extra = clasificar_horas_extra(Decimal(8), Decimal(8), "diurna")
    assert not sin_extra.hay_horas
    assert sin_extra.total == Decimal("0.00")


def test_tipo_de_asistencia_deducido():
    assert tipo_segun_horas(Decimal(8), 0) == "presente"
    assert tipo_segun_horas(Decimal(8), 15) == "tardanza"
    assert tipo_segun_horas(Decimal(0), 0) == "ausente"


def test_parseo_de_horas_de_cualquier_procedencia():
    assert parsear_hora("07:30") == time(7, 30)
    assert parsear_hora("7") == time(7, 0)
    assert parsear_hora("07:30:45") == time(7, 30)
    assert parsear_hora("2026-01-05T08:15:00") == time(8, 15)
    assert parsear_hora(time(9, 45)) == time(9, 45)
    assert parsear_hora("25:99") is None
    assert parsear_hora("no es hora") is None
    assert parsear_hora(None, time(8, 0)) == time(8, 0)
    assert parsear_hora("07:00") == time(7, 0)


def test_formato_de_horas_y_minutos():
    assert formatear_hora(time(7, 5)) == "07:05"
    assert formatear_hora(None) == ""
    assert formatear_minutos(90) == "1h 30m"
    assert formatear_minutos(0) == "0h 00m"
    assert formatear_minutos(-5) == "0h 00m"


@pytest.mark.parametrize(
    ("entrada", "salida", "esperado"),
    [
        (time(7, 0), time(15, 0), Decimal("8.00")),
        (time(8, 30), time(12, 30), Decimal("4.00")),
        (time(22, 0), time(5, 0), Decimal("7.00")),
    ],
)
def test_jornadas_tipicas(entrada, salida, esperado):
    assert calcular_horas_trabajadas(entrada, salida) == esperado
