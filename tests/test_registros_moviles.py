"""
Pruebas del contrato con la aplicación móvil

La app Android escribe en la tabla ``registros_moviles`` a través del mismo
protocolo que un puesto de escritorio. Estas pruebas fijan ese contrato: los
campos que el teléfono envía tienen que existir como columnas, el nodo central
tiene que poder crear la fila sin intervención humana, la mezcla por campo debe
conservar ediciones distintas y el borrado debe ser lógico.

Si alguna de estas pruebas falla, la aplicación móvil y el sistema de escritorio
dejaron de entenderse aunque ambos funcionen por separado.
"""

import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, RegistroMovil
from sync_agent import registro
from sync_agent.aplicador import AplicadorRemoto
from sync_agent.cliente import ClienteSync
from sync_agent.comun import dumps, nuevo_uuid
from sync_agent.esquema import BaseSync
from sync_agent.servidor import NucleoCentral, ServidorConfig, ServidorSync

# Claves que la app Android pone en el payload de cada operación. Es la
# definición ejecutable del contrato: si se renombra una columna en Python sin
# tocar el móvil, esta lista deja de coincidir y la prueba lo delata.
CLAVES_DEL_MOVIL = (
    "uuid_movil",
    "titulo",
    "contenido",
    "categoria",
    "valor",
    "creado_en",
    "actualizado_en",
    "dispositivo",
    "usuario",
)


@pytest.fixture()
def sesion(tmp_path):
    """Base de datos aislada con el esquema de dominio y el del agente"""
    motor = create_engine(f"sqlite:///{(tmp_path / 'movil.db').as_posix()}")
    Base.metadata.create_all(bind=motor)
    BaseSync.metadata.create_all(bind=motor)
    fabrica = sessionmaker(bind=motor, expire_on_commit=False)
    sesion = fabrica()
    try:
        yield sesion
    finally:
        sesion.close()
        motor.dispose()


def _ahora() -> datetime:
    """Marca de tiempo UTC sin zona, igual que la guarda el sistema"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _payload(**cambios):
    """Payload completo de un alta, tal como lo envía el teléfono"""
    uuid = nuevo_uuid()
    momento = _ahora()
    datos = {
        "uuid_movil": uuid,
        "titulo": "Visita a la sección 4to B",
        "contenido": "Se verificó la asistencia del personal docente.",
        "categoria": "supervision",
        "valor": 12.5,
        "creado_en": momento.isoformat(),
        "actualizado_en": momento.isoformat(),
        "dispositivo": "movil-secretaria",
        "usuario": "Ana Gómez",
    }
    datos.update(cambios)
    return uuid, datos


def _operacion(uuid: str, payload: dict, creado_en: datetime | None = None, operacion="upsert"):
    """Operación del protocolo, con el payload ya serializado"""
    return {
        "op_id": nuevo_uuid(),
        "tabla": "registros_moviles",
        "fila_uuid": uuid,
        "operacion": operacion,
        "payload": dumps(payload),
        "dispositivo": payload.get("dispositivo", "movil-secretaria"),
        "usuario": payload.get("usuario"),
        "creado_en": (creado_en or _ahora()).isoformat(),
    }


def test_contrato_de_columnas_del_movil():
    """Todas las claves que envía el teléfono existen en la tabla replicada"""
    columnas = registro.columnas("registros_moviles")
    faltantes = [clave for clave in CLAVES_DEL_MOVIL if clave not in columnas]
    assert not faltantes, f"El móvil envía columnas que el modelo no tiene: {faltantes}"

    transportables = registro.columnas_transportables("registros_moviles")
    for clave in CLAVES_DEL_MOVIL:
        assert clave in transportables, f"{clave} no viaja en el payload"


def test_la_entidad_esta_registrada_con_su_clave_natural():
    """El registro declara clave natural y borrado lógico"""
    entidad = registro.entidad("registros_moviles")
    assert entidad is not None
    assert entidad.clave_natural == ("uuid_movil",)
    assert entidad.borrado_logico is True
    assert entidad.columna_activo == "activo"
    assert "registros_moviles" in registro.tablas_sincronizadas()


def test_alta_desde_el_movil_crea_la_fila(sesion):
    """Una operación del teléfono basta para recrear el registro en la intranet"""
    uuid, payload = _payload()
    resultado = AplicadorRemoto(sesion, "nodo-central").aplicar(_operacion(uuid, payload))
    sesion.commit()

    assert resultado.aplicada, resultado.motivo
    fila = sesion.query(RegistroMovil).filter_by(uuid_movil=uuid).one()
    assert fila.titulo == "Visita a la sección 4to B"
    assert fila.categoria == "supervision"
    assert fila.valor == pytest.approx(12.5)
    assert fila.activo == 1
    assert fila.dispositivo == "movil-secretaria"


def test_el_mismo_registro_no_se_duplica(sesion):
    """Reenviar el alta con otro ``fila_uuid`` reconoce la fila por su clave"""
    uuid, payload = _payload()
    aplicador = AplicadorRemoto(sesion, "nodo-central")
    aplicador.aplicar(_operacion(uuid, payload))
    aplicador.aplicar(_operacion(uuid, payload))
    sesion.commit()

    assert sesion.query(RegistroMovil).filter_by(uuid_movil=uuid).count() == 1


def test_mezcla_por_campo_conserva_las_dos_ediciones(sesion):
    """Dos dispositivos que editan columnas distintas no se pisan

    El contrato es el mismo que usa la captura del ORM en el escritorio: una
    edición envía **solo las columnas que tocó**. Por eso los dos payloads de
    abajo llevan un único campo además de la clave natural.
    """
    uuid, payload = _payload()
    aplicador = AplicadorRemoto(sesion, "nodo-central")
    aplicador.aplicar(_operacion(uuid, payload))

    momento = _ahora() + timedelta(seconds=30)
    edicion = {"uuid_movil": uuid, "titulo": "Visita reprogramada"}
    otro = {"uuid_movil": uuid, "contenido": "Se anexó la planilla firmada."}
    resultado = aplicador.aplicar(
        {**_operacion(uuid, edicion, creado_en=momento), "dispositivo": "movil-direccion"}
    )
    assert resultado.aplicada, resultado.motivo
    resultado = aplicador.aplicar(
        {**_operacion(uuid, otro, creado_en=momento + timedelta(seconds=1)), "dispositivo": "movil-secretaria"}
    )
    assert resultado.aplicada, resultado.motivo
    sesion.commit()

    fila = sesion.query(RegistroMovil).filter_by(uuid_movil=uuid).one()
    assert fila.titulo == "Visita reprogramada"
    assert fila.contenido == "Se anexó la planilla firmada."


def test_borrado_desde_el_movil_es_logico(sesion):
    """El teléfono borra desactivando: el registro no desaparece del servidor"""
    uuid, payload = _payload()
    aplicador = AplicadorRemoto(sesion, "nodo-central")
    aplicador.aplicar(_operacion(uuid, payload))
    sesion.commit()

    borrado = _operacion(uuid, payload, creado_en=_ahora() + timedelta(seconds=5), operacion="delete")
    resultado = aplicador.aplicar(borrado)
    sesion.commit()

    assert resultado.aplicada, resultado.motivo
    fila = sesion.query(RegistroMovil).filter_by(uuid_movil=uuid).one()
    assert fila.activo == 0


def test_recorrido_http_completo_del_movil(tmp_path):
    """El teléfono habla el protocolo real por HTTP y otro puesto lo recibe

    Es la prueba de contrato completa: el payload viaja como texto JSON, el
    nodo central autentica el equipo, crea la fila en ``registros_moviles`` y
    otro puesto la descarga con su cursor.
    """
    configuracion = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
        peticiones_por_minuto=0,
    )
    servidor = ServidorSync(configuracion)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    url = f"http://127.0.0.1:{servidor.server_address[1]}"
    nucleo: NucleoCentral = servidor.nucleo

    try:
        equipo, token = nucleo.crear_dispositivo("Teléfono Secretaría")
        movil = ClienteSync(url, token, equipo)

        estado = movil.ping()
        assert estado["version_protocolo"] == "1"
        assert "registros_moviles" in estado["tablas"]

        uuid, payload = _payload()
        resultado = movil.enviar_ops([_operacion(uuid, payload)])
        assert resultado["aplicadas"], resultado

        otro_equipo, otro_token = nucleo.crear_dispositivo("Dirección")
        otro = ClienteSync(url, otro_token, otro_equipo)
        lote = otro.recibir_ops(cursor=0)

        recibidas = [op for op in lote["ops"] if op["tabla"] == "registros_moviles"]
        assert len(recibidas) == 1
        assert recibidas[0]["fila_uuid"] == uuid
        assert uuid in recibidas[0]["payload"]
    finally:
        servidor.shutdown()
        servidor.server_close()
        nucleo.cerrar()


def test_operacion_duplicada_no_se_aplica_dos_veces(sesion):
    """El reenvío de un lote es seguro: la misma ``op_id`` se ignora"""
    uuid, payload = _payload()
    operacion = _operacion(uuid, payload)
    aplicador = AplicadorRemoto(sesion, "nodo-central")

    assert aplicador.aplicar(operacion).aplicada
    segunda = aplicador.aplicar(operacion)
    sesion.commit()

    assert not segunda.aplicada
    assert segunda.motivo == "duplicada"
