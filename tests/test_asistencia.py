"""
Pruebas del dominio de asistencia

Comprueban que el registro de jornadas calcule horas trabajadas, tardanzas
y horas extra contra el horario del empleado, que las ausencias y los
feriados se clasifiquen solos y que las incidencias aprobadas marquen la
asistencia sin recapturar datos a mano.
"""

from datetime import date, time, timedelta

import pytest

from src.services.asistencia_service import AsistenciaService
from src.services.empleado_service import EmpleadoService
from src.services.incidencia_service import IncidenciaService

# Lunes y domingo de una semana laboral de referencia
LUNES = date(2026, 1, 5)
MARTES = date(2026, 1, 6)
DOMINGO = date(2026, 1, 11)


@pytest.fixture()
def empleado(session):
    return EmpleadoService(session).crear_empleado(
        {
            "nombres": "Lucía",
            "apellidos": "Méndez",
            "cedula": "99001122",
            "tipo_empleado": "administrativo",
            "cargo": "Secretaria académica",
            "departamento": "Secretaría",
            "fecha_contratacion": date(2021, 2, 1),
            "salario_base": 1500.0,
        }
    )


@pytest.fixture()
def servicio(session):
    return AsistenciaService(session)


def test_jornada_completa_calcula_horas_y_tipo(servicio, empleado):
    registro = servicio.registrar_jornada(
        empleado_id=empleado.id,
        fecha=LUNES,
        hora_entrada="07:00",
        hora_salida="15:00",
        registrado_por="admin",
    )
    assert registro.id is not None
    assert registro.tipo_valor == "presente"
    assert float(registro.horas_trabajadas) == pytest.approx(8.0)
    assert int(registro.minutos_tardanza or 0) == 0
    assert not registro.es_falta
    assert float(registro.total_horas_extra) == pytest.approx(0.0)


def test_entrada_tarde_marca_tardanza_tras_la_tolerancia(servicio, empleado):
    registro = servicio.registrar_jornada(
        empleado_id=empleado.id,
        fecha=LUNES,
        hora_entrada="07:30",
        hora_salida="15:00",
    )
    # Tolerancia por defecto de 10 minutos: 20 de tardanza real
    assert int(registro.minutos_tardanza) == 20
    assert registro.tipo_valor == "tardanza"
    assert registro.tiene_tardanza


def test_jornada_extendida_genera_horas_extra_diurnas(servicio, empleado):
    registro = servicio.registrar_jornada(
        empleado_id=empleado.id,
        fecha=LUNES,
        hora_entrada="07:00",
        hora_salida="18:00",
    )
    # 11 horas reales contra 8 previstas
    assert float(registro.horas_extra_diurnas) == pytest.approx(3.0)
    assert registro.tiene_horas_extra
    extra = servicio.horas_extra_periodo(empleado.id, LUNES, LUNES)
    assert float(extra.diurnas) == pytest.approx(3.0)
    assert float(extra.total) == pytest.approx(3.0)


def test_trabajar_en_dia_de_descanso_paga_horas_feriadas(servicio, empleado):
    registro = servicio.registrar_jornada(
        empleado_id=empleado.id,
        fecha=DOMINGO,
        hora_entrada="08:00",
        hora_salida="12:00",
    )
    assert float(registro.horas_extra_feriadas) == pytest.approx(4.0)
    assert float(registro.horas_extra_diurnas) == pytest.approx(0.0)


def test_ausencia_registrada_es_falta_sin_horas(servicio, empleado):
    registro = servicio.registrar_ausencia(
        empleado_id=empleado.id,
        fecha=MARTES,
        justificada=False,
        observaciones="No se presentó",
    )
    assert registro.tipo_valor == "ausente"
    assert registro.es_falta
    assert float(registro.horas_trabajadas) == pytest.approx(0.0)


def test_la_misma_fecha_se_actualiza_y_no_se_duplica(servicio, empleado):
    primero = servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    segundo = servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="08:00", hora_salida="16:00"
    )
    assert segundo.id == primero.id
    registros = servicio.listar_por_periodo(LUNES, LUNES)
    assert len(registros) == 1


def test_resumen_del_periodo_suma_horas_faltas_y_ausentismo(servicio, empleado):
    servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    servicio.registrar_ausencia(empleado_id=empleado.id, fecha=MARTES, justificada=False)

    resumen = servicio.resumen_periodo(empleado.id, LUNES, MARTES)
    assert resumen["dias_registrados"] == 2
    assert resumen["dias_trabajados"] == 1
    assert float(resumen["horas_trabajadas"]) == pytest.approx(8.0)
    assert resumen["faltas_injustificadas"] == 1

    totales = servicio.obtener_totales(empleado.id, LUNES, MARTES)
    assert totales["faltas_injustificadas"] == 1


def test_las_incidencias_aprobadas_marcan_la_asistencia(session, servicio, empleado):
    incidencias = IncidenciaService(session)
    incidencia = incidencias.crear_incidencia(
        {
            "empleado_id": empleado.id,
            "tipo_incidencia": "vacaciones",
            "fecha_inicio": LUNES,
            "fecha_fin": MARTES,
            "motivo": "Vacaciones anuales",
        }
    )
    assert incidencias.aprobar_incidencia(incidencia.id, aprobado_por="admin")

    marcados = servicio.aplicar_incidencias_aprobadas(empleado.id, LUNES, MARTES)
    assert marcados == 2
    registros = servicio.listar_por_empleado(empleado.id, LUNES, MARTES)
    assert {registro.tipo_valor for registro in registros} == {"vacaciones"}
    assert all(registro.justificada for registro in registros)

    # Una segunda pasada no vuelve a marcar los mismos días
    assert servicio.aplicar_incidencias_aprobadas(empleado.id, LUNES, MARTES) == 0


def test_no_se_marcan_incidencias_pendientes(session, servicio, empleado):
    IncidenciaService(session).crear_incidencia(
        {
            "empleado_id": empleado.id,
            "tipo_incidencia": "permiso",
            "fecha_inicio": LUNES,
            "fecha_fin": LUNES,
            "motivo": "Trámite",
        }
    )
    assert servicio.aplicar_incidencias_aprobadas(empleado.id, LUNES, LUNES) == 0


def test_dias_trabajados_no_cuentan_ausencias(servicio, empleado):
    servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    servicio.registrar_ausencia(empleado_id=empleado.id, fecha=MARTES, justificada=True)
    assert servicio.dias_trabajados_periodo(empleado.id, LUNES, MARTES) == 1


def test_estadisticas_de_asistencia_del_periodo(servicio, empleado):
    servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    servicio.registrar_ausencia(empleado_id=empleado.id, fecha=MARTES, justificada=False)
    estadisticas = servicio.obtener_estadisticas(LUNES, MARTES)
    assert estadisticas["total_registros"] == 2
    assert estadisticas["faltas"] == 1


def test_registro_de_jornada_invalido(servicio, empleado):
    with pytest.raises(ValueError):
        servicio.registrar_jornada(empleado_id=empleado.id, fecha=None)


def test_validacion_de_datos_de_asistencia(servicio, empleado):
    assert servicio.validar_datos_asistencia({}) != []
    assert servicio.validar_datos_asistencia(
        {"empleado_id": empleado.id, "fecha": LUNES, "hora_entrada": "25:99"}
    ) != []
    assert (
        servicio.validar_datos_asistencia(
            {
                "empleado_id": empleado.id,
                "fecha": LUNES,
                "hora_entrada": "07:00",
                "hora_salida": "15:00",
            }
        )
        == []
    )


def test_actualizar_y_eliminar_asistencia(servicio, empleado):
    registro = servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    actualizado = servicio.actualizar_asistencia(
        registro.id, {"hora_salida": "17:00", "tipo": "presente"}
    )
    assert float(actualizado.horas_trabajadas) == pytest.approx(10.0)

    assert servicio.obtener_asistencia(registro.id) is not None
    assert servicio.eliminar_asistencia(registro.id)
    assert servicio.obtener_asistencia(registro.id) is None


def test_listado_de_faltas_y_tardanzas(servicio, empleado):
    servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:45", hora_salida="15:00"
    )
    servicio.registrar_ausencia(empleado_id=empleado.id, fecha=MARTES, justificada=False)

    assert len(servicio.listar_faltas(LUNES, MARTES)) == 1
    assert len(servicio.listar_tardanzas(LUNES, MARTES)) == 1


def test_empleados_sin_registro_del_dia(servicio, empleado):
    pendientes = servicio.empleados_sin_registro(LUNES)
    assert empleado.id in [item.id for item in pendientes]
    servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="07:00", hora_salida="15:00"
    )
    pendientes = servicio.empleados_sin_registro(LUNES)
    assert empleado.id not in [item.id for item in pendientes]


def test_horario_del_empleado_define_la_jornada_prevista(session, servicio, empleado):
    """Con horario cargado, la jornada prevista y la tolerancia son las suyas"""
    from src.models import Horario, TipoJornada

    session.add(
        Horario(
            empleado_id=empleado.id,
            dia_semana=LUNES.weekday(),
            hora_inicio=time(8, 0),
            hora_fin=time(16, 0),
            descanso_minutos=60,
            tolerancia_minutos=5,
            tipo_jornada=TipoJornada.NOCTURNA.value,
            activo=1,
        )
    )
    session.commit()

    registro = servicio.registrar_jornada(
        empleado_id=empleado.id, fecha=LUNES, hora_entrada="08:10", hora_salida="17:30"
    )
    # 9.5 horas reales - 1 hora de descanso = 8.5; previstas 7 (8 h - 1 de descanso)
    assert int(registro.minutos_tardanza) == 5
    # La jornada nocturna clasifica el exceso como hora nocturna
    assert float(registro.horas_extra_nocturnas) > 0


def test_alerta_de_exceso_de_horas_extra_semanales(servicio, empleado):
    """Cuatro jornadas de 12 horas superan el tope semanal configurado"""
    for dia in (LUNES, MARTES, LUNES + timedelta(days=2), LUNES + timedelta(days=3)):
        servicio.registrar_jornada(
            empleado_id=empleado.id,
            fecha=dia,
            hora_entrada="07:00",
            hora_salida="19:00",
        )
    excesos = servicio.empleados_con_exceso_horas(
        LUNES, LUNES + timedelta(days=6)
    )
    assert any(item["empleado_id"] == empleado.id for item in excesos)
    assert all(item["horas_extra"] > item["limite"] for item in excesos)
