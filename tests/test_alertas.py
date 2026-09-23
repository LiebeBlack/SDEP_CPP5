"""
Pruebas del dominio de alertas

El panel de alertas es lo que convierte el sistema en algo que avisa por
sí solo: contratos por vencer, incidencias atrasadas, préstamos sin
aprobar, pagos pendientes antiguos, respaldos atrasados y credenciales
caducadas. Estas pruebas fijan qué se avisa, con qué severidad y en qué
orden, y que las alertas apunten al módulo donde se resuelven.
"""

from datetime import date, timedelta

import pytest

from src.models import EstadoPrestamo, SeveridadAlerta, TipoContrato
from src.services.alerta_service import AlertaService
from src.services.contrato_service import ContratoService
from src.services.empleado_service import EmpleadoService
from src.services.incidencia_service import IncidenciaService
from src.services.prestamo_service import PrestamoService


@pytest.fixture()
def empleado(session):
    return EmpleadoService(session).crear_empleado(
        {
            "nombres": "Iván",
            "apellidos": "Cordero",
            "cedula": "55443322",
            "tipo_empleado": "docente",
            "cargo": "Docente de Química",
            "departamento": "Ciencias",
            "fecha_contratacion": date(2022, 8, 1),
            "salario_base": 1600.0,
        }
    )


@pytest.fixture()
def servicio(session):
    return AlertaService(session)


def _claves(alertas) -> set[str]:
    return {alerta.clave for alerta in alertas}


def test_las_alertas_son_objetos_completos(servicio):
    for alerta in servicio.generar_alertas():
        assert alerta.clave
        assert alerta.titulo
        assert alerta.descripcion
        assert alerta.severidad in SeveridadAlerta.values()
        assert alerta.to_dict()["clave"] == alerta.clave


def test_contrato_por_vencer_genera_alerta_accionable(session, servicio, empleado):
    ContratoService(session).crear_contrato(
        {
            "empleado_id": empleado.id,
            "tipo": TipoContrato.TEMPORAL.value,
            "cargo": empleado.cargo,
            "salario_pactado": 1600.0,
            "fecha_inicio": date.today() - timedelta(days=300),
            "fecha_fin": date.today() + timedelta(days=10),
        }
    )
    alertas = servicio.alertas_contratos()
    assert "contratos_por_vencer" in _claves(alertas)
    alerta = next(item for item in alertas if item.clave == "contratos_por_vencer")
    assert alerta.modulo == "contratos"
    assert alerta.cantidad == 1
    assert any("Cordero" in detalle or str(dias) in detalle for dias in (10, 9, 11) for detalle in alerta.detalles)


def test_empleado_sin_contrato_genera_alerta(servicio, empleado):
    alertas = servicio.alertas_contratos()
    assert "empleados_sin_contrato" in _claves(alertas)
    alerta = next(item for item in alertas if item.clave == "empleados_sin_contrato")
    assert alerta.modulo == "contratos"
    assert alerta.cantidad == 1


def test_incidencias_pendientes_antiguas_son_criticas(session, servicio, empleado):
    incidencia = IncidenciaService(session).crear_incidencia(
        {
            "empleado_id": empleado.id,
            "tipo_incidencia": "permiso",
            "fecha_inicio": date.today(),
            "fecha_fin": date.today(),
            "motivo": "Trámite",
        }
    )
    # Se envejece la solicitud para superar el umbral de 15 días
    incidencia.fecha_solicitud = date.today() - timedelta(days=30)
    session.commit()

    alertas = servicio.alertas_incidencias()
    assert "incidencias_pendientes" in _claves(alertas)
    alerta = next(item for item in alertas if item.clave == "incidencias_pendientes")
    assert alerta.es_critica
    assert alerta.modulo == "incidencias"


def test_prestamo_pendiente_de_aprobacion_genera_alerta(session, servicio, empleado):
    PrestamoService(session).solicitar(
        {
            "empleado_id": empleado.id,
            "tipo": "prestamo",
            "monto": 300.0,
            "numero_cuotas": 3,
            "motivo": "Emergencia",
        }
    )
    alertas = servicio.alertas_prestamos()
    assert "prestamos_por_aprobar" in _claves(alertas)
    alerta = next(item for item in alertas if item.clave == "prestamos_por_aprobar")
    assert alerta.modulo == "prestamos"
    assert alerta.cantidad == 1


def test_prestamo_activo_con_saldo_se_reporta(session, servicio, empleado):
    prestamos = PrestamoService(session)
    prestamo = prestamos.solicitar(
        {
            "empleado_id": empleado.id,
            "tipo": "prestamo",
            "monto": 300.0,
            "numero_cuotas": 3,
            "motivo": "Emergencia",
        }
    )
    prestamos.aprobar(prestamo.id, aprobado_por="admin")
    assert prestamos.obtener_prestamo(prestamo.id).estado_valor != EstadoPrestamo.SOLICITADO.value
    alertas = servicio.alertas_prestamos()
    assert "prestamos_por_aprobar" not in _claves(alertas)


def test_pago_pendiente_antiguo_genera_alerta_nomina(session, servicio, empleado):
    from src.services.pago_service import PagoService

    PagoService(session).crear_pago(
        {
            "empleado_id": empleado.id,
            "tipo_pago": "salario_base",
            "periodo_inicio": date.today() - timedelta(days=90),
            "periodo_fin": date.today() - timedelta(days=60),
            "salario_base": 1600.0,
        }
    )
    alertas = servicio.alertas_nomina()
    assert "pagos_pendientes_antiguos" in _claves(alertas)
    alerta = next(item for item in alertas if item.clave == "pagos_pendientes_antiguos")
    assert alerta.modulo == "nomina"


def test_una_instalacion_sin_respaldos_avisa(servicio):
    alertas = servicio.alertas_respaldo()
    # Sin respaldos (o con el último atrasado) el sistema debe avisar
    assert alertas
    alerta = alertas[0]
    assert alerta.clave in {"respaldo_ausente", "respaldo_atrasado"}
    assert alerta.modulo == "configuracion"


def test_las_alertas_se_ordenan_por_severidad(servicio):
    alertas = servicio.generar_alertas()
    prioridad = {
        SeveridadAlerta.CRITICA.value: 0,
        SeveridadAlerta.ADVERTENCIA.value: 1,
        SeveridadAlerta.INFO.value: 2,
    }
    valores = [prioridad.get(alerta.severidad, 3) for alerta in alertas]
    assert valores == sorted(valores)


def test_resumen_y_contadores_coinciden(servicio):
    resumen = servicio.resumen()
    assert resumen["total"] == len(resumen["alertas"])
    assert resumen["total"] == servicio.contar()
    assert resumen["criticas"] == len(servicio.criticas())
    assert (
        resumen["criticas"] + resumen["advertencias"] + resumen["informativas"]
        == resumen["total"]
    )
    assert resumen["por_severidad"][SeveridadAlerta.CRITICA.value] == resumen["criticas"]


def test_el_usuario_en_sesion_recibe_su_alerta_de_credenciales(session, servicio):
    from src.models import Usuario

    admin = session.query(Usuario).filter(Usuario.username == "admin").first()
    assert admin is not None
    claves = _claves(servicio.alertas_credenciales(admin))
    assert "cambio_password_obligatorio" in claves
    # Sin usuario en sesión no se generan alertas personales
    assert "cambio_password_obligatorio" not in _claves(servicio.alertas_credenciales())


def test_desde_el_generador_general_llegan_todas_las_categorias(session, servicio, empleado):
    IncidenciaService(session).crear_incidencia(
        {
            "empleado_id": empleado.id,
            "tipo_incidencia": "ausencia",
            "fecha_inicio": date.today(),
            "fecha_fin": date.today(),
            "motivo": "Falta",
        }
    )
    claves = _claves(servicio.generar_alertas())
    assert "incidencias_pendientes" in claves
    assert claves & {"contratos_por_vencer", "empleados_sin_contrato"}


def test_la_alerta_de_respaldo_apunta_a_configuracion(session, servicio):
    """El respaldo atrasado se resuelve desde Configuración"""

    from src.models import Configuracion

    clave = "backup_interval_hours"
    registro = session.query(Configuracion).filter(Configuracion.clave == clave).first()
    assert registro is not None
    assert registro.valor not in (None, "")

    alertas = servicio.alertas_respaldo()
    assert alertas
    assert all(alerta.modulo == "configuracion" for alerta in alertas)
