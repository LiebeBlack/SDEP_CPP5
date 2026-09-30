"""
Pruebas de integración del agente de sincronización

Se levanta un nodo central real (HTTP en un puerto libre, base y almacén de
binarios en un directorio temporal) y se sincroniza contra él el puesto que
representa la base de datos de la prueba. El "segundo puesto" se simula
enviando al nodo central las mismas operaciones que habría producido su
journal, de modo que se comprueba el recorrido completo:

    alta local -> journal -> nodo central -> otro puesto
    alta ajena  -> nodo central -> mezcla por campo -> fila local
"""

import threading
from datetime import datetime, timedelta

import pytest

from src.models import Documento, Empleado
from src.services.empleado_service import EmpleadoService
from sync_agent.agente import AgenteSincronizacion
from sync_agent.captura import establecer_dispositivo
from sync_agent.cliente import ClienteSync
from sync_agent.comun import dumps, hash_bytes, loads, nuevo_uuid
from sync_agent.config import cargar, guardar
from sync_agent.esquema import (
    BLOB_DISPONIBLE,
    BLOB_SUBIDO,
    CONFIRMADA,
    PENDIENTE,
    BlobSync,
    JournalOp,
    SyncId,
)
from sync_agent.servidor import NucleoCentral, ServidorConfig, ServidorSync


class Escenario:
    """Nodo central en marcha más los dos puestos que hablan con él"""

    def __init__(self, tmp_path, entorno):
        self.entorno = entorno
        config = ServidorConfig(
            url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
            dir_blobs=tmp_path / "blobs",
            host="127.0.0.1",
            puerto=0,
        )
        self.servidor = ServidorSync(config)
        self.puerto = self.servidor.server_address[1]
        self.url = f"http://127.0.0.1:{self.puerto}"
        self._hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)

    @property
    def nucleo(self) -> NucleoCentral:
        return self.servidor.nucleo

    # -- ciclo de vida -------------------------------------------------
    def __enter__(self):
        self._hilo.start()
        self.dispositivo_a, self.token_a = self.nucleo.crear_dispositivo("Puesto A")
        self.dispositivo_b, self.token_b = self.nucleo.crear_dispositivo("Puesto B")
        # El puesto que representa esta base de datos es el A
        guardar(
            habilitado=True,
            url_servidor=self.url,
            token=self.token_a,
            dispositivo_id=self.dispositivo_a,
            intervalo_segundos=5,
        )
        self.config = cargar()
        establecer_dispositivo(self.config.dispositivo_id)
        return self

    def __exit__(self, *_excepcion):
        self.servidor.shutdown()
        self.servidor.server_close()
        self._hilo.join(timeout=5)
        self.nucleo.cerrar()

    # -- utilidades ----------------------------------------------------
    def ciclo(self) -> dict:
        """Un ciclo de sincronización completo del puesto A"""
        return AgenteSincronizacion(cargar()).ciclo()

    def cliente_b(self) -> ClienteSync:
        """Cliente del puesto B (el que simula al otro equipo)"""
        return ClienteSync(self.url, self.token_b, self.dispositivo_b, timeout=5)

    def crear_empleado(self, cedula="12345678", **cambios):
        datos = {
            "nombres": "Ana",
            "apellidos": "Gómez",
            "cedula": cedula,
            "tipo_empleado": "docente",
            "cargo": "Docente",
            "salario_base": 1200.0,
        }
        datos.update(cambios)
        sesion = self.entorno.get_session()
        try:
            return EmpleadoService(sesion).crear_empleado(datos)
        finally:
            self.entorno.close_session(sesion)

    def operaciones_locales(self):
        sesion = self.entorno.new_session()
        try:
            return sesion.query(JournalOp).order_by(JournalOp.id).all()
        finally:
            self.entorno.close_session(sesion)

    def empleado_local(self, cedula):
        sesion = self.entorno.new_session()
        try:
            return sesion.query(Empleado).filter(Empleado.cedula == cedula).first()
        finally:
            self.entorno.close_session(sesion)

    def operacion_del_servidor(self):
        """Operaciones del log central vistas desde el puesto B (excluye las de B)"""
        dispositivo = self.nucleo.autenticar(self.dispositivo_b, self.token_b)
        return self.nucleo.pull(dispositivo, 0, 100)["ops"]


@pytest.fixture()
def escenario(entorno_sync, tmp_path):
    with Escenario(tmp_path, entorno_sync) as montado:
        yield montado


# ----------------------------------------------------------------------
# Recorrido completo de una operación
# ----------------------------------------------------------------------
def test_una_alta_local_llega_al_nodo_central(escenario):
    escenario.crear_empleado()
    operaciones = escenario.operaciones_locales()
    assert len(operaciones) == 1
    assert operaciones[0].estado == PENDIENTE

    resultado = escenario.ciclo()
    assert resultado["correcto"] is True, resultado.get("mensaje")

    assert escenario.operaciones_locales()[0].estado == CONFIRMADA
    recibidas = escenario.nucleo.pull(
        escenario.nucleo.autenticar(escenario.dispositivo_b, escenario.token_b), 0, 100
    )
    assert [op["op_id"] for op in recibidas["ops"]] == [operaciones[0].op_id]
    assert loads(recibidas["ops"][0]["payload"])["cedula"] == "12345678"


def test_un_ciclo_posterior_no_reenvia_lo_confirmado(escenario):
    escenario.crear_empleado()
    escenario.ciclo()
    segundo = escenario.ciclo()
    assert segundo["correcto"] is True
    assert escenario.nucleo.cursor_actual() == 1


def test_una_fila_creada_en_otro_puesto_aparece_localmente(escenario):
    cedula = "30000000"
    operacion = {
        "op_id": nuevo_uuid(),
        "tabla": "empleados",
        "fila_uuid": nuevo_uuid(),
        "operacion": "upsert",
        "payload": dumps(
            {
                "cedula": cedula,
                "nombres": "Carlos",
                "apellidos": "Rivas",
                "tipo_empleado": "administrativo",
                "cargo": "Administrativo",
                "departamento": "Administración",
                "salario_base": 800.0,
                "activo": 1,
            }
        ),
        "base_op_id": None,
        "dispositivo": escenario.dispositivo_b,
        "usuario": "otro-puesto",
        "creado_en": datetime.now().isoformat(),
    }
    escenario.cliente_b().enviar_ops([operacion])

    resultado = escenario.ciclo()
    assert resultado["correcto"] is True, resultado.get("mensaje")

    creado = escenario.empleado_local(cedula)
    assert creado is not None
    assert creado.nombres == "Carlos"
    assert creado.cargo == "Administrativo"

    # La fila recibida queda con identidad global, lista para volver a viajar
    sesion = escenario.entorno.new_session()
    try:
        fila = (
            sesion.query(SyncId)
            .filter(SyncId.tabla == "empleados", SyncId.id_local == creado.id)
            .one()
        )
        assert fila.uuid == operacion["fila_uuid"]
    finally:
        escenario.entorno.close_session(sesion)


def test_una_edicion_remota_posterior_se_aplica(escenario):
    escenario.crear_empleado()
    escenario.ciclo()

    original = escenario.operacion_del_servidor()[0]
    actualizacion = {
        "op_id": nuevo_uuid(),
        "tabla": "empleados",
        "fila_uuid": original["fila_uuid"],
        "operacion": "upsert",
        "payload": dumps({"cargo": "Director Académico"}),
        "base_op_id": original["op_id"],
        "dispositivo": escenario.dispositivo_b,
        "usuario": "otro-puesto",
        "creado_en": (datetime.fromisoformat(original["creado_en"]) + timedelta(minutes=5)).isoformat(),
    }
    escenario.cliente_b().enviar_ops([actualizacion])

    assert escenario.ciclo()["correcto"] is True
    assert escenario.empleado_local("12345678").cargo == "Director Académico"


def test_una_edicion_remota_antigua_no_pisa_lo_local(escenario):
    escenario.crear_empleado()
    escenario.ciclo()
    original = escenario.operacion_del_servidor()[0]

    antigua = {
        "op_id": nuevo_uuid(),
        "tabla": "empleados",
        "fila_uuid": original["fila_uuid"],
        "operacion": "upsert",
        "payload": dumps({"cargo": "Secretaria"}),
        "base_op_id": original["op_id"],
        "dispositivo": escenario.dispositivo_b,
        "usuario": "otro-puesto",
        "creado_en": (
            datetime.fromisoformat(original["creado_en"]) - timedelta(hours=1)
        ).isoformat(),
    }
    escenario.cliente_b().enviar_ops([antigua])

    assert escenario.ciclo()["correcto"] is True
    assert escenario.empleado_local("12345678").cargo == "Docente"

    # El valor perdedor no se descarta: quien vio el choque fue el nodo
    # central (es el árbitro de la mezcla), así que allí queda registrado con
    # la regla aplicada, listo para exportarse y revisarse.
    conflictos = escenario.nucleo.conflictos()
    assert any(conflicto["campo"] == "cargo" for conflicto in conflictos)
    assert any(conflicto["ganador"] == "local" for conflicto in conflictos)


def test_campos_distintos_del_mismo_registro_se_fusionan(escenario):
    """Dos puestos que editan columnas distintas conservan las dos ediciones"""
    escenario.crear_empleado()
    escenario.ciclo()
    original = escenario.operacion_del_servidor()[0]

    remota = {
        "op_id": nuevo_uuid(),
        "tabla": "empleados",
        "fila_uuid": original["fila_uuid"],
        "operacion": "upsert",
        "payload": dumps({"telefono": "555-9999"}),
        "base_op_id": original["op_id"],
        "dispositivo": escenario.dispositivo_b,
        "usuario": "otro-puesto",
        "creado_en": (
            datetime.fromisoformat(original["creado_en"]) + timedelta(minutes=10)
        ).isoformat(),
    }
    escenario.cliente_b().enviar_ops([remota])
    assert escenario.ciclo()["correcto"] is True

    empleado = escenario.empleado_local("12345678")
    assert empleado.telefono == "555-9999"
    assert empleado.cargo == "Docente"


# ----------------------------------------------------------------------
# Binarios
# ----------------------------------------------------------------------
def test_el_contenido_de_un_documento_llega_al_nodo_central(escenario):
    sesion = escenario.entorno.get_session()
    try:
        empleado = EmpleadoService(sesion).crear_empleado(
            {
                "nombres": "Ana",
                "apellidos": "Gómez",
                "cedula": "12345678",
                "tipo_empleado": "docente",
                "cargo": "Docente",
                "salario_base": 1200.0,
            }
        )
        contenido = b"titulo escaneado en el puesto A"
        sesion.add(
            Documento(
                empleado_id=empleado.id,
                tipo_documento="titulo",
                titulo="Título",
                nombre_archivo="titulo.pdf",
                ruta_archivo="documents/titulo.pdf",
                contenido_binario=contenido,
            )
        )
        sesion.commit()
    finally:
        escenario.entorno.close_session(sesion)

    assert escenario.ciclo()["correcto"] is True

    # La operación viajó sin el contenido...
    sesion = escenario.entorno.new_session()
    try:
        documentos = (
            sesion.query(JournalOp).filter(JournalOp.tabla == "documentos").all()
        )
        assert documentos
        assert "__blob__" in loads(documentos[0].payload)["contenido_binario"]
    finally:
        escenario.entorno.close_session(sesion)

    # ...y el archivo llegó por el canal de binarios
    digest = hash_bytes(b"titulo escaneado en el puesto A")
    assert escenario.nucleo.leer_blob(digest) == b"titulo escaneado en el puesto A"

    sesion = escenario.entorno.new_session()
    try:
        blob = sesion.get(BlobSync, digest)
        assert blob is not None
        assert blob.estado in (BLOB_SUBIDO, BLOB_DISPONIBLE)
    finally:
        escenario.entorno.close_session(sesion)
