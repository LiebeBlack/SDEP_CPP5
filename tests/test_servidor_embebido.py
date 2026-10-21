"""
Pruebas del servidor central embebido en la aplicación de escritorio

Cubren el arranque real sobre un puerto libre, la creación de las cuentas
iniciales, el alta de este equipo como puesto cliente, el respeto a un
servidor remoto ya configurado y el caso de puerto ocupado. Cada prueba usa
un directorio temporal distinto para no compartir la base central.
"""

import json
import urllib.request

import pytest

from sync_agent.servidor_embebido import (
    CLAVE_SERVIDOR_AUTO,
    ESTADO_ACTIVO,
    ESTADO_DETENIDO,
    ESTADO_OCUPADO,
    ServidorEmbebido,
    preferencia_servidor,
)


@pytest.fixture()
def servidor(tmp_path, entorno_sync):
    """Nodo central aislado (base y blobs en el directorio temporal)"""
    nodo = ServidorEmbebido(directorio=tmp_path / "nodo", puerto=0)
    yield nodo
    nodo.detener()


def test_arranca_y_responde_el_ping(servidor):
    estado = servidor.iniciar(esperar=True)
    assert estado["estado"] == ESTADO_ACTIVO
    assert estado["puerto"] > 0

    with urllib.request.urlopen(f"{estado['url_local']}/api/v1/ping", timeout=5) as respuesta:
        datos = json.loads(respuesta.read().decode("utf-8"))
    assert datos["servidor"] == "nodo-central-sincronizacion"
    assert "empleados" in datos["tablas"]

    servidor.detener()
    assert servidor.estado()["estado"] == ESTADO_DETENIDO


def test_auto_configura_usuarios_y_puesto_cliente(servidor, tmp_path):
    estado = servidor.iniciar(esperar=True)
    assert estado["estado"] == ESTADO_ACTIVO
    assert estado["usuarios_creados"] is True
    assert estado["cliente_configurado"] is True

    from sync_agent import config as config_sync

    config = config_sync.cargar()
    assert config.habilitado is True
    assert config.url_servidor == estado["url_local"]
    assert config.token
    assert config.dispositivo_id

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.models import Usuario

    motor = create_engine(f"sqlite:///{(tmp_path / 'nodo' / 'sync_central.db').as_posix()}")
    try:
        with sessionmaker(bind=motor)() as sesion:
            usuarios = {usuario.username for usuario in sesion.query(Usuario).all()}
    finally:
        motor.dispose()
    assert {"admin", "manager", "user", "viewer"} <= usuarios


def test_el_telefono_entra_con_la_cuenta_del_escritorio(servidor, session):
    """El nodo central copia las cuentas locales y el móvil usa esa clave"""
    estado = servidor.iniciar(esperar=True)
    peticion = urllib.request.Request(
        f"{estado['url_local']}/api/v1/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(peticion, timeout=5) as respuesta:
        datos = json.loads(respuesta.read().decode("utf-8"))
    assert datos["username"] == "admin"
    assert datos["sesion_token"]


def test_el_nodo_local_reemplaza_un_destino_remoto(servidor):
    """Si este equipo pasa a ser el servidor, deja de apuntar a otro nodo"""
    from sync_agent import config as config_sync

    config_sync.guardar(
        habilitado=True,
        url_servidor="http://otro-equipo:8765",
        token="token-remoto",
        dispositivo_id="equipo-remoto",
    )

    estado = servidor.iniciar(esperar=True)
    assert estado["estado"] == ESTADO_ACTIVO
    assert estado["cliente_configurado"] is True

    actual = config_sync.cargar()
    assert actual.url_servidor == estado["url_local"]
    assert actual.token != "token-remoto"
    assert actual.dispositivo_id != "equipo-remoto"


def test_reiniciar_reutiliza_el_dispositivo_del_puesto(servidor):
    from sync_agent import config as config_sync

    assert servidor.iniciar(esperar=True)["estado"] == ESTADO_ACTIVO
    primero = config_sync.cargar()
    servidor.detener()

    assert servidor.iniciar(esperar=True)["estado"] == ESTADO_ACTIVO
    segundo = config_sync.cargar()
    assert segundo.dispositivo_id == primero.dispositivo_id
    assert segundo.token == primero.token


def test_puerto_ocupado_se_informa_y_el_primero_sigue_activo(tmp_path, entorno_sync):
    primero = ServidorEmbebido(directorio=tmp_path / "primero", puerto=0)
    segundo = None
    try:
        activo = primero.iniciar(esperar=True)
        assert activo["estado"] == ESTADO_ACTIVO

        segundo = ServidorEmbebido(directorio=tmp_path / "segundo", puerto=activo["puerto"])
        ocupado = segundo.iniciar(esperar=True, timeout=10)
        assert ocupado["estado"] == ESTADO_OCUPADO
        assert str(activo["puerto"]) in str(ocupado["error"])
        assert primero.estado()["estado"] == ESTADO_ACTIVO
    finally:
        if segundo is not None:
            segundo.detener()
        primero.detener()


def test_preferencia_se_pregunta_solo_la_primera_vez(entorno_sync):
    from src.config import settings

    assert preferencia_servidor() is None
    settings.set_config_value(CLAVE_SERVIDOR_AUTO, True)
    assert preferencia_servidor() is True
    settings.set_config_value(CLAVE_SERVIDOR_AUTO, False)
    assert preferencia_servidor() is False
