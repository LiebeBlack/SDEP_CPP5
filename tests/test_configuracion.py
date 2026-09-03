"""Pruebas del servicio de configuración del sistema"""

import pytest

from src.services.configuracion_service import ConfiguracionService


def test_seed_de_configuracion_presente(session):
    servicio = ConfiguracionService(session)
    # Valores tipados según tipo_dato declarado en la siembra
    assert servicio.obtener_valor("porcentaje_seguro") == 4.5
    assert servicio.obtener_valor("porcentaje_pension") == 5.0
    assert servicio.obtener_valor("dias_vacaciones_anual") == 15
    assert servicio.obtener_valor("backup_enabled") is True


def test_categorias_sembradas(session):
    servicio = ConfiguracionService(session)
    general = servicio.obtener_configuracion_general()
    nomina = servicio.obtener_configuracion_nomina()
    rh = servicio.obtener_configuracion_recursos_humanos()
    assert "nombre_institucion" in general
    assert "porcentaje_seguro" in nomina
    assert "dias_vacaciones_anual" in rh


def test_actualizar_valor(session):
    servicio = ConfiguracionService(session)
    config = servicio.obtener_por_clave("nombre_institucion")
    assert config is not None

    actualizada = servicio.actualizar_configuracion(
        config.id, {"valor": "Colegio San Martín"})
    assert actualizada.valor == "Colegio San Martín"
    session.expire_all()
    assert servicio.obtener_valor("nombre_institucion") == "Colegio San Martín"


def test_actualizar_con_tipado_bool(session):
    servicio = ConfiguracionService(session)
    config = servicio.obtener_por_clave("audit_enabled")
    servicio.actualizar_configuracion(config.id, {"valor": False})
    session.expire_all()
    assert servicio.obtener_valor("audit_enabled") is False


def test_clave_duplicada_rechazada(session):
    servicio = ConfiguracionService(session)
    with pytest.raises(ValueError):
        servicio.crear_configuracion({
            "clave": "nombre_institucion",
            "valor": "Otro nombre",
            "tipo_dato": "string",
            "categoria": "general",
        })


def test_establecer_valor_crea_si_no_existe(session):
    servicio = ConfiguracionService(session)
    assert servicio.establecer_valor("nueva_clave_prueba", 42)
    session.expire_all()
    config = servicio.obtener_por_clave("nueva_clave_prueba")
    assert config is not None
    assert config.valor_typed == 42


def test_eliminar_configuracion(session):
    servicio = ConfiguracionService(session)
    config = servicio.obtener_por_clave("ruc")
    assert servicio.eliminar_configuracion(config.id)
    session.expire_all()
    assert servicio.obtener_por_clave("ruc") is None


def test_validar_datos(session):
    servicio = ConfiguracionService(session)
    errores = servicio.validar_datos_configuracion({
        "clave": "", "tipo_dato": "xml"})
    assert len(errores) >= 2
